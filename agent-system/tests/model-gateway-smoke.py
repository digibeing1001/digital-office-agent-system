#!/usr/bin/env python3
from __future__ import annotations

import json
import datetime as dt
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
GATEWAY = ROOT / "agent-system" / "bin" / "model-gateway"


def python_script(path: Path) -> list[str]:
    if os.name == "nt":
        return [sys.executable, str(path)]
    return [str(path)]


def assert_private_file_mode(testcase: unittest.TestCase, path: Path) -> None:
    if os.name == "nt":
        testcase.assertTrue(path.exists())
        return
    testcase.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)


class FakeModelHandler(BaseHTTPRequestHandler):
    calls: list[dict[str, Any]] = []
    response_attempts = 0

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length).decode("utf-8"))
        self.__class__.calls.append({"path": self.path, "headers": dict(self.headers), "body": body})
        if self.path == "/v1/responses":
            self.__class__.response_attempts += 1
            if self.__class__.response_attempts == 1:
                self.send_response(429)
                self.end_headers()
                self.wfile.write(b'{"error":"retry"}')
                return
            payload = {"id": "resp-test", "output_text": "openai-ok", "usage": {"input_tokens": 4, "output_tokens": 2}}
        elif self.path == "/v1/chat/completions":
            payload = {"id": "chat-test", "choices": [{"message": {"content": "compatible-ok"}}], "usage": {"prompt_tokens": 3, "completion_tokens": 1}}
        elif self.path == "/v1/messages":
            payload = {"id": "msg-test", "content": [{"type": "text", "text": "anthropic-ok"}], "usage": {"input_tokens": 5, "output_tokens": 2}}
        elif self.path == "/v1/models/gemini-test:generateContent":
            payload = {"responseId": "gem-test", "candidates": [{"content": {"parts": [{"text": "gemini-ok"}]}}], "usageMetadata": {"promptTokenCount": 2, "candidatesTokenCount": 2}}
        else:
            self.send_response(404)
            self.end_headers()
            return
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


class ModelGatewaySmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeModelHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.temp = tempfile.TemporaryDirectory(prefix="digital-office-model-gateway-")
        cls.temp_path = Path(cls.temp.name)
        cls.system_root = cls.temp_path / "agent-system"
        (cls.system_root / "settings").mkdir(parents=True)
        local_hermes = cls.temp_path / "bin" / ("hermes.cmd" if os.name == "nt" else "hermes")
        local_hermes.parent.mkdir(parents=True)
        local_codex = cls.temp_path / "bin" / ("codex.cmd" if os.name == "nt" else "codex")
        if os.name == "nt":
            local_hermes.write_text("@echo off\r\nexit /b 0\r\n", encoding="utf-8")
            local_codex.write_text("@echo off\r\nif \"%1\"==\"exec\" if \"%2\"==\"--help\" echo codex-help& exit /b 0\r\necho codex-local-ok %*\r\nexit /b 0\r\n", encoding="utf-8")
        else:
            local_hermes.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            local_hermes.chmod(0o700)
            local_codex.write_text("#!/bin/sh\nif [ \"$1\" = \"exec\" ] && [ \"$2\" = \"--help\" ]; then echo codex-help; exit 0; fi\necho codex-local-ok \"$@\"\n", encoding="utf-8")
            local_codex.chmod(0o700)
        cls.local_codex = local_codex
        shutil.copy2(ROOT / "agent-system" / "ai-native-loop.manifest.json", cls.system_root / "ai-native-loop.manifest.json")
        shutil.copy2(ROOT / "agent-system" / "agents.registry.json", cls.system_root / "agents.registry.json")
        port = cls.server.server_address[1]
        registry = {
            "kind": "digital-office-model-providers",
            "version": "test",
            "defaults": {"request_timeout_seconds": 3, "max_output_tokens": 64, "retry_attempts": 3, "max_response_bytes": 100000},
            "providers": {
                "openai": {"protocol": "openai_responses", "base_url": f"http://127.0.0.1:{port}/v1", "api_key_env": "TEST_OPENAI_KEY"},
                "compatible": {"protocol": "openai_chat_completions", "base_url": f"http://127.0.0.1:{port}/v1", "api_key_env": "TEST_COMPATIBLE_KEY"},
                "anthropic": {"protocol": "anthropic_messages", "base_url": f"http://127.0.0.1:{port}/v1", "api_key_env": "TEST_ANTHROPIC_KEY", "api_version": "2023-06-01"},
                "gemini": {"protocol": "gemini_generate_content", "base_url": f"http://127.0.0.1:{port}/v1", "api_key_env": "TEST_GEMINI_KEY"},
            },
        }
        cls.registry_path = cls.temp_path / "providers.json"
        cls.registry_path.write_text(json.dumps(registry), encoding="utf-8")
        cls.runtime_path = cls.temp_path / "runtime.json"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.temp.cleanup()

    def environment(self) -> dict[str, str]:
        return {
            **os.environ,
            "HERMES_HOME": str(self.temp_path),
            "DIGITAL_OFFICE_SYSTEM_HOME": str(self.system_root),
            "DIGITAL_OFFICE_MODEL_GATEWAY": str(GATEWAY),
            "DIGITAL_OFFICE_OFFICE_SYSTEM": str(ROOT / "agent-system" / "bin" / "office-system.py"),
            "DIGITAL_OFFICE_LOCAL_RUNTIME_PROBE_TIMEOUT": "0.5",
            "DIGITAL_OFFICE_MODEL_PROVIDER_REGISTRY": str(self.registry_path),
            "DIGITAL_OFFICE_MODEL_RUNTIME": str(self.runtime_path),
            "TEST_OPENAI_KEY": "openai-secret",
            "TEST_COMPATIBLE_KEY": "compatible-secret",
            "TEST_ANTHROPIC_KEY": "anthropic-secret",
            "TEST_GEMINI_KEY": "gemini-secret",
            "DIGITAL_OFFICE_CODEX_COMMAND": str(self.local_codex),
            "DIGITAL_OFFICE_CLAUDE_CODE_COMMAND": "/bin/echo",
            "DIGITAL_OFFICE_OPENCLAW_COMMAND": "/bin/echo",
        }

    def invoke(self, provider: str, model: str) -> dict[str, Any]:
        proc = subprocess.run([*python_script(GATEWAY), "invoke", "--provider", provider, "--model", model, "--system", "system-test", "--prompt", "prompt-test", "--json"], text=True, capture_output=True, env=self.environment(), timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def test_supported_protocols_and_retry(self) -> None:
        FakeModelHandler.response_attempts = 0
        cases = [("openai", "openai-test", "openai-ok"), ("compatible", "compatible-test", "compatible-ok"), ("anthropic", "anthropic-test", "anthropic-ok"), ("gemini", "gemini-test", "gemini-ok")]
        for provider, model, expected in cases:
            with self.subTest(provider=provider):
                result = self.invoke(provider, model)
                self.assertEqual(result["text"], expected)
                self.assertGreater(result["usage"]["total_tokens"], 0)
        self.assertEqual(FakeModelHandler.response_attempts, 2)
        headers = {key.lower(): value for key, value in FakeModelHandler.calls[-1]["headers"].items()}
        self.assertEqual(headers.get("x-goog-api-key"), "gemini-secret")

    def test_status_redacts_secrets_and_configure_is_private(self) -> None:
        status_proc = subprocess.run([*python_script(GATEWAY), "status"], text=True, capture_output=True, env=self.environment(), timeout=5)
        self.assertEqual(status_proc.returncode, 0, status_proc.stderr)
        self.assertNotIn("openai-secret", status_proc.stdout)
        configure_proc = subprocess.run([*python_script(GATEWAY), "configure", "--agent", "legal", "--mode", "direct_api", "--provider", "openai", "--model", "openai-test", "--confirmed"], text=True, capture_output=True, env=self.environment(), timeout=5)
        self.assertEqual(configure_proc.returncode, 0, configure_proc.stderr)
        runtime = json.loads(self.runtime_path.read_text(encoding="utf-8"))
        self.assertEqual(runtime["agents"]["legal"]["mode"], "direct_api")
        assert_private_file_mode(self, self.runtime_path)
        router_proc = subprocess.run([*python_script(ROOT / "scripts" / "agent-router"), "--agent", "legal", "summarize this short note"], text=True, capture_output=True, env=self.environment(), timeout=10)
        self.assertEqual(router_proc.returncode, 0, router_proc.stderr)
        self.assertIn("runtime: direct_api", router_proc.stdout)
        self.assertIn("openai-ok", router_proc.stdout)
        router_call = next(call for call in reversed(FakeModelHandler.calls) if call["path"] == "/v1/responses")
        self.assertIn("digital-lawyer-workflows", router_call["body"]["instructions"])

    def test_missing_key_fails_closed(self) -> None:
        env = self.environment()
        env.pop("TEST_OPENAI_KEY")
        proc = subprocess.run([*python_script(GATEWAY), "invoke", "--provider", "openai", "--model", "openai-test", "--prompt", "test"], text=True, capture_output=True, env=env, timeout=5)
        self.assertEqual(proc.returncode, 3)
        self.assertIn("provider_unconfigured", proc.stderr)

    def test_router_records_model_usage_in_governed_loop(self) -> None:
        env = self.environment()
        configure = subprocess.run([*python_script(GATEWAY), "configure", "--agent", "writer", "--mode", "direct_api", "--provider", "openai", "--model", "openai-test", "--confirmed"], text=True, capture_output=True, env=env, timeout=5)
        self.assertEqual(configure.returncode, 0, configure.stderr)
        run_id = "model-accounting"
        run_dir = self.system_root / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        manifest = json.loads((self.system_root / "ai-native-loop.manifest.json").read_text(encoding="utf-8"))
        budgets = dict(manifest["controller"]["default_budgets"])
        budgets["max_model_calls"] = 1
        run = {
            "version": "2.0.0",
            "kind": "digital-office-loop-run",
            "run_id": run_id,
            "context_id": run_id,
            "task_id": "model-accounting-task",
            "status": "acting",
            "current_stage": "act",
            "agent_id": "writer",
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "control": {"cycle_index": 1, "budgets": budgets, "usage": {"tool_calls": 0, "model_calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_microunits": 0}, "stage_retries": {}},
            "stages": {},
            "events": [],
        }
        (run_dir / "run.json").write_text(json.dumps(run), encoding="utf-8")
        router = subprocess.run([*python_script(ROOT / "scripts" / "agent-router"), "--agent", "writer", "--run-id", run_id, "draft a short internal greeting"], text=True, capture_output=True, env=env, timeout=15)
        self.assertEqual(router.returncode, 0, router.stderr)
        recorded = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        self.assertEqual(recorded["control"]["usage"]["model_calls"], 1)
        self.assertIn("max_model_calls_exhausted", recorded.get("blockers", []))
        self.assertGreater(recorded["control"]["usage"]["input_tokens"], 0)
        ledger = [json.loads(line) for line in (run_dir / "ledger.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertIn("model_call_completed", [item["event"] for item in ledger])

    def test_stored_connection_is_private_and_auto_resolution_is_deterministic(self) -> None:
        env = self.environment()
        env.pop("TEST_COMPATIBLE_KEY")
        connection = subprocess.run(
            [*python_script(GATEWAY), "connection-set", "--provider", "compatible", "--base-url", f"http://127.0.0.1:{self.server.server_address[1]}/v1", "--model", "compatible-test", "--secret-stdin", "--confirmed"],
            input="stored-compatible-secret",
            text=True,
            capture_output=True,
            env=env,
            timeout=5,
        )
        self.assertEqual(connection.returncode, 0, connection.stderr)
        credentials = self.system_root / "settings" / "model-credentials.json"
        assert_private_file_mode(self, credentials)
        status_proc = subprocess.run([*python_script(GATEWAY), "status", "--provider", "compatible"], text=True, capture_output=True, env=env, timeout=5)
        self.assertEqual(status_proc.returncode, 0, status_proc.stderr)
        self.assertNotIn("stored-compatible-secret", status_proc.stdout)
        provider = json.loads(status_proc.stdout)["providers"][0]
        self.assertEqual(provider["secret_hint"], "...cret")
        runtime_proc = subprocess.run([*python_script(GATEWAY), "runtime-set", "--default-mode", "auto", "--selection-policy", "api_first", "--provider-order", "compatible,openai", "--confirmed"], text=True, capture_output=True, env=env, timeout=5)
        self.assertEqual(runtime_proc.returncode, 0, runtime_proc.stderr)
        resolve_proc = subprocess.run([*python_script(GATEWAY), "resolve", "--agent", "researcher", "--requested-mode", "auto", "--host-provider", "host-provider", "--host-model", "host-model"], text=True, capture_output=True, env=env, timeout=5)
        self.assertEqual(resolve_proc.returncode, 0, resolve_proc.stderr)
        selected = json.loads(resolve_proc.stdout)["execution"]
        self.assertEqual((selected["mode"], selected["provider"], selected["model"]), ("direct_api", "compatible", "compatible-test"))
        local_policy = subprocess.run([*python_script(GATEWAY), "runtime-set", "--selection-policy", "local_first", "--confirmed"], text=True, capture_output=True, env=env, timeout=5)
        self.assertEqual(local_policy.returncode, 0, local_policy.stderr)
        local_resolve = subprocess.run([*python_script(GATEWAY), "resolve", "--agent", "researcher", "--requested-mode", "auto", "--host-provider", "host-provider", "--host-model", "host-model"], text=True, capture_output=True, env=env, timeout=5)
        self.assertEqual(local_resolve.returncode, 0, local_resolve.stderr)
        self.assertEqual(json.loads(local_resolve.stdout)["execution"]["mode"], "host")

    def test_router_executes_selected_local_runtime(self) -> None:
        env = self.environment()
        configure = subprocess.run([*python_script(GATEWAY), "configure", "--agent", "writer", "--mode", "host", "--local-runtime", "codex", "--confirmed"], text=True, capture_output=True, env=env, timeout=5)
        self.assertEqual(configure.returncode, 0, configure.stderr)
        router = subprocess.run([*python_script(ROOT / "scripts" / "agent-router"), "--agent", "writer", "--runtime", "host", "draft local runtime note"], text=True, capture_output=True, env=env, timeout=10)
        self.assertEqual(router.returncode, 0, router.stderr)
        self.assertIn("runtime: host", router.stdout)
        self.assertIn("codex-local-ok", router.stdout)
        self.assertIn("exec", router.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
