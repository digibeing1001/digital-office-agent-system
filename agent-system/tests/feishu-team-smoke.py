#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "bin" / "feishu-team-gateway.py"
SPEC = importlib.util.spec_from_file_location("feishu_team_gateway", PATH)
assert SPEC and SPEC.loader
GATEWAY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATEWAY)
MANIFEST = json.loads((ROOT / "feishu-team.example.json").read_text(encoding="utf-8"))


def environment():
    env = {MANIFEST["chat_id_env"]: "oc_project"}
    for index, agent in enumerate(MANIFEST["agents"]):
        env[agent["app_id_env"]] = f"cli_{index}"
        env[agent["open_id_env"]] = f"ou_{index}"
    return env


def main():
    env = environment()
    GATEWAY.validate(MANIFEST)
    inventory = {"agents": {item["agent_id"]: {
        "app_id": env[item["app_id_env"]], "open_id": env[item["open_id_env"]]
    } for item in MANIFEST["agents"]}}
    inventory_env = GATEWAY.inventory_environment(MANIFEST, inventory, {})
    assert inventory_env == {key: value for key, value in env.items() if key != MANIFEST["chat_id_env"]}
    specialists = ["pm", "researcher", "planner", "vibe-designer", "coder", "writer"]
    proposal = GATEWAY.staffing_proposal(
        MANIFEST, objective="Run a seven-bot project team", specialists=specialists
    )
    assert proposal["core_agents"] == ["secretary"]
    assert len(proposal["selected_agents"]) == 7
    assert GATEWAY.invite_batch_sizes(len(proposal["selected_agents"])) == [5, 2]
    commands = GATEWAY.provision_plan(
        MANIFEST, env, proposal=proposal, confirmation_token=proposal["confirmation_token"]
    )
    assert len(commands) == 2 and commands[0][3:5] == ["im", "+chat-create"]
    first_batch = commands[0][commands[0].index("--bots") + 1].split(",")
    second_batch = json.loads(commands[1][commands[1].index("--data") + 1])["id_list"]
    assert len(first_batch) == 5
    assert len(second_batch) == 2
    assert first_batch + second_batch == [
        env[agent["app_id_env"]]
        for agent in MANIFEST["agents"]
        if agent["agent_id"] in proposal["selected_agents"]
    ]
    try:
        GATEWAY.provision_plan(MANIFEST, env, proposal=proposal, confirmation_token="not-confirmed")
        raise AssertionError("unconfirmed staffing must fail closed")
    except GATEWAY.ContractError:
        pass
    class Result:
        returncode = 0
        stderr = ""
        stdout = "{}"
    calls = []
    def runner(command, **_kwargs):
        calls.append(command)
        result = Result()
        if len(calls) == 1:
            result.stdout = json.dumps({"data": {"chat_id": "oc_created"}})
        return result
    applied = GATEWAY.apply_provision_plan(MANIFEST, commands, runner=runner)
    assert applied["status"] == "deployed" and applied["chat_id"] == "oc_created"
    assert len(calls) == 2 and "oc_created" in calls[1]
    handoff = GATEWAY.build_handoff(
        MANIFEST, sender="secretary", target="researcher", task="调研证据",
        correlation_id="corr-1", hop=1, visited_edges=[], env=env,
    )
    secretary = env[MANIFEST["agents"][0]["open_id_env"]]
    researcher = env[next(item for item in MANIFEST["agents"] if item["agent_id"] == "researcher")["open_id_env"]]
    event = {
        "chat_id": "oc_project", "message_id": "om_1", "sender_type": "bot",
        "sender_id": secretary, "mentions": [{"id": researcher}], "content": handoff["text"],
    }
    with tempfile.TemporaryDirectory() as state:
        accepted = GATEWAY.route_event(MANIFEST, event, current_agent="researcher", state_dir=state, env=env)
        assert accepted["accepted"] and accepted["reason"] == "bot_handoff"
        assert GATEWAY.route_event(MANIFEST, event, current_agent="researcher", state_dir=state, env=env)["reason"] == "duplicate_message"
        wrong = dict(event, message_id="om_2", chat_id="oc_other")
        assert not GATEWAY.route_event(MANIFEST, wrong, current_agent="researcher", state_dir=state, env=env)["accepted"]
    print("feishu team smoke: PASS")


if __name__ == "__main__":
    main()
