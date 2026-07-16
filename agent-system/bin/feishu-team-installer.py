#!/usr/bin/env python3
"""Governed installer sessions for importing selected Agent teams into Feishu."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Mapping


class InstallerError(ValueError):
    pass


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallerError(f"cannot read JSON: {path}") from exc
    if not isinstance(value, dict):
        raise InstallerError(f"JSON root must be an object: {path}")
    return value


def write_private_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(temporary, 0o600)
    except OSError:
        pass
    os.replace(temporary, path)


def catalog_file(root: Path) -> Path:
    return root / "feishu-teams" / "catalog.json"


def inventory_file(root: Path) -> Path:
    return root.parent / ".digital-office" / "feishu-bot-inventory.json"


def sessions_dir(root: Path) -> Path:
    return root / "runs" / "feishu-installer"


def load_catalog(root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    catalog = read_json(catalog_file(root))
    items = catalog.get("teams")
    if not isinstance(items, list) or not items:
        raise InstallerError("team catalog must contain a non-empty teams array")
    manifests: dict[str, dict[str, Any]] = {}
    seen_profiles: dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict) or not item.get("team_id") or not item.get("manifest"):
            raise InstallerError("each catalog team requires team_id and manifest")
        team_id = str(item["team_id"])
        if team_id in manifests:
            raise InstallerError(f"duplicate team_id: {team_id}")
        path = (catalog_file(root).parent / str(item["manifest"])).resolve()
        if path.parent != catalog_file(root).parent.resolve():
            raise InstallerError(f"manifest escapes catalog directory: {item['manifest']}")
        manifest = read_json(path)
        if manifest.get("team_id") != team_id:
            raise InstallerError(f"catalog/manifest team_id mismatch: {team_id}")
        agents = manifest.get("agents")
        if not isinstance(agents, list) or not agents:
            raise InstallerError(f"team {team_id} has no agents")
        for agent in agents:
            profile = str(agent.get("profile", "")) if isinstance(agent, dict) else ""
            agent_id = str(agent.get("agent_id", "")) if isinstance(agent, dict) else ""
            if not profile or not agent_id:
                raise InstallerError(f"team {team_id} contains an incomplete agent")
            if profile in seen_profiles:
                raise InstallerError(f"lark-cli profile {profile} is shared by {seen_profiles[profile]} and {team_id}/{agent_id}")
            seen_profiles[profile] = f"{team_id}/{agent_id}"
        manifests[team_id] = {"path": path, "manifest": manifest}
    return catalog, manifests


def load_inventory(root: Path) -> dict[str, Any]:
    path = inventory_file(root)
    if not path.exists():
        return {"version": "2.0.0", "bots": {}}
    value = read_json(path)
    if value.get("version") == "2.0.0" and isinstance(value.get("bots"), dict):
        return value
    if value.get("team_id") and isinstance(value.get("agents"), dict):
        bots = {
            f"{value['team_id']}/{agent_id}": {"team_id": value["team_id"], "agent_id": agent_id, **record}
            for agent_id, record in value["agents"].items() if isinstance(record, dict)
        }
        return {"version": "2.0.0", "bots": bots}
    raise InstallerError("unsupported Feishu Bot inventory format")


def preflight(root: Path) -> dict[str, Any]:
    node = shutil.which("node")
    npm = shutil.which("npm")
    local_lark = root / "feishu-bootstrap" / "node_modules" / ".bin" / ("lark-cli.cmd" if os.name == "nt" else "lark-cli")
    lark = str(local_lark) if local_lark.exists() else shutil.which("lark-cli") or shutil.which("lark-cli.cmd")
    sdk_package = root / "feishu-bootstrap" / "node_modules" / "@larksuiteoapi" / "node-sdk" / "package.json"
    host = "hermes" if (root.parent / "SOUL.md").exists() else "openclaw" if (root.parent / "AGENTS.md").exists() else "generic"
    node_version = ""
    node_supported = False
    if node:
        try:
            node_version = subprocess.run(
                [node, "--version"], capture_output=True, text=True, timeout=5, check=False,
            ).stdout.strip()
            match = re.fullmatch(r"v?(\d+)(?:\.\d+){1,2}", node_version)
            node_supported = bool(match and int(match.group(1)) >= 20)
        except (OSError, subprocess.SubprocessError):
            pass
    checks = {
        "agent_host": {"ready": host in {"hermes", "openclaw"}, "value": host, "required": False},
        "node": {"ready": node_supported, "value": node or "", "version": node_version, "required": True},
        "npm": {"ready": bool(npm), "value": npm or "", "required": False},
        "lark_cli": {"ready": bool(lark), "value": lark or "", "required": True},
        "feishu_sdk": {"ready": sdk_package.exists(), "value": str(sdk_package), "required": True},
    }
    blocking = [name for name, check in checks.items() if check["required"] and not check["ready"]]
    return {"ready": not blocking, "blocking": blocking, "checks": checks}


def team_catalog(root: Path) -> dict[str, Any]:
    catalog, manifests = load_catalog(root)
    inventory = load_inventory(root)
    records = inventory.get("bots", {})
    teams = []
    for item in catalog["teams"]:
        team_id = str(item["team_id"])
        manifest = manifests[team_id]["manifest"]
        roles = []
        for agent in manifest["agents"]:
            bot_key = f"{team_id}/{agent['agent_id']}"
            record = records.get(bot_key, {}) if isinstance(records, dict) else {}
            roles.append({
                "bot_key": bot_key,
                "agent_id": agent["agent_id"],
                "display_name": agent.get("display_name", agent["agent_id"]),
                "profile": agent["profile"],
                "status": "ready" if isinstance(record, dict) and record.get("status") == "ready" else "not_installed",
            })
        ready_count = sum(1 for role in roles if role["status"] == "ready")
        teams.append({**item, "agent_count": len(roles), "ready_count": ready_count, "roles": roles})
    return {
        "schema_version": "1.0", "kind": "digital-office-feishu-installer-catalog",
        "preflight": preflight(root), "inventory": str(inventory_file(root)), "teams": teams,
    }


def installation_plan(root: Path, team_ids: list[str]) -> dict[str, Any]:
    if not team_ids:
        raise InstallerError("select at least one Agent team")
    _, manifests = load_catalog(root)
    unknown = sorted(set(team_ids) - set(manifests))
    if unknown:
        raise InstallerError(f"unknown team_ids: {', '.join(unknown)}")
    inventory = load_inventory(root)
    records = inventory.get("bots", {})
    bots: list[dict[str, Any]] = []
    manifest_paths: list[str] = []
    for team_id in dict.fromkeys(team_ids):
        entry = manifests[team_id]
        manifest_paths.append(str(entry["path"]))
        for agent in entry["manifest"]["agents"]:
            bot_key = f"{team_id}/{agent['agent_id']}"
            record = records.get(bot_key, {}) if isinstance(records, dict) else {}
            bots.append({
                "bot_key": bot_key, "team_id": team_id, "agent_id": agent["agent_id"],
                "display_name": agent.get("display_name", agent["agent_id"]), "profile": agent["profile"],
                "status": "ready" if isinstance(record, dict) and record.get("status") == "ready" else "missing",
            })
    missing = [bot for bot in bots if bot["status"] == "missing"]
    return {
        "team_ids": list(dict.fromkeys(team_ids)), "manifest_paths": manifest_paths, "bots": bots,
        "bot_count": len(bots), "ready_count": len(bots) - len(missing), "missing_count": len(missing),
        "online_confirmations_required": len(missing), "requires_explicit_confirmation": True,
    }


def process_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events[-1000:]


def session_status(root: Path, session_id: str) -> dict[str, Any]:
    if not re.fullmatch(r"[a-f0-9]{32}", session_id):
        raise InstallerError("invalid installer session id")
    directory = sessions_dir(root) / session_id
    record = read_json(directory / "session.json")
    events = read_events(directory / "events.ndjson")
    event_names = [str(item.get("event", "")) for item in events]
    if "session_complete" in event_names:
        status = "complete"
    elif "failed" in event_names:
        status = "failed"
    elif process_running(int(record.get("pid", 0))):
        status = "running"
    else:
        status = "failed" if events else "starting"
    latest_authorization = None
    for index in range(len(events) - 1, -1, -1):
        candidate = events[index]
        if candidate.get("event") != "authorization_required":
            continue
        bot_key = candidate.get("bot_key")
        resolved = any(
            item.get("bot_key") == bot_key and item.get("event") in {"ready", "already_ready", "failed"}
            for item in events[index + 1:]
        )
        if not resolved:
            latest_authorization = candidate
        break
    ready_keys = {str(item.get("bot_key")) for item in events if item.get("event") in {"ready", "already_ready"}}
    failed = next((item for item in reversed(events) if item.get("event") == "failed"), None)
    return {
        **record, "status": status, "events": events, "ready_count": len(ready_keys),
        "latest_authorization": latest_authorization, "failure": failed,
    }


def start_session(
    root: Path, *, team_ids: list[str], confirmed: bool,
    notify_profile: str = "", notify_chat_id: str = "",
) -> dict[str, Any]:
    if not confirmed:
        raise InstallerError("confirmed=true is required to create Feishu applications")
    if bool(notify_profile) != bool(notify_chat_id):
        raise InstallerError("notify_profile and notify_chat_id must be supplied together")
    readiness = preflight(root)
    if not readiness["ready"]:
        raise InstallerError(f"installer preflight is blocked: {', '.join(readiness['blocking'])}")
    plan = installation_plan(root, team_ids)
    session_id = uuid.uuid4().hex
    directory = sessions_dir(root) / session_id
    directory.mkdir(parents=True, exist_ok=False)
    events = directory / "events.ndjson"
    stdout_log = directory / "stdout.log"
    stderr_log = directory / "stderr.log"
    node = str(readiness["checks"]["node"]["value"])
    command = [
        node, str(root / "bin" / "feishu-team-bootstrap.mjs"),
        "--output", str(inventory_file(root)),
        "--sdk-root", str(root / "feishu-bootstrap"),
        "--lark-cli", str(readiness["checks"]["lark_cli"]["value"]),
        "--event-file", str(events),
    ]
    for manifest in plan["manifest_paths"]:
        command.extend(["--manifest", manifest])
    if notify_profile:
        command.extend(["--notify-profile", notify_profile, "--notify-chat-id", notify_chat_id])
    command.append("--confirm-create")
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    with stdout_log.open("w", encoding="utf-8") as stdout, stderr_log.open("w", encoding="utf-8") as stderr:
        process = subprocess.Popen(
            command, cwd=str(root.parent), stdout=stdout, stderr=stderr,
            stdin=subprocess.DEVNULL, close_fds=os.name != "nt", creationflags=creationflags,
        )
    record = {
        "schema_version": "1.0", "kind": "digital-office-feishu-installer-session",
        "session_id": session_id, "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "pid": process.pid, "team_ids": plan["team_ids"], "bot_count": plan["bot_count"],
        "initial_ready_count": plan["ready_count"], "missing_count": plan["missing_count"],
        "notify_chat_configured": bool(notify_chat_id),
    }
    write_private_json(directory / "session.json", record)
    return {**record, "status": "starting", "plan": plan}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--root", help="agent-system root; defaults to this installation")
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("catalog")
    plan = commands.add_parser("plan")
    plan.add_argument("--team", action="append", default=[])
    start = commands.add_parser("start")
    start.add_argument("--team", action="append", default=[])
    start.add_argument("--notify-profile", default="")
    start.add_argument("--notify-chat-id", default="")
    start.add_argument("--confirmed", action="store_true")
    status = commands.add_parser("status")
    status.add_argument("--session", required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = Path(args.root).expanduser().resolve() if args.root else system_root()
    try:
        if args.command == "catalog":
            output = team_catalog(root)
        elif args.command == "plan":
            output = installation_plan(root, args.team)
        elif args.command == "start":
            output = start_session(
                root, team_ids=args.team, confirmed=args.confirmed,
                notify_profile=args.notify_profile, notify_chat_id=args.notify_chat_id,
            )
        else:
            output = session_status(root, args.session)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (InstallerError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
