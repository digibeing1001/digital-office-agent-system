#!/usr/bin/env python3
"""GUI-facing control plane for the portable digital-office agent system."""

from __future__ import annotations

import argparse
import http.server
import hashlib
import math
import datetime as dt
import importlib.util
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


TEXT_EXTS = {".md", ".txt", ".json", ".csv"}
DOCX_EXTS = {".docx"}
PDF_EXTS = {".pdf"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
LOOP_STAGES = ["perceive", "plan", "execute", "reflect", "iterate"]
LOOP_STATUS_BY_STAGE = {
    "perceive": "perceiving",
    "plan": "planning",
    "execute": "executing",
    "reflect": "reflecting",
    "iterate": "iterating",
}
ITERATION_DECISION_TO_STATUS = {
    "confirm": "confirmed_for_application",
    "tune": "needs_tuning",
    "pause": "paused_by_user",
    "reject": "rejected",
}
STATUS_LABELS = {
    "received": "接收需求",
    "in_progress": "正在推动需求",
    "completed": "已完成需求",
    "downloaded_deployed": "已下载部署",
    "pending_user_confirmation": "等待用户确认",
    "confirmed_for_activation": "已确认，等待注册部署",
    "needs_tuning": "通过对话微调需求",
    "paused_by_user": "暂不处理",
    "needs_more_info": "需要补充信息",
    "rejected": "暂不受理",
    "send_failed": "发送失败",
}
TASK_STATUSES = {
    "queued",
    "running",
    "waiting_approval",
    "blocked",
    "completed",
    "failed",
    "cancelled",
}
WORKFLOW_CONTROL_ACTIONS = {"run", "pause", "stop", "resume"}
CANVAS_NODE_TYPES = {
    "start",
    "agent_task",
    "text_instruction",
    "file_ref",
    "folder_ref",
    "knowledge_scope",
    "approval_gate",
    "human_input",
    "output_artifact",
    "merge_summary",
    "condition",
    "parallel_group",
}
SIMPLE_CANVAS_NODE_TYPES = {"agent_task", "text_instruction", "file_ref", "folder_ref", "knowledge_scope", "approval_gate", "output_artifact"}
NODE_IO_TYPES = {
    "start": {"outputs": {"control"}},
    "text_instruction": {"outputs": {"instruction"}},
    "file_ref": {"outputs": {"file_reference"}},
    "folder_ref": {"outputs": {"folder_reference"}},
    "knowledge_scope": {"outputs": {"knowledge_scope"}},
    "human_input": {"outputs": {"human_input", "instruction", "file_reference"}},
    "agent_task": {"inputs": {"control", "instruction", "file_reference", "folder_reference", "knowledge_scope", "human_input", "artifact"}, "outputs": {"artifact", "report", "decision"}},
    "approval_gate": {"inputs": {"artifact", "proposal", "decision"}, "outputs": {"approved", "rejected"}},
    "output_artifact": {"inputs": {"artifact", "report", "approved", "human_input"}},
    "merge_summary": {"inputs": {"artifact", "report"}, "outputs": {"report", "artifact"}},
    "condition": {"inputs": {"decision", "artifact", "approved"}, "outputs": {"decision"}},
    "parallel_group": {"inputs": {"control", "instruction"}, "outputs": {"artifact", "report"}},
}
KNOWLEDGE_SPACE_TYPES = {"personal", "project", "team", "company", "workflow_artifacts", "shared_with_me"}
KNOWLEDGE_RESOURCE_TYPES = {"folder", "item"}
KNOWLEDGE_PERMISSIONS = {"read", "write", "manage"}
KNOWLEDGE_TARGET_TYPES = {"user", "role", "agent", "project", "workflow"}
APPROVAL_STATUSES = {"pending", "approved", "rejected", "cancelled", "expired"}
APPROVAL_DECISION_TO_STATUS = {
    "approve": "approved",
    "reject": "rejected",
    "cancel": "cancelled",
}
TENANT_ADMIN_ROLES = {"owner", "enterprise_admin"}
ROLE_ACTIONS = {
    "owner": {"*"},
    "enterprise_admin": {
        "approval.create",
        "approval.decide",
        "audit.read",
        "notification.read",
        "project.manage",
        "knowledge.manage",
        "knowledge.read",
        "release.approve",
        "support.grant",
        "task.manage",
        "task.read",
        "workflow.cancel",
        "workflow.control",
        "workflow.edit",
        "workflow.read",
        "workflow.resume",
        "workflow.retry",
        "workflow.start",
        "workbench.read",
    },
    "project_manager": {
        "agent.delegate",
        "approval.create",
        "approval.decide",
        "knowledge.manage",
        "knowledge.read",
        "notification.read",
        "task.manage",
        "task.read",
        "workflow.cancel",
        "workflow.control",
        "workflow.edit",
        "workflow.read",
        "workflow.resume",
        "workflow.retry",
        "workflow.start",
        "workbench.read",
    },
    "professional_reviewer": {
        "approval.decide",
        "knowledge.read",
        "notification.read",
        "regulated_output.approve",
        "task.read",
        "workflow.read",
        "workbench.read",
    },
    "member": {
        "agent.delegate",
        "approval.create",
        "knowledge.read",
        "notification.read",
        "task.read",
        "workflow.read",
        "workflow.start",
        "workbench.read",
    },
    "viewer": {"knowledge.read", "notification.read", "task.read", "workflow.read", "workbench.read"},
}
ONBOARDING_FIELDS = [
    "assistant_style",
    "address_style",
    "language",
    "initiative_level",
    "pushback_style",
    "approval_strictness",
    "memory_mode",
    "work_mode",
]
ONBOARDING_OUTPUTS = {
    "preferences_json": "settings/user-preferences.json",
    "preferences_markdown": "settings/user-preferences.md",
}


def maybe_reexec_venv() -> None:
    if os.environ.get("OFFICE_SYSTEM_NO_VENV"):
        return
    script_root = Path(__file__).resolve().parent.parent
    venv_python = script_root / ".venv" / "bin" / "python"
    if not venv_python.exists():
        return
    if Path(sys.executable).resolve() == venv_python.resolve():
        return
    os.execv(str(venv_python), [str(venv_python), __file__, *sys.argv[1:]])


maybe_reexec_venv()


def system_root() -> Path:
    configured = os.environ.get("DIGITAL_OFFICE_SYSTEM_HOME")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parent.parent


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff._-]+", "-", value)
    value = value.strip("-._")
    return value or uuid.uuid4().hex[:8]


SAFE_COMPONENT_RE = re.compile(r"^[A-Za-z0-9_\u4e00-\u9fff][A-Za-z0-9._\-\u4e00-\u9fff]{0,127}$")
SAFE_CLAIM_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,256}$")


def safe_component(value: str, label: str) -> str:
    value = str(value or "").strip()
    if not SAFE_COMPONENT_RE.fullmatch(value) or "/" in value or "\\" in value or value in {".", ".."}:
        print(f"office-system: invalid {label}: {value!r}", file=sys.stderr)
        raise SystemExit(2)
    return value


def safe_claim(value: str | None, label: str, required: bool = True) -> str:
    value = str(value or "").strip()
    if not value and not required:
        return ""
    if not SAFE_CLAIM_RE.fullmatch(value):
        print(f"office-system: invalid {label}: {value!r}", file=sys.stderr)
        raise SystemExit(2)
    return value


def registered_agent(root: Path, value: str) -> str:
    agent = safe_component(value, "agent id")
    registry = read_json(root / "agents.registry.json")
    if agent not in registry.get("agents", {}):
        print(f"office-system: unknown agent id: {agent}", file=sys.stderr)
        raise SystemExit(2)
    return agent


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with tmp.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def append_jsonl(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_log(root: Path, event: dict[str, Any]) -> None:
    event = {"time": now_iso(), **event}
    log = root / "logs" / "office-system.jsonl"
    append_jsonl(log, event)


def onboarding_presets(root: Path) -> dict[str, Any]:
    return read_json(root / "onboarding.presets.json")


def onboarding_preferences_path(root: Path) -> Path:
    return root / ONBOARDING_OUTPUTS["preferences_json"]


def onboarding_preferences_markdown_path(root: Path) -> Path:
    return root / ONBOARDING_OUTPUTS["preferences_markdown"]


def current_onboarding_preferences(root: Path) -> dict[str, Any] | None:
    path = onboarding_preferences_path(root)
    if not path.exists():
        return None
    return read_json(path)


def validate_onboarding_choices(presets: dict[str, Any], choices: dict[str, str]) -> None:
    fields = presets.get("fields", {})
    for field in ONBOARDING_FIELDS:
        if field not in fields:
            print(f"office-system: onboarding presets missing field: {field}", file=sys.stderr)
            raise SystemExit(2)
        value = choices.get(field)
        if value not in (fields.get(field, {}).get("choices") or {}):
            print(f"office-system: invalid onboarding choice for {field}: {value!r}", file=sys.stderr)
            raise SystemExit(2)


def choice_summary(presets: dict[str, Any], field: str, value: str) -> dict[str, str]:
    option = presets["fields"][field]["choices"][value]
    return {
        "field": field,
        "value": value,
        "label": option.get("label", value),
        "description": option.get("description", ""),
    }


def render_onboarding_markdown(preferences: dict[str, Any]) -> str:
    choices = preferences.get("choices", {})
    summaries = preferences.get("choice_summaries", [])
    lines = [
        "# Digital Office User Preferences",
        "",
        "This file is generated by the GUI onboarding or settings flow. It is local runtime state and must not be committed to the public repository.",
        "",
        "## Identity",
        "",
        f"- Tenant: {preferences.get('tenant_id', '') or 'default'}",
        f"- User: {preferences.get('user_id', '') or 'default'}",
        f"- Company: {preferences.get('company_name', '') or 'not set'}",
        f"- Secretary display name: {preferences.get('secretary_name', '') or 'Digital Office Secretary'}",
        "",
        "## Selected Behavior",
        "",
    ]
    for item in summaries:
        lines.append(f"- {item['field']}: {item['label']} ({item['value']})")
        if item.get("description"):
            lines.append(f"  - {item['description']}")
    lines.extend(
        [
            "",
            "## Runtime Instruction",
            "",
            "- Treat these choices as user preferences, not immutable system law.",
            "- Safety, authorization, approval, knowledge-source priority, and production harness gates override persona preferences.",
            "- If the user changes preferences in the GUI, reload this file before continuing the conversation.",
            "- Do not infer personal preferences that were not selected or explicitly confirmed by the user.",
            "",
            "## Compact Summary",
            "",
            f"- assistant_style: {choices.get('assistant_style')}",
            f"- address_style: {choices.get('address_style')}",
            f"- language: {choices.get('language')}",
            f"- initiative_level: {choices.get('initiative_level')}",
            f"- pushback_style: {choices.get('pushback_style')}",
            f"- approval_strictness: {choices.get('approval_strictness')}",
            f"- memory_mode: {choices.get('memory_mode')}",
            f"- work_mode: {choices.get('work_mode')}",
        ]
    )
    tone_note = preferences.get("tone_note", "")
    if tone_note:
        lines.extend(["", "## User Tone Note", "", tone_note])
    return "\n".join(lines) + "\n"


def onboarding_options(args: argparse.Namespace) -> int:
    root = system_root()
    presets = onboarding_presets(root)
    current = current_onboarding_preferences(root)
    agents = agent_summaries(root)
    projects = project_summaries(root, 1000)
    payload = {
        "presets": presets,
        "current": current,
        "configured": current is not None,
        "outputs": ONBOARDING_OUTPUTS,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def onboarding_status(args: argparse.Namespace) -> int:
    root = system_root()
    current = current_onboarding_preferences(root)
    payload = {
        "configured": current is not None,
        "preferences_json": str(onboarding_preferences_path(root)),
        "preferences_markdown": str(onboarding_preferences_markdown_path(root)),
        "preferences": current or {},
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if current is not None else 1


def onboarding_apply(args: argparse.Namespace) -> int:
    if not args.confirmed:
        print("office-system: preference changes require --confirmed after GUI user review", file=sys.stderr)
        return 2
    root = system_root()
    presets = onboarding_presets(root)
    defaults = presets.get("default_choices", {})
    current = current_onboarding_preferences(root) or {}
    current_choices = current.get("choices", {})
    choices = {
        field: getattr(args, field.replace("-", "_"), None) or current_choices.get(field) or defaults.get(field)
        for field in ONBOARDING_FIELDS
    }
    validate_onboarding_choices(presets, choices)
    preferences = {
        "version": "1.0.0",
        "kind": "digital-office-user-preferences",
        "configured": True,
        "configured_at": current.get("configured_at") or now_iso(),
        "updated_at": now_iso(),
        "tenant_id": safe_claim(args.tenant or current.get("tenant_id") or "default", "tenant", required=False),
        "user_id": safe_claim(args.user or current.get("user_id") or "default", "user", required=False),
        "company_name": safe_claim(args.company_name if args.company_name is not None else current.get("company_name", ""), "company name", required=False),
        "secretary_name": safe_claim(args.secretary_name or current.get("secretary_name") or "Digital Office Secretary", "secretary name"),
        "tone_note": safe_claim(args.tone_note if args.tone_note is not None else current.get("tone_note", ""), "tone note", required=False),
        "choices": choices,
        "choice_summaries": [choice_summary(presets, field, choices[field]) for field in ONBOARDING_FIELDS],
        "source": getattr(args, "preference_source", "gui_first_run_onboarding"),
        "outputs": ONBOARDING_OUTPUTS,
    }
    write_json(onboarding_preferences_path(root), preferences)
    write_text(onboarding_preferences_markdown_path(root), render_onboarding_markdown(preferences))
    append_log(root, {"event": "preference_update", "tenant": preferences["tenant_id"], "user": preferences["user_id"], "source": preferences["source"]})
    print(json.dumps(preferences, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def add_preferences_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--tenant")
    parser.add_argument("--user")
    parser.add_argument("--company-name")
    parser.add_argument("--secretary-name")
    parser.add_argument("--assistant-style")
    parser.add_argument("--address-style")
    parser.add_argument("--language")
    parser.add_argument("--initiative-level")
    parser.add_argument("--pushback-style")
    parser.add_argument("--approval-strictness")
    parser.add_argument("--memory-mode")
    parser.add_argument("--work-mode")
    parser.add_argument("--tone-note")
    parser.add_argument("--confirmed", action="store_true")


def read_last_jsonl(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    last = ""
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                last = line
    if not last:
        return None
    try:
        return json.loads(last)
    except json.JSONDecodeError:
        return None


def append_audit_event(
    root: Path,
    event_type: str,
    *,
    actor_id: str = "",
    actor_role: str = "",
    tenant_id: str = "",
    deployment_id: str = "",
    project_id: str = "",
    agent_id: str = "",
    resource_type: str = "",
    resource_id: str = "",
    workflow_run_id: str = "",
    task_id: str = "",
    approval_id: str = "",
    outcome: str = "recorded",
    reason: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path = root / "logs" / "audit-events.jsonl"
    previous = read_last_jsonl(path)
    event = {
        "version": "1.0.0",
        "kind": "digital-office-audit-event",
        "event_id": f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}",
        "time": now_iso(),
        "event": event_type,
        "actor": {"user_id": actor_id, "role": actor_role},
        "tenant_id": tenant_id,
        "deployment_id": deployment_id,
        "project_id": project_id,
        "agent_id": agent_id,
        "resource": {"type": resource_type, "id": resource_id},
        "links": {
            "workflow_run_id": workflow_run_id,
            "task_id": task_id,
            "approval_id": approval_id,
        },
        "outcome": outcome,
        "reason": reason,
        "extra": extra or {},
        "previous_event_hash": (previous or {}).get("event_hash", ""),
    }
    encoded = json.dumps(event, ensure_ascii=False, sort_keys=True).encode("utf-8")
    event["event_hash"] = hashlib.sha256(encoded).hexdigest()
    append_jsonl(path, event)
    append_log(root, {"event": "audit_event", "audit_event": event_type, "event_id": event["event_id"], "outcome": outcome})
    return event


def notification_path(root: Path, notification_id: str) -> Path:
    return root / "notifications" / f"{safe_component(notification_id, 'notification id')}.json"


def emit_notification(
    root: Path,
    *,
    user_id: str,
    title: str,
    body: str,
    topic: str,
    resource_type: str,
    resource_id: str,
    severity: str = "info",
) -> dict[str, Any]:
    notification_id = f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    record = {
        "version": "1.0.0",
        "kind": "digital-office-notification",
        "notification_id": notification_id,
        "user_id": safe_claim(user_id, "notification user", required=False),
        "title": safe_claim(title, "notification title"),
        "body": body,
        "topic": safe_component(topic, "notification topic"),
        "resource_type": safe_component(resource_type, "notification resource type"),
        "resource_id": safe_claim(resource_id, "notification resource id", required=False),
        "severity": safe_component(severity, "notification severity"),
        "status": "unread",
        "created_at": now_iso(),
    }
    write_json(notification_path(root, notification_id), record)
    append_log(root, {"event": "notification_created", "notification_id": notification_id, "topic": topic, "user_id": record["user_id"]})
    return record


def read_records(directory: Path, kind: str | None = None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not directory.exists():
        return records
    for path in sorted(directory.glob("*.json")):
        try:
            data = read_json(path)
        except Exception:
            continue
        if kind and data.get("kind") != kind:
            continue
        records.append(data)
    records.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
    return records


def find_by_idempotency(root: Path, directory: str, key: str | None) -> dict[str, Any] | None:
    if not key:
        return None
    for record in read_records(root / directory):
        if record.get("idempotency_key") == key:
            return record
    return None


def task_path(root: Path, task_id: str) -> Path:
    return root / "tasks" / f"{safe_component(task_id, 'task id')}.json"


def approval_path(root: Path, approval_id: str) -> Path:
    return root / "approvals" / f"{safe_component(approval_id, 'approval id')}.json"


def load_task(root: Path, task_id: str) -> dict[str, Any]:
    path = task_path(root, task_id)
    if not path.exists():
        print(f"office-system: task not found: {task_id}", file=sys.stderr)
        raise SystemExit(2)
    return read_json(path)


def load_approval(root: Path, approval_id: str) -> dict[str, Any]:
    path = approval_path(root, approval_id)
    if not path.exists():
        print(f"office-system: approval not found: {approval_id}", file=sys.stderr)
        raise SystemExit(2)
    return read_json(path)


def update_task_status(root: Path, task_id: str, status: str, *, message: str = "", actor_id: str = "", actor_role: str = "") -> dict[str, Any]:
    status = safe_component(status, "task status")
    if status not in TASK_STATUSES:
        print(f"office-system: invalid task status: {status}", file=sys.stderr)
        raise SystemExit(2)
    task = load_task(root, task_id)
    task["status"] = status
    task["updated_at"] = now_iso()
    task.setdefault("history", []).append({"time": task["updated_at"], "status": status, "message": message, "actor_id": actor_id, "actor_role": actor_role})
    write_json(task_path(root, task_id), task)
    return task


def project_path(root: Path, project: str) -> Path:
    return root / "projects" / safe_component(project, "project id")


def ensure_project(root: Path, project: str) -> Path:
    path = project_path(root, project)
    if not (path / "project.json").exists():
        print(f"office-system: project not found: {project}", file=sys.stderr)
        raise SystemExit(2)
    return path


def load_project_record(root: Path, project: str) -> dict[str, Any] | None:
    if not project:
        return None
    project_dir = ensure_project(root, project)
    return read_json(project_dir / "project.json")


def project_member(project_data: dict[str, Any] | None, user_id: str) -> dict[str, Any] | None:
    if not project_data:
        return None
    for member in project_data.get("human_members", []) or []:
        if member.get("user_id") == user_id and member.get("status", "active") == "active":
            return member
    return None


def role_allows_action(role: str, action: str) -> bool:
    allowed = ROLE_ACTIONS.get(role, set())
    return "*" in allowed or action in allowed


def compute_authorization_decision(
    root: Path,
    *,
    tenant_id: str,
    deployment_id: str,
    user_id: str,
    user_role: str,
    action: str,
    resource_type: str,
    resource_id: str,
    project_id: str = "",
    agent_id: str = "",
    workflow_run_id: str = "",
    reason: str = "",
    audit: bool = True,
) -> dict[str, Any]:
    tenant_id = safe_claim(tenant_id, "tenant id")
    deployment_id = safe_claim(deployment_id, "deployment id")
    user_id = safe_claim(user_id, "user id")
    user_role = safe_component(user_role, "user role")
    action = safe_claim(action, "action")
    resource_type = safe_component(resource_type, "resource type")
    resource_id = safe_claim(resource_id, "resource id")
    project_id = safe_component(project_id, "project id") if project_id else ""
    agent_id = registered_agent(root, agent_id) if agent_id else ""
    workflow_run_id = safe_claim(workflow_run_id, "workflow run id", required=False)

    reasons: list[str] = []
    project_data = load_project_record(root, project_id) if project_id else None
    if not role_allows_action(user_role, action):
        reasons.append(f"role {user_role} cannot perform {action}")

    members = (project_data or {}).get("human_members", []) if project_data else []
    if project_id and members and user_role not in TENANT_ADMIN_ROLES:
        member = project_member(project_data, user_id)
        if not member:
            reasons.append("user is not an active project member")
        elif member.get("role") and member.get("role") != user_role:
            reasons.append("user role claim does not match project membership")

    if action in {"workflow.start", "agent.delegate"} and project_data and agent_id:
        roster = project_data.get("agent_roster", []) or []
        global_intake_agent = action == "workflow.start" and agent_id == "secretary"
        if agent_id not in roster and not global_intake_agent:
            reasons.append("agent is not on the project roster")

    if action == "regulated_output.approve" and user_role != "professional_reviewer":
        reasons.append("regulated outputs require professional_reviewer approval")

    allowed = not reasons
    decision = {
        "version": "1.0.0",
        "kind": "digital-office-authorization-decision",
        "decision_id": f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}",
        "allowed": allowed,
        "outcome": "allow" if allowed else "deny",
        "reasons": reasons,
        "tenant_id": tenant_id,
        "deployment_id": deployment_id,
        "user_id": user_id,
        "user_role": user_role,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "project_id": project_id,
        "agent_id": agent_id,
        "workflow_run_id": workflow_run_id,
        "reason": reason,
        "created_at": now_iso(),
    }
    if audit:
        event = append_audit_event(
            root,
            "authorization_decision",
            actor_id=user_id,
            actor_role=user_role,
            tenant_id=tenant_id,
            deployment_id=deployment_id,
            project_id=project_id,
            agent_id=agent_id,
            resource_type=resource_type,
            resource_id=resource_id,
            workflow_run_id=workflow_run_id,
            outcome=decision["outcome"],
            reason="; ".join(reasons) if reasons else reason,
            extra={"action": action, "decision_id": decision["decision_id"]},
        )
        decision["audit_event_id"] = event["event_id"]
    return decision


def copy_template_project(root: Path, project_id: str, name: str, agents: list[str], schedule: str) -> Path:
    template = root / "projects" / "_template"
    project_id = safe_component(project_id, "project id")
    target = project_path(root, project_id)
    if target.exists():
        print(f"office-system: project already exists: {project_id}", file=sys.stderr)
        raise SystemExit(2)
    shutil.copytree(template, target)
    data = read_json(target / "project.json")
    data.update(
        {
            "project_id": project_id,
            "name": name,
            "status": "active",
            "created_at": now_iso(),
        }
    )
    if agents:
        data["agent_roster"] = agents
    data.setdefault("methodology_promotion", {})["schedule"] = schedule
    write_json(target / "project.json", data)
    return target


def entry_root(root: Path, scope: str, project: str | None) -> Path:
    if scope == "company":
        return root / "knowledge" / "company" / "entries"
    if not project:
        print("office-system: --project is required for project knowledge", file=sys.stderr)
        raise SystemExit(2)
    return ensure_project(root, project) / "knowledge" / "entries"


def classify_file(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in TEXT_EXTS:
        return "text"
    if ext in DOCX_EXTS:
        return "word"
    if ext in PDF_EXTS:
        return "pdf"
    if ext in IMAGE_EXTS:
        return "image"
    return "binary"


def extract_text_file(source: Path, target: Path) -> tuple[str, str]:
    try:
        text = source.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = source.read_text(encoding="utf-8", errors="replace")
    write_text(target, text)
    return "local_extracted", "python_stdlib"


def extract_docx(source: Path, target: Path) -> tuple[str, str]:
    try:
        import docx  # type: ignore

        document = docx.Document(str(source))
        text_parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
        for table in document.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    text_parts.append(" | ".join(cells))
        write_text(target, "\n\n".join(text_parts).strip() + "\n")
        return "local_extracted", "python_docx"
    except Exception:
        pass

    paragraphs: list[str] = []
    try:
        with zipfile.ZipFile(source) as archive:
            xml = archive.read("word/document.xml")
        tree = ElementTree.fromstring(xml)
        namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        for para in tree.iter(f"{namespace}p"):
            chunks = [node.text for node in para.iter(f"{namespace}t") if node.text]
            if chunks:
                paragraphs.append("".join(chunks))
    except Exception as exc:
        write_text(target.with_name("extraction-error.txt"), f"docx extraction failed: {exc}\n")
        return "pending_extraction", "python_stdlib_zip_xml"
    write_text(target, "\n\n".join(paragraphs).strip() + "\n")
    return "local_extracted", "python_stdlib_zip_xml"


def extract_pdf(source: Path, target: Path) -> tuple[str, str]:
    tool = shutil.which("pdftotext")
    if tool:
        proc = subprocess.run([tool, str(source), "-"], text=True, capture_output=True)
        if proc.returncode == 0:
            write_text(target, proc.stdout)
            return "local_extracted", "poppler_pdftotext"

    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(source))
        pages = []
        for index, page in enumerate(reader.pages, start=1):
            pages.append(f"\n\n--- page {index} ---\n\n{page.extract_text() or ''}")
        write_text(target, "\n".join(pages).strip() + "\n")
        return "local_extracted", "pypdf"
    except Exception as exc:
        write_text(target.with_name("README.md"), f"PDF text extraction pending or failed: {exc}\n")
        return "pending_local_model_install", "poppler_pdftotext_or_pypdf"


def extract_image_rapidocr(source: Path, target: Path) -> tuple[str, str] | None:
    try:
        from rapidocr_onnxruntime import RapidOCR  # type: ignore
    except Exception:
        return None
    try:
        engine = RapidOCR()
        result, _ = engine(str(source))
        lines = []
        for item in result or []:
            text = item[1] if len(item) > 1 else ""
            score = item[2] if len(item) > 2 else ""
            if text:
                lines.append(f"{text}\t{score}")
        write_text(target, "\n".join(lines).strip() + "\n")
        return "local_extracted", "rapidocr_onnxruntime"
    except Exception as exc:
        write_text(target.with_name("rapidocr-error.txt"), f"rapidocr failed: {exc}\n")
        return None


def extract_image_ocr(source: Path, target: Path) -> tuple[str, str]:
    rapid = extract_image_rapidocr(source, target)
    if rapid:
        return rapid

    tool = shutil.which("tesseract")
    if not tool:
        write_text(
            target.with_name("README.md"),
            "Image OCR pending. Install base-ocr-python for RapidOCR or base-ocr for Tesseract OCR.\n",
        )
        return "pending_local_model_install", "rapidocr_or_tesseract"
    proc = subprocess.run([tool, str(source), "stdout", "-l", "eng+chi_sim"], text=True, capture_output=True)
    if proc.returncode != 0:
        write_text(target.with_name("ocr-error.txt"), proc.stderr or "tesseract failed\n")
        return "pending_extraction", "tesseract_cli"
    write_text(target, proc.stdout)
    return "local_extracted", "tesseract_cli"


def run_extraction(source: Path, extracted_dir: Path, kind: str) -> tuple[str, str]:
    extracted_dir.mkdir(parents=True, exist_ok=True)
    target = extracted_dir / "text.md"
    if kind == "text":
        return extract_text_file(source, target)
    if kind == "word" and source.suffix.lower() == ".docx":
        return extract_docx(source, target)
    if kind == "pdf":
        return extract_pdf(source, target)
    if kind == "image":
        return extract_image_ocr(source, extracted_dir / "ocr.txt")
    write_text(extracted_dir / "README.md", f"No local extractor registered for {source.suffix}.\n")
    return "pending_extraction", "none"


def add_file_entry(args: argparse.Namespace) -> int:
    root = system_root()
    source = Path(args.file).expanduser().resolve()
    if not source.exists():
        print(f"office-system: file not found: {source}", file=sys.stderr)
        return 2
    title = args.title or source.stem
    entry_id = f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{slugify(title)}"
    base = entry_root(root, args.scope, args.project) / entry_id
    source_dir = base / "source"
    extracted_dir = base / "extracted"
    source_dir.mkdir(parents=True, exist_ok=True)
    copied = source_dir / source.name
    shutil.copy2(source, copied)

    kind = args.kind or classify_file(source)
    status, extractor = run_extraction(copied, extracted_dir, kind)
    review_status = "pending_review" if status == "local_extracted" else status
    entry = {
        "version": "1.0.0",
        "entry_id": entry_id,
        "scope": args.scope,
        "project_id": args.project,
        "title": title,
        "kind": kind,
        "mime_type": mimetypes.guess_type(source.name)[0],
        "source_file": str(copied.relative_to(root)),
        "extracted_dir": str(extracted_dir.relative_to(root)),
        "status": review_status,
        "extractor": extractor,
        "created_at": now_iso(),
        "agent_readable": args.approve,
        "notes": args.notes or "",
    }
    if args.approve:
        entry["status"] = "approved_for_agent_use"
    write_json(base / "entry.json", entry)
    append_log(root, {"event": "knowledge_add_file", "entry_id": entry_id, "scope": args.scope, "project": args.project})
    print(json.dumps(entry, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def add_text_entry(args: argparse.Namespace) -> int:
    root = system_root()
    body = args.body if args.body is not None else sys.stdin.read()
    title = args.title
    entry_id = f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{slugify(title)}"
    base = entry_root(root, args.scope, args.project) / entry_id
    write_text(base / "source" / "entry.md", body.rstrip() + "\n")
    write_text(base / "extracted" / "text.md", body.rstrip() + "\n")
    entry = {
        "version": "1.0.0",
        "entry_id": entry_id,
        "scope": args.scope,
        "project_id": args.project,
        "title": title,
        "kind": "text",
        "source_file": str((base / "source" / "entry.md").relative_to(root)),
        "extracted_dir": str((base / "extracted").relative_to(root)),
        "status": "approved_for_agent_use" if args.approve else "pending_review",
        "extractor": "gui_text_entry",
        "created_at": now_iso(),
        "agent_readable": args.approve,
    }
    write_json(base / "entry.json", entry)
    append_log(root, {"event": "knowledge_add_text", "entry_id": entry_id, "scope": args.scope, "project": args.project})
    print(json.dumps(entry, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def add_rule(args: argparse.Namespace) -> int:
    root = system_root()
    body = args.body if args.body is not None else sys.stdin.read()
    filename = f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{slugify(args.title)}.md"
    if args.scope == "global":
        target = root / "rules" / "global" / filename
    elif args.scope == "agent":
        if not args.agent:
            print("office-system: --agent is required for agent rule", file=sys.stderr)
            return 2
        agent = registered_agent(root, args.agent)
        target = root / "rules" / "agents" / f"{agent}.md"
        body = f"\n\n## {args.title}\n\n{body.rstrip()}\n"
        if target.exists():
            target.write_text(target.read_text(encoding="utf-8") + body, encoding="utf-8")
            print(str(target))
            return 0
    else:
        if not args.project:
            print("office-system: --project is required for project rule", file=sys.stderr)
            return 2
        target = ensure_project(root, args.project) / "rules" / filename
    text = f"# {args.title}\n\n{body.rstrip()}\n"
    write_text(target, text)
    append_log(root, {"event": "rule_add", "scope": args.scope, "target": str(target.relative_to(root))})
    print(str(target))
    return 0


def iter_entry_manifests(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted(path.glob("*/entry.json"))


def load_entries(root: Path, base: Path) -> list[dict[str, Any]]:
    entries = []
    for manifest in iter_entry_manifests(base):
        try:
            entry = read_json(manifest)
            entry["_manifest"] = str(manifest.relative_to(root))
            entries.append(entry)
        except Exception:
            continue
    return entries


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]", text.lower())
    return [word for word in words if word.strip()]


def chunk_text(text: str, size: int = 1200, overlap: int = 180) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def extracted_text_for_entry(root: Path, entry: dict[str, Any]) -> str:
    extracted = root / str(entry.get("extracted_dir", ""))
    if not extracted.exists():
        return ""
    parts: list[str] = []
    for path in sorted(extracted.glob("*.md")) + sorted(extracted.glob("*.txt")):
        try:
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
    return "\n\n".join(parts)


def rag_entry_base(root: Path, scope: str, project: str | None) -> Path:
    if scope == "company":
        return root / "knowledge" / "company" / "entries"
    if not project:
        print("office-system: --project is required for project RAG", file=sys.stderr)
        raise SystemExit(2)
    return ensure_project(root, project) / "knowledge" / "entries"


def rag_index_dir(root: Path, scope: str, project: str | None) -> Path:
    if scope == "company":
        return root / "knowledge" / "company" / "index"
    if not project:
        print("office-system: --project is required for project RAG", file=sys.stderr)
        raise SystemExit(2)
    return ensure_project(root, project) / "knowledge" / "index"


def try_embed(texts: list[str], model_name: str) -> tuple[list[list[float]] | None, str]:
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except Exception:
        return None, "sentence_transformers_not_installed"
    try:
        model = SentenceTransformer(model_name)
        vectors = model.encode(texts, normalize_embeddings=True).tolist()
        return vectors, model_name
    except Exception as exc:
        return None, f"embedding_failed:{exc}"


def rag_index(args: argparse.Namespace) -> int:
    root = system_root()
    entries = load_entries(root, rag_entry_base(root, args.scope, args.project))
    records: list[dict[str, Any]] = []
    for entry in entries:
        if entry.get("status") == "archived":
            continue
        if not args.include_pending and not entry.get("agent_readable") and entry.get("status") != "approved_for_agent_use":
            continue
        text = extracted_text_for_entry(root, entry)
        for index, chunk in enumerate(chunk_text(text, args.chunk_chars, args.chunk_overlap), start=1):
            records.append(
                {
                    "chunk_id": f"{entry.get('entry_id')}::{index}",
                    "entry_id": entry.get("entry_id"),
                    "title": entry.get("title"),
                    "scope": args.scope,
                    "project_id": args.project,
                    "source_file": entry.get("source_file"),
                    "status": entry.get("status"),
                    "text": chunk,
                    "tokens": tokenize(chunk),
                }
            )

    mode = args.mode
    embedding_status = "not_requested"
    if records and mode in {"auto", "embedding"}:
        vectors, embedding_status = try_embed([record["text"] for record in records], args.embedding_model)
        if vectors:
            for record, vector in zip(records, vectors):
                record["embedding"] = vector
            mode = "embedding"
        elif args.mode == "embedding":
            print(f"office-system: embedding index failed: {embedding_status}", file=sys.stderr)
            return 1
        else:
            mode = "lexical"
    elif mode == "auto":
        mode = "lexical"

    target_dir = rag_index_dir(root, args.scope, args.project)
    target_dir.mkdir(parents=True, exist_ok=True)
    index_file = target_dir / "index.jsonl"
    with index_file.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    meta = {
        "version": "1.0.0",
        "scope": args.scope,
        "project_id": args.project,
        "mode": mode,
        "embedding_model": args.embedding_model if mode == "embedding" else None,
        "embedding_status": embedding_status,
        "chunks": len(records),
        "created_at": now_iso(),
    }
    write_json(target_dir / "index.meta.json", meta)
    append_log(root, {"event": "rag_index", "scope": args.scope, "project": args.project, "chunks": len(records), "mode": mode})
    print(json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def lexical_score(query_tokens: list[str], record_tokens: list[str]) -> float:
    if not query_tokens or not record_tokens:
        return 0.0
    counts: dict[str, int] = {}
    for token in record_tokens:
        counts[token] = counts.get(token, 0) + 1
    score = 0.0
    for token in query_tokens:
        score += math.log1p(counts.get(token, 0))
    return score / math.sqrt(len(record_tokens))


def dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def rag_search(args: argparse.Namespace) -> int:
    root = system_root()
    index_dir = rag_index_dir(root, args.scope, args.project)
    index_file = index_dir / "index.jsonl"
    if not index_file.exists():
        print(f"office-system: RAG index not found: {index_file}", file=sys.stderr)
        return 2
    meta = read_json(index_dir / "index.meta.json") if (index_dir / "index.meta.json").exists() else {}
    records = []
    with index_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))

    scored: list[tuple[float, dict[str, Any]]] = []
    if meta.get("mode") == "embedding":
        vectors, status = try_embed([args.query], meta.get("embedding_model") or args.embedding_model)
        if vectors:
            query_vector = vectors[0]
            for record in records:
                vector = record.get("embedding")
                if vector:
                    scored.append((dot(query_vector, vector), record))
        else:
            print(f"office-system: embedding search unavailable, falling back to lexical: {status}", file=sys.stderr)

    if not scored:
        query_tokens = tokenize(args.query)
        scored = [(lexical_score(query_tokens, record.get("tokens", [])), record) for record in records]

    results = [
        {
            "score": score,
            "chunk_id": record.get("chunk_id"),
            "entry_id": record.get("entry_id"),
            "title": record.get("title"),
            "source_file": record.get("source_file"),
            "status": record.get("status"),
            "text": record.get("text"),
        }
        for score, record in sorted(scored, key=lambda item: item[0], reverse=True)[: args.limit]
        if score > 0
    ]
    print(json.dumps({"query": args.query, "scope": args.scope, "project_id": args.project, "results": results}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def context(args: argparse.Namespace) -> int:
    root = system_root()
    agent = args.agent
    project = args.project
    project_dir = ensure_project(root, project) if project else None
    project_data = read_json(project_dir / "project.json") if project_dir else None

    print("# Digital Office Agent Context")
    print()
    print("## Priority")
    print("1. Current user task and explicit project selection")
    print("2. System bootstrap and company global rules")
    print("3. Active project rules and project knowledge source files")
    print("4. Agent-specific rules")
    print("5. Company global knowledge and approved methodologies")
    print("6. Licensed industry references mounted by entitlement")
    print("7. KeyMemory project relay snapshots, preferences, approved summaries, and retrieval pointers")
    print()
    print("Fact authority: project knowledge > company global knowledge > licensed industry reference > KeyMemory.")
    print("Handoff authority: current task > KeyMemory project relay > project latest decisions > company methods.")
    print("If KeyMemory or licensed references conflict with source-backed project or company knowledge, source-backed knowledge wins.")
    print()

    preferences = current_onboarding_preferences(root)
    print("## User Preferences")
    if preferences:
        print(f"- source: {preferences.get('source', 'unknown')}")
        print(f"- secretary_name: {preferences.get('secretary_name')}")
        print(f"- company_name: {preferences.get('company_name') or 'not set'}")
        for field in ONBOARDING_FIELDS:
            print(f"- {field}: {preferences.get('choices', {}).get(field)}")
    else:
        print("- not configured; use the neutral default behavior and let the GUI show global settings.")
    print("- Preferences do not override safety, authorization, approval, knowledge authority, or production harness gates.")
    print()

    print("## Rule Layers")
    for path in sorted((root / "rules" / "global").glob("*.md")):
        print(f"- company/global: {path.relative_to(root)}")
    if project_dir:
        for path in sorted((project_dir / "rules").glob("*.md")):
            print(f"- project/{project}: {path.relative_to(root)}")
    if agent:
        agent_rule = root / "rules" / "agents" / f"{agent}.md"
        if agent_rule.exists():
            print(f"- agent/{agent}: {agent_rule.relative_to(root)}")
    print()

    if project_data:
        print("## Project")
        print(f"- id: {project_data.get('project_id')}")
        print(f"- name: {project_data.get('name')}")
        print(f"- status: {project_data.get('status')}")
        print(f"- agent_roster: {', '.join(project_data.get('agent_roster', []))}")
        print(f"- methodology_schedule: {project_data.get('methodology_promotion', {}).get('schedule')}")
        print()

    print("## Project Knowledge")
    if project_dir:
        entries = load_entries(root, project_dir / "knowledge" / "entries")
        if entries:
            for entry in entries:
                print(f"- {entry.get('entry_id')}: {entry.get('title')} [{entry.get('kind')}, {entry.get('status')}]")
                print(f"  source: {entry.get('source_file')}")
                print(f"  extracted: {entry.get('extracted_dir')}")
        else:
            print("- none")
    else:
        print("- no active project")
    print()

    print("## Company Knowledge")
    company_entries = load_entries(root, root / "knowledge" / "company" / "entries")
    if company_entries:
        for entry in company_entries:
            print(f"- {entry.get('entry_id')}: {entry.get('title')} [{entry.get('kind')}, {entry.get('status')}]")
            print(f"  source: {entry.get('source_file')}")
    else:
        print("- no entry manifests yet")
    print()
    print("## KeyMemory")
    print("- Use after source-backed project and company knowledge.")
    print("- Allowed: preferences, durable operating memories, approved methodology summaries, semantic pointers.")
    print("- Forbidden: raw PDF/Word/image storage, unapproved project drafts, ordinary plaintext secrets.")
    return 0


def create_project(args: argparse.Namespace) -> int:
    root = system_root()
    project_id = args.project or slugify(args.name)
    agents = [registered_agent(root, item.strip()) for item in args.agents.split(",") if item.strip()] if args.agents else []
    target = copy_template_project(root, project_id, args.name, agents, args.methodology_schedule)
    append_log(root, {"event": "project_create", "project": project_id})
    print(str(target))
    return 0


def run_record_path(root: Path, run_id: str) -> Path:
    return root / "runs" / safe_component(run_id, "run id") / "run.json"


def load_run_record(root: Path, run_id: str) -> dict[str, Any]:
    path = run_record_path(root, run_id)
    if not path.exists():
        print(f"office-system: workflow run not found: {run_id}", file=sys.stderr)
        raise SystemExit(2)
    return read_json(path)


def read_run_records(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted((root / "runs").glob("*/run.json")):
        try:
            records.append(read_json(path))
        except Exception:
            continue
    records.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
    return records


def find_run_by_idempotency(root: Path, key: str | None) -> dict[str, Any] | None:
    if not key:
        return None
    for record in read_run_records(root):
        if record.get("idempotency_key") == key:
            return record
    return None


def loop_stage_records(root: Path) -> dict[str, Any]:
    manifest = loop_manifest(root)
    return {
        stage: {
            "status": "pending",
            "required_artifacts": manifest["stages"][stage]["required_artifacts"],
            "gates": [{"gate": gate, "status": "pending"} for gate in manifest["stages"][stage]["gates"]],
            "artifacts": [],
            "notes": [],
        }
        for stage in LOOP_STAGES
    }


def route_task(root: Path, task: str, requested_agent: str, workflow: str | None) -> dict[str, Any]:
    router = root.parent / "scripts" / "agent-router"
    if not router.exists():
        print(f"office-system: agent router not found: {router}", file=sys.stderr)
        raise SystemExit(2)
    command = [str(router), "--route-json", "--agent", requested_agent or "auto"]
    if workflow:
        command.extend(["--workflow", workflow])
    command.append(task)
    proc = subprocess.run(
        command,
        text=True,
        capture_output=True,
        env={**os.environ, "HERMES_HOME": str(root.parent)},
    )
    if proc.returncode not in {0, 3}:
        print(proc.stderr or proc.stdout or "office-system: route failed", file=sys.stderr)
        raise SystemExit(proc.returncode)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        print("office-system: router returned invalid JSON", file=sys.stderr)
        raise SystemExit(1)


def task_title(body: str) -> str:
    compact = re.sub(r"\s+", " ", body).strip()
    return compact[:80] or "Untitled task"


def parse_json_arg(value: str | None, path: str | None, label: str) -> dict[str, Any]:
    if path:
        return read_json(Path(path).expanduser())
    if value:
        try:
            data = json.loads(value)
        except json.JSONDecodeError as exc:
            print(f"office-system: invalid {label} JSON: {exc}", file=sys.stderr)
            raise SystemExit(2)
        if not isinstance(data, dict):
            print(f"office-system: {label} JSON must be an object", file=sys.stderr)
            raise SystemExit(2)
        return data
    text = sys.stdin.read().strip()
    if not text:
        print(f"office-system: {label} JSON is required", file=sys.stderr)
        raise SystemExit(2)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"office-system: invalid {label} JSON: {exc}", file=sys.stderr)
        raise SystemExit(2)
    if not isinstance(data, dict):
        print(f"office-system: {label} JSON must be an object", file=sys.stderr)
        raise SystemExit(2)
    return data


def canvas_node(node_id: str, node_type: str, title: str, **extra: Any) -> dict[str, Any]:
    node_id = safe_component(node_id, "node id")
    if node_type not in CANVAS_NODE_TYPES:
        print(f"office-system: invalid canvas node type: {node_type}", file=sys.stderr)
        raise SystemExit(2)
    node = {
        "node_id": node_id,
        "type": node_type,
        "title": safe_claim(title, "node title"),
        "inputs": sorted(NODE_IO_TYPES.get(node_type, {}).get("inputs", set())),
        "outputs": sorted(NODE_IO_TYPES.get(node_type, {}).get("outputs", set())),
        "status": "pending",
    }
    node.update({key: value for key, value in extra.items() if value not in (None, "")})
    return node


def default_canvas_from_route(root: Path, *, route: dict[str, Any], body: str, agent_id: str, workflow: str) -> dict[str, Any]:
    steps = route.get("steps") or ([agent_id] if agent_id else [])
    nodes = [canvas_node("start", "start", "Start")]
    edges: list[dict[str, str]] = []
    previous = "start"
    for index, step_agent in enumerate(steps, start=1):
        registered = registered_agent(root, str(step_agent))
        node_id = f"agent-{index}-{registered}"
        nodes.append(
            canvas_node(
                node_id,
                "agent_task",
                f"{registered} task",
                agent_id=registered,
                instruction=body,
                execution_mode="direct" if workflow == "direct_agent" else "workflow",
            )
        )
        edges.append({"from": previous, "to": node_id})
        previous = node_id
    output_id = "final-output"
    nodes.append(canvas_node(output_id, "output_artifact", "Final output", required=True))
    edges.append({"from": previous, "to": output_id})
    return {
        "mode": "simple",
        "nodes": nodes,
        "edges": edges,
        "entry_node_id": "start",
        "final_node_id": output_id,
        "workflow": workflow,
    }


def new_canvas_revision(
    root: Path,
    *,
    revision_id: str,
    status: str,
    created_by: str,
    source: str,
    parent_revision_id: str = "",
    canvas: dict[str, Any],
    change_summary: str = "",
) -> dict[str, Any]:
    validation = validate_canvas(root, canvas)
    return {
        "revision_id": safe_component(revision_id, "revision id"),
        "status": safe_component(status, "revision status"),
        "created_at": now_iso(),
        "created_by": safe_claim(created_by, "revision creator", required=False),
        "source": safe_component(source, "revision source"),
        "parent_revision_id": safe_claim(parent_revision_id, "parent revision id", required=False),
        "change_summary": safe_claim(change_summary, "change summary", required=False),
        "canvas": canvas,
        "validation": validation,
    }


def initial_canvas_revision(root: Path, *, route: dict[str, Any], body: str, agent_id: str, workflow: str, created_by: str) -> dict[str, Any]:
    revision_id = f"rev-{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
    canvas = default_canvas_from_route(root, route=route, body=body, agent_id=agent_id, workflow=workflow)
    return new_canvas_revision(
        root,
        revision_id=revision_id,
        status="active",
        created_by=created_by,
        source="workflow_start",
        canvas=canvas,
        change_summary="Initial workflow canvas generated from router decision.",
    )


def revision_list(run: dict[str, Any]) -> list[dict[str, Any]]:
    return run.setdefault("revisions", [])


def find_revision(run: dict[str, Any], revision_id: str) -> dict[str, Any] | None:
    revision_id = safe_component(revision_id, "revision id")
    for revision in revision_list(run):
        if revision.get("revision_id") == revision_id:
            return revision
    return None


def active_revision(run: dict[str, Any]) -> dict[str, Any] | None:
    active_id = run.get("active_revision_id")
    if active_id:
        found = find_revision(run, active_id)
        if found:
            return found
    for revision in revision_list(run):
        if revision.get("status") == "active":
            return revision
    return None


def normalize_canvas_payload(root: Path, payload: dict[str, Any], base_canvas: dict[str, Any] | None = None) -> dict[str, Any]:
    canvas = json.loads(json.dumps(base_canvas or {"mode": "simple", "nodes": [], "edges": []}, ensure_ascii=False))
    if "mode" in payload:
        mode = safe_component(str(payload["mode"]), "canvas mode")
        if mode not in {"simple", "professional", "admin"}:
            print(f"office-system: invalid canvas mode: {mode}", file=sys.stderr)
            raise SystemExit(2)
        canvas["mode"] = mode
    if "nodes" in payload:
        if not isinstance(payload["nodes"], list):
            print("office-system: canvas nodes must be a list", file=sys.stderr)
            raise SystemExit(2)
        nodes = []
        for item in payload["nodes"]:
            if not isinstance(item, dict):
                print("office-system: canvas node must be an object", file=sys.stderr)
                raise SystemExit(2)
            node_type = safe_component(str(item.get("type", "")), "canvas node type")
            node_id = safe_component(str(item.get("node_id", "")), "node id")
            title = safe_claim(str(item.get("title") or node_id), "node title")
            extra = {key: value for key, value in item.items() if key not in {"node_id", "type", "title", "inputs", "outputs"}}
            nodes.append(canvas_node(node_id, node_type, title, **extra))
        canvas["nodes"] = nodes
    if "edges" in payload:
        if not isinstance(payload["edges"], list):
            print("office-system: canvas edges must be a list", file=sys.stderr)
            raise SystemExit(2)
        edges = []
        for item in payload["edges"]:
            if not isinstance(item, dict):
                print("office-system: canvas edge must be an object", file=sys.stderr)
                raise SystemExit(2)
            edges.append({"from": safe_component(str(item.get("from", "")), "edge from"), "to": safe_component(str(item.get("to", "")), "edge to")})
        canvas["edges"] = edges
    for operation in payload.get("operations", []) or []:
        if not isinstance(operation, dict):
            print("office-system: canvas operation must be an object", file=sys.stderr)
            raise SystemExit(2)
        apply_canvas_operation(root, canvas, operation)
    return canvas


def apply_canvas_operation(root: Path, canvas: dict[str, Any], operation: dict[str, Any]) -> None:
    op = safe_component(str(operation.get("op", "")), "canvas operation")
    nodes = canvas.setdefault("nodes", [])
    edges = canvas.setdefault("edges", [])
    if op == "add_node":
        item = operation.get("node")
        if not isinstance(item, dict):
            print("office-system: add_node requires node object", file=sys.stderr)
            raise SystemExit(2)
        node = normalize_canvas_payload(root, {"nodes": [item]})["nodes"][0]
        if any(existing.get("node_id") == node["node_id"] for existing in nodes):
            print(f"office-system: canvas node already exists: {node['node_id']}", file=sys.stderr)
            raise SystemExit(2)
        nodes.append(node)
    elif op == "remove_node":
        node_id = safe_component(str(operation.get("node_id", "")), "node id")
        canvas["nodes"] = [node for node in nodes if node.get("node_id") != node_id]
        canvas["edges"] = [edge for edge in edges if edge.get("from") != node_id and edge.get("to") != node_id]
    elif op == "replace_node":
        item = operation.get("node")
        if not isinstance(item, dict):
            print("office-system: replace_node requires node object", file=sys.stderr)
            raise SystemExit(2)
        node = normalize_canvas_payload(root, {"nodes": [item]})["nodes"][0]
        replaced = False
        for index, existing in enumerate(nodes):
            if existing.get("node_id") == node["node_id"]:
                nodes[index] = node
                replaced = True
                break
        if not replaced:
            print(f"office-system: canvas node not found: {node['node_id']}", file=sys.stderr)
            raise SystemExit(2)
    elif op == "add_edge":
        edge = {"from": safe_component(str(operation.get("from", "")), "edge from"), "to": safe_component(str(operation.get("to", "")), "edge to")}
        if edge not in edges:
            edges.append(edge)
    elif op == "remove_edge":
        edge = {"from": safe_component(str(operation.get("from", "")), "edge from"), "to": safe_component(str(operation.get("to", "")), "edge to")}
        canvas["edges"] = [item for item in edges if item != edge]
    else:
        print(f"office-system: unsupported canvas operation: {op}", file=sys.stderr)
        raise SystemExit(2)


def validate_canvas(root: Path, canvas: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    nodes = canvas.get("nodes") or []
    edges = canvas.get("edges") or []
    node_by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return {"status": "invalid", "errors": ["canvas nodes and edges must be lists"], "warnings": warnings}
    for node in nodes:
        node_id = str(node.get("node_id", ""))
        node_type = str(node.get("type", ""))
        if not node_id:
            errors.append("node missing node_id")
            continue
        if node_id in node_by_id:
            errors.append(f"duplicate node id: {node_id}")
            continue
        node_by_id[node_id] = node
        if node_type not in CANVAS_NODE_TYPES:
            errors.append(f"invalid node type for {node_id}: {node_type}")
        if canvas.get("mode", "simple") == "simple" and node_type not in SIMPLE_CANVAS_NODE_TYPES | {"start"}:
            warnings.append(f"{node_id} uses advanced component {node_type}")
        if node_type == "agent_task":
            agent = str(node.get("agent_id", ""))
            if not agent:
                errors.append(f"agent_task {node_id} missing agent_id")
            else:
                try:
                    registered_agent(root, agent)
                except SystemExit:
                    errors.append(f"agent_task {node_id} references unknown agent {agent}")
            if not str(node.get("instruction", "")).strip():
                errors.append(f"agent_task {node_id} missing instruction")
        if node_type == "file_ref" and not node.get("file_id"):
            errors.append(f"file_ref {node_id} missing file_id")
        if node_type == "folder_ref" and not node.get("folder_id"):
            errors.append(f"folder_ref {node_id} missing folder_id")
        if node_type == "knowledge_scope" and not (node.get("scope_id") or node.get("space_id")):
            errors.append(f"knowledge_scope {node_id} missing scope_id or space_id")

    if not any(node.get("type") == "start" for node in nodes):
        errors.append("canvas must include a start node")
    if not any(node.get("type") == "output_artifact" for node in nodes):
        errors.append("canvas must include a final output_artifact node")

    incoming: dict[str, int] = {node_id: 0 for node_id in node_by_id}
    outgoing: dict[str, int] = {node_id: 0 for node_id in node_by_id}
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_by_id}
    for edge in edges:
        source = str(edge.get("from", ""))
        target = str(edge.get("to", ""))
        if source not in node_by_id:
            errors.append(f"edge references missing source node: {source}")
            continue
        if target not in node_by_id:
            errors.append(f"edge references missing target node: {target}")
            continue
        source_outputs = set(node_by_id[source].get("outputs") or NODE_IO_TYPES.get(str(node_by_id[source].get("type")), {}).get("outputs", set()))
        target_inputs = set(node_by_id[target].get("inputs") or NODE_IO_TYPES.get(str(node_by_id[target].get("type")), {}).get("inputs", set()))
        if target_inputs and source_outputs and not source_outputs.intersection(target_inputs):
            errors.append(f"edge {source}->{target} has incompatible output/input types")
        incoming[target] += 1
        outgoing[source] += 1
        adjacency[source].append(target)

    for node_id, node in node_by_id.items():
        node_type = node.get("type")
        if node_type != "start" and incoming.get(node_id, 0) == 0:
            errors.append(f"node is unreachable: {node_id}")
        if node_type != "output_artifact" and outgoing.get(node_id, 0) == 0:
            errors.append(f"node has no outgoing edge: {node_id}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visiting:
            errors.append(f"cycle detected at node: {node_id}")
            return
        if node_id in visited:
            return
        visiting.add(node_id)
        for child in adjacency.get(node_id, []):
            visit(child)
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in node_by_id:
        visit(node_id)

    for node in nodes:
        if node.get("type") == "agent_task" and (node.get("risk") in {"high", "regulated"} or node.get("requires_approval")):
            seen: set[str] = set()
            stack = list(adjacency.get(str(node.get("node_id")), []))
            has_approval = False
            while stack:
                current = stack.pop()
                if current in seen:
                    continue
                seen.add(current)
                if node_by_id.get(current, {}).get("type") == "approval_gate":
                    has_approval = True
                    break
                stack.extend(adjacency.get(current, []))
            if not has_approval:
                errors.append(f"high-risk agent node lacks downstream approval_gate: {node.get('node_id')}")

    return {"status": "valid" if not errors else "invalid", "errors": errors, "warnings": warnings}


def create_task_record(
    root: Path,
    *,
    task_id: str,
    title: str,
    body: str,
    status: str,
    priority: str,
    project_id: str,
    agent_id: str,
    workflow_run_id: str,
    assigned_user: str,
    requested_by: str,
    route: dict[str, Any],
    idempotency_key: str = "",
) -> dict[str, Any]:
    if status not in TASK_STATUSES:
        print(f"office-system: invalid task status: {status}", file=sys.stderr)
        raise SystemExit(2)
    task = {
        "version": "1.0.0",
        "kind": "digital-office-task",
        "task_id": task_id,
        "title": title,
        "body": body,
        "status": status,
        "priority": priority,
        "project_id": project_id,
        "agent_id": agent_id,
        "assigned_agent": agent_id,
        "assigned_user": assigned_user,
        "requested_by": requested_by,
        "workflow_run_id": workflow_run_id,
        "route": route,
        "idempotency_key": idempotency_key,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "history": [{"time": now_iso(), "status": status, "message": "task created"}],
        "artifacts": [],
    }
    write_json(task_path(root, task_id), task)
    return task


def auth_decision(args: argparse.Namespace) -> int:
    root = system_root()
    decision = compute_authorization_decision(
        root,
        tenant_id=args.tenant,
        deployment_id=args.deployment,
        user_id=args.user,
        user_role=args.role,
        action=args.action,
        resource_type=args.resource_type,
        resource_id=args.resource_id,
        project_id=args.project or "",
        agent_id=args.agent or "",
        workflow_run_id=args.workflow_run or "",
        reason=args.reason or "",
    )
    print(json.dumps(decision, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if decision["allowed"] else 2


def workflow_start(args: argparse.Namespace) -> int:
    root = system_root()
    body = args.task if args.task is not None else sys.stdin.read()
    body = body.strip()
    if not body:
        print("office-system: workflow-start requires --task or stdin body", file=sys.stderr)
        return 2
    existing = find_run_by_idempotency(root, args.idempotency_key)
    if existing:
        print(json.dumps({"idempotent": True, "run": existing}, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    project = safe_component(args.project, "project id") if args.project else ""
    if project:
        ensure_project(root, project)
    route = route_task(root, body, args.agent, args.workflow)
    agent = registered_agent(root, str(route.get("agent", ""))) if route.get("agent") else ""
    run_id = safe_component(args.run_id, "run id") if args.run_id else f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    task_id = safe_component(args.task_id, "task id") if args.task_id else f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    if run_record_path(root, run_id).exists():
        print(f"office-system: workflow run already exists: {run_id}", file=sys.stderr)
        return 2
    if task_path(root, task_id).exists():
        print(f"office-system: task already exists: {task_id}", file=sys.stderr)
        return 2

    auth = compute_authorization_decision(
        root,
        tenant_id=args.tenant,
        deployment_id=args.deployment,
        user_id=args.user,
        user_role=args.role,
        action="workflow.start",
        resource_type="workflow_run",
        resource_id=run_id,
        project_id=project,
        agent_id=agent,
        workflow_run_id=run_id,
        reason=args.reason or "",
    )
    if not auth["allowed"]:
        print(json.dumps({"authorization": auth, "status": "denied"}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    needs_clarification = bool(route.get("fallback") or route.get("clarification_required"))
    run_status = "blocked" if needs_clarification else "created"
    task_status = "blocked" if needs_clarification else "queued"
    initial_revision = initial_canvas_revision(root, route=route, body=body, agent_id=agent, workflow=route.get("workflow", ""), created_by=args.user)
    run = {
        "version": "1.0.0",
        "kind": "digital-office-workflow-run",
        "run_id": run_id,
        "run_type": "workflow_run",
        "status": run_status,
        "current_stage": "perceive",
        "project_id": project,
        "agent_id": agent,
        "workflow": route.get("workflow", ""),
        "requested_by": safe_claim(args.user, "requested by"),
        "requested_by_role": safe_component(args.role, "requested by role"),
        "tenant_id": safe_claim(args.tenant, "tenant id"),
        "deployment_id": safe_claim(args.deployment, "deployment id"),
        "task": body,
        "task_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "tasks": [task_id],
        "approvals": [],
        "route": route,
        "active_revision_id": initial_revision["revision_id"],
        "revisions": [initial_revision],
        "canvas": initial_revision["canvas"],
        "authorization": auth,
        "blockers": ["clarification_required"] if needs_clarification else [],
        "idempotency_key": args.idempotency_key or "",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "stages": loop_stage_records(root),
        "events": [{"time": now_iso(), "event": "workflow_started", "status": run_status}],
    }
    task = create_task_record(
        root,
        task_id=task_id,
        title=args.title or task_title(body),
        body=body,
        status=task_status,
        priority=args.priority,
        project_id=project,
        agent_id=agent,
        workflow_run_id=run_id,
        assigned_user=args.user,
        requested_by=args.user,
        route=route,
        idempotency_key=args.idempotency_key or "",
    )
    write_json(run_record_path(root, run_id), run)
    event = append_audit_event(
        root,
        "workflow_started",
        actor_id=args.user,
        actor_role=args.role,
        tenant_id=args.tenant,
        deployment_id=args.deployment,
        project_id=project,
        agent_id=agent,
        resource_type="workflow_run",
        resource_id=run_id,
        workflow_run_id=run_id,
        task_id=task_id,
        outcome="blocked" if needs_clarification else "created",
        reason="clarification required" if needs_clarification else args.reason or "",
        extra={"workflow": run["workflow"], "route_confidence": route.get("confidence")},
    )
    emit_notification(
        root,
        user_id=args.user,
        title="Workflow started" if not needs_clarification else "Workflow needs clarification",
        body=task["title"],
        topic="workflow",
        resource_type="workflow_run",
        resource_id=run_id,
        severity="warning" if needs_clarification else "info",
    )
    print(
        json.dumps(
            {
                "run_id": run_id,
                "task_id": task_id,
                "status": run_status,
                "task_status": task_status,
                "route": route,
                "authorization": auth,
                "audit_event_id": event["event_id"],
                "next_actions": ["workflow-status", "task-status", "approval-create"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def workflow_status(args: argparse.Namespace) -> int:
    root = system_root()
    print(json.dumps(load_run_record(root, args.run_id), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def workflow_list(args: argparse.Namespace) -> int:
    root = system_root()
    project = safe_component(args.project, "project id") if args.project else ""
    records = []
    for run in read_run_records(root):
        if args.status and run.get("status") != args.status:
            continue
        if project and run.get("project_id") != project:
            continue
        if args.user and run.get("requested_by") != args.user:
            continue
        records.append(run)
        if len(records) >= args.limit:
            break
    print(json.dumps({"runs": records}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def linked_tasks(root: Path, run: dict[str, Any]) -> list[str]:
    return [safe_component(task_id, "task id") for task_id in run.get("tasks", []) if task_id]


def sync_run_status_from_tasks(root: Path, run_id: str) -> dict[str, Any] | None:
    if not run_id:
        return None
    run = load_run_record(root, run_id)
    task_ids = linked_tasks(root, run)
    if not task_ids:
        return run
    tasks = [load_task(root, task_id) for task_id in task_ids]
    statuses = {task.get("status") for task in tasks}
    next_status = ""
    event_name = ""
    if statuses == {"completed"}:
        next_status = "completed"
        event_name = "workflow_completed"
    elif "failed" in statuses:
        next_status = "blocked"
        event_name = "workflow_blocked_by_task_failure"
        run.setdefault("blockers", [])
        if "task_failed" not in run["blockers"]:
            run["blockers"].append("task_failed")
    elif statuses == {"cancelled"}:
        next_status = "cancelled"
        event_name = "workflow_cancelled_by_tasks"
    elif "waiting_approval" in statuses:
        next_status = "waiting_user_confirmation"
        event_name = "workflow_waiting_for_task_approval"
    if not next_status or run.get("status") == next_status:
        return run
    run["status"] = next_status
    run["updated_at"] = now_iso()
    run.setdefault("events", []).append({"time": run["updated_at"], "event": event_name, "task_statuses": sorted(str(item) for item in statuses)})
    write_json(run_record_path(root, run_id), run)
    return run


def workflow_cancel(args: argparse.Namespace) -> int:
    root = system_root()
    if not args.confirmed:
        print("office-system: workflow-cancel requires --confirmed", file=sys.stderr)
        return 2
    run = load_run_record(root, args.run_id)
    auth = compute_authorization_decision(
        root,
        tenant_id=run.get("tenant_id", "local"),
        deployment_id=run.get("deployment_id", "local"),
        user_id=args.requested_by,
        user_role=args.role,
        action="workflow.cancel",
        resource_type="workflow_run",
        resource_id=args.run_id,
        project_id=run.get("project_id", ""),
        agent_id=run.get("agent_id", ""),
        workflow_run_id=args.run_id,
    )
    if not auth["allowed"]:
        print(json.dumps({"authorization": auth, "status": "denied"}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    if run.get("status") in {"completed", "cancelled"}:
        print("office-system: completed or cancelled workflow cannot be cancelled again", file=sys.stderr)
        return 2
    run["status"] = "cancelled"
    run["updated_at"] = now_iso()
    run.setdefault("events", []).append({"time": run["updated_at"], "event": "workflow_cancelled", "reason": args.reason or ""})
    for task_id in linked_tasks(root, run):
        update_task_status(root, task_id, "cancelled", message=args.reason or "workflow cancelled", actor_id=args.requested_by or "", actor_role=args.role or "")
    write_json(run_record_path(root, args.run_id), run)
    append_audit_event(
        root,
        "workflow_cancelled",
        actor_id=args.requested_by or "",
        actor_role=args.role or "",
        project_id=run.get("project_id", ""),
        agent_id=run.get("agent_id", ""),
        resource_type="workflow_run",
        resource_id=args.run_id,
        workflow_run_id=args.run_id,
        outcome="cancelled",
        reason=args.reason or "",
    )
    print(json.dumps({"run_id": args.run_id, "status": "cancelled"}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def workflow_resume(args: argparse.Namespace) -> int:
    root = system_root()
    run = load_run_record(root, args.run_id)
    auth = compute_authorization_decision(
        root,
        tenant_id=run.get("tenant_id", "local"),
        deployment_id=run.get("deployment_id", "local"),
        user_id=args.requested_by,
        user_role=args.role,
        action="workflow.resume",
        resource_type="workflow_run",
        resource_id=args.run_id,
        project_id=run.get("project_id", ""),
        agent_id=run.get("agent_id", ""),
        workflow_run_id=args.run_id,
    )
    if not auth["allowed"]:
        print(json.dumps({"authorization": auth, "status": "denied"}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    if run.get("status") == "cancelled":
        print("office-system: cancelled workflow must be retried instead of resumed", file=sys.stderr)
        return 2
    if run.get("status") == "completed":
        print("office-system: completed workflow cannot be resumed", file=sys.stderr)
        return 2
    run["status"] = LOOP_STATUS_BY_STAGE.get(run.get("current_stage", "perceive"), "created")
    run["updated_at"] = now_iso()
    run.setdefault("blockers", [])
    run["blockers"] = [item for item in run["blockers"] if item != "clarification_required"]
    run.setdefault("events", []).append({"time": run["updated_at"], "event": "workflow_resumed", "reason": args.reason or ""})
    for task_id in linked_tasks(root, run):
        task = load_task(root, task_id)
        if task.get("status") in {"blocked", "waiting_approval"}:
            update_task_status(root, task_id, "queued", message=args.reason or "workflow resumed", actor_id=args.requested_by or "", actor_role=args.role or "")
    write_json(run_record_path(root, args.run_id), run)
    append_audit_event(root, "workflow_resumed", actor_id=args.requested_by or "", actor_role=args.role or "", project_id=run.get("project_id", ""), agent_id=run.get("agent_id", ""), resource_type="workflow_run", resource_id=args.run_id, workflow_run_id=args.run_id, outcome="resumed", reason=args.reason or "")
    print(json.dumps({"run_id": args.run_id, "status": run["status"]}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def workflow_retry(args: argparse.Namespace) -> int:
    root = system_root()
    run = load_run_record(root, args.run_id)
    auth = compute_authorization_decision(
        root,
        tenant_id=run.get("tenant_id", "local"),
        deployment_id=run.get("deployment_id", "local"),
        user_id=args.requested_by,
        user_role=args.role,
        action="workflow.retry",
        resource_type="workflow_run",
        resource_id=args.run_id,
        project_id=run.get("project_id", ""),
        agent_id=run.get("agent_id", ""),
        workflow_run_id=args.run_id,
    )
    if not auth["allowed"]:
        print(json.dumps({"authorization": auth, "status": "denied"}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    stage = args.stage or run.get("current_stage") or "perceive"
    if stage not in LOOP_STAGES:
        print(f"office-system: invalid retry stage: {stage}", file=sys.stderr)
        return 2
    retry = {
        "time": now_iso(),
        "stage": stage,
        "requested_by": safe_claim(args.requested_by, "requested by", required=False),
        "reason": args.reason or "",
    }
    run.setdefault("retries", []).append(retry)
    run["current_stage"] = stage
    run["status"] = LOOP_STATUS_BY_STAGE.get(stage, "created")
    run["updated_at"] = now_iso()
    run.setdefault("events", []).append({"time": run["updated_at"], "event": "workflow_retry", "stage": stage, "reason": args.reason or ""})
    stage_state = run.setdefault("stages", {}).setdefault(stage, {"artifacts": [], "notes": [], "gates": []})
    stage_state["status"] = "pending"
    for task_id in linked_tasks(root, run):
        task = load_task(root, task_id)
        if task.get("status") in {"failed", "blocked", "cancelled"}:
            update_task_status(root, task_id, "queued", message=args.reason or "workflow retry", actor_id=args.requested_by or "", actor_role=args.role or "")
    write_json(run_record_path(root, args.run_id), run)
    append_audit_event(root, "workflow_retry", actor_id=args.requested_by or "", actor_role=args.role or "", project_id=run.get("project_id", ""), agent_id=run.get("agent_id", ""), resource_type="workflow_run", resource_id=args.run_id, workflow_run_id=args.run_id, outcome="retry_scheduled", reason=args.reason or "", extra={"stage": stage})
    print(json.dumps({"run_id": args.run_id, "stage": stage, "status": run["status"]}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def agent_invoke(args: argparse.Namespace) -> int:
    root = system_root()
    if not args.project:
        print(json.dumps({"status": "denied", "error": "agent-invoke requires --project for governed dispatch"}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    project = safe_component(args.project, "project id")
    ensure_project(root, project)
    registry = read_json(root / "agents.registry.json")
    agent = safe_component(args.agent, "agent id")
    if agent not in registry.get("agents", {}):
        print(json.dumps({"status": "denied", "error": "unknown agent", "agent_id": agent}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    body = args.task if args.task is not None else sys.stdin.read()
    body = body.strip()
    if not body:
        print(json.dumps({"status": "denied", "error": "agent-invoke requires --task or stdin body"}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    run_id = safe_component(args.run_id, "run id") if args.run_id else f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    task_id = safe_component(args.task_id, "task id") if args.task_id else f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    if run_record_path(root, run_id).exists() or task_path(root, task_id).exists():
        print(json.dumps({"status": "denied", "error": "run or task already exists", "run_id": run_id, "task_id": task_id}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    auth = compute_authorization_decision(root, tenant_id=args.tenant, deployment_id=args.deployment, user_id=args.user, user_role=args.role, action="agent.delegate", resource_type="agent", resource_id=agent, project_id=project, agent_id=agent, workflow_run_id=run_id, reason=args.reason or "direct GUI @Agent invocation")
    if not auth["allowed"]:
        print(json.dumps({"authorization": auth, "status": "denied"}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    route = {"agent": agent, "workflow": "direct_agent", "steps": [agent], "confidence": "direct", "routing_reason": "explicit_agent_invocation", "display_name": registry["agents"][agent].get("display_name", agent)}
    initial_revision = initial_canvas_revision(root, route=route, body=body, agent_id=agent, workflow="direct_agent", created_by=args.user)
    run = {
        "version": "1.0.0",
        "kind": "digital-office-workflow-run",
        "run_id": run_id,
        "run_type": "workflow_run",
        "invocation_mode": "direct_agent",
        "status": "created",
        "current_stage": "execute",
        "project_id": project,
        "agent_id": agent,
        "workflow": "direct_agent",
        "requested_by": safe_claim(args.user, "requested by"),
        "requested_by_role": safe_component(args.role, "requested by role"),
        "tenant_id": safe_claim(args.tenant, "tenant id"),
        "deployment_id": safe_claim(args.deployment, "deployment id"),
        "task": body,
        "task_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "tasks": [task_id],
        "approvals": [],
        "route": route,
        "active_revision_id": initial_revision["revision_id"],
        "revisions": [initial_revision],
        "canvas": initial_revision["canvas"],
        "authorization": auth,
        "blockers": [],
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "stages": loop_stage_records(root),
        "events": [{"time": now_iso(), "event": "agent_invoked", "agent_id": agent, "status": "created"}],
    }
    task = create_task_record(root, task_id=task_id, title=args.title or task_title(body), body=body, status="queued", priority=args.priority, project_id=project, agent_id=agent, workflow_run_id=run_id, assigned_user=args.user, requested_by=args.user, route=route, idempotency_key="")
    task["invocation_mode"] = "direct_agent"
    write_json(task_path(root, task_id), task)
    write_json(run_record_path(root, run_id), run)
    event = append_audit_event(root, "agent_invoked", actor_id=args.user, actor_role=args.role, tenant_id=args.tenant, deployment_id=args.deployment, project_id=project, agent_id=agent, resource_type="agent", resource_id=agent, workflow_run_id=run_id, task_id=task_id, outcome="created", reason=args.reason or "direct GUI @Agent invocation")
    emit_notification(root, user_id=args.user, title="Agent task queued", body=task["title"], topic="agent", resource_type="workflow_run", resource_id=run_id, severity="info")
    print(json.dumps({"status": "created", "invocation_mode": "direct_agent", "agent_id": agent, "project_id": project, "requested_by": args.user, "workflow_run_id": run_id, "task_id": task_id, "active_revision_id": initial_revision["revision_id"], "authorization": auth, "audit_event_id": event["event_id"]}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def authorize_workflow_mutation(root: Path, run: dict[str, Any], user: str, role: str, action: str) -> dict[str, Any]:
    return compute_authorization_decision(root, tenant_id=run.get("tenant_id", "local"), deployment_id=run.get("deployment_id", "local"), user_id=user, user_role=role, action=action, resource_type="workflow_run", resource_id=run.get("run_id", ""), project_id=run.get("project_id", ""), agent_id=run.get("agent_id", ""), workflow_run_id=run.get("run_id", ""))


def workflow_draft_create(args: argparse.Namespace) -> int:
    root = system_root()
    run = load_run_record(root, args.run_id)
    auth = authorize_workflow_mutation(root, run, args.created_by, args.role, "workflow.edit")
    if not auth["allowed"]:
        print(json.dumps({"authorization": auth, "status": "denied"}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    parent = active_revision(run)
    if not parent:
        parent = initial_canvas_revision(root, route=run.get("route", {}), body=run.get("task", ""), agent_id=run.get("agent_id", ""), workflow=run.get("workflow", ""), created_by=args.created_by)
        revision_list(run).append(parent)
        run["active_revision_id"] = parent["revision_id"]
        run["canvas"] = parent["canvas"]
    revision_id = safe_component(args.revision_id, "revision id") if args.revision_id else f"draft-{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
    if find_revision(run, revision_id):
        print(f"office-system: workflow revision already exists: {revision_id}", file=sys.stderr)
        return 2
    draft = new_canvas_revision(root, revision_id=revision_id, status="draft", created_by=args.created_by, source="gui_canvas_editor", parent_revision_id=parent["revision_id"], canvas=parent["canvas"], change_summary=args.summary or "Draft workflow canvas revision.")
    revision_list(run).append(draft)
    run["updated_at"] = now_iso()
    run.setdefault("events", []).append({"time": run["updated_at"], "event": "workflow_draft_created", "revision_id": revision_id, "parent_revision_id": parent["revision_id"]})
    write_json(run_record_path(root, args.run_id), run)
    append_audit_event(root, "workflow_draft_created", actor_id=args.created_by, actor_role=args.role, project_id=run.get("project_id", ""), agent_id=run.get("agent_id", ""), resource_type="workflow_run", resource_id=args.run_id, workflow_run_id=args.run_id, outcome="draft", reason=args.summary or "")
    print(json.dumps({"run_id": args.run_id, "revision": draft}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def workflow_draft_patch(args: argparse.Namespace) -> int:
    root = system_root()
    run = load_run_record(root, args.run_id)
    revision = find_revision(run, args.revision_id)
    if not revision or revision.get("status") != "draft":
        print("office-system: workflow draft revision not found or not draft", file=sys.stderr)
        return 2
    auth = authorize_workflow_mutation(root, run, args.updated_by, args.role, "workflow.edit")
    if not auth["allowed"]:
        print(json.dumps({"authorization": auth, "status": "denied"}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    patch = parse_json_arg(args.patch_json, args.patch_file, "workflow patch")
    old_canvas = revision.get("canvas", {})
    old_completed = {node.get("node_id"): node for node in old_canvas.get("nodes", []) if node.get("status") == "completed"}
    canvas = normalize_canvas_payload(root, patch, old_canvas)
    new_by_id = {node.get("node_id"): node for node in canvas.get("nodes", [])}
    for node_id, old_node in old_completed.items():
        if node_id not in new_by_id or new_by_id[node_id] != old_node:
            print(f"office-system: completed node cannot be modified in draft revision: {node_id}", file=sys.stderr)
            return 2
    revision["canvas"] = canvas
    revision["updated_at"] = now_iso()
    revision["updated_by"] = safe_claim(args.updated_by, "updated by", required=False)
    revision["change_summary"] = args.summary or revision.get("change_summary", "")
    revision["validation"] = validate_canvas(root, canvas)
    run["updated_at"] = now_iso()
    run.setdefault("events", []).append({"time": run["updated_at"], "event": "workflow_draft_patched", "revision_id": args.revision_id, "validation_status": revision["validation"]["status"]})
    write_json(run_record_path(root, args.run_id), run)
    append_audit_event(root, "workflow_draft_patched", actor_id=args.updated_by, actor_role=args.role, project_id=run.get("project_id", ""), agent_id=run.get("agent_id", ""), resource_type="workflow_run", resource_id=args.run_id, workflow_run_id=args.run_id, outcome=revision["validation"]["status"], reason=args.summary or "")
    print(json.dumps({"run_id": args.run_id, "revision": revision}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def workflow_draft_validate(args: argparse.Namespace) -> int:
    root = system_root()
    run = load_run_record(root, args.run_id)
    revision = find_revision(run, args.revision_id)
    if not revision:
        print("office-system: workflow revision not found", file=sys.stderr)
        return 2
    revision["validation"] = validate_canvas(root, revision.get("canvas", {}))
    revision["validated_at"] = now_iso()
    write_json(run_record_path(root, args.run_id), run)
    print(json.dumps({"run_id": args.run_id, "revision_id": args.revision_id, "validation": revision["validation"]}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def workflow_draft_activate(args: argparse.Namespace) -> int:
    root = system_root()
    if not args.confirmed:
        print("office-system: workflow-draft-activate requires --confirmed", file=sys.stderr)
        return 2
    run = load_run_record(root, args.run_id)
    revision = find_revision(run, args.revision_id)
    if not revision or revision.get("status") != "draft":
        print("office-system: workflow draft revision not found or not draft", file=sys.stderr)
        return 2
    auth = authorize_workflow_mutation(root, run, args.activated_by, args.role, "workflow.edit")
    if not auth["allowed"]:
        print(json.dumps({"authorization": auth, "status": "denied"}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    validation = validate_canvas(root, revision.get("canvas", {}))
    revision["validation"] = validation
    if validation["status"] != "valid":
        write_json(run_record_path(root, args.run_id), run)
        print(json.dumps({"status": "invalid", "validation": validation}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    for item in revision_list(run):
        if item.get("status") == "active":
            item["status"] = "superseded"
            item["superseded_at"] = now_iso()
    revision["status"] = "active"
    revision["activated_at"] = now_iso()
    revision["activated_by"] = safe_claim(args.activated_by, "activated by", required=False)
    run["active_revision_id"] = args.revision_id
    run["canvas"] = revision.get("canvas", {})
    run["updated_at"] = now_iso()
    run.setdefault("events", []).append({"time": run["updated_at"], "event": "workflow_draft_activated", "revision_id": args.revision_id})
    write_json(run_record_path(root, args.run_id), run)
    append_audit_event(root, "workflow_draft_activated", actor_id=args.activated_by, actor_role=args.role, project_id=run.get("project_id", ""), agent_id=run.get("agent_id", ""), resource_type="workflow_run", resource_id=args.run_id, workflow_run_id=args.run_id, outcome="active", reason=args.reason or "")
    print(json.dumps({"run_id": args.run_id, "active_revision_id": args.revision_id, "validation": validation}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def workflow_control(args: argparse.Namespace) -> int:
    root = system_root()
    action = safe_component(args.action, "workflow control action")
    if action not in WORKFLOW_CONTROL_ACTIONS:
        print(f"office-system: invalid workflow control action: {action}", file=sys.stderr)
        return 2
    if action == "stop" and not args.confirmed:
        print("office-system: workflow stop requires --confirmed", file=sys.stderr)
        return 2
    run = load_run_record(root, args.run_id)
    auth = authorize_workflow_mutation(root, run, args.requested_by, args.role, "workflow.control")
    if not auth["allowed"]:
        print(json.dumps({"authorization": auth, "status": "denied"}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    if run.get("status") in {"completed", "cancelled", "stopped"}:
        print("office-system: completed, cancelled, or stopped workflow cannot be controlled", file=sys.stderr)
        return 2
    if action in {"run", "resume"}:
        run["status"] = LOOP_STATUS_BY_STAGE.get(run.get("current_stage", "perceive"), "created")
        run["pause_requested"] = False
        outcome = "running"
    elif action == "pause":
        run["pause_requested"] = True
        run["status"] = "paused_after_current_node"
        outcome = "pause_requested"
    else:
        run["status"] = "stopped"
        run["pause_requested"] = False
        outcome = "stopped"
        for task_id in linked_tasks(root, run):
            task = load_task(root, task_id)
            if task.get("status") not in {"completed", "failed", "cancelled"}:
                update_task_status(root, task_id, "cancelled", message=args.reason or "workflow stopped", actor_id=args.requested_by, actor_role=args.role)
    run["updated_at"] = now_iso()
    run.setdefault("events", []).append({"time": run["updated_at"], "event": f"workflow_control_{action}", "reason": args.reason or ""})
    write_json(run_record_path(root, args.run_id), run)
    append_audit_event(root, f"workflow_control_{action}", actor_id=args.requested_by, actor_role=args.role, project_id=run.get("project_id", ""), agent_id=run.get("agent_id", ""), resource_type="workflow_run", resource_id=args.run_id, workflow_run_id=args.run_id, outcome=outcome, reason=args.reason or "")
    print(json.dumps({"run_id": args.run_id, "action": action, "status": run["status"], "outcome": outcome}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def workflow_node_context(args: argparse.Namespace) -> int:
    root = system_root()
    run = load_run_record(root, args.run_id)
    active = active_revision(run)
    if not active:
        print("office-system: workflow has no active revision", file=sys.stderr)
        return 2
    if args.revision_id and args.revision_id != active.get("revision_id"):
        print(json.dumps({"status": "stale_revision", "active_revision_id": active.get("revision_id"), "requested_revision_id": args.revision_id}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    node_id = safe_component(args.node_id, "node id")
    nodes = active.get("canvas", {}).get("nodes", [])
    node = next((item for item in nodes if item.get("node_id") == node_id), None)
    if not node:
        print(f"office-system: workflow node not found: {node_id}", file=sys.stderr)
        return 2
    edges = active.get("canvas", {}).get("edges", [])
    upstream_ids = [edge["from"] for edge in edges if edge.get("to") == node_id]
    downstream_ids = [edge["to"] for edge in edges if edge.get("from") == node_id]
    upstream_nodes = [item for item in nodes if item.get("node_id") in upstream_ids]
    print(json.dumps({"kind": "digital-office-workflow-node-context", "run_id": args.run_id, "project_id": run.get("project_id", ""), "active_revision_id": active.get("revision_id"), "node_id": node_id, "node": node, "upstream_node_ids": upstream_ids, "downstream_node_ids": downstream_ids, "inputs": upstream_nodes, "run_status": run.get("status"), "pause_requested": bool(run.get("pause_requested"))}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def task_list(args: argparse.Namespace) -> int:
    root = system_root()
    project = safe_component(args.project, "project id") if args.project else ""
    records = []
    for task in read_records(root / "tasks", "digital-office-task"):
        if args.status and task.get("status") != args.status:
            continue
        if project and task.get("project_id") != project:
            continue
        if args.assigned_agent and task.get("assigned_agent") != args.assigned_agent:
            continue
        if args.assigned_user and task.get("assigned_user") != args.assigned_user:
            continue
        records.append(task)
        if len(records) >= args.limit:
            break
    print(json.dumps({"tasks": records}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def task_status(args: argparse.Namespace) -> int:
    root = system_root()
    print(json.dumps(load_task(root, args.task_id), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def task_update(args: argparse.Namespace) -> int:
    root = system_root()
    task = load_task(root, args.task_id)
    run = load_run_record(root, task["workflow_run_id"]) if task.get("workflow_run_id") else {}
    auth = compute_authorization_decision(
        root,
        tenant_id=run.get("tenant_id", "local"),
        deployment_id=run.get("deployment_id", "local"),
        user_id=args.updated_by,
        user_role=args.role,
        action="task.manage",
        resource_type="task",
        resource_id=args.task_id,
        project_id=task.get("project_id", ""),
        agent_id=task.get("assigned_agent", ""),
        workflow_run_id=task.get("workflow_run_id", ""),
    )
    if not auth["allowed"]:
        print(json.dumps({"authorization": auth, "status": "denied"}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    if args.status:
        task = update_task_status(root, args.task_id, args.status, message=args.summary or "", actor_id=args.updated_by or "", actor_role=args.role or "")
    if args.assigned_agent:
        task["assigned_agent"] = registered_agent(root, args.assigned_agent)
    if args.assigned_user:
        task["assigned_user"] = safe_claim(args.assigned_user, "assigned user")
    for artifact in args.artifact or []:
        task.setdefault("artifacts", []).append(safe_claim(artifact, "artifact"))
    task["updated_at"] = now_iso()
    write_json(task_path(root, args.task_id), task)
    if task.get("workflow_run_id"):
        sync_run_status_from_tasks(root, task["workflow_run_id"])
    append_audit_event(root, "task_updated", actor_id=args.updated_by or "", actor_role=args.role or "", project_id=task.get("project_id", ""), agent_id=task.get("assigned_agent", ""), resource_type="task", resource_id=args.task_id, workflow_run_id=task.get("workflow_run_id", ""), task_id=args.task_id, outcome=task.get("status", "updated"), reason=args.summary or "")
    print(json.dumps(task, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def approval_create(args: argparse.Namespace) -> int:
    root = system_root()
    existing = find_by_idempotency(root, "approvals", args.idempotency_key)
    if existing:
        print(json.dumps({"idempotent": True, "approval": existing}, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    project = safe_component(args.project, "project id") if args.project else ""
    agent = registered_agent(root, args.agent) if args.agent else ""
    approval_id = safe_component(args.approval_id, "approval id") if args.approval_id else f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    if approval_path(root, approval_id).exists():
        print(f"office-system: approval already exists: {approval_id}", file=sys.stderr)
        return 2
    auth = compute_authorization_decision(
        root,
        tenant_id=args.tenant,
        deployment_id=args.deployment,
        user_id=args.requested_by,
        user_role=args.requested_by_role,
        action="approval.create",
        resource_type=args.resource_type,
        resource_id=args.resource_id,
        project_id=project,
        agent_id=agent,
        workflow_run_id=args.workflow_run or "",
    )
    if not auth["allowed"]:
        print(json.dumps({"authorization": auth, "status": "denied"}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    record = {
        "version": "1.0.0",
        "kind": "digital-office-approval",
        "approval_id": approval_id,
        "status": "pending",
        "title": args.title,
        "body": args.body or "",
        "action": safe_claim(args.action, "approval action"),
        "resource_type": safe_component(args.resource_type, "resource type"),
        "resource_id": safe_claim(args.resource_id, "resource id"),
        "tenant_id": safe_claim(args.tenant, "tenant id"),
        "deployment_id": safe_claim(args.deployment, "deployment id"),
        "project_id": project,
        "agent_id": agent,
        "workflow_run_id": safe_claim(args.workflow_run, "workflow run id", required=False),
        "task_id": safe_claim(args.task_id, "task id", required=False),
        "requested_by": safe_claim(args.requested_by, "requested by"),
        "requested_by_role": safe_component(args.requested_by_role, "requested by role"),
        "approver_role": safe_component(args.approver_role, "approver role"),
        "risk": args.risk or "",
        "expires_at": safe_claim(args.expires_at, "expires at", required=False),
        "idempotency_key": args.idempotency_key or "",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "decisions": [],
    }
    write_json(approval_path(root, approval_id), record)
    if record["task_id"]:
        update_task_status(root, record["task_id"], "waiting_approval", message=f"waiting for approval {approval_id}", actor_id=args.requested_by, actor_role=args.requested_by_role)
    if record["workflow_run_id"]:
        run = load_run_record(root, record["workflow_run_id"])
        run.setdefault("approvals", []).append(approval_id)
        run["status"] = "waiting_user_confirmation"
        run["updated_at"] = now_iso()
        run.setdefault("events", []).append({"time": run["updated_at"], "event": "approval_requested", "approval_id": approval_id})
        write_json(run_record_path(root, record["workflow_run_id"]), run)
    event = append_audit_event(root, "approval_created", actor_id=args.requested_by, actor_role=args.requested_by_role, tenant_id=args.tenant, deployment_id=args.deployment, project_id=project, agent_id=agent, resource_type="approval", resource_id=approval_id, workflow_run_id=record["workflow_run_id"], task_id=record["task_id"], approval_id=approval_id, outcome="pending", reason=args.title)
    emit_notification(root, user_id="", title="Approval requested", body=args.title, topic="approval", resource_type="approval", resource_id=approval_id, severity="warning")
    print(json.dumps({"approval": record, "audit_event_id": event["event_id"]}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def approval_list(args: argparse.Namespace) -> int:
    root = system_root()
    project = safe_component(args.project, "project id") if args.project else ""
    records = []
    for approval in read_records(root / "approvals", "digital-office-approval"):
        if args.status and approval.get("status") != args.status:
            continue
        if project and approval.get("project_id") != project:
            continue
        if args.approver_role and approval.get("approver_role") != args.approver_role:
            continue
        records.append(approval)
        if len(records) >= args.limit:
            break
    print(json.dumps({"approvals": records}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def approval_decision(args: argparse.Namespace) -> int:
    root = system_root()
    if args.decision in {"approve", "reject"} and not args.confirmed:
        print("office-system: approval decision requires --confirmed", file=sys.stderr)
        return 2
    approval = load_approval(root, args.approval_id)
    auth = compute_authorization_decision(
        root,
        tenant_id=approval.get("tenant_id", "local"),
        deployment_id=approval.get("deployment_id", "local"),
        user_id=args.decided_by,
        user_role=args.role,
        action="approval.decide",
        resource_type="approval",
        resource_id=args.approval_id,
        project_id=approval.get("project_id", ""),
        agent_id=approval.get("agent_id", ""),
        workflow_run_id=approval.get("workflow_run_id", ""),
    )
    if not auth["allowed"]:
        print(json.dumps({"authorization": auth, "status": "denied"}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    if approval.get("status") != "pending":
        print("office-system: approval is not pending", file=sys.stderr)
        return 2
    if approval.get("approver_role") == "professional_reviewer" and args.role != "professional_reviewer":
        print("office-system: this approval requires professional_reviewer", file=sys.stderr)
        return 2
    if args.role not in TENANT_ADMIN_ROLES and args.role != approval.get("approver_role"):
        print("office-system: actor role does not match required approver role", file=sys.stderr)
        return 2
    status = APPROVAL_DECISION_TO_STATUS[args.decision]
    approval["status"] = status
    approval["updated_at"] = now_iso()
    approval["decisions"].append({"time": approval["updated_at"], "decision": args.decision, "decided_by": args.decided_by, "role": args.role, "message": args.message or ""})
    write_json(approval_path(root, args.approval_id), approval)
    if approval.get("task_id"):
        update_task_status(root, approval["task_id"], "queued" if status == "approved" else "blocked", message=args.message or f"approval {status}", actor_id=args.decided_by, actor_role=args.role)
    if approval.get("workflow_run_id"):
        run = load_run_record(root, approval["workflow_run_id"])
        if status == "approved":
            run["status"] = LOOP_STATUS_BY_STAGE.get(run.get("current_stage", "perceive"), "created")
        else:
            run["status"] = "blocked"
            run.setdefault("blockers", []).append(f"approval_{status}")
        run["updated_at"] = now_iso()
        run.setdefault("events", []).append({"time": run["updated_at"], "event": "approval_decision", "approval_id": args.approval_id, "status": status})
        write_json(run_record_path(root, approval["workflow_run_id"]), run)
    event = append_audit_event(root, "approval_decision", actor_id=args.decided_by, actor_role=args.role, tenant_id=approval.get("tenant_id", ""), deployment_id=approval.get("deployment_id", ""), project_id=approval.get("project_id", ""), agent_id=approval.get("agent_id", ""), resource_type="approval", resource_id=args.approval_id, workflow_run_id=approval.get("workflow_run_id", ""), task_id=approval.get("task_id", ""), approval_id=args.approval_id, outcome=status, reason=args.message or "")
    emit_notification(root, user_id=approval.get("requested_by", ""), title=f"Approval {status}", body=approval.get("title", ""), topic="approval", resource_type="approval", resource_id=args.approval_id, severity="info" if status == "approved" else "warning")
    print(json.dumps({"approval": approval, "audit_event_id": event["event_id"]}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def audit_events(args: argparse.Namespace) -> int:
    root = system_root()
    path = root / "logs" / "audit-events.jsonl"
    records = []
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if args.event and event.get("event") != args.event:
                    continue
                if args.resource_type and event.get("resource", {}).get("type") != args.resource_type:
                    continue
                if args.resource_id and event.get("resource", {}).get("id") != args.resource_id:
                    continue
                records.append(event)
    records = records[-args.limit :]
    print(json.dumps({"events": records}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def notification_list(args: argparse.Namespace) -> int:
    root = system_root()
    records = []
    for notification in read_records(root / "notifications", "digital-office-notification"):
        if args.user and notification.get("user_id") not in {"", args.user}:
            continue
        if args.unread_only and notification.get("status") != "unread":
            continue
        records.append(notification)
        if len(records) >= args.limit:
            break
    print(json.dumps({"notifications": records}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def notification_mark_read(args: argparse.Namespace) -> int:
    root = system_root()
    notification = read_json(notification_path(root, args.notification_id))
    notification["status"] = "read"
    notification["read_at"] = now_iso()
    write_json(notification_path(root, args.notification_id), notification)
    append_log(root, {"event": "notification_read", "notification_id": args.notification_id, "user_id": args.user or ""})
    print(json.dumps(notification, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def methodology_draft(args: argparse.Namespace) -> int:
    root = system_root()
    project_dir = ensure_project(root, args.project)
    project = read_json(project_dir / "project.json")
    entries = load_entries(root, project_dir / "knowledge" / "entries")
    stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    target = project_dir / "reports" / "methodology-review" / "drafts" / f"{stamp}-methodology-summary.md"
    lines = [
        f"# Methodology Summary Draft: {project.get('name')}",
        "",
        f"- Project ID: {project.get('project_id')}",
        f"- Period: {args.period}",
        f"- Created at: {now_iso()}",
        "- State: draft_created",
        "",
        "## User Review Required",
        "",
        "This draft must be shown in the GUI. The user may edit it before approval. It must not be promoted to company knowledge until the user confirms.",
        "",
        "## Evidence Inventory",
    ]
    if entries:
        for entry in entries:
            lines.append(f"- {entry.get('entry_id')}: {entry.get('title')} [{entry.get('kind')}, {entry.get('status')}]")
    else:
        lines.append("- No project knowledge entries yet.")
    lines.extend(
        [
            "",
            "## Reusable Methodology",
            "",
            "TODO: Summarize what worked, what failed, reusable workflows, decision rules, templates, and risks.",
            "",
            "## Applicability",
            "",
            "TODO: Explain which future projects should reuse this methodology and which should not.",
            "",
            "## User Edits",
            "",
            "TODO: GUI user may edit this section before approval.",
        ]
    )
    write_text(target, "\n".join(lines) + "\n")
    append_log(root, {"event": "methodology_draft", "project": args.project, "draft": str(target.relative_to(root))})
    print(str(target))
    return 0


def methodology_approve(args: argparse.Namespace) -> int:
    root = system_root()
    project_dir = ensure_project(root, args.project)
    draft = Path(args.draft)
    draft_base = (project_dir / "reports" / "methodology-review" / "drafts").resolve()
    if not draft.is_absolute():
        draft = draft_base / safe_component(args.draft.removesuffix(".md"), "draft id")
        if draft.suffix != ".md":
            draft = draft.with_suffix(".md")
    else:
        draft = draft.resolve()
        if not draft.is_relative_to(draft_base):
            print(f"office-system: methodology draft must be under {draft_base}", file=sys.stderr)
            return 2
    if not draft.exists():
        print(f"office-system: draft not found: {draft}", file=sys.stderr)
        return 2
    if not args.confirmed:
        print("office-system: approval requires --confirmed after GUI user review/edit", file=sys.stderr)
        return 2
    target = root / "knowledge" / "company" / "methodologies" / "approved" / draft.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(draft, target)
    append_log(root, {"event": "methodology_approve", "project": args.project, "target": str(target.relative_to(root))})
    print(str(target))
    return 0


def relay_add(args: argparse.Namespace) -> int:
    root = system_root()
    project_dir = ensure_project(root, args.project)
    agent = registered_agent(root, args.agent)
    refs = args.source_ref or []
    next_actions = args.next_action or []
    body = args.body if args.body is not None else sys.stdin.read()
    relay = {
        "version": "1.0.0",
        "relay_id": f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}",
        "project_id": args.project,
        "subproject_id": args.subproject,
        "agent": agent,
        "title": args.title,
        "summary": body.strip(),
        "status": args.status,
        "source_refs": refs,
        "next_actions": next_actions,
        "created_at": now_iso(),
        "authority": "relay_only",
        "sync_status": "pending_keymemory_sync",
    }
    outbox = project_dir / "relay" / "keymemory-outbox.jsonl"
    outbox.parent.mkdir(parents=True, exist_ok=True)
    with outbox.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(relay, ensure_ascii=False, sort_keys=True) + "\n")
    append_log(root, {"event": "relay_add", "project": args.project, "agent": agent, "relay_id": relay["relay_id"]})
    print(json.dumps(relay, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def agent_request_config_path(root: Path) -> Path:
    configured = os.environ.get("DIGITAL_OFFICE_AGENT_REQUEST_CONFIG")
    if configured:
        return Path(configured).expanduser()
    return root / "agent-requests" / "config.json"


def load_agent_request_config(root: Path) -> dict[str, Any]:
    path = agent_request_config_path(root)
    if path.exists():
        return read_json(path)
    example = root / "agent-requests" / "config.example.json"
    if example.exists():
        return read_json(example)
    return {
        "tenant_id": "",
        "server_url": "",
        "status_url": "",
        "auth_env": "DIGITAL_OFFICE_AGENT_REQUEST_TOKEN",
        "customer_visible_statuses": STATUS_LABELS,
    }


def agent_request_labels(config: dict[str, Any]) -> dict[str, str]:
    labels = dict(config.get("customer_visible_statuses", {}))
    labels.update(config.get("internal_statuses", {}))
    return labels


def send_json(url: str, payload: dict[str, Any], auth_env: str, timeout: int) -> tuple[int, str]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    request.add_header("Content-Type", "application/json")
    token = os.environ.get(auth_env, "")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.read().decode("utf-8", errors="replace")


def agent_request_submit(args: argparse.Namespace) -> int:
    root = system_root()
    config = load_agent_request_config(root)
    if config.get("require_user_submit_confirmation", True) and not args.confirmed:
        print("office-system: agent request submission requires --confirmed after user review", file=sys.stderr)
        return 2

    body = args.body if args.body is not None else sys.stdin.read()
    request_id = f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    labels = agent_request_labels(config)
    payload = {
        "version": "1.0.0",
        "kind": "agent-plugin-request",
        "request_id": request_id,
        "tenant_id": config.get("tenant_id", ""),
        "project_id": args.project,
        "requested_by": args.requested_by,
        "title": args.title,
        "priority": args.priority,
        "body": body.strip(),
        "status": "received",
        "status_label": labels.get("received", STATUS_LABELS["received"]),
        "created_at": now_iso(),
        "source": "digital_office_secretary_agent",
        "skill_changes_requested": False,
        "notes": "This request asks the provider to design and publish an Agent plugin package. Customer-site skill add/remove/recompose operations are forbidden.",
    }
    payload = redact_obj(payload, config)

    outbox = root / "agent-requests" / "outbox" / f"{request_id}.json"
    write_json(outbox, {**payload, "sync_status": "pending_send"})

    server_url = config.get("server_url")
    sync_status = "pending_server_config"
    receipt: dict[str, Any] | None = None
    if server_url:
        try:
            status, response_body = send_json(server_url, payload, config.get("auth_env", "DIGITAL_OFFICE_AGENT_REQUEST_TOKEN"), args.timeout)
            sync_status = "sent"
            receipt = {
                "time": now_iso(),
                "request_id": request_id,
                "server_url": server_url,
                "status": status,
                "response": response_body[:2000],
            }
            write_json(root / "agent-requests" / "receipts" / f"{request_id}.json", receipt)
        except urllib.error.URLError as exc:
            sync_status = "send_failed"
            receipt = {
                "time": now_iso(),
                "request_id": request_id,
                "server_url": server_url,
                "error": str(exc),
            }
            write_json(root / "agent-requests" / "receipts" / f"{request_id}-failed.json", receipt)

    state = {
        **payload,
        "sync_status": sync_status,
        "outbox": str(outbox.relative_to(root)),
        "receipt": receipt,
    }
    write_json(root / "agent-requests" / "status" / f"{request_id}.json", state)
    append_log(root, {"event": "agent_request_submit", "request_id": request_id, "status": "received", "sync_status": sync_status})
    print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if sync_status != "send_failed" else 1


def agent_request_set_status(args: argparse.Namespace) -> int:
    root = system_root()
    config = load_agent_request_config(root)
    labels = agent_request_labels(config)
    request_id = safe_component(args.request_id, "request id")
    status_file = root / "agent-requests" / "status" / f"{request_id}.json"
    state = read_json(status_file) if status_file.exists() else {
        "version": "1.0.0",
        "kind": "agent-plugin-request-status",
        "request_id": request_id,
        "tenant_id": config.get("tenant_id", ""),
    }
    state["status"] = args.status
    state["status_label"] = labels.get(args.status, args.status)
    state["status_updated_at"] = now_iso()
    if args.message:
        state["status_message"] = args.message
    if args.package:
        state["agent_plugin_package"] = args.package
    write_json(status_file, state)
    append_log(root, {"event": "agent_request_set_status", "request_id": request_id, "status": args.status})
    print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def agent_request_status(args: argparse.Namespace) -> int:
    root = system_root()
    request_id = safe_component(args.request_id, "request id")
    status_file = root / "agent-requests" / "status" / f"{request_id}.json"
    if not status_file.exists():
        print(f"office-system: request status not found: {request_id}", file=sys.stderr)
        return 2
    print(json.dumps(read_json(status_file), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


SKILL_CHANGE_PATTERNS = [
    re.compile(r"(?i)\b(add|remove|delete|install|uninstall|replace|compose|recompose)\b.{0,40}\bskill\b"),
    re.compile(r"(?i)\bskill\b.{0,40}\b(add|remove|delete|install|uninstall|replace|compose|recompose)\b"),
    re.compile(r"(增加|新增|删除|移除|安装|卸载|替换|重新组合|重组).{0,20}skill", re.IGNORECASE),
    re.compile(r"skill.{0,20}(增加|新增|删除|移除|安装|卸载|替换|重新组合|重组)", re.IGNORECASE),
]


def contains_skill_change(text: str) -> bool:
    return any(pattern.search(text) for pattern in SKILL_CHANGE_PATTERNS)


def agent_improvement_draft(args: argparse.Namespace) -> int:
    root = system_root()
    agent = registered_agent(root, args.agent)
    body = args.body if args.body is not None else sys.stdin.read()
    if contains_skill_change(body):
        print("office-system: existing Agent improvements may change SOUL/workflow only; skill add/remove/install/recompose is forbidden", file=sys.stderr)
        return 2
    stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    draft_id = f"{stamp}-{args.kind}-{slugify(args.title)}"
    target = root / "agent-improvements" / agent / "drafts" / f"{draft_id}.md"
    lines = [
        f"# Agent Improvement Draft: {args.title}",
        "",
        f"- Agent: {agent}",
        f"- Kind: {args.kind}",
        f"- Project: {args.project or ''}",
        f"- Created at: {now_iso()}",
        "- State: draft_created",
        "- Skill changes: forbidden",
        "",
        "## User-Approved Change",
        "",
        body.strip(),
        "",
        "## Activation Rule",
        "",
        "This draft may improve the existing Agent SOUL document or workflow overlay only. It must not add, remove, install, or recompose skills.",
    ]
    write_text(target, "\n".join(lines) + "\n")
    append_log(root, {"event": "agent_improvement_draft", "agent": agent, "kind": args.kind, "draft": str(target.relative_to(root))})
    print(str(target))
    return 0


def agent_improvement_approve(args: argparse.Namespace) -> int:
    root = system_root()
    agent = registered_agent(root, args.agent)
    if not args.confirmed:
        print("office-system: approving an Agent improvement requires --confirmed after user review", file=sys.stderr)
        return 2
    draft = Path(args.draft).expanduser()
    draft_base = (root / "agent-improvements" / agent / "drafts").resolve()
    if not draft.is_absolute():
        draft_name = safe_component(args.draft.removesuffix(".md"), "draft id") + ".md"
        draft = draft_base / draft_name
    else:
        draft = draft.resolve()
        if not draft.is_relative_to(draft_base):
            print(f"office-system: draft must be under {draft_base}", file=sys.stderr)
            return 2
    if not draft.exists():
        print(f"office-system: draft not found: {draft}", file=sys.stderr)
        return 2
    text = draft.read_text(encoding="utf-8", errors="replace")
    if contains_skill_change(text):
        print("office-system: draft contains a forbidden skill change request", file=sys.stderr)
        return 2
    target = root / "agent-improvements" / agent / "approved" / draft.name
    shutil.copy2(draft, target)
    append_log(root, {"event": "agent_improvement_approve", "agent": agent, "target": str(target.relative_to(root))})
    print(str(target))
    return 0


def resolve_plugin_manifest(package: str) -> tuple[Path, Path, dict[str, Any]]:
    path = Path(package).expanduser()
    if path.is_file():
        return path.parent, path, read_json(path)
    candidates = [
        path / "agent-plugin.json",
        path / "plugin.manifest.json",
        path / "agent-plugin.manifest.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return path, candidate, read_json(candidate)
    print(f"office-system: no Agent plugin manifest found in {path}", file=sys.stderr)
    raise SystemExit(2)


def agent_plugin_report(args: argparse.Namespace) -> int:
    root = system_root()
    package_dir, manifest_path, manifest = resolve_plugin_manifest(args.package)
    agent_id = manifest.get("agent_id") or manifest.get("registry_entry", {}).get("id")
    if not agent_id:
        print("office-system: Agent plugin manifest must contain agent_id", file=sys.stderr)
        return 2
    agent_id = safe_component(agent_id, "agent id")
    project_id = safe_component(args.project, "project id") if args.project else ""
    if project_id:
        ensure_project(root, project_id)
    registry = read_json(root / "agents.registry.json")
    current_agents = sorted(registry.get("agents", {}).keys())
    workflows = manifest.get("workflows", {})
    route_tests = manifest.get("route_tests", [])
    stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    report_id = f"{stamp}-{slugify(agent_id)}"
    target = root / "agent-plugins" / "reports" / f"{report_id}-integration-report.md"
    lines = [
        f"# New Agent Integration Report: {manifest.get('display_name', agent_id)}",
        "",
        "- State: pending_user_confirmation",
        f"- Agent ID: {agent_id}",
        f"- Package: {package_dir}",
        f"- Manifest: {manifest_path}",
        f"- Created at: {now_iso()}",
        f"- Report ID: {report_id}",
        "",
        "## Current System",
        "",
        f"- Existing agents: {', '.join(current_agents)}",
        f"- Target project: {project_id or 'global / not project-specific'}",
        "",
        "## How This Agent Will Be Added",
        "",
        "1. Copy the bundled profile template into the local profiles directory if needed.",
        "2. Add the packaged registry entry to `agent-system/agents.registry.json`.",
        "3. Add packaged workflow definitions and route tests.",
        "4. Optionally add the Agent to the selected project roster.",
        "5. Run router health checks before the Agent becomes active.",
        "",
        "## Workflow Impact",
        "",
    ]
    if workflows:
        for name, workflow in workflows.items():
            lines.append(f"- {name}: {workflow.get('label', '')}")
    else:
        lines.append("- No extra workflows declared by the package.")
    lines.extend(["", "## Route Tests", ""])
    if route_tests:
        for test in route_tests:
            lines.append(f"- `{test.get('prompt')}` -> `{test.get('expect')}`")
    else:
        lines.append("- No route tests declared by the package.")
    lines.extend(
        [
            "",
            "## User Confirmation Required",
            "",
            "The new Agent is not registered yet. Show this report in the GUI and wait for user confirmation.",
            "",
            "Available GUI actions:",
            "",
            "1. Confirm: register and deploy this Agent into the selected workflow.",
            "2. Tune Through Conversation: keep discussing and update the integration report before deployment.",
            "3. Pause: do not process now; keep the task suspended until the user returns.",
        ]
    )
    write_text(target, "\n".join(lines) + "\n")
    state = {
        "report_id": report_id,
        "request_id": safe_component(args.request_id, "request id") if args.request_id else None,
        "agent_id": agent_id,
        "status": "pending_user_confirmation",
        "status_label": STATUS_LABELS["pending_user_confirmation"],
        "package": str(package_dir),
        "manifest": str(manifest_path),
        "report": str(target.relative_to(root)),
        "project_id": project_id,
        "created_at": now_iso(),
        "allowed_actions": ["confirm", "tune", "pause"],
    }
    write_json(root / "agent-plugins" / "status" / f"{report_id}.json", state)
    if args.request_id:
        request_id = safe_component(args.request_id, "request id")
        status_file = root / "agent-requests" / "status" / f"{request_id}.json"
        request_state = read_json(status_file) if status_file.exists() else {"request_id": args.request_id}
        request_state["status"] = "pending_user_confirmation"
        request_state["status_label"] = STATUS_LABELS["pending_user_confirmation"]
        request_state["agent_plugin_report"] = str(target.relative_to(root))
        request_state["agent_plugin_report_id"] = report_id
        request_state["status_updated_at"] = now_iso()
        write_json(status_file, request_state)
    append_log(root, {"event": "agent_plugin_report", "agent": agent_id, "report": str(target.relative_to(root)), "report_id": report_id})
    print(str(target))
    return 0


def agent_plugin_decision(args: argparse.Namespace) -> int:
    root = system_root()
    report_id = safe_component(args.report_id, "report id")
    status_file = root / "agent-plugins" / "status" / f"{report_id}.json"
    if not status_file.exists():
        print(f"office-system: plugin report status not found: {report_id}", file=sys.stderr)
        return 2
    state = read_json(status_file)
    if args.decision == "confirm":
        state["status"] = "confirmed_for_activation"
        state["status_label"] = STATUS_LABELS["confirmed_for_activation"]
        state["next_action"] = f"run agent-plugin-activate --report-id {report_id} --confirmed"
        state.pop("pause_reason", None)
    elif args.decision == "tune":
        state["status"] = "needs_tuning"
        state["status_label"] = STATUS_LABELS["needs_tuning"]
        state.pop("pause_reason", None)
        if args.message:
            state.setdefault("tuning_notes", []).append({"time": now_iso(), "message": args.message})
        state["next_action"] = "secretary continues requirement conversation and regenerates the integration report"
    elif args.decision == "pause":
        state["status"] = "paused_by_user"
        state["status_label"] = STATUS_LABELS["paused_by_user"]
        if args.message:
            state["pause_reason"] = args.message
        state["next_action"] = "do nothing until the user resumes"
    state["decision_updated_at"] = now_iso()
    write_json(status_file, state)
    append_log(root, {"event": "agent_plugin_decision", "report_id": report_id, "decision": args.decision})
    print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def agent_plugin_activate(args: argparse.Namespace) -> int:
    root = system_root()
    request_id = safe_component(args.request_id, "request id") if args.request_id else None
    project_id = safe_component(args.project, "project id") if args.project else ""
    if not args.confirmed:
        print("office-system: Agent plugin activation requires --confirmed after user review of the integration report", file=sys.stderr)
        return 2
    if not args.report_id:
        print("office-system: Agent plugin activation requires --report-id after the user confirms an integration report", file=sys.stderr)
        return 2
    report_id = safe_component(args.report_id, "report id")
    report_status_file = root / "agent-plugins" / "status" / f"{report_id}.json"
    if not report_status_file.exists():
        print(f"office-system: plugin report status not found: {report_id}", file=sys.stderr)
        return 2
    report_state = read_json(report_status_file)
    if report_state.get("status") != "confirmed_for_activation":
        print("office-system: Agent plugin activation requires a confirmed integration report", file=sys.stderr)
        return 2
    report_request = report_state.get("request_id") or None
    if request_id != report_request:
        print("office-system: activation request id must match the confirmed integration report", file=sys.stderr)
        return 2
    report_project = report_state.get("project_id") or ""
    if project_id != report_project:
        print("office-system: activation project must match the confirmed integration report", file=sys.stderr)
        return 2
    if args.report:
        report_path = Path(args.report).expanduser()
        if not report_path.is_absolute():
            report_path = root / args.report
        if not report_path.exists():
            print(f"office-system: integration report not found: {args.report}", file=sys.stderr)
            return 2
    package_dir, manifest_path, manifest = resolve_plugin_manifest(args.package)
    registry_entry = manifest.get("registry_entry")
    if not isinstance(registry_entry, dict):
        print("office-system: Agent plugin manifest must include registry_entry", file=sys.stderr)
        return 2
    agent_id = manifest.get("agent_id") or registry_entry.get("id")
    if not agent_id:
        print("office-system: Agent plugin manifest must contain agent_id", file=sys.stderr)
        return 2
    agent_id = safe_component(agent_id, "agent id")
    if report_state.get("agent_id") and report_state.get("agent_id") != agent_id:
        print("office-system: Agent plugin package does not match the confirmed integration report", file=sys.stderr)
        return 2

    registry_path_value = root / "agents.registry.json"
    registry = read_json(registry_path_value)
    if agent_id in registry.get("agents", {}) and not args.replace_agent:
        print(f"office-system: agent already registered: {agent_id}; pass --replace-agent to replace", file=sys.stderr)
        return 2

    stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    target_profile: Path | None = None
    profile_backup: Path | None = None
    profile_name = registry_entry.get("profile")
    if profile_name:
        profile_name = safe_component(profile_name, "profile name")
        source_profile = package_dir / "profiles" / profile_name
        target_profile = root.parent / "profiles" / profile_name
        if source_profile.exists():
            if target_profile.exists() and not args.replace_profile:
                print(f"office-system: profile already exists: {target_profile}; pass --replace-profile to replace", file=sys.stderr)
                return 2
            if target_profile.exists():
                profile_backup = target_profile.with_name(f"{target_profile.name}.bak.{stamp}")
                shutil.copytree(target_profile, profile_backup)
                shutil.rmtree(target_profile)
            shutil.copytree(source_profile, target_profile)

    backup = registry_path_value.with_suffix(f".json.bak.{stamp}")
    shutil.copy2(registry_path_value, backup)
    entry = dict(registry_entry)
    entry.pop("id", None)
    registry.setdefault("agents", {})[agent_id] = entry
    registry.setdefault("aliases", {}).update(manifest.get("aliases", {}))
    registry.setdefault("workflows", {}).update(manifest.get("workflows", {}))
    registry.setdefault("route_tests", []).extend(manifest.get("route_tests", []))
    write_json(registry_path_value, registry)

    project_file: Path | None = None
    project_backup: dict[str, Any] | None = None
    if project_id:
        project_dir = ensure_project(root, project_id)
        project_file = project_dir / "project.json"
        project = read_json(project_file)
        project_backup = json.loads(json.dumps(project))
        roster = project.setdefault("agent_roster", [])
        if agent_id not in roster:
            roster.append(agent_id)
        write_json(project_file, project)

    router = root.parent / "scripts" / "agent-router"
    health_proc = subprocess.run([str(router), "--health"], text=True, capture_output=True)
    if health_proc.returncode != 0:
        shutil.copy2(backup, registry_path_value)
        if project_file and project_backup is not None:
            write_json(project_file, project_backup)
        if target_profile and target_profile.exists():
            shutil.rmtree(target_profile)
        if profile_backup and profile_backup.exists():
            shutil.copytree(profile_backup, target_profile)
        print("office-system: router health failed after Agent registration; registry rolled back", file=sys.stderr)
        if health_proc.stdout:
            print(health_proc.stdout, file=sys.stderr)
        if health_proc.stderr:
            print(health_proc.stderr, file=sys.stderr)
        return 1

    state = {
        "agent_id": agent_id,
        "status": "activated",
        "status_label": STATUS_LABELS["downloaded_deployed"],
        "request_id": request_id,
        "report_id": report_id,
        "package": str(package_dir),
        "manifest": str(manifest_path),
        "registry_backup": str(backup),
        "project_id": project_id,
        "router_health": "passed",
    }
    if request_id:
        status_file = root / "agent-requests" / "status" / f"{request_id}.json"
        request_state = read_json(status_file) if status_file.exists() else {"request_id": request_id}
        request_state["status"] = "downloaded_deployed"
        request_state["status_label"] = STATUS_LABELS["downloaded_deployed"]
        request_state["deployed_agent_id"] = agent_id
        request_state["status_updated_at"] = now_iso()
        write_json(status_file, request_state)
    report_state["status"] = "activated"
    report_state["status_label"] = STATUS_LABELS["downloaded_deployed"]
    report_state["activated_agent_id"] = agent_id
    report_state["activated_at"] = now_iso()
    write_json(report_status_file, report_state)
    append_log(root, {"event": "agent_plugin_activate", "agent": agent_id, "project": project_id})
    print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def consent_path(root: Path) -> Path:
    configured = os.environ.get("DIGITAL_OFFICE_CONSENT_FILE")
    if configured:
        return Path(configured).expanduser()
    return root / "data-sharing" / "consent.json"


def load_consent(root: Path) -> dict[str, Any]:
    path = consent_path(root)
    if path.exists():
        return read_json(path)
    example = root / "data-sharing" / "consent.example.json"
    if example.exists():
        return read_json(example)
    return {"enabled": False, "allowed_scopes": {}}


REDACTION_PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "phone_cn": re.compile(r"\b1[3-9]\d{9}\b"),
    "id_card_cn": re.compile(r"\b\d{17}[\dXx]\b"),
    "api_key": re.compile(r"\b(?:sk|gho|ghp|xoxb|hf)_[A-Za-z0-9_\-]{16,}\b"),
    "bearer_token": re.compile(r"Bearer\s+[A-Za-z0-9._\-]{16,}", re.IGNORECASE),
    "secret_like": re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*[^\s,;]{6,}"),
}


def redact_text(text: str, consent: dict[str, Any]) -> str:
    redaction = consent.get("redaction", {})
    if not redaction.get("enabled", True):
        return text
    replacement = redaction.get("replace_with", "[REDACTED]")
    for name in redaction.get("patterns", []):
        pattern = REDACTION_PATTERNS.get(name)
        if pattern:
            text = pattern.sub(replacement, text)
    return text


def redact_obj(value: Any, consent: dict[str, Any]) -> Any:
    if isinstance(value, str):
        return redact_text(value, consent)
    if isinstance(value, list):
        return [redact_obj(item, consent) for item in value]
    if isinstance(value, dict):
        return {key: redact_obj(item, consent) for key, item in value.items()}
    return value


def read_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return rows[-limit:] if limit else rows


def approved_methodology_summaries(root: Path, consent: dict[str, Any]) -> list[dict[str, Any]]:
    allowed = (
        consent.get("industry_experience_sharing", {}).get("enabled", False)
        and consent.get("allowed_scopes", {}).get("approved_methodologies", False)
    )
    if not allowed:
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted((root / "knowledge" / "company" / "methodologies" / "approved").glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        rows.append(
            {
                "path": str(path.relative_to(root)),
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "text": redact_text(text, consent),
            }
        )
    return rows


def relay_summaries(root: Path, consent: dict[str, Any]) -> list[dict[str, Any]]:
    allowed = (
        consent.get("industry_experience_sharing", {}).get("enabled", False)
        and consent.get("allowed_scopes", {}).get("project_relay_summaries", False)
    )
    if not allowed:
        return []
    rows: list[dict[str, Any]] = []
    for outbox in sorted((root / "projects").glob("*/relay/keymemory-outbox.jsonl")):
        for row in read_jsonl(outbox):
            sanitized = redact_obj(row, consent)
            project_id = str(sanitized.get("project_id", ""))
            subproject_id = str(sanitized.get("subproject_id", ""))
            source_refs = sanitized.get("source_refs", []) or []
            sanitized["project_hash"] = hashlib.sha256(project_id.encode("utf-8")).hexdigest() if project_id else ""
            sanitized["subproject_hash"] = hashlib.sha256(subproject_id.encode("utf-8")).hexdigest() if subproject_id else ""
            sanitized["source_ref_hashes"] = [
                hashlib.sha256(str(ref).encode("utf-8")).hexdigest() for ref in source_refs
            ]
            sanitized.pop("project_id", None)
            sanitized.pop("subproject_id", None)
            sanitized.pop("source_refs", None)
            rows.append(sanitized)
    return rows


def telemetry_payload(root: Path, consent: dict[str, Any]) -> dict[str, Any]:
    allowed = consent.get("allowed_scopes", {})
    health_data = {
        "agents_registry": (root / "agents.registry.json").exists(),
        "knowledge_registry": (root / "knowledge.registry.json").exists(),
        "rules_registry": (root / "rules" / "rules.registry.json").exists(),
        "multimodal_pipeline": (root / "multimodal.pipeline.json").exists(),
        "rag_pipeline": (root / "rag.pipeline.json").exists(),
        "tesseract": bool(shutil.which("tesseract")),
        "pdftotext": bool(shutil.which("pdftotext")),
        "sentence_transformers": bool(importlib.util.find_spec("sentence_transformers")),
    }
    payload: dict[str, Any] = {
        "version": "1.0.0",
        "tenant_id": consent.get("tenant_id"),
        "exported_at": now_iso(),
        "mode": consent.get("mode"),
        "experience_telemetry": consent.get("experience_telemetry", {}),
        "industry_experience_sharing": consent.get("industry_experience_sharing", {}),
        "contains_raw_documents": false_value(),
        "contains_raw_images": false_value(),
        "contains_raw_keymemory_records": false_value(),
        "health": health_data if allowed.get("system_health", True) else {},
        "model_capability_status": health_data if allowed.get("model_capability_status", True) else {},
        "route_events": read_jsonl(root / "logs" / "router-events.jsonl", limit=500) if allowed.get("agent_routes", True) else [],
        "office_events": read_jsonl(root / "logs" / "office-system.jsonl", limit=500) if allowed.get("workflow_metrics", True) else [],
        "approved_methodologies": approved_methodology_summaries(root, consent),
        "project_relay_summaries": relay_summaries(root, consent),
    }
    return redact_obj(payload, consent)


def false_value() -> bool:
    return False


def telemetry_status(args: argparse.Namespace) -> int:
    root = system_root()
    consent = load_consent(root)
    status = {
        "consent_file": str(consent_path(root)),
        "enabled": consent.get("enabled", False),
        "server_configured": bool(consent.get("server_url")),
        "experience_telemetry_enabled": consent.get("experience_telemetry", {}).get("enabled", False),
        "industry_experience_sharing_enabled": consent.get("industry_experience_sharing", {}).get("enabled", False),
        "allowed_scopes": consent.get("allowed_scopes", {}),
    }
    print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def telemetry_export(args: argparse.Namespace) -> int:
    root = system_root()
    consent = load_consent(root)
    if not consent.get("enabled", False):
        print("office-system: telemetry disabled by consent file", file=sys.stderr)
        return 2
    payload = telemetry_payload(root, consent)
    stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    target = root / "data-sharing" / "exports" / f"{stamp}-telemetry-bundle.json"
    write_json(target, payload)
    append_log(root, {"event": "telemetry_export", "target": str(target.relative_to(root))})
    print(str(target))
    return 0


def telemetry_send(args: argparse.Namespace) -> int:
    root = system_root()
    consent = load_consent(root)
    if not consent.get("enabled", False):
        print("office-system: telemetry disabled by consent file", file=sys.stderr)
        return 2
    if consent.get("review", {}).get("require_admin_review_before_send", True) and not args.confirmed:
        print("office-system: telemetry-send requires --confirmed after admin review", file=sys.stderr)
        return 2
    server_url = consent.get("server_url")
    if not server_url:
        print("office-system: telemetry server_url is not configured", file=sys.stderr)
        return 2
    token = os.environ.get(consent.get("auth_env", "DIGITAL_OFFICE_TELEMETRY_TOKEN"), "")
    bundle = Path(args.bundle).expanduser()
    if not bundle.is_absolute():
        bundle = root / "data-sharing" / "exports" / args.bundle
    if not bundle.exists():
        print(f"office-system: bundle not found: {bundle}", file=sys.stderr)
        return 2
    data = bundle.read_bytes()
    request = urllib.request.Request(server_url, data=data, method="POST")
    request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            receipt = {
                "time": now_iso(),
                "bundle": str(bundle.relative_to(root)) if bundle.is_relative_to(root) else str(bundle),
                "server_url": server_url,
                "status": response.status,
                "response": body[:2000],
            }
    except urllib.error.URLError as exc:
        print(f"office-system: telemetry send failed: {exc}", file=sys.stderr)
        return 1
    target = root / "data-sharing" / "receipts" / f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-receipt.json"
    write_json(target, receipt)
    append_log(root, {"event": "telemetry_send", "receipt": str(target.relative_to(root))})
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def identity_context(args: argparse.Namespace) -> int:
    root = system_root()
    project = safe_component(args.project, "project id") if args.project else ""
    agent = registered_agent(root, args.agent) if args.agent else ""
    if project:
        ensure_project(root, project)
    claims = {
        "version": "1.0.0",
        "kind": "digital-office-identity-context",
        "tenant_id": safe_claim(args.tenant, "tenant id"),
        "deployment_id": safe_claim(args.deployment, "deployment id"),
        "user_id": safe_claim(args.user, "user id"),
        "user_role": safe_claim(args.role, "user role"),
        "project_id": project,
        "agent_id": agent,
        "workflow_run_id": safe_claim(args.workflow_run, "workflow run id", required=False),
        "session_id": safe_claim(args.session, "session id", required=False),
        "created_at": now_iso(),
    }
    append_log(root, {"event": "identity_context", "tenant_id": claims["tenant_id"], "deployment_id": claims["deployment_id"], "user_id": claims["user_id"], "project": project, "agent": agent})
    print(json.dumps(claims, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


CUSTOMER_OWNED_MOUNT_TARGETS = {"company_knowledge", "project_knowledge", "agent_specialist_context"}
PROVIDER_SOLD_MOUNT_TARGETS = {"licensed_company_reference", "licensed_project_reference", "licensed_agent_reference"}


def knowledge_source_mount(args: argparse.Namespace) -> int:
    root = system_root()
    source_class = args.source_class
    mount_target = args.mount_target
    project = safe_component(args.project, "project id") if args.project else ""
    agent = registered_agent(root, args.agent) if args.agent else ""
    if project:
        ensure_project(root, project)
    if mount_target in {"project_knowledge", "licensed_project_reference"} and not project:
        print("office-system: project-scoped knowledge mounts require --project", file=sys.stderr)
        return 2
    if mount_target in {"agent_specialist_context", "licensed_agent_reference"} and not agent:
        print("office-system: agent-scoped knowledge mounts require --agent", file=sys.stderr)
        return 2
    if source_class == "customer_owned_external_kb" and mount_target not in CUSTOMER_OWNED_MOUNT_TARGETS:
        print("office-system: customer-owned external KB cannot be mounted as licensed industry reference", file=sys.stderr)
        return 2
    if source_class == "provider_sold_industry_kb" and mount_target not in PROVIDER_SOLD_MOUNT_TARGETS:
        print("office-system: provider-sold industry KB must be mounted as licensed reference, not company/project source storage", file=sys.stderr)
        return 2
    mount_id = args.mount_id or f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{slugify(args.source_id)}"
    mount_id = safe_component(mount_id, "mount id")
    provider_sold = source_class == "provider_sold_industry_kb"
    record = {
        "version": "1.0.0",
        "kind": "digital-office-knowledge-source-mount",
        "mount_id": mount_id,
        "source_class": source_class,
        "source_id": safe_claim(args.source_id, "source id"),
        "display_name": safe_claim(args.display_name or args.source_id, "display name"),
        "provider": safe_claim(args.provider, "provider", required=False),
        "tenant_id": safe_claim(args.tenant, "tenant id"),
        "deployment_id": safe_claim(args.deployment, "deployment id"),
        "created_by": safe_claim(args.created_by, "created by"),
        "mount_target": mount_target,
        "project_id": project,
        "agent_id": agent,
        "entitlement_id": safe_claim(args.entitlement, "entitlement id", required=provider_sold),
        "license_sku": safe_claim(args.license_sku, "license sku", required=False),
        "allowed_users": [safe_claim(item, "allowed user") for item in (args.allowed_user or [])],
        "allowed_roles": [safe_claim(item, "allowed role") for item in (args.allowed_role or [])],
        "inside_digital_office_only": provider_sold,
        "download_allowed": not provider_sold,
        "export_allowed": not provider_sold,
        "plain_source_files_on_customer_host": not provider_sold,
        "retrieval_mode": "controlled_remote_retrieval" if provider_sold else args.sync_mode,
        "created_at": now_iso(),
        "status": "active",
    }
    target = root / "knowledge" / "mounts" / f"{mount_id}.json"
    if target.exists() and not args.replace:
        print(f"office-system: knowledge mount already exists: {mount_id}; pass --replace to replace", file=sys.stderr)
        return 2
    write_json(target, record)
    append_log(root, {"event": "knowledge_source_mounted", "mount_id": mount_id, "source_class": source_class, "mount_target": mount_target, "tenant_id": record["tenant_id"], "deployment_id": record["deployment_id"], "created_by": record["created_by"]})
    print(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def load_mount_record(root: Path, mount_id: str) -> dict[str, Any]:
    mount_id = safe_component(mount_id, "mount id")
    path = root / "knowledge" / "mounts" / f"{mount_id}.json"
    if not path.exists():
        print(f"office-system: knowledge mount not found: {mount_id}", file=sys.stderr)
        raise SystemExit(2)
    return read_json(path)


def validate_mount_access(args: argparse.Namespace, mount: dict[str, Any], project: str, agent: str) -> int:
    if mount.get("status") != "active":
        print("office-system: knowledge mount is not active", file=sys.stderr)
        return 2
    if mount.get("source_class") != args.source_class:
        print("office-system: knowledge access source class does not match mount", file=sys.stderr)
        return 2
    if mount.get("source_id") != args.source_id:
        print("office-system: knowledge access source id does not match mount", file=sys.stderr)
        return 2
    if mount.get("project_id") and mount.get("project_id") != project:
        print("office-system: knowledge access project does not match mount scope", file=sys.stderr)
        return 2
    if mount.get("agent_id") and mount.get("agent_id") != agent:
        print("office-system: knowledge access Agent does not match mount scope", file=sys.stderr)
        return 2

    allowed_users = mount.get("allowed_users") or []
    allowed_roles = mount.get("allowed_roles") or []
    if args.decision == "allow":
        if allowed_users and args.user not in allowed_users:
            print("office-system: user is not allowed by this knowledge mount", file=sys.stderr)
            return 2
        if allowed_roles and args.role not in allowed_roles:
            print("office-system: role is not allowed by this knowledge mount", file=sys.stderr)
            return 2
        if args.source_class == "provider_sold_industry_kb":
            if not args.entitlement:
                print("office-system: provider-sold industry knowledge access requires --entitlement", file=sys.stderr)
                return 2
            if not args.knowledge_pack:
                print("office-system: provider-sold industry knowledge access requires --knowledge-pack", file=sys.stderr)
                return 2
            if args.knowledge_pack != mount.get("source_id"):
                print("office-system: knowledge pack does not match knowledge mount", file=sys.stderr)
                return 2
            if mount.get("entitlement_id") and mount.get("entitlement_id") != args.entitlement:
                print("office-system: entitlement does not match knowledge mount", file=sys.stderr)
                return 2
    return 0


def knowledge_access_log(args: argparse.Namespace) -> int:
    root = system_root()
    project = safe_component(args.project, "project id") if args.project else ""
    agent = registered_agent(root, args.agent) if args.agent else ""
    if project:
        ensure_project(root, project)
    mount_id = safe_component(args.mount_id, "mount id")
    mount = load_mount_record(root, mount_id)
    validation = validate_mount_access(args, mount, project, agent)
    if validation != 0:
        return validation
    query_hash = hashlib.sha256((args.query or "").encode("utf-8")).hexdigest() if args.query else ""
    event = {
        "time": now_iso(),
        "event": "knowledge_access",
        "tenant_id": safe_claim(args.tenant, "tenant id"),
        "deployment_id": safe_claim(args.deployment, "deployment id"),
        "user_id": safe_claim(args.user, "user id"),
        "user_role": safe_claim(args.role, "user role"),
        "project_id": project,
        "agent_id": agent,
        "workflow_run_id": safe_claim(args.workflow_run, "workflow run id", required=False),
        "source_class": args.source_class,
        "source_id": safe_claim(args.source_id, "source id"),
        "mount_id": mount_id,
        "knowledge_pack_id": safe_claim(args.knowledge_pack, "knowledge pack id", required=False),
        "entitlement_id": safe_claim(args.entitlement, "entitlement id", required=False),
        "query_hash": query_hash,
        "result_source_ids": [safe_claim(item, "result source id") for item in (args.result_source_id or [])],
        "snippet_count": args.snippet_count,
        "decision": args.decision,
        "deny_reason": safe_claim(args.deny_reason, "deny reason", required=False),
    }
    log = root / "logs" / "knowledge-access.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    append_log(root, {"event": "knowledge_access_log", "mount_id": event["mount_id"], "source_class": args.source_class, "decision": args.decision, "tenant_id": event["tenant_id"], "deployment_id": event["deployment_id"], "user_id": event["user_id"]})
    print(json.dumps(event, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def knowledge_spaces_root(root: Path) -> Path:
    return root / "knowledge" / "spaces"


def knowledge_space_id_for(space_type: str, *, owner: str = "", project: str = "", team: str = "", workflow_run: str = "") -> str:
    space_type = safe_component(space_type, "knowledge space type")
    if space_type not in KNOWLEDGE_SPACE_TYPES:
        print(f"office-system: invalid knowledge space type: {space_type}", file=sys.stderr)
        raise SystemExit(2)
    if space_type == "personal":
        owner = safe_claim(owner, "space owner")
        return safe_component(f"personal-{slugify(owner)}", "knowledge space id")
    if space_type == "project":
        project = safe_component(project, "project id")
        return safe_component(f"project-{project}", "knowledge space id")
    if space_type == "team":
        team = safe_component(team, "team id")
        return safe_component(f"team-{team}", "knowledge space id")
    if space_type == "workflow_artifacts":
        workflow_run = safe_component(workflow_run, "workflow run id")
        return safe_component(f"workflow-{workflow_run}", "knowledge space id")
    if space_type == "shared_with_me":
        owner = safe_claim(owner, "shared-with-me user")
        return safe_component(f"shared-{slugify(owner)}", "knowledge space id")
    return "company"


def knowledge_space_dir(root: Path, space_id: str) -> Path:
    return knowledge_spaces_root(root) / safe_component(space_id, "knowledge space id")


def knowledge_folder_path(root: Path, space_id: str, folder_id: str) -> Path:
    return knowledge_space_dir(root, space_id) / "folders" / f"{safe_component(folder_id, 'folder id')}.json"


def knowledge_item_path(root: Path, space_id: str, item_id: str) -> Path:
    return knowledge_space_dir(root, space_id) / "items" / f"{safe_component(item_id, 'item id')}.json"


def knowledge_share_path(root: Path, space_id: str, share_id: str) -> Path:
    return knowledge_space_dir(root, space_id) / "shares" / f"{safe_component(share_id, 'share id')}.json"


def ensure_knowledge_space(
    root: Path,
    *,
    space_type: str,
    owner: str = "",
    project: str = "",
    team: str = "",
    workflow_run: str = "",
    created_by: str = "",
) -> dict[str, Any]:
    space_id = knowledge_space_id_for(space_type, owner=owner, project=project, team=team, workflow_run=workflow_run)
    if space_type == "project":
        ensure_project(root, project)
    if space_type == "workflow_artifacts" and not run_record_path(root, workflow_run).exists():
        print(f"office-system: workflow run not found: {workflow_run}", file=sys.stderr)
        raise SystemExit(2)
    if space_type == "shared_with_me":
        return {
            "version": "1.0.0",
            "kind": "digital-office-knowledge-space",
            "space_id": space_id,
            "space_type": "shared_with_me",
            "owner_user_id": safe_claim(owner, "shared-with-me user"),
            "virtual": True,
        }
    directory = knowledge_space_dir(root, space_id)
    record_path = directory / "space.json"
    if record_path.exists():
        return read_json(record_path)
    record = {
        "version": "1.0.0",
        "kind": "digital-office-knowledge-space",
        "space_id": space_id,
        "space_type": space_type,
        "owner_user_id": safe_claim(owner, "space owner", required=space_type == "personal"),
        "project_id": safe_component(project, "project id") if project else "",
        "team_id": safe_component(team, "team id") if team else "",
        "workflow_run_id": safe_component(workflow_run, "workflow run id") if workflow_run else "",
        "default_visibility": "private" if space_type == "personal" else space_type,
        "created_by": safe_claim(created_by, "created by", required=False),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    write_json(record_path, record)
    root_folder = {
        "version": "1.0.0",
        "kind": "digital-office-knowledge-folder",
        "space_id": space_id,
        "folder_id": "root",
        "parent_folder_id": "",
        "title": "Root",
        "created_by": record["created_by"],
        "created_at": record["created_at"],
        "updated_at": record["updated_at"],
    }
    write_json(knowledge_folder_path(root, space_id, "root"), root_folder)
    append_log(root, {"event": "knowledge_space_created", "space_id": space_id, "space_type": space_type, "created_by": record["created_by"]})
    return record


def load_knowledge_space(root: Path, space_id: str) -> dict[str, Any]:
    path = knowledge_space_dir(root, space_id) / "space.json"
    if not path.exists():
        print(f"office-system: knowledge space not found: {space_id}", file=sys.stderr)
        raise SystemExit(2)
    return read_json(path)


def load_knowledge_folders(root: Path, space_id: str) -> list[dict[str, Any]]:
    return read_records(knowledge_space_dir(root, space_id) / "folders", "digital-office-knowledge-folder")


def load_knowledge_items(root: Path, space_id: str) -> list[dict[str, Any]]:
    return read_records(knowledge_space_dir(root, space_id) / "items", "digital-office-knowledge-item")


def load_knowledge_shares(root: Path, space_id: str) -> list[dict[str, Any]]:
    return read_records(knowledge_space_dir(root, space_id) / "shares", "digital-office-knowledge-share")


def space_from_args(root: Path, args: argparse.Namespace, *, create: bool = True) -> dict[str, Any]:
    space_type = args.space_type
    owner = getattr(args, "owner", "") or getattr(args, "user", "") or getattr(args, "created_by", "") or getattr(args, "shared_by", "")
    project = getattr(args, "project", "") or ""
    team = getattr(args, "team", "") or ""
    workflow_run = getattr(args, "workflow_run", "") or ""
    if create:
        return ensure_knowledge_space(root, space_type=space_type, owner=owner, project=project, team=team, workflow_run=workflow_run, created_by=getattr(args, "created_by", "") or getattr(args, "shared_by", "") or getattr(args, "user", ""))
    space_id = knowledge_space_id_for(space_type, owner=owner, project=project, team=team, workflow_run=workflow_run)
    if space_type == "shared_with_me":
        return ensure_knowledge_space(root, space_type=space_type, owner=owner, project=project, team=team, workflow_run=workflow_run, created_by="")
    return load_knowledge_space(root, space_id)


def target_matches_share(share: dict[str, Any], *, user: str, role: str, agent: str, project: str, workflow_run: str) -> bool:
    target_type = share.get("target_type")
    target_id = share.get("target_id")
    return (
        (target_type == "user" and target_id == user)
        or (target_type == "role" and target_id == role)
        or (target_type == "agent" and target_id == agent)
        or (target_type == "project" and target_id == project)
        or (target_type == "workflow" and target_id == workflow_run)
    )


def permission_rank(permission: str) -> int:
    return {"read": 1, "write": 2, "manage": 3}.get(permission, 0)


def folder_lineage(root: Path, space_id: str, folder_id: str) -> list[str]:
    folders = {folder.get("folder_id"): folder for folder in load_knowledge_folders(root, space_id)}
    lineage: list[str] = []
    current = safe_component(folder_id, "folder id")
    seen: set[str] = set()
    while current and current not in seen and current in folders:
        lineage.append(current)
        seen.add(current)
        current = folders[current].get("parent_folder_id", "")
    if "root" not in lineage:
        lineage.append("root")
    return lineage


def knowledge_resource_targets(root: Path, space_id: str, resource_type: str, resource_id: str) -> tuple[list[str], list[str]]:
    resource_type = safe_component(resource_type, "knowledge resource type")
    resource_id = safe_component(resource_id, "knowledge resource id")
    if resource_type == "folder":
        if not knowledge_folder_path(root, space_id, resource_id).exists():
            print(f"office-system: folder not found: {resource_id}", file=sys.stderr)
            raise SystemExit(2)
        return [], folder_lineage(root, space_id, resource_id)
    if resource_type == "item":
        item_path = knowledge_item_path(root, space_id, resource_id)
        if not item_path.exists():
            print(f"office-system: item not found: {resource_id}", file=sys.stderr)
            raise SystemExit(2)
        item = read_json(item_path)
        return [resource_id], folder_lineage(root, space_id, item.get("folder_id", "root"))
    print(f"office-system: invalid knowledge resource type: {resource_type}", file=sys.stderr)
    raise SystemExit(2)


def share_applies_to_resource(share: dict[str, Any], *, item_ids: list[str], folder_ids: list[str]) -> bool:
    resource_type = share.get("resource_type")
    resource_id = share.get("resource_id")
    if resource_type == "item":
        return resource_id in item_ids
    if resource_type == "folder":
        if resource_id not in folder_ids:
            return False
        if share.get("inherit", True):
            return True
        return not item_ids and bool(folder_ids) and resource_id == folder_ids[0]
    return False


def knowledge_access_allowed(
    root: Path,
    *,
    space: dict[str, Any],
    resource_type: str,
    resource_id: str,
    permission: str,
    user: str,
    role: str,
    agent: str = "",
    project: str = "",
    workflow_run: str = "",
) -> dict[str, Any]:
    permission = safe_component(permission, "knowledge permission")
    if permission not in KNOWLEDGE_PERMISSIONS:
        print(f"office-system: invalid knowledge permission: {permission}", file=sys.stderr)
        raise SystemExit(2)
    user = safe_claim(user, "user id")
    role = safe_component(role, "user role")
    agent = registered_agent(root, agent) if agent else ""
    project = safe_component(project, "project id") if project else space.get("project_id", "")
    workflow_run = safe_component(workflow_run, "workflow run id") if workflow_run else ""
    space_id = space["space_id"]
    item_ids, folder_ids = knowledge_resource_targets(root, space_id, resource_type, resource_id)
    matching_shares = [
        share
        for share in load_knowledge_shares(root, space_id)
        if target_matches_share(share, user=user, role=role, agent=agent, project=project, workflow_run=workflow_run)
        and share_applies_to_resource(share, item_ids=item_ids, folder_ids=folder_ids)
        and permission_rank(share.get("permission", "")) >= permission_rank(permission)
    ]
    denies = [share for share in matching_shares if share.get("effect") == "deny"]
    if denies:
        return {"allowed": False, "outcome": "deny", "reasons": ["explicit deny share matched"], "matched_shares": [share.get("share_id") for share in denies]}
    allows = [share for share in matching_shares if share.get("effect") == "allow"]
    if allows:
        return {"allowed": True, "outcome": "allow", "reasons": ["explicit allow share matched"], "matched_shares": [share.get("share_id") for share in allows]}

    space_type = space.get("space_type")
    owner_user_id = space.get("owner_user_id", "")
    if space_type == "personal":
        if owner_user_id and user == owner_user_id:
            return {"allowed": True, "outcome": "allow", "reasons": ["personal space owner"], "matched_shares": []}
        return {"allowed": False, "outcome": "deny", "reasons": ["personal space is private by default"], "matched_shares": []}
    if space_type == "project":
        auth = compute_authorization_decision(root, tenant_id="local", deployment_id="local", user_id=user, user_role=role, action="knowledge.read" if permission == "read" else "knowledge.manage", resource_type="knowledge", resource_id=space_id, project_id=space.get("project_id", ""), audit=False)
        return {"allowed": auth["allowed"], "outcome": auth["outcome"], "reasons": auth["reasons"] or [f"project space {permission} allowed by role"], "matched_shares": []}
    if space_type in {"team", "company", "workflow_artifacts"}:
        action = "knowledge.read" if permission == "read" else "knowledge.manage"
        allowed = role_allows_action(role, action)
        return {"allowed": allowed, "outcome": "allow" if allowed else "deny", "reasons": [f"role {role} {'can' if allowed else 'cannot'} perform {action}"], "matched_shares": []}
    return {"allowed": False, "outcome": "deny", "reasons": ["unsupported knowledge space type"], "matched_shares": []}


def append_knowledge_acl_log(root: Path, event: dict[str, Any]) -> dict[str, Any]:
    event = {"time": now_iso(), "event": "knowledge_acl_access", **event}
    append_jsonl(root / "logs" / "knowledge-access.jsonl", event)
    append_log(root, {"event": "knowledge_acl_access", "space_id": event.get("space_id", ""), "resource_type": event.get("resource_type", ""), "resource_id": event.get("resource_id", ""), "decision": event.get("outcome", "")})
    return event


def authorize_knowledge_manage(root: Path, space: dict[str, Any], *, user: str, role: str) -> dict[str, Any]:
    user = safe_claim(user, "user id")
    role = safe_component(role, "user role")
    if space.get("space_type") == "personal" and space.get("owner_user_id") == user:
        return {"allowed": True, "outcome": "allow", "reasons": ["personal space owner"]}
    return compute_authorization_decision(root, tenant_id="local", deployment_id="local", user_id=user, user_role=role, action="knowledge.manage", resource_type="knowledge", resource_id=space.get("space_id", ""), project_id=space.get("project_id", ""), audit=False)


def knowledge_folder_create(args: argparse.Namespace) -> int:
    root = system_root()
    space = space_from_args(root, args, create=True)
    auth = authorize_knowledge_manage(root, space, user=args.created_by, role=args.role)
    if not auth["allowed"]:
        print(json.dumps({"authorization": auth, "status": "denied"}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    folder_id = safe_component(args.folder_id or slugify(args.title), "folder id")
    parent_id = safe_component(args.parent_folder, "parent folder id")
    if not knowledge_folder_path(root, space["space_id"], parent_id).exists():
        print(f"office-system: parent folder not found: {parent_id}", file=sys.stderr)
        return 2
    target = knowledge_folder_path(root, space["space_id"], folder_id)
    if target.exists() and not args.replace:
        print(f"office-system: folder already exists: {folder_id}; pass --replace to replace", file=sys.stderr)
        return 2
    record = {
        "version": "1.0.0",
        "kind": "digital-office-knowledge-folder",
        "space_id": space["space_id"],
        "folder_id": folder_id,
        "parent_folder_id": parent_id,
        "title": safe_claim(args.title, "folder title"),
        "created_by": safe_claim(args.created_by, "created by"),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    write_json(target, record)
    append_audit_event(root, "knowledge_folder_created", actor_id=args.created_by, actor_role=args.role, project_id=space.get("project_id", ""), resource_type="knowledge_folder", resource_id=folder_id, outcome="created", extra={"space_id": space["space_id"]})
    print(json.dumps({"space": space, "folder": record}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def knowledge_item_add(args: argparse.Namespace) -> int:
    root = system_root()
    space = space_from_args(root, args, create=True)
    auth = authorize_knowledge_manage(root, space, user=args.created_by, role=args.role)
    if not auth["allowed"]:
        print(json.dumps({"authorization": auth, "status": "denied"}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    folder_id = safe_component(args.folder_id, "folder id")
    if not knowledge_folder_path(root, space["space_id"], folder_id).exists():
        print(f"office-system: folder not found: {folder_id}", file=sys.stderr)
        return 2
    item_id = safe_component(args.item_id or f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{slugify(args.title)}", "item id")
    target = knowledge_item_path(root, space["space_id"], item_id)
    if target.exists() and not args.replace:
        print(f"office-system: item already exists: {item_id}; pass --replace to replace", file=sys.stderr)
        return 2
    record = {
        "version": "1.0.0",
        "kind": "digital-office-knowledge-item",
        "space_id": space["space_id"],
        "item_id": item_id,
        "folder_id": folder_id,
        "title": safe_claim(args.title, "item title"),
        "source_ref": safe_claim(args.source_ref, "source reference"),
        "content_type": safe_claim(args.content_type or "application/octet-stream", "content type"),
        "connector_id": safe_claim(args.connector_id, "connector id", required=False),
        "snapshot_mode_default": True,
        "created_by": safe_claim(args.created_by, "created by"),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    write_json(target, record)
    append_audit_event(root, "knowledge_item_added", actor_id=args.created_by, actor_role=args.role, project_id=space.get("project_id", ""), resource_type="knowledge_item", resource_id=item_id, outcome="created", extra={"space_id": space["space_id"], "folder_id": folder_id})
    print(json.dumps({"space": space, "item": record}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def knowledge_share(args: argparse.Namespace) -> int:
    root = system_root()
    space = space_from_args(root, args, create=True)
    auth = authorize_knowledge_manage(root, space, user=args.shared_by, role=args.role)
    if not auth["allowed"]:
        print(json.dumps({"authorization": auth, "status": "denied"}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    resource_type = safe_component(args.resource_type, "knowledge resource type")
    resource_id = safe_component(args.resource_id, "knowledge resource id")
    knowledge_resource_targets(root, space["space_id"], resource_type, resource_id)
    target_type = safe_component(args.target_type, "share target type")
    if target_type not in KNOWLEDGE_TARGET_TYPES:
        print(f"office-system: invalid share target type: {target_type}", file=sys.stderr)
        return 2
    permission = safe_component(args.permission, "knowledge permission")
    if permission not in KNOWLEDGE_PERMISSIONS:
        print(f"office-system: invalid knowledge permission: {permission}", file=sys.stderr)
        return 2
    share_id = safe_component(args.share_id or f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}", "share id")
    record = {
        "version": "1.0.0",
        "kind": "digital-office-knowledge-share",
        "share_id": share_id,
        "space_id": space["space_id"],
        "resource_type": resource_type,
        "resource_id": resource_id,
        "effect": args.effect,
        "permission": permission,
        "target_type": target_type,
        "target_id": safe_claim(args.target_id, "share target id"),
        "inherit": not args.no_inherit,
        "created_by": safe_claim(args.shared_by, "shared by"),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "reason": safe_claim(args.reason, "share reason", required=False),
    }
    write_json(knowledge_share_path(root, space["space_id"], share_id), record)
    append_audit_event(root, "knowledge_share_updated", actor_id=args.shared_by, actor_role=args.role, project_id=space.get("project_id", ""), resource_type="knowledge_share", resource_id=share_id, outcome=args.effect, reason=args.reason or "", extra={"space_id": space["space_id"]})
    print(json.dumps({"space": space, "share": record}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def knowledge_access_check(args: argparse.Namespace) -> int:
    root = system_root()
    space = space_from_args(root, args, create=False)
    decision = knowledge_access_allowed(root, space=space, resource_type=args.resource_type, resource_id=args.resource_id, permission=args.permission, user=args.user, role=args.role, agent=args.agent or "", project=args.project or "", workflow_run=args.workflow_run or "")
    event = append_knowledge_acl_log(
        root,
        {
            "space_id": space["space_id"],
            "space_type": space.get("space_type", ""),
            "resource_type": args.resource_type,
            "resource_id": args.resource_id,
            "permission": args.permission,
            "user_id": args.user,
            "user_role": args.role,
            "agent_id": args.agent or "",
            "project_id": args.project or space.get("project_id", ""),
            "workflow_run_id": args.workflow_run or "",
            "outcome": decision["outcome"],
            "reasons": decision["reasons"],
        },
    )
    print(json.dumps({"space": space, "decision": decision, "access_event": event}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if decision["allowed"] else 2


def folder_descendants(folders: list[dict[str, Any]], folder_id: str) -> set[str]:
    children: dict[str, list[str]] = {}
    for folder in folders:
        children.setdefault(folder.get("parent_folder_id", ""), []).append(folder.get("folder_id", ""))
    seen: set[str] = set()
    stack = [folder_id]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(child for child in children.get(current, []) if child)
    return seen


def knowledge_scope_resolve(args: argparse.Namespace) -> int:
    root = system_root()
    space = space_from_args(root, args, create=False)
    folders = load_knowledge_folders(root, space["space_id"])
    items = load_knowledge_items(root, space["space_id"])
    folder_id = safe_component(args.folder_id, "folder id") if args.folder_id else ""
    item_id = safe_component(args.item_id, "item id") if args.item_id else ""
    snapshot_mode = not args.live_mode
    resolved_items: list[dict[str, Any]] = []
    resolved_folders: list[dict[str, Any]] = []
    if item_id:
        candidates = [item for item in items if item.get("item_id") == item_id]
    else:
        selected_folder = folder_id or "root"
        descendant_ids = folder_descendants(folders, selected_folder)
        resolved_folders = [folder for folder in folders if folder.get("folder_id") in descendant_ids]
        candidates = [item for item in items if item.get("folder_id") in descendant_ids]
    for item in candidates:
        decision = knowledge_access_allowed(root, space=space, resource_type="item", resource_id=item.get("item_id", ""), permission="read", user=args.user, role=args.role, agent=args.agent or "", project=args.project or "", workflow_run=args.workflow_run or "")
        append_knowledge_acl_log(root, {"space_id": space["space_id"], "resource_type": "item", "resource_id": item.get("item_id", ""), "permission": "read", "user_id": args.user, "user_role": args.role, "agent_id": args.agent or "", "project_id": args.project or space.get("project_id", ""), "workflow_run_id": args.workflow_run or "", "outcome": decision["outcome"], "reasons": decision["reasons"], "source": "knowledge_scope_resolve"})
        if decision["allowed"]:
            resolved_items.append(item)
    snapshot = {
        "snapshot_id": f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}" if snapshot_mode else "",
        "mode": "snapshot" if snapshot_mode else "live",
        "created_at": now_iso() if snapshot_mode else "",
        "item_ids": [item.get("item_id") for item in resolved_items],
        "folder_ids": [folder.get("folder_id") for folder in resolved_folders],
    }
    print(json.dumps({"kind": "digital-office-knowledge-scope", "space": space, "snapshot": snapshot, "items": resolved_items, "folders": resolved_folders}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def knowledge_tree(args: argparse.Namespace) -> int:
    root = system_root()
    if args.space_type == "shared_with_me":
        spaces: list[dict[str, Any]] = []
        visible_items: list[dict[str, Any]] = []
        for space_file in sorted(knowledge_spaces_root(root).glob("*/space.json")):
            space = read_json(space_file)
            for item in load_knowledge_items(root, space["space_id"]):
                decision = knowledge_access_allowed(root, space=space, resource_type="item", resource_id=item.get("item_id", ""), permission="read", user=args.user, role=args.role, agent=args.agent or "", project=args.project or "", workflow_run=args.workflow_run or "")
                if decision["allowed"] and not (space.get("space_type") == "personal" and space.get("owner_user_id") == args.user):
                    spaces.append(space)
                    visible_items.append(item)
        unique_spaces = {space["space_id"]: space for space in spaces}
        print(json.dumps({"kind": "digital-office-knowledge-tree", "space_type": "shared_with_me", "spaces": list(unique_spaces.values()), "items": visible_items}, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    space = space_from_args(root, args, create=False)
    folders = []
    for folder in load_knowledge_folders(root, space["space_id"]):
        decision = knowledge_access_allowed(root, space=space, resource_type="folder", resource_id=folder.get("folder_id", ""), permission="read", user=args.user, role=args.role, agent=args.agent or "", project=args.project or "", workflow_run=args.workflow_run or "")
        if decision["allowed"]:
            folders.append(folder)
    items = []
    for item in load_knowledge_items(root, space["space_id"]):
        decision = knowledge_access_allowed(root, space=space, resource_type="item", resource_id=item.get("item_id", ""), permission="read", user=args.user, role=args.role, agent=args.agent or "", project=args.project or "", workflow_run=args.workflow_run or "")
        if decision["allowed"]:
            items.append(item)
    print(json.dumps({"kind": "digital-office-knowledge-tree", "space": space, "folders": folders, "items": items}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def knowledge_space_summaries(root: Path, *, user: str = "", role: str = "", limit: int = 50) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for space_file in sorted(knowledge_spaces_root(root).glob("*/space.json")):
        try:
            space = read_json(space_file)
        except Exception:
            continue
        folders = load_knowledge_folders(root, space["space_id"])
        items = load_knowledge_items(root, space["space_id"])
        visible = True
        if space.get("space_type") == "personal" and user and space.get("owner_user_id") != user:
            visible = False
        if user and role and items:
            visible = any(
                knowledge_access_allowed(root, space=space, resource_type="item", resource_id=item.get("item_id", ""), permission="read", user=user, role=role, project=space.get("project_id", ""))["allowed"]
                for item in items
            )
        elif space.get("space_type") == "personal" and user:
            visible = space.get("owner_user_id") == user
        if visible:
            summaries.append(
                {
                    "space_id": space["space_id"],
                    "space_type": space.get("space_type", ""),
                    "owner_user_id": space.get("owner_user_id", ""),
                    "project_id": space.get("project_id", ""),
                    "folder_count": len(folders),
                    "item_count": len(items),
                    "updated_at": space.get("updated_at", space.get("created_at", "")),
                }
            )
        if len(summaries) >= limit:
            break
    return summaries


def workbench_state(args: argparse.Namespace) -> int:
    root = system_root()
    limit = max(1, min(args.limit, 100))
    project = safe_component(args.project, "project id") if args.project else ""
    if project:
        ensure_project(root, project)
    auth = compute_authorization_decision(root, tenant_id=args.tenant, deployment_id=args.deployment, user_id=args.user, user_role=args.role, action="workbench.read", resource_type="workbench", resource_id=args.role, project_id=project, audit=True)
    if not auth["allowed"]:
        print(json.dumps({"authorization": auth, "status": "denied"}, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    runs = [run for run in read_run_records(root) if not project or run.get("project_id") == project]
    tasks = [task for task in read_records(root / "tasks", "digital-office-task") if not project or task.get("project_id") == project]
    approvals = [approval for approval in read_records(root / "approvals", "digital-office-approval") if not project or approval.get("project_id") == project]
    notifications = [item for item in read_records(root / "notifications", "digital-office-notification") if item.get("user_id") in {"", args.user}]
    if args.role not in TENANT_ADMIN_ROLES and args.role != "project_manager":
        runs = [run for run in runs if run.get("requested_by") in {"", args.user}]
        tasks = [task for task in tasks if task.get("requested_by") in {"", args.user} or task.get("assigned_user") in {"", args.user}]
        approvals = [approval for approval in approvals if approval.get("requested_by") in {"", args.user} or approval.get("approver_role") == args.role]
    agent_load: dict[str, int] = {}
    for task in tasks:
        agent = task.get("assigned_agent") or task.get("agent_id") or "unassigned"
        agent_load[agent] = agent_load.get(agent, 0) + 1
    if args.role in TENANT_ADMIN_ROLES:
        view = "owner_global"
        sections = {
            "project_health": project_summaries(root, limit),
            "blocked_workflows": compact_records([run for run in runs if run.get("status") in {"blocked", "waiting_user_confirmation", "paused_after_current_node"}], ["run_id", "status", "project_id", "agent_id", "updated_at"], limit),
            "cost_and_load": {"agent_load": dict(sorted(agent_load.items())), "queued_tasks": sum(1 for item in tasks if item.get("status") == "queued")},
            "pending_approvals": compact_records([item for item in approvals if item.get("status") == "pending"], ["approval_id", "title", "project_id", "approver_role", "updated_at"], limit),
            "knowledge_spaces": knowledge_space_summaries(root, user=args.user, role=args.role, limit=limit),
            "system_health": health_checks(root),
        }
    elif args.role == "project_manager":
        view = "project_lead"
        sections = {
            "project_progress": compact_records(runs, ["run_id", "status", "project_id", "agent_id", "workflow", "updated_at"], limit),
            "team_tasks": compact_records(tasks, ["task_id", "title", "status", "priority", "assigned_agent", "assigned_user", "updated_at"], limit),
            "blocked_items": compact_records([item for item in tasks if item.get("status") in {"blocked", "waiting_approval", "failed"}], ["task_id", "title", "status", "workflow_run_id", "updated_at"], limit),
            "knowledge_spaces": knowledge_space_summaries(root, user=args.user, role=args.role, limit=limit),
        }
    elif args.role == "professional_reviewer":
        view = "approver"
        sections = {
            "pending_approvals": compact_records([item for item in approvals if item.get("status") == "pending" and item.get("approver_role") == "professional_reviewer"], ["approval_id", "title", "risk", "project_id", "workflow_run_id", "updated_at"], limit),
            "recent_decisions": compact_records([item for item in approvals if item.get("status") != "pending"], ["approval_id", "title", "status", "updated_at"], limit),
        }
    elif args.role == "viewer":
        view = "viewer"
        visible_projects = [item for item in project_summaries(root, limit) if not project or item.get("project_id") == project]
        sections = {
            "visible_projects": visible_projects,
            "recent_outputs": compact_records([run for run in runs if run.get("status") == "completed"], ["run_id", "project_id", "agent_id", "workflow", "updated_at"], limit),
            "notifications": compact_records(notifications, ["notification_id", "title", "topic", "status", "created_at"], limit),
        }
    else:
        view = "member"
        sections = {
            "my_tasks": compact_records(tasks, ["task_id", "title", "status", "priority", "project_id", "workflow_run_id", "updated_at"], limit),
            "my_workflows": compact_records(runs, ["run_id", "status", "project_id", "agent_id", "workflow", "updated_at"], limit),
            "notifications": compact_records(notifications, ["notification_id", "title", "topic", "status", "created_at"], limit),
            "knowledge_spaces": knowledge_space_summaries(root, user=args.user, role=args.role, limit=limit),
        }
    payload = {
        "kind": "digital-office-workbench-state",
        "version": "1.0.0",
        "generated_at": now_iso(),
        "tenant_id": args.tenant,
        "deployment_id": args.deployment,
        "user_id": args.user,
        "role": args.role,
        "project_id": project,
        "view": view,
        "authorization": auth,
        "sections": sections,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def loop_manifest(root: Path) -> dict[str, Any]:
    return read_json(root / "ai-native-loop.manifest.json")


def loop_run_path(root: Path, run_id: str) -> Path:
    return root / "runs" / safe_component(run_id, "run id") / "run.json"


def loop_start(args: argparse.Namespace) -> int:
    root = system_root()
    manifest = loop_manifest(root)
    project = safe_component(args.project, "project id") if args.project else ""
    agent = registered_agent(root, args.agent) if args.agent else ""
    if project:
        ensure_project(root, project)
    run_id = safe_component(args.run_id, "run id") if args.run_id else f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    task = args.task if args.task is not None else sys.stdin.read()
    run = {
        "version": "1.0.0",
        "kind": "digital-office-ai-native-loop-run",
        "run_id": run_id,
        "status": "created",
        "current_stage": "perceive",
        "project_id": project,
        "agent_id": agent,
        "workflow": safe_claim(args.workflow, "workflow", required=False),
        "requested_by": safe_claim(args.requested_by, "requested by", required=False),
        "task": task.strip(),
        "task_sha256": hashlib.sha256(task.encode("utf-8")).hexdigest(),
        "created_at": now_iso(),
        "stages": {
            stage: {
                "status": "pending",
                "required_artifacts": manifest["stages"][stage]["required_artifacts"],
                "gates": [
                    {
                        "gate": gate,
                        "status": "pending"
                    }
                    for gate in manifest["stages"][stage]["gates"]
                ],
                "artifacts": [],
                "notes": []
            }
            for stage in LOOP_STAGES
        },
        "hard_rules": manifest.get("hard_rules", []),
    }
    if args.dry_run:
        print(json.dumps(run, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    target = loop_run_path(root, run_id)
    if target.exists():
        print(f"office-system: loop run already exists: {run_id}", file=sys.stderr)
        return 2
    write_json(target, run)
    append_log(root, {"event": "loop_start", "run_id": run_id, "project": project, "agent": agent})
    print(json.dumps({"run_id": run_id, "path": str(target.relative_to(root)), "status": "created"}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def loop_stage(args: argparse.Namespace) -> int:
    root = system_root()
    run_id = safe_component(args.run_id, "run id")
    stage = args.stage
    target = loop_run_path(root, run_id)
    if not target.exists():
        print(f"office-system: loop run not found: {run_id}", file=sys.stderr)
        return 2
    run = read_json(target)
    stage_state = run.setdefault("stages", {}).setdefault(stage, {"artifacts": [], "notes": [], "gates": []})
    stage_state["status"] = args.status
    if args.summary:
        stage_state.setdefault("notes", []).append({"time": now_iso(), "summary": args.summary})
    body = args.body if args.body is not None else ""
    if body:
        stage_state.setdefault("notes", []).append({"time": now_iso(), "body": body})
    for artifact in args.artifact or []:
        stage_state.setdefault("artifacts", []).append(safe_claim(artifact, "artifact"))
    for gate in args.gate or []:
        if ":" not in gate:
            print("office-system: --gate must be gate_id:status", file=sys.stderr)
            return 2
        gate_id, gate_status = gate.split(":", 1)
        stage_state.setdefault("gate_updates", []).append(
            {
                "time": now_iso(),
                "gate": safe_claim(gate_id, "gate id"),
                "status": safe_claim(gate_status, "gate status"),
            }
        )
    if args.status == "started":
        run["status"] = LOOP_STATUS_BY_STAGE[stage]
        run["current_stage"] = stage
    elif args.status in {"failed", "blocked"}:
        run["status"] = "blocked"
        run["current_stage"] = stage
    elif args.status == "completed":
        current_index = LOOP_STAGES.index(stage)
        next_stage = LOOP_STAGES[current_index + 1] if current_index + 1 < len(LOOP_STAGES) else None
        run["current_stage"] = next_stage or stage
        if next_stage:
            run["status"] = LOOP_STATUS_BY_STAGE[next_stage]
        else:
            run["status"] = "completed"
    run["updated_at"] = now_iso()
    write_json(target, run)
    append_log(root, {"event": "loop_stage", "run_id": run_id, "stage": stage, "status": args.status})
    print(json.dumps({"run_id": run_id, "stage": stage, "status": args.status, "run_status": run["status"]}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def loop_status(args: argparse.Namespace) -> int:
    root = system_root()
    target = loop_run_path(root, args.run_id)
    if not target.exists():
        print(f"office-system: loop run not found: {args.run_id}", file=sys.stderr)
        return 2
    print(json.dumps(read_json(target), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def iteration_proposal_id(title: str) -> str:
    return f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}-{slugify(title)}"


def iteration_status_path(root: Path, proposal_id: str) -> Path:
    return root / "iterations" / "status" / f"{safe_component(proposal_id, 'proposal id')}.json"


def iteration_proposal_create(args: argparse.Namespace) -> int:
    root = system_root()
    project = safe_component(args.project, "project id") if args.project else ""
    agent = registered_agent(root, args.agent) if args.agent else ""
    if project:
        ensure_project(root, project)
    if args.run_id:
        run_path = loop_run_path(root, args.run_id)
        if not run_path.exists():
            print(f"office-system: loop run not found: {args.run_id}", file=sys.stderr)
            return 2
    body = args.body if args.body is not None else sys.stdin.read()
    proposal_id = iteration_proposal_id(args.title)
    report = root / "iterations" / "proposals" / f"{proposal_id}.md"
    status_file = iteration_status_path(root, proposal_id)
    proposal = {
        "version": "1.0.0",
        "kind": "digital-office-iteration-proposal",
        "proposal_id": proposal_id,
        "status": "pending_user_confirmation",
        "title": args.title,
        "target": args.target,
        "run_id": safe_component(args.run_id, "run id") if args.run_id else "",
        "project_id": project,
        "agent_id": agent,
        "summary": args.summary,
        "body": body.strip(),
        "expected_impact": args.expected_impact,
        "risk": args.risk,
        "rollback": args.rollback,
        "source_refs": [safe_claim(item, "source ref") for item in (args.source_ref or [])],
        "regression_checks": [safe_claim(item, "regression check") for item in (args.regression_check or [])],
        "requires_user_confirmation": True,
        "auto_apply_allowed": False,
        "created_at": now_iso(),
        "report": str(report.relative_to(root)),
        "allowed_decisions": ["confirm", "tune", "pause", "reject"],
    }
    lines = [
        f"# Iteration Proposal: {args.title}",
        "",
        "- State: pending_user_confirmation",
        f"- Proposal ID: {proposal_id}",
        f"- Target: {args.target}",
        f"- Run ID: {proposal['run_id']}",
        f"- Project: {project}",
        f"- Agent: {agent}",
        f"- Created at: {proposal['created_at']}",
        "",
        "## What Will Change",
        "",
        body.strip() or args.summary,
        "",
        "## Why This Is Suggested",
        "",
        args.summary,
        "",
        "## Expected Impact",
        "",
        args.expected_impact,
        "",
        "## Risk",
        "",
        args.risk,
        "",
        "## Rollback",
        "",
        args.rollback,
        "",
        "## Regression Checks",
        "",
    ]
    if args.regression_check:
        lines.extend(f"- {item}" for item in args.regression_check)
    else:
        lines.append("- No regression check provided yet. This proposal cannot be called production-ready until one is added.")
    lines.extend(
        [
            "",
            "## User Decision Required",
            "",
            "This proposal is not applied automatically. The GUI must show the change, risk, rollback, and regression checks, then wait for one of: Confirm, Tune Through Conversation, Pause, Reject.",
        ]
    )
    write_text(report, "\n".join(lines) + "\n")
    write_json(status_file, proposal)
    append_log(root, {"event": "iteration_proposal_create", "proposal_id": proposal_id, "target": args.target, "run_id": proposal["run_id"]})
    print(json.dumps({"proposal_id": proposal_id, "status": proposal["status"], "report": proposal["report"], "status_file": str(status_file.relative_to(root))}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def iteration_proposal_decision(args: argparse.Namespace) -> int:
    root = system_root()
    proposal_id = safe_component(args.proposal_id, "proposal id")
    status_file = iteration_status_path(root, proposal_id)
    if not status_file.exists():
        print(f"office-system: iteration proposal not found: {proposal_id}", file=sys.stderr)
        return 2
    state = read_json(status_file)
    state["status"] = ITERATION_DECISION_TO_STATUS[args.decision]
    state["decision"] = args.decision
    state["decision_updated_at"] = now_iso()
    if args.message:
        state.setdefault("decision_messages", []).append({"time": now_iso(), "message": args.message})
    if args.decision == "confirm":
        state["next_action"] = f"iteration-proposal-apply --proposal-id {proposal_id} --confirmed"
    elif args.decision == "tune":
        state["next_action"] = "secretary continues the iteration conversation and regenerates or updates the proposal"
    elif args.decision == "pause":
        state["next_action"] = "do nothing until the user resumes"
    elif args.decision == "reject":
        state["next_action"] = "do not apply this proposal"
    write_json(status_file, state)
    append_log(root, {"event": "iteration_proposal_decision", "proposal_id": proposal_id, "decision": args.decision})
    print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def iteration_proposal_apply(args: argparse.Namespace) -> int:
    root = system_root()
    proposal_id = safe_component(args.proposal_id, "proposal id")
    status_file = iteration_status_path(root, proposal_id)
    if not status_file.exists():
        print(f"office-system: iteration proposal not found: {proposal_id}", file=sys.stderr)
        return 2
    if not args.confirmed:
        print("office-system: iteration application requires --confirmed after the user reviews the proposal", file=sys.stderr)
        return 2
    state = read_json(status_file)
    if state.get("status") != "confirmed_for_application":
        print("office-system: iteration proposal must be confirmed before application", file=sys.stderr)
        return 2
    record = {
        "version": "1.0.0",
        "kind": "digital-office-applied-iteration-record",
        "proposal_id": proposal_id,
        "target": state.get("target"),
        "applied_at": now_iso(),
        "applied_by": safe_claim(args.applied_by, "applied by", required=False),
        "artifacts": [safe_claim(item, "artifact") for item in (args.artifact or [])],
        "regression_result": args.regression_result or "",
        "rollback": state.get("rollback", ""),
        "note": args.note or "",
    }
    state["status"] = "applied_verified" if args.regression_result else "applied_pending_regression"
    state["applied_at"] = record["applied_at"]
    state["applied_record"] = f"iterations/applied/{proposal_id}.json"
    write_json(root / "iterations" / "applied" / f"{proposal_id}.json", record)
    write_json(status_file, state)
    append_log(root, {"event": "iteration_proposal_apply", "proposal_id": proposal_id, "status": state["status"]})
    print(json.dumps({"proposal_id": proposal_id, "status": state["status"], "applied_record": state["applied_record"]}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def health_checks(root: Path) -> dict[str, Any]:
    return {
        "root": str(root),
        "agents_registry": (root / "agents.registry.json").exists(),
        "knowledge_registry": (root / "knowledge.registry.json").exists(),
        "identity_access_registry": (root / "identity.access.registry.json").exists(),
        "industry_solutions_registry": (root / "industry-solutions.registry.json").exists(),
        "external_knowledge_sources_registry": (root / "external-knowledge-sources.registry.json").exists(),
        "ai_native_loop_manifest": (root / "ai-native-loop.manifest.json").exists(),
        "onboarding_presets": (root / "onboarding.presets.json").exists(),
        "settings_dir": (root / "settings").exists(),
        "user_preferences_configured": onboarding_preferences_path(root).exists(),
        "rules_registry": (root / "rules" / "rules.registry.json").exists(),
        "multimodal_pipeline": (root / "multimodal.pipeline.json").exists(),
        "rag_pipeline": (root / "rag.pipeline.json").exists(),
        "workflow_runs_dir": (root / "runs").exists(),
        "task_inbox_dir": (root / "tasks").exists(),
        "approval_center_dir": (root / "approvals").exists(),
        "notifications_dir": (root / "notifications").exists(),
        "audit_logs_dir": (root / "logs").exists(),
        "knowledge_spaces_dir": (root / "knowledge" / "spaces").exists(),
        "web_app_dir": (root / "web" / "app").exists(),
        "web_index": (root / "web" / "app" / "index.html").exists(),
        "pwa_manifest": (root / "web" / "app" / "manifest.webmanifest").exists(),
        "service_worker": (root / "web" / "app" / "service-worker.js").exists(),
        "tesseract": bool(shutil.which("tesseract")),
        "pdftotext": bool(shutil.which("pdftotext")),
        "rapidocr_onnxruntime": bool(importlib.util.find_spec("rapidocr_onnxruntime")),
        "pypdf": bool(importlib.util.find_spec("pypdf")),
        "python_docx": bool(importlib.util.find_spec("docx")),
        "sentence_transformers": bool(importlib.util.find_spec("sentence_transformers")),
        "python_docx_builtin": True,
    }


def required_health_keys() -> tuple[str, ...]:
    return (
        "agents_registry",
        "knowledge_registry",
        "identity_access_registry",
        "industry_solutions_registry",
        "external_knowledge_sources_registry",
        "ai_native_loop_manifest",
        "onboarding_presets",
        "settings_dir",
        "rules_registry",
        "multimodal_pipeline",
        "workflow_runs_dir",
        "task_inbox_dir",
        "approval_center_dir",
        "notifications_dir",
        "audit_logs_dir",
        "knowledge_spaces_dir",
        "web_app_dir",
        "web_index",
        "pwa_manifest",
        "service_worker",
    )


def status_counts(records: list[dict[str, Any]], field: str = "status") -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        key = str(record.get(field) or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def compact_records(records: list[dict[str, Any]], fields: list[str], limit: int) -> list[dict[str, Any]]:
    compacted = []
    for record in records[:limit]:
        compacted.append({field: record.get(field, "") for field in fields})
    return compacted


def project_summaries(root: Path, limit: int) -> list[dict[str, Any]]:
    projects: list[dict[str, Any]] = []
    for path in sorted((root / "projects").glob("*/project.json")):
        if path.parent.name == "_template":
            continue
        try:
            data = read_json(path)
        except Exception:
            continue
        projects.append(
            {
                "project_id": data.get("project_id", path.parent.name),
                "name": data.get("name", path.parent.name),
                "status": data.get("status", ""),
                "agent_roster": data.get("agent_roster", []),
                "updated_at": data.get("updated_at", data.get("created_at", "")),
            }
        )
    projects.sort(key=lambda item: str(item.get("updated_at") or ""), reverse=True)
    return projects[:limit]


def agent_summaries(root: Path) -> list[dict[str, Any]]:
    registry = read_json(root / "agents.registry.json")
    agents = []
    for agent_id, agent in sorted(registry.get("agents", {}).items()):
        agents.append(
            {
                "agent_id": agent_id,
                "display_name": agent.get("display_name", agent_id),
                "profile": agent.get("profile", ""),
                "portable_role": agent.get("portable_role", ""),
                "orchestration_roles": agent.get("orchestration_roles", []),
                "skills": agent.get("skills", []),
            }
        )
    return agents


def gui_capabilities() -> list[dict[str, Any]]:
    return [
        {"id": "global_settings", "status": "ready", "commands": ["settings-options", "settings-status", "settings-update"]},
        {"id": "first_run_onboarding", "status": "ready", "commands": ["onboarding-options", "onboarding-apply"]},
        {"id": "web_ui_pwa", "status": "ready", "commands": ["web-config", "web-serve"], "routes": ["/", "/manifest.webmanifest", "/service-worker.js", "/api/health", "/api/gui-state", "/api/web-app"]},
        {"id": "workflow_control_plane", "status": "ready", "commands": ["workflow-start", "workflow-status", "workflow-list", "workflow-cancel", "workflow-resume", "workflow-retry", "workflow-control"]},
        {"id": "direct_agent_invocation", "status": "ready", "commands": ["agent-invoke"]},
        {"id": "workflow_canvas_revisions", "status": "ready", "commands": ["workflow-draft-create", "workflow-draft-patch", "workflow-draft-validate", "workflow-draft-activate", "workflow-node-context"]},
        {"id": "workflow_runtime_controls", "status": "ready", "commands": ["workflow-control", "workflow-node-context"]},
        {"id": "task_inbox", "status": "ready", "commands": ["task-list", "task-status", "task-update"]},
        {"id": "approval_center", "status": "ready", "commands": ["approval-create", "approval-list", "approval-decision"]},
        {"id": "notification_center", "status": "ready", "commands": ["notification-list", "notification-mark-read"]},
        {"id": "audit_events", "status": "ready", "commands": ["audit-events"]},
        {"id": "project_knowledge", "status": "ready", "commands": ["knowledge-add", "knowledge-add-text", "rag-index", "rag-search"]},
        {"id": "knowledge_spaces", "status": "ready", "commands": ["knowledge-tree", "knowledge-folder-create", "knowledge-item-add", "knowledge-share", "knowledge-scope-resolve", "knowledge-access-check"]},
        {"id": "role_workbenches", "status": "ready", "commands": ["workbench-state"]},
        {"id": "agent_registry", "status": "ready", "commands": ["agent-plugin-report", "agent-plugin-decision", "agent-plugin-activate"]},
        {"id": "product_updates", "status": "ready", "commands": ["iteration-proposal-create", "iteration-proposal-decision", "iteration-proposal-apply"]},
        {"id": "data_sharing", "status": "ready", "commands": ["telemetry-status", "telemetry-export", "telemetry-send"]},
        {"id": "external_knowledge_sources", "status": "ready", "commands": ["knowledge-source-mount", "knowledge-access-log"]},
    ]


def build_gui_state_payload(root: Path, *, project: str = "", user: str = "", role: str = "", limit: int = 20) -> dict[str, Any]:
    limit = max(1, min(limit, 100))
    project = safe_component(project, "project id") if project else ""
    user = safe_claim(user, "user", required=False)
    role = safe_component(role, "role") if role else ""
    preferences = current_onboarding_preferences(root)
    runs = [
        run
        for run in read_run_records(root)
        if (not project or run.get("project_id") == project) and (not user or run.get("requested_by") in {"", user})
    ]
    tasks = [
        task
        for task in read_records(root / "tasks", "digital-office-task")
        if (not project or task.get("project_id") == project) and (not user or task.get("requested_by") in {"", user} or task.get("assigned_user") in {"", user})
    ]
    approvals = [
        approval
        for approval in read_records(root / "approvals", "digital-office-approval")
        if (not project or approval.get("project_id") == project) and (not user or approval.get("requested_by") in {"", user})
    ]
    notifications = [
        notification
        for notification in read_records(root / "notifications", "digital-office-notification")
        if not user or notification.get("user_id") in {"", user}
    ]
    audit_rows = read_jsonl(root / "logs" / "audit-events.jsonl", limit=limit)
    company_entries = load_entries(root, root / "knowledge" / "company" / "entries")
    mounts = read_records(root / "knowledge" / "mounts")
    checks = health_checks(root)
    agents = agent_summaries(root)
    projects = project_summaries(root, 1000)
    active_workflows = [run for run in runs if run.get("status") not in {"completed", "cancelled", "stopped"}]
    draft_revision_count = sum(1 for run in runs for revision in run.get("revisions", []) if revision.get("status") == "draft")
    knowledge_spaces = knowledge_space_summaries(root, user=user, role=role, limit=limit)
    payload = {
        "kind": "digital-office-gui-state",
        "version": "1.0.0",
        "generated_at": now_iso(),
        "scope": {"project_id": project, "user_id": user, "role": role},
        "health": {"status": "ok" if all(checks[k] for k in required_health_keys()) else "degraded", "checks": checks},
        "settings": {
            "configured": preferences is not None,
            "outputs": ONBOARDING_OUTPUTS,
            "preferences": preferences or {},
            "options_command": "settings-options",
            "update_command": "settings-update --confirmed",
        },
        "capabilities": gui_capabilities(),
        "agents": {"count": len(agents), "items": agents},
        "projects": {"count": len(projects), "items": projects[:limit]},
        "workflows": {
            "count": len(runs),
            "active_count": len(active_workflows),
            "draft_revision_count": draft_revision_count,
            "by_status": status_counts(runs),
            "recent": compact_records(runs, ["run_id", "title", "status", "project_id", "agent_id", "workflow", "invocation_mode", "active_revision_id", "requested_by", "created_at", "updated_at"], limit),
        },
        "tasks": {
            "count": len(tasks),
            "by_status": status_counts(tasks),
            "recent": compact_records(tasks, ["task_id", "title", "status", "priority", "project_id", "assigned_agent", "assigned_user", "workflow_run_id", "updated_at"], limit),
        },
        "approvals": {
            "count": len(approvals),
            "by_status": status_counts(approvals),
            "recent": compact_records(approvals, ["approval_id", "title", "status", "approver_role", "project_id", "workflow_run_id", "task_id", "updated_at"], limit),
        },
        "notifications": {
            "count": len(notifications),
            "unread": sum(1 for item in notifications if item.get("status") == "unread"),
            "by_status": status_counts(notifications),
            "recent": compact_records(notifications, ["notification_id", "title", "topic", "status", "severity", "resource_type", "resource_id", "created_at"], limit),
        },
        "knowledge": {
            "company_entries": len(company_entries),
            "external_mounts": len(mounts),
            "spaces": {"count": len(knowledge_spaces), "items": knowledge_spaces},
            "rag_index_configured": (root / "rag.pipeline.json").exists(),
        },
        "workbench": {
            "command": "workbench-state",
            "entry_points": ["owner_global", "project_lead", "member", "approver", "admin", "viewer"],
        },
        "audit": {"recent": audit_rows[-limit:]},
        "next_gui_actions": [
            "Show settings status and prompt for configuration when settings.configured is false.",
            "Surface pending approvals, unread notifications, blocked workflows, and waiting tasks on the home screen.",
            "Use agent-invoke for explicit @Agent dispatch and keep every dispatch linked to a workflow run and task.",
            "Use workflow draft revisions for canvas edits; activate only after validation and explicit confirmation.",
            "Resolve knowledge folders through knowledge-scope-resolve before running Agent nodes.",
            "Route all mutating actions through the matching command and require explicit GUI confirmation where commands expose --confirmed.",
        ],
    }
    return payload


def gui_state(args: argparse.Namespace) -> int:
    root = system_root()
    payload = build_gui_state_payload(root, project=args.project or "", user=args.user or "", role=args.role or "", limit=args.limit)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def web_static_root(root: Path) -> Path:
    return root / "web" / "app"


def web_app_config(root: Path, *, public_url: str = "", user: str = "", role: str = "", project: str = "", tenant: str = "", deployment: str = "") -> dict[str, Any]:
    checks = health_checks(root)
    return {
        "kind": "digital-office-web-app-config",
        "version": "1.0.0",
        "generated_at": now_iso(),
        "app": {
            "name": "Digital Office",
            "short_name": "Office",
            "mode": "web_ui_pwa",
            "public_url": safe_claim(public_url, "public url", required=False),
            "static_root": str(web_static_root(root)),
            "manifest": "/manifest.webmanifest",
            "service_worker": "/service-worker.js",
            "start_url": "/",
        },
        "default_scope": {
            "tenant_id": safe_claim(tenant, "tenant id", required=False),
            "deployment_id": safe_claim(deployment, "deployment id", required=False),
            "user_id": safe_claim(user, "user id", required=False),
            "role": safe_component(role, "role") if role else "",
            "project_id": safe_component(project, "project id") if project else "",
        },
        "api": {
            "read_routes": [
                {"method": "GET", "path": "/api/health", "description": "Return office-system health checks and PWA readiness."},
                {"method": "GET", "path": "/api/gui-state", "description": "Return the home-screen GUI state snapshot."},
                {"method": "GET", "path": "/api/web-app", "description": "Return this Web/PWA configuration contract."},
            ],
            "mutation_policy": "Mutating GUI actions must call explicit governed commands or future dedicated API routes. Do not expose a generic remote shell/CLI execution endpoint.",
        },
        "pwa": {
            "installable_shell": checks.get("pwa_manifest") and checks.get("service_worker") and checks.get("web_index"),
            "offline_shell": True,
            "cache_name": "digital-office-shell-v1",
        },
        "deployment": {
            "recommended": "Serve behind HTTPS reverse proxy such as Caddy or Nginx. Bind web-serve to 127.0.0.1 for reverse proxy deployments, or to 0.0.0.0 only on trusted LAN/VPN networks.",
            "examples": ["agent-system/deploy/Caddyfile.example", "agent-system/deploy/nginx.conf.example", "agent-system/deploy/systemd/digital-office-web.service.example"],
        },
        "health": {"status": "ok" if all(checks[key] for key in required_health_keys()) else "degraded", "checks": checks},
    }


def web_config(args: argparse.Namespace) -> int:
    root = system_root()
    payload = web_app_config(root, public_url=args.public_url or "", user=args.user or "", role=args.role or "", project=args.project or "", tenant=args.tenant or "", deployment=args.deployment or "")
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload["health"]["status"] == "ok" else 1


def web_json_response(handler: http.server.BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def web_serve(args: argparse.Namespace) -> int:
    root = system_root()
    static_root = Path(args.static_dir).expanduser() if args.static_dir else web_static_root(root)
    static_root = static_root.resolve()
    if not static_root.exists():
        print(f"office-system: web static directory not found: {static_root}", file=sys.stderr)
        return 2
    public_url = args.public_url or ""
    default_scope = {
        "tenant": args.tenant or "",
        "deployment": args.deployment or "",
        "user": args.user or "",
        "role": args.role or "",
        "project": args.project or "",
    }
    allow_origin = args.allow_origin or ""

    class DigitalOfficeHandler(http.server.SimpleHTTPRequestHandler):
        server_version = "DigitalOfficeWeb/1.0"
        extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".webmanifest": "application/manifest+json", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml"}

        def log_message(self, format: str, *values: Any) -> None:
            if not args.quiet:
                super().log_message(format, *values)

        def end_headers(self) -> None:
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "same-origin")
            self.send_header("X-Frame-Options", "DENY")
            if allow_origin:
                self.send_header("Access-Control-Allow-Origin", allow_origin)
            super().end_headers()

        def translate_path(self, path: str) -> str:
            parsed = urllib.parse.urlparse(path)
            request_path = urllib.parse.unquote(parsed.path)
            if request_path in {"", "/"}:
                request_path = "/index.html"
            candidate = (static_root / request_path.lstrip("/")).resolve()
            try:
                if not candidate.is_relative_to(static_root):
                    return str(static_root / "index.html")
            except AttributeError:
                if os.path.commonpath([str(candidate), str(static_root)]) != str(static_root):
                    return str(static_root / "index.html")
            if candidate.is_dir():
                candidate = candidate / "index.html"
            if not candidate.exists() and "." not in candidate.name:
                candidate = static_root / "index.html"
            return str(candidate)

        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            query = urllib.parse.parse_qs(parsed.query)

            def one(name: str, default: str = "") -> str:
                values = query.get(name)
                return values[0] if values else default

            if parsed.path in {"/healthz", "/api/health"}:
                checks = health_checks(root)
                web_json_response(self, 200 if all(checks[key] for key in required_health_keys()) else 503, {"status": "ok" if all(checks[key] for key in required_health_keys()) else "degraded", "checks": checks, "generated_at": now_iso()})
                return
            if parsed.path == "/api/gui-state":
                try:
                    payload = build_gui_state_payload(root, project=one("project", default_scope["project"]), user=one("user", default_scope["user"]), role=one("role", default_scope["role"]), limit=int(one("limit", "20")))
                except (SystemExit, ValueError) as exc:
                    web_json_response(self, 400, {"status": "error", "error": str(exc)})
                    return
                web_json_response(self, 200, payload)
                return
            if parsed.path == "/api/web-app":
                payload = web_app_config(root, public_url=public_url, user=one("user", default_scope["user"]), role=one("role", default_scope["role"]), project=one("project", default_scope["project"]), tenant=one("tenant", default_scope["tenant"]), deployment=one("deployment", default_scope["deployment"]))
                web_json_response(self, 200 if payload["health"]["status"] == "ok" else 503, payload)
                return
            if parsed.path.startswith("/api/"):
                web_json_response(self, 404, {"status": "not_found", "path": parsed.path})
                return
            super().do_GET()

    server = http.server.ThreadingHTTPServer((args.host, args.port), DigitalOfficeHandler)
    print(json.dumps({"status": "serving", "host": args.host, "port": args.port, "static_root": str(static_root), "url": f"http://{args.host}:{args.port}/", "api": ["/api/health", "/api/gui-state", "/api/web-app"]}, ensure_ascii=False, indent=2, sort_keys=True))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\noffice-system: web server stopped", file=sys.stderr)
    finally:
        server.server_close()
    return 0


def health(args: argparse.Namespace) -> int:
    root = system_root()
    checks = health_checks(root)
    print(json.dumps(checks, ensure_ascii=False, indent=2, sort_keys=True))
    required = required_health_keys()
    return 0 if all(checks[k] for k in required) else 1


def add_knowledge_space_selector(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--space-type", choices=sorted(KNOWLEDGE_SPACE_TYPES), required=True)
    parser.add_argument("--owner")
    parser.add_argument("--project")
    parser.add_argument("--team")
    parser.add_argument("--workflow-run")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="office-system")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("project-create")
    p.add_argument("--project")
    p.add_argument("--name", required=True)
    p.add_argument("--agents", default="")
    p.add_argument("--methodology-schedule", choices=["manual", "weekly", "monthly", "on_project_close"], default="manual")
    p.set_defaults(func=create_project)

    p = sub.add_parser("knowledge-add")
    p.add_argument("--scope", choices=["company", "project"], required=True)
    p.add_argument("--project")
    p.add_argument("--file", required=True)
    p.add_argument("--title")
    p.add_argument("--kind", choices=["text", "word", "pdf", "image", "binary"])
    p.add_argument("--notes")
    p.add_argument("--approve", action="store_true")
    p.set_defaults(func=add_file_entry)

    p = sub.add_parser("knowledge-add-text")
    p.add_argument("--scope", choices=["company", "project"], required=True)
    p.add_argument("--project")
    p.add_argument("--title", required=True)
    p.add_argument("--body")
    p.add_argument("--approve", action="store_true")
    p.set_defaults(func=add_text_entry)

    p = sub.add_parser("knowledge-folder-create")
    add_knowledge_space_selector(p)
    p.add_argument("--folder-id")
    p.add_argument("--parent-folder", default="root")
    p.add_argument("--title", required=True)
    p.add_argument("--created-by", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--replace", action="store_true")
    p.set_defaults(func=knowledge_folder_create)

    p = sub.add_parser("knowledge-item-add")
    add_knowledge_space_selector(p)
    p.add_argument("--item-id")
    p.add_argument("--folder-id", default="root")
    p.add_argument("--title", required=True)
    p.add_argument("--source-ref", required=True)
    p.add_argument("--content-type")
    p.add_argument("--connector-id")
    p.add_argument("--created-by", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--replace", action="store_true")
    p.set_defaults(func=knowledge_item_add)

    p = sub.add_parser("knowledge-share")
    add_knowledge_space_selector(p)
    p.add_argument("--resource-type", choices=sorted(KNOWLEDGE_RESOURCE_TYPES), required=True)
    p.add_argument("--resource-id", required=True)
    p.add_argument("--target-type", choices=sorted(KNOWLEDGE_TARGET_TYPES), required=True)
    p.add_argument("--target-id", required=True)
    p.add_argument("--permission", choices=sorted(KNOWLEDGE_PERMISSIONS), default="read")
    p.add_argument("--effect", choices=["allow", "deny"], default="allow")
    p.add_argument("--shared-by", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--share-id")
    p.add_argument("--reason")
    p.add_argument("--no-inherit", action="store_true")
    p.set_defaults(func=knowledge_share)

    p = sub.add_parser("knowledge-access-check")
    add_knowledge_space_selector(p)
    p.add_argument("--resource-type", choices=sorted(KNOWLEDGE_RESOURCE_TYPES), required=True)
    p.add_argument("--resource-id", required=True)
    p.add_argument("--permission", choices=sorted(KNOWLEDGE_PERMISSIONS), default="read")
    p.add_argument("--user", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--agent")
    p.set_defaults(func=knowledge_access_check)

    p = sub.add_parser("knowledge-scope-resolve")
    add_knowledge_space_selector(p)
    p.add_argument("--folder-id")
    p.add_argument("--item-id")
    p.add_argument("--user", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--agent")
    p.add_argument("--live-mode", action="store_true")
    p.set_defaults(func=knowledge_scope_resolve)

    p = sub.add_parser("knowledge-tree")
    add_knowledge_space_selector(p)
    p.add_argument("--user", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--agent")
    p.set_defaults(func=knowledge_tree)

    p = sub.add_parser("rule-add")
    p.add_argument("--scope", choices=["global", "agent", "project"], required=True)
    p.add_argument("--project")
    p.add_argument("--agent")
    p.add_argument("--title", required=True)
    p.add_argument("--body")
    p.set_defaults(func=add_rule)

    p = sub.add_parser("context")
    p.add_argument("--project")
    p.add_argument("--agent")
    p.set_defaults(func=context)

    p = sub.add_parser("gui-state")
    p.add_argument("--project")
    p.add_argument("--user")
    p.add_argument("--role")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=gui_state)

    p = sub.add_parser("web-config")
    p.add_argument("--public-url")
    p.add_argument("--tenant")
    p.add_argument("--deployment")
    p.add_argument("--user")
    p.add_argument("--role")
    p.add_argument("--project")
    p.set_defaults(func=web_config)

    p = sub.add_parser("web-serve")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8787)
    p.add_argument("--static-dir")
    p.add_argument("--public-url")
    p.add_argument("--tenant")
    p.add_argument("--deployment")
    p.add_argument("--user")
    p.add_argument("--role")
    p.add_argument("--project")
    p.add_argument("--allow-origin")
    p.add_argument("--quiet", action="store_true")
    p.set_defaults(func=web_serve)

    p = sub.add_parser("workbench-state")
    p.add_argument("--tenant", required=True)
    p.add_argument("--deployment", required=True)
    p.add_argument("--user", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--project")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=workbench_state)

    p = sub.add_parser("onboarding-options")
    p.set_defaults(func=onboarding_options)

    p = sub.add_parser("onboarding-status")
    p.set_defaults(func=onboarding_status)

    p = sub.add_parser("onboarding-apply")
    add_preferences_arguments(p)
    p.set_defaults(func=onboarding_apply, preference_source="gui_first_run_onboarding")

    p = sub.add_parser("settings-options")
    p.set_defaults(func=onboarding_options)

    p = sub.add_parser("settings-status")
    p.set_defaults(func=onboarding_status)

    p = sub.add_parser("settings-update")
    add_preferences_arguments(p)
    p.set_defaults(func=onboarding_apply, preference_source="gui_settings_update")

    p = sub.add_parser("identity-context")
    p.add_argument("--tenant", required=True)
    p.add_argument("--deployment", required=True)
    p.add_argument("--user", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--project")
    p.add_argument("--agent")
    p.add_argument("--workflow-run")
    p.add_argument("--session")
    p.set_defaults(func=identity_context)

    p = sub.add_parser("auth-decision")
    p.add_argument("--tenant", required=True)
    p.add_argument("--deployment", required=True)
    p.add_argument("--user", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--action", required=True)
    p.add_argument("--resource-type", required=True)
    p.add_argument("--resource-id", required=True)
    p.add_argument("--project")
    p.add_argument("--agent")
    p.add_argument("--workflow-run")
    p.add_argument("--reason")
    p.set_defaults(func=auth_decision)

    p = sub.add_parser("workflow-start")
    p.add_argument("--tenant", required=True)
    p.add_argument("--deployment", required=True)
    p.add_argument("--user", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--task")
    p.add_argument("--title")
    p.add_argument("--project")
    p.add_argument("--agent", default="auto")
    p.add_argument("--workflow")
    p.add_argument("--priority", choices=["low", "normal", "high", "urgent"], default="normal")
    p.add_argument("--run-id")
    p.add_argument("--task-id")
    p.add_argument("--idempotency-key")
    p.add_argument("--reason")
    p.set_defaults(func=workflow_start)

    p = sub.add_parser("agent-invoke")
    p.add_argument("--tenant", required=True)
    p.add_argument("--deployment", required=True)
    p.add_argument("--user", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--project", required=True)
    p.add_argument("--agent", required=True)
    p.add_argument("--task")
    p.add_argument("--title")
    p.add_argument("--priority", choices=["low", "normal", "high", "urgent"], default="normal")
    p.add_argument("--run-id")
    p.add_argument("--task-id")
    p.add_argument("--reason")
    p.set_defaults(func=agent_invoke)

    p = sub.add_parser("workflow-status")
    p.add_argument("--run-id", required=True)
    p.set_defaults(func=workflow_status)

    p = sub.add_parser("workflow-list")
    p.add_argument("--status")
    p.add_argument("--project")
    p.add_argument("--user")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=workflow_list)

    p = sub.add_parser("workflow-cancel")
    p.add_argument("--run-id", required=True)
    p.add_argument("--requested-by", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--reason")
    p.add_argument("--confirmed", action="store_true")
    p.set_defaults(func=workflow_cancel)

    p = sub.add_parser("workflow-resume")
    p.add_argument("--run-id", required=True)
    p.add_argument("--requested-by", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--reason")
    p.set_defaults(func=workflow_resume)

    p = sub.add_parser("workflow-retry")
    p.add_argument("--run-id", required=True)
    p.add_argument("--stage", choices=LOOP_STAGES)
    p.add_argument("--requested-by", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--reason")
    p.set_defaults(func=workflow_retry)

    p = sub.add_parser("workflow-draft-create")
    p.add_argument("--run-id", required=True)
    p.add_argument("--created-by", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--revision-id")
    p.add_argument("--summary")
    p.set_defaults(func=workflow_draft_create)

    p = sub.add_parser("workflow-draft-patch")
    p.add_argument("--run-id", required=True)
    p.add_argument("--revision-id", required=True)
    p.add_argument("--updated-by", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--patch-json")
    p.add_argument("--patch-file")
    p.add_argument("--summary")
    p.set_defaults(func=workflow_draft_patch)

    p = sub.add_parser("workflow-draft-validate")
    p.add_argument("--run-id", required=True)
    p.add_argument("--revision-id", required=True)
    p.set_defaults(func=workflow_draft_validate)

    p = sub.add_parser("workflow-draft-activate")
    p.add_argument("--run-id", required=True)
    p.add_argument("--revision-id", required=True)
    p.add_argument("--activated-by", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--reason")
    p.add_argument("--confirmed", action="store_true")
    p.set_defaults(func=workflow_draft_activate)

    p = sub.add_parser("workflow-control")
    p.add_argument("--run-id", required=True)
    p.add_argument("--action", choices=sorted(WORKFLOW_CONTROL_ACTIONS), required=True)
    p.add_argument("--requested-by", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--reason")
    p.add_argument("--confirmed", action="store_true")
    p.set_defaults(func=workflow_control)

    p = sub.add_parser("workflow-node-context")
    p.add_argument("--run-id", required=True)
    p.add_argument("--node-id", required=True)
    p.add_argument("--revision-id")
    p.set_defaults(func=workflow_node_context)

    p = sub.add_parser("task-list")
    p.add_argument("--status", choices=sorted(TASK_STATUSES))
    p.add_argument("--project")
    p.add_argument("--assigned-agent")
    p.add_argument("--assigned-user")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=task_list)

    p = sub.add_parser("task-status")
    p.add_argument("--task-id", required=True)
    p.set_defaults(func=task_status)

    p = sub.add_parser("task-update")
    p.add_argument("--task-id", required=True)
    p.add_argument("--status", choices=sorted(TASK_STATUSES))
    p.add_argument("--summary")
    p.add_argument("--artifact", action="append")
    p.add_argument("--assigned-agent")
    p.add_argument("--assigned-user")
    p.add_argument("--updated-by", required=True)
    p.add_argument("--role", required=True)
    p.set_defaults(func=task_update)

    p = sub.add_parser("approval-create")
    p.add_argument("--tenant", required=True)
    p.add_argument("--deployment", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--body")
    p.add_argument("--action", required=True)
    p.add_argument("--resource-type", required=True)
    p.add_argument("--resource-id", required=True)
    p.add_argument("--requested-by", required=True)
    p.add_argument("--requested-by-role", required=True)
    p.add_argument("--approver-role", default="project_manager")
    p.add_argument("--project")
    p.add_argument("--agent")
    p.add_argument("--workflow-run")
    p.add_argument("--task-id")
    p.add_argument("--risk")
    p.add_argument("--expires-at")
    p.add_argument("--approval-id")
    p.add_argument("--idempotency-key")
    p.set_defaults(func=approval_create)

    p = sub.add_parser("approval-list")
    p.add_argument("--status", choices=sorted(APPROVAL_STATUSES))
    p.add_argument("--project")
    p.add_argument("--approver-role")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=approval_list)

    p = sub.add_parser("approval-decision")
    p.add_argument("--approval-id", required=True)
    p.add_argument("--decision", choices=["approve", "reject", "cancel"], required=True)
    p.add_argument("--decided-by", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--message")
    p.add_argument("--confirmed", action="store_true")
    p.set_defaults(func=approval_decision)

    p = sub.add_parser("audit-events")
    p.add_argument("--event")
    p.add_argument("--resource-type")
    p.add_argument("--resource-id")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=audit_events)

    p = sub.add_parser("notification-list")
    p.add_argument("--user")
    p.add_argument("--unread-only", action="store_true")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=notification_list)

    p = sub.add_parser("notification-mark-read")
    p.add_argument("--notification-id", required=True)
    p.add_argument("--user")
    p.set_defaults(func=notification_mark_read)

    p = sub.add_parser("loop-start")
    p.add_argument("--run-id")
    p.add_argument("--task")
    p.add_argument("--project")
    p.add_argument("--agent")
    p.add_argument("--workflow", default="")
    p.add_argument("--requested-by", default="")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=loop_start)

    p = sub.add_parser("loop-stage")
    p.add_argument("--run-id", required=True)
    p.add_argument("--stage", choices=LOOP_STAGES, required=True)
    p.add_argument("--status", choices=["started", "completed", "failed", "blocked"], required=True)
    p.add_argument("--summary")
    p.add_argument("--body")
    p.add_argument("--artifact", action="append")
    p.add_argument("--gate", action="append")
    p.set_defaults(func=loop_stage)

    p = sub.add_parser("loop-status")
    p.add_argument("--run-id", required=True)
    p.set_defaults(func=loop_status)

    p = sub.add_parser("iteration-proposal-create")
    p.add_argument("--title", required=True)
    p.add_argument("--target", choices=["agent", "workflow", "rule", "knowledge", "harness", "release", "model", "product"], required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--body")
    p.add_argument("--expected-impact", required=True)
    p.add_argument("--risk", required=True)
    p.add_argument("--rollback", required=True)
    p.add_argument("--run-id")
    p.add_argument("--project")
    p.add_argument("--agent")
    p.add_argument("--source-ref", action="append")
    p.add_argument("--regression-check", action="append")
    p.set_defaults(func=iteration_proposal_create)

    p = sub.add_parser("iteration-proposal-decision")
    p.add_argument("--proposal-id", required=True)
    p.add_argument("--decision", choices=["confirm", "tune", "pause", "reject"], required=True)
    p.add_argument("--message")
    p.set_defaults(func=iteration_proposal_decision)

    p = sub.add_parser("iteration-proposal-apply")
    p.add_argument("--proposal-id", required=True)
    p.add_argument("--confirmed", action="store_true")
    p.add_argument("--applied-by", default="")
    p.add_argument("--artifact", action="append")
    p.add_argument("--regression-result")
    p.add_argument("--note")
    p.set_defaults(func=iteration_proposal_apply)

    p = sub.add_parser("methodology-draft")
    p.add_argument("--project", required=True)
    p.add_argument("--period", default="manual")
    p.set_defaults(func=methodology_draft)

    p = sub.add_parser("methodology-approve")
    p.add_argument("--project", required=True)
    p.add_argument("--draft", required=True)
    p.add_argument("--confirmed", action="store_true")
    p.set_defaults(func=methodology_approve)

    p = sub.add_parser("relay-add")
    p.add_argument("--project", required=True)
    p.add_argument("--subproject")
    p.add_argument("--agent", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--body")
    p.add_argument("--status", choices=["active", "blocked", "done", "superseded"], default="active")
    p.add_argument("--source-ref", action="append")
    p.add_argument("--next-action", action="append")
    p.set_defaults(func=relay_add)

    p = sub.add_parser("agent-request-submit")
    p.add_argument("--title", required=True)
    p.add_argument("--body")
    p.add_argument("--project")
    p.add_argument("--requested-by")
    p.add_argument("--priority", choices=["low", "normal", "high", "urgent"], default="normal")
    p.add_argument("--confirmed", action="store_true")
    p.add_argument("--timeout", type=int, default=30)
    p.set_defaults(func=agent_request_submit)

    p = sub.add_parser("agent-request-status")
    p.add_argument("--request-id", required=True)
    p.set_defaults(func=agent_request_status)

    p = sub.add_parser("agent-request-set-status")
    p.add_argument("--request-id", required=True)
    p.add_argument(
        "--status",
        choices=["received", "in_progress", "completed", "downloaded_deployed", "pending_user_confirmation", "needs_tuning", "paused_by_user", "needs_more_info", "rejected"],
        required=True,
    )
    p.add_argument("--message")
    p.add_argument("--package")
    p.set_defaults(func=agent_request_set_status)

    p = sub.add_parser("agent-improvement-draft")
    p.add_argument("--agent", required=True)
    p.add_argument("--kind", choices=["soul", "workflow"], required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--body")
    p.add_argument("--project")
    p.set_defaults(func=agent_improvement_draft)

    p = sub.add_parser("agent-improvement-approve")
    p.add_argument("--agent", required=True)
    p.add_argument("--draft", required=True)
    p.add_argument("--confirmed", action="store_true")
    p.set_defaults(func=agent_improvement_approve)

    p = sub.add_parser("agent-plugin-report")
    p.add_argument("--package", required=True)
    p.add_argument("--project")
    p.add_argument("--request-id")
    p.set_defaults(func=agent_plugin_report)

    p = sub.add_parser("agent-plugin-decision")
    p.add_argument("--report-id", required=True)
    p.add_argument("--decision", choices=["confirm", "tune", "pause"], required=True)
    p.add_argument("--message")
    p.set_defaults(func=agent_plugin_decision)

    p = sub.add_parser("agent-plugin-activate")
    p.add_argument("--package", required=True)
    p.add_argument("--project")
    p.add_argument("--report")
    p.add_argument("--report-id")
    p.add_argument("--request-id")
    p.add_argument("--confirmed", action="store_true")
    p.add_argument("--replace-agent", action="store_true")
    p.add_argument("--replace-profile", action="store_true")
    p.set_defaults(func=agent_plugin_activate)

    p = sub.add_parser("rag-index")
    p.add_argument("--scope", choices=["company", "project"], required=True)
    p.add_argument("--project")
    p.add_argument("--mode", choices=["auto", "lexical", "embedding"], default="auto")
    p.add_argument("--embedding-model", default="BAAI/bge-small-zh-v1.5")
    p.add_argument("--chunk-chars", type=int, default=1200)
    p.add_argument("--chunk-overlap", type=int, default=180)
    p.add_argument("--include-pending", action="store_true")
    p.set_defaults(func=rag_index)

    p = sub.add_parser("rag-search")
    p.add_argument("--scope", choices=["company", "project"], required=True)
    p.add_argument("--project")
    p.add_argument("--query", required=True)
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--embedding-model", default="BAAI/bge-small-zh-v1.5")
    p.set_defaults(func=rag_search)

    p = sub.add_parser("knowledge-source-mount")
    p.add_argument("--source-class", choices=["customer_owned_external_kb", "provider_sold_industry_kb"], required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--display-name")
    p.add_argument("--provider", default="")
    p.add_argument("--tenant", required=True)
    p.add_argument("--deployment", required=True)
    p.add_argument("--created-by", required=True)
    p.add_argument("--mount-target", choices=["company_knowledge", "project_knowledge", "agent_specialist_context", "licensed_company_reference", "licensed_project_reference", "licensed_agent_reference"], required=True)
    p.add_argument("--project")
    p.add_argument("--agent")
    p.add_argument("--entitlement")
    p.add_argument("--license-sku")
    p.add_argument("--sync-mode", choices=["metadata_only", "selected_items", "excerpt_index", "embedding_index", "full_customer_owned_sync", "controlled_remote_retrieval"], default="excerpt_index")
    p.add_argument("--allowed-user", action="append")
    p.add_argument("--allowed-role", action="append")
    p.add_argument("--mount-id")
    p.add_argument("--replace", action="store_true")
    p.set_defaults(func=knowledge_source_mount)

    p = sub.add_parser("knowledge-access-log")
    p.add_argument("--tenant", required=True)
    p.add_argument("--deployment", required=True)
    p.add_argument("--user", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--project")
    p.add_argument("--agent")
    p.add_argument("--workflow-run")
    p.add_argument("--source-class", choices=["customer_owned_external_kb", "provider_sold_industry_kb"], required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--mount-id", required=True)
    p.add_argument("--knowledge-pack")
    p.add_argument("--entitlement")
    p.add_argument("--query")
    p.add_argument("--result-source-id", action="append")
    p.add_argument("--snippet-count", type=int, default=0)
    p.add_argument("--decision", choices=["allow", "deny"], required=True)
    p.add_argument("--deny-reason")
    p.set_defaults(func=knowledge_access_log)

    p = sub.add_parser("telemetry-status")
    p.set_defaults(func=telemetry_status)

    p = sub.add_parser("telemetry-export")
    p.set_defaults(func=telemetry_export)

    p = sub.add_parser("telemetry-send")
    p.add_argument("--bundle", required=True)
    p.add_argument("--confirmed", action="store_true")
    p.add_argument("--timeout", type=int, default=30)
    p.set_defaults(func=telemetry_send)

    p = sub.add_parser("health")
    p.set_defaults(func=health)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
