#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "bin" / "feishu-team-installer.py"
SPEC = importlib.util.spec_from_file_location("feishu_team_installer", PATH)
assert SPEC and SPEC.loader
INSTALLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTALLER)


def main() -> None:
    catalog = INSTALLER.team_catalog(ROOT)
    assert catalog["kind"] == "digital-office-feishu-installer-catalog"
    assert len(catalog["teams"]) == 4
    assert sum(team["agent_count"] for team in catalog["teams"]) == 33
    assert {team["team_id"] for team in catalog["teams"]} == {
        "digital-office-product-team", "digital-office-research-team",
        "digital-office-writer-team", "fde-team",
    }

    plan = INSTALLER.installation_plan(
        ROOT, ["digital-office-product-team", "digital-office-research-team"],
    )
    assert plan["bot_count"] == 16
    assert plan["online_confirmations_required"] == plan["missing_count"]
    assert len({bot["bot_key"] for bot in plan["bots"]}) == 16
    assert len({bot["profile"] for bot in plan["bots"]}) == 16

    try:
        INSTALLER.start_session(ROOT, team_ids=["digital-office-product-team"], confirmed=False)
        raise AssertionError("unconfirmed external writes must fail closed")
    except INSTALLER.InstallerError:
        pass

    with tempfile.TemporaryDirectory() as temporary:
        temp_root = Path(temporary)
        session_id = "a" * 32
        directory = temp_root / "runs" / "feishu-installer" / session_id
        directory.mkdir(parents=True)
        (directory / "session.json").write_text(json.dumps({
            "schema_version": "1.0", "session_id": session_id, "pid": 0,
            "team_ids": ["digital-office-product-team"], "bot_count": 2,
            "initial_ready_count": 0, "missing_count": 2,
        }), encoding="utf-8")
        events = [
            {"event": "authorization_required", "time": "2026-01-01T00:00:00Z", "bot_key": "team/a", "authorization_url": "https://open.feishu.cn/example", "expires_in": 600},
            {"event": "ready", "time": "2026-01-01T00:01:00Z", "bot_key": "team/a"},
            {"event": "already_ready", "time": "2026-01-01T00:01:01Z", "bot_key": "team/b"},
            {"event": "session_complete", "time": "2026-01-01T00:01:02Z", "ready_count": 2, "bot_count": 2},
        ]
        (directory / "events.ndjson").write_text(
            json.dumps(events[0]) + "\n", encoding="utf-8",
        )
        waiting = INSTALLER.session_status(temp_root, session_id)
        assert waiting["latest_authorization"]["authorization_url"].startswith("https://open.feishu.cn/")
        (directory / "events.ndjson").write_text(
            "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8",
        )
        status = INSTALLER.session_status(temp_root, session_id)
        assert status["status"] == "complete"
        assert status["ready_count"] == 2
        assert status["latest_authorization"] is None

    print("feishu installer smoke: PASS")


if __name__ == "__main__":
    main()
