#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
GATEWAY = ROOT / "agent-system" / "bin" / "model-gateway"


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
            "DIGITAL_OFFICE_MODEL_PROVIDER_REGISTRY": str(self.registry_path),
            "DIGITAL_OFFICE_MODEL_RUNTIME": str(self.runtime_path),
            "TEST_OPENAI_KEY": "openai-secret",
            "TEST_COMPATIBLE_KEY": "compatible-secret",
            "TEST_ANTHROPIC_KEY": "anthropic-secret",
            "TEST_GEMINI_KEY": "gemini-secret",
        }

    def invoke(self, provider: str, model: str) -> dict[str, Any]:
        proc = subprocess.run([str(GATEWAY), "invoke", "--provider", provider, "--model", model, "--system", "system-test", "--prompt", "prompt-test", "--json"], text=True, capture_output=True, env=self.environment(), timeout=10)
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
        status_proc = subprocess.run([str(GATEWAY), "status"], text=True, capture_output=True, env=self.environment(), timeout=5)
        self.assertEqual(status_proc.returncode, 0, status_proc.stderr)
        self.assertNotIn("openai-secret", status_proc.stdout)
        configure_proc = subprocess.run([str(GATEWAY), "configure", "--agent", "legal", "--mode", "direct_api", "--provider", "openai", "--model", "openai-test", "--confirmed"], text=True, capture_output=True, env=self.environment(), timeout=5)
        self.assertEqual(configure_proc.returncode, 0, configure_proc.stderr)
        runtime = json.loads(self.runtime_path.read_text(encoding="utf-8"))
        self.assertEqual(runtime["agents"]["legal"]["mode"], "direct_api")
        self.assertEqual(stat.S_IMODE(self.runtime_path.stat().st_mode), 0o600)
        router_proc = subprocess.run([str(ROOT / "scripts" / "agent-router"), "--agent", "legal", "summarize this short note"], text=True, capture_output=True, env=self.environment(), timeout=10)
        self.assertEqual(router_proc.returncode, 0, router_proc.stderr)
        self.assertIn("runtime: direct_api", router_proc.stdout)
        self.assertIn("openai-ok", router_proc.stdout)
        router_call = next(call for call in reversed(FakeModelHandler.calls) if call["path"] == "/v1/responses")
        self.assertIn("digital-lawyer-workflows", router_call["body"]["instructions"])

    def test_missing_key_fails_closed(self) -> None:
        env = self.environment()
        env.pop("TEST_OPENAI_KEY")
        proc = subprocess.run([str(GATEWAY), "invoke", "--provider", "openai", "--model", "openai-test", "--prompt", "test"], text=True, capture_output=True, env=env, timeout=5)
        self.assertEqual(proc.returncode, 3)
        self.assertIn("provider_unconfigured", proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
