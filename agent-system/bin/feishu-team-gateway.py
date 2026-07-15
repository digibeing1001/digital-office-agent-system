#!/usr/bin/env python3
"""Dry-run provisioning and fail-closed routing for project-scoped Feishu Agent teams."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping


PREFIX = "[DIGITAL_OFFICE_HANDOFF_V1]"
MAX_BOTS_PER_CHAT = 15
MAX_BOTS_PER_INVITE = 5


class ContractError(ValueError):
    pass


def invite_batch_sizes(bot_count: int) -> list[int]:
    """Split the actual confirmed roster by Feishu's per-request ceiling."""
    if bot_count < 1 or bot_count > MAX_BOTS_PER_CHAT:
        raise ContractError("confirmed bot count must be between 1 and 15")
    return [
        min(MAX_BOTS_PER_INVITE, bot_count - start)
        for start in range(0, bot_count, MAX_BOTS_PER_INVITE)
    ]


def load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ContractError(f"{path} must contain a JSON object")
    return value


def validate(manifest: Mapping[str, Any]) -> None:
    required = ("team_id", "project_id", "chat_id_env", "secretary_agent_id", "agents")
    missing = [key for key in required if not manifest.get(key)]
    if missing:
        raise ContractError(f"manifest missing: {', '.join(missing)}")
    agents = list(manifest["agents"])
    if not 1 <= len(agents) <= MAX_BOTS_PER_CHAT:
        raise ContractError("Feishu allows 1 to 15 bots in one chat")
    ids = [str(item.get("agent_id", "")) for item in agents]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise ContractError("agent_id values must be present and unique")
    if manifest["secretary_agent_id"] not in ids:
        raise ContractError("secretary_agent_id is not in agents")
    for item in agents:
        for key in ("profile", "app_id_env", "open_id_env"):
            if not item.get(key):
                raise ContractError(f"agent {item.get('agent_id')} missing {key}")


def _required_env(name: str, env: Mapping[str, str]) -> str:
    value = env.get(name, "")
    if not value:
        raise ContractError(f"environment variable {name} is required")
    return value


def inventory_environment(
    manifest: Mapping[str, Any], inventory: Mapping[str, Any] | None,
    base: Mapping[str, str] = os.environ,
) -> dict[str, str]:
    """Merge non-secret App/Open IDs from bootstrap inventory into runtime env."""
    result = dict(base)
    if not inventory:
        return result
    records = inventory.get("agents", {})
    if not isinstance(records, Mapping):
        raise ContractError("bot inventory agents must be an object")
    for agent in manifest.get("agents", []):
        record = records.get(agent["agent_id"], {})
        if not isinstance(record, Mapping):
            continue
        if record.get("app_id"):
            result.setdefault(agent["app_id_env"], str(record["app_id"]))
        if record.get("open_id"):
            result.setdefault(agent["open_id_env"], str(record["open_id"]))
    return result


def staffing_proposal(
    manifest: Mapping[str, Any], *, objective: str, specialists: list[str],
) -> dict[str, Any]:
    """Create the secretary-dispatcher's proposal that a human must confirm."""
    validate(manifest)
    if not objective.strip():
        raise ContractError("staffing objective is required")
    known = {item["agent_id"] for item in manifest["agents"]}
    core = [manifest["secretary_agent_id"]]
    unknown = sorted(set(specialists) - known)
    if unknown:
        raise ContractError(f"unknown specialists: {', '.join(unknown)}")
    selected_set = set(core + specialists)
    selected = [item["agent_id"] for item in manifest["agents"] if item["agent_id"] in selected_set]
    proposal = {
        "schema_version": "1.0", "kind": "feishu-team-staffing-proposal",
        "team_id": manifest["team_id"], "project_id": manifest["project_id"],
        "objective": objective.strip(), "core_agents": core, "selected_agents": selected,
        "requires_human_confirmation": True,
    }
    canonical = json.dumps(proposal, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    proposal["confirmation_token"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:40]
    return proposal


def provision_plan(
    manifest: Mapping[str, Any], env: Mapping[str, str], *, proposal: Mapping[str, Any],
    confirmation_token: str,
) -> list[list[str]]:
    """Return argv arrays only after the exact staffing proposal is confirmed."""
    validate(manifest)
    expected = staffing_proposal(
        manifest, objective=str(proposal.get("objective", "")),
        specialists=[
            str(agent_id) for agent_id in proposal.get("selected_agents", [])
            if agent_id != manifest["secretary_agent_id"]
        ],
    )
    if proposal.get("confirmation_token") != expected["confirmation_token"]:
        raise ContractError("staffing proposal was modified after it was issued")
    if not confirmation_token or confirmation_token != expected["confirmation_token"]:
        raise ContractError("the exact staffing proposal has not been confirmed")
    selected = set(expected["selected_agents"])
    agents = [item for item in manifest["agents"] if item["agent_id"] in selected]
    app_ids = [_required_env(item["app_id_env"], env) for item in agents]
    secretary = next(item for item in agents if item["agent_id"] == manifest["secretary_agent_id"])
    commands = [[
        "lark-cli", "--profile", secretary["profile"], "im", "+chat-create",
        "--name", manifest.get("chat_name", manifest["team_id"]),
        "--description", manifest.get("description", f"Project {manifest['project_id']} expert team"),
        "--bots", ",".join(app_ids[:MAX_BOTS_PER_INVITE]),
        "--type", "private", "--set-bot-manager", "--as", "bot",
    ]]
    chat_ref = f"${{{manifest['chat_id_env']}}}"
    for start in range(MAX_BOTS_PER_INVITE, len(app_ids), MAX_BOTS_PER_INVITE):
        batch = app_ids[start:start + MAX_BOTS_PER_INVITE]
        commands.append([
            "lark-cli", "--profile", secretary["profile"], "im", "chat.members", "create",
            "--chat-id", chat_ref, "--member-id-type", "app_id",
            "--data", json.dumps({"id_list": batch}, separators=(",", ":")), "--as", "bot",
        ])
    return commands


def apply_provision_plan(
    manifest: Mapping[str, Any], commands: list[list[str]], *,
    runner: Any = subprocess.run,
) -> dict[str, Any]:
    """Create the confirmed group and add selected bots; never accepts shell strings."""
    if not commands:
        raise ContractError("provision plan is empty")
    chat_id = ""
    results = []
    chat_ref = f"${{{manifest['chat_id_env']}}}"
    for index, planned in enumerate(commands):
        command = [chat_id if value == chat_ref else value for value in planned]
        if any(value == chat_ref for value in command):
            raise ContractError("chat_id was not returned by the create-chat command")
        completed = runner(command, capture_output=True, text=True, encoding="utf-8")
        if completed.returncode != 0:
            raise ContractError(f"provision command {index + 1} failed: {completed.stderr.strip()}")
        try:
            response = json.loads(completed.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise ContractError(f"provision command {index + 1} returned invalid JSON") from exc
        if index == 0:
            data = response.get("data", response)
            chat_id = str(data.get("chat_id") or data.get("chat", {}).get("chat_id") or "")
            if not chat_id:
                raise ContractError("create-chat response did not contain chat_id")
        results.append({"step": index + 1, "status": "success"})
    return {"status": "deployed", "chat_id": chat_id, "steps": results}


def build_handoff(
    manifest: Mapping[str, Any], *, sender: str, target: str, task: str,
    correlation_id: str, hop: int, visited_edges: list[str], env: Mapping[str, str],
) -> dict[str, str]:
    validate(manifest)
    by_id = {item["agent_id"]: item for item in manifest["agents"]}
    if sender == target or sender not in by_id or target not in by_id:
        raise ContractError("sender and target must be different agents in the same team")
    edge = f"{sender}->{target}"
    if edge in visited_edges:
        raise ContractError("repeated routing edge would create a loop")
    if hop < 1 or hop > int(manifest.get("policy", {}).get("max_hops", 6)):
        raise ContractError("handoff hop budget exceeded")
    open_id = _required_env(by_id[target]["open_id_env"], env)
    envelope = {
        "schema_version": "1.0", "team_id": manifest["team_id"],
        "project_id": manifest["project_id"], "from": sender, "to": target,
        "task": task, "correlation_id": correlation_id, "hop": hop,
        "visited_edges": visited_edges + [edge],
    }
    payload = json.dumps(envelope, ensure_ascii=False, separators=(",", ":"))
    return {
        "text": f'<at user_id="{open_id}">{target}</at> {PREFIX}\n{payload}',
        "idempotency_key": hashlib.sha256(payload.encode("utf-8")).hexdigest()[:40],
    }


def _mention_ids(event: Mapping[str, Any]) -> set[str]:
    result: set[str] = set()
    for mention in event.get("mentions", []) or []:
        value = mention.get("id", "") if isinstance(mention, Mapping) else ""
        if isinstance(value, Mapping):
            value = value.get("open_id", "")
        if value:
            result.add(str(value))
    return result


def _envelope(content: str) -> dict[str, Any]:
    marker = content.find(PREFIX)
    if marker < 0:
        raise ContractError("bot message is missing the typed handoff envelope")
    try:
        value = json.loads(content[marker + len(PREFIX):].strip())
    except json.JSONDecodeError as exc:
        raise ContractError("handoff envelope is invalid JSON") from exc
    if not isinstance(value, dict):
        raise ContractError("handoff envelope must be an object")
    return value


def claim_message(state_dir: str | Path, project_id: str, message_id: str) -> bool:
    """Atomically claim one delivery by creating a project-scoped marker file."""
    if not message_id:
        raise ContractError("message_id is required for deduplication")
    project = hashlib.sha256(project_id.encode("utf-8")).hexdigest()
    message = hashlib.sha256(message_id.encode("utf-8")).hexdigest()
    directory = Path(state_dir).expanduser().resolve() / project / "feishu-message-claims"
    directory.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(directory / message), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump({"message_id": message_id}, handle)
        handle.flush()
        os.fsync(handle.fileno())
    return True


def route_event(
    manifest: Mapping[str, Any], event: Mapping[str, Any], *, current_agent: str,
    state_dir: str | Path, env: Mapping[str, str],
) -> dict[str, Any]:
    try:
        validate(manifest)
        by_id = {item["agent_id"]: item for item in manifest["agents"]}
        current = by_id.get(current_agent)
        if not current:
            raise ContractError("current agent is not in this team")
        if event.get("chat_id") != _required_env(manifest["chat_id_env"], env):
            raise ContractError("event belongs to another project chat")
        if _required_env(current["open_id_env"], env) not in _mention_ids(event):
            raise ContractError("current bot was not explicitly mentioned")
        if not claim_message(state_dir, manifest["project_id"], str(event.get("message_id", ""))):
            return {"accepted": False, "reason": "duplicate_message"}
        if event.get("sender_type") == "user":
            if current_agent != manifest["secretary_agent_id"]:
                raise ContractError("human requests enter through the secretary only")
            return {"accepted": True, "reason": "human_to_secretary"}
        if event.get("sender_type") != "bot":
            raise ContractError("unsupported sender type")
        sender_map = {_required_env(item["open_id_env"], env): item["agent_id"] for item in manifest["agents"]}
        sender = sender_map.get(str(event.get("sender_id", "")))
        if not sender:
            raise ContractError("sender bot is not allowlisted")
        handoff = _envelope(str(event.get("content", "")))
        required = ("team_id", "project_id", "from", "to", "task", "correlation_id", "hop", "visited_edges")
        if any(key not in handoff for key in required):
            raise ContractError("handoff envelope is incomplete")
        if (handoff["team_id"], handoff["project_id"]) != (manifest["team_id"], manifest["project_id"]):
            raise ContractError("handoff belongs to another team or project")
        if handoff["from"] != sender or handoff["to"] != current_agent:
            raise ContractError("handoff sender or target does not match the event")
        hop = int(handoff["hop"])
        if hop < 1 or hop > int(manifest.get("policy", {}).get("max_hops", 6)):
            raise ContractError("handoff hop budget exceeded")
        edge = f"{sender}->{current_agent}"
        visited = list(handoff["visited_edges"])
        if not visited or visited[-1] != edge or visited.count(edge) != 1:
            raise ContractError("handoff route contains a repeated or inconsistent edge")
        return {"accepted": True, "reason": "bot_handoff", "envelope": handoff}
    except (ContractError, TypeError, ValueError) as exc:
        return {"accepted": False, "reason": str(exc)}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--manifest", required=True)
    result.add_argument("--inventory", help="non-secret inventory created by feishu-team-bootstrap.mjs")
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("validate")
    staffing = commands.add_parser("staffing-proposal")
    staffing.add_argument("--objective", required=True)
    staffing.add_argument("--specialist", action="append", default=[])
    provision = commands.add_parser("provision-plan")
    provision.add_argument("--staffing-file", required=True)
    provision.add_argument("--confirm-token", required=True)
    apply = commands.add_parser("provision-apply")
    apply.add_argument("--staffing-file", required=True)
    apply.add_argument("--confirm-token", required=True)
    apply.add_argument("--confirm-write", action="store_true", help="confirm external group/member writes")
    route = commands.add_parser("route-event")
    route.add_argument("--current-agent", required=True)
    route.add_argument("--event-file", required=True)
    route.add_argument("--state-dir", required=True)
    handoff = commands.add_parser("handoff-plan")
    handoff.add_argument("--from-agent", required=True)
    handoff.add_argument("--to-agent", required=True)
    handoff.add_argument("--task", required=True)
    handoff.add_argument("--correlation-id", required=True)
    handoff.add_argument("--hop", type=int, default=1)
    handoff.add_argument("--visited-edge", action="append", default=[])
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        manifest = load_json(args.manifest)
        inventory = load_json(args.inventory) if args.inventory else None
        runtime_env = inventory_environment(manifest, inventory)
        if args.command == "validate":
            validate(manifest)
            output: Any = {"valid": True, "bot_count": len(manifest["agents"])}
        elif args.command == "staffing-proposal":
            output = staffing_proposal(manifest, objective=args.objective, specialists=args.specialist)
        elif args.command in {"provision-plan", "provision-apply"}:
            proposal = load_json(args.staffing_file)
            plan = provision_plan(
                manifest, runtime_env, proposal=proposal, confirmation_token=args.confirm_token,
            )
            if args.command == "provision-apply":
                if not args.confirm_write:
                    raise ContractError("--confirm-write is required for external Feishu writes")
                output = apply_provision_plan(manifest, plan)
            else:
                selected_count = len(proposal["selected_agents"])
                output = {
                    "dry_run": True,
                    "confirmed_proposal": proposal["confirmation_token"],
                    "selected_bot_count": selected_count,
                    "batch_sizes": invite_batch_sizes(selected_count),
                    "commands": plan,
                }
        elif args.command == "route-event":
            output = route_event(manifest, load_json(args.event_file), current_agent=args.current_agent, state_dir=args.state_dir, env=runtime_env)
        else:
            output = build_handoff(
                manifest, sender=args.from_agent, target=args.to_agent, task=args.task,
                correlation_id=args.correlation_id, hop=args.hop,
                visited_edges=args.visited_edge, env=runtime_env,
            )
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0 if output.get("accepted", True) else 2
    except (ContractError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
