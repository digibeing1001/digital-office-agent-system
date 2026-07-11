#!/usr/bin/env python3
"""Deterministic tests for the durable dispatch contract."""

from __future__ import annotations

import importlib.util
import json
import multiprocessing
import tempfile
import unittest
from pathlib import Path


OFFICE_PATH = Path(__file__).resolve().parents[1] / "bin" / "office-system.py"
SPEC = importlib.util.spec_from_file_location("digital_office_system", OFFICE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot import {OFFICE_PATH}")
OFFICE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OFFICE)


def _race_for_dispatch_lease(root: str, start_event, result_queue, owner: str) -> None:
    start_event.wait(timeout=10)
    result = OFFICE.acquire_dispatch_lease(Path(root), "run-1", owner=owner, ttl_seconds=60)
    result_queue.put({"owner": owner, "acquired": result.get("acquired"), "reason": result.get("reason")})


class DispatchLeaseContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="digital-office-runtime-")
        self.root = Path(self._tmp.name) / "agent-system"
        (self.root / "runs" / "run-1").mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_active_lease_blocks_duplicate_dispatch_and_owner_controls_release(self) -> None:
        first = OFFICE.acquire_dispatch_lease(self.root, "run-1", owner="worker-a", ttl_seconds=60)
        self.assertTrue(first["acquired"])
        lease = first["lease"]
        self.assertEqual(lease["kind"], "digital-office-dispatch-lease")
        self.assertEqual(lease["status"], "active")
        active_status = OFFICE.dispatch_lease_status(self.root, "run-1")
        self.assertTrue(active_status["active"])
        self.assertEqual(active_status["lease_id"], lease["lease_id"])

        duplicate = OFFICE.acquire_dispatch_lease(self.root, "run-1", owner="worker-b", ttl_seconds=60)
        self.assertFalse(duplicate["acquired"])
        self.assertEqual(duplicate["reason"], "dispatch_already_leased")
        self.assertEqual(duplicate["lease"]["lease_id"], lease["lease_id"])

        wrong_owner = OFFICE.release_dispatch_lease(self.root, "run-1", "wrong-lease-id")
        self.assertFalse(wrong_owner["released"])
        self.assertEqual(wrong_owner["reason"], "dispatch_lease_owner_mismatch")

        released = OFFICE.release_dispatch_lease(
            self.root,
            "run-1",
            lease["lease_id"],
            outcome="dispatch_completed",
        )
        self.assertTrue(released["released"])
        self.assertEqual(released["lease"]["status"], "released")
        self.assertEqual(released["lease"]["outcome"], "dispatch_completed")
        self.assertFalse(OFFICE.dispatch_lease_status(self.root, "run-1")["active"])

        replacement = OFFICE.acquire_dispatch_lease(self.root, "run-1", owner="worker-b", ttl_seconds=60)
        self.assertTrue(replacement["acquired"])
        self.assertNotEqual(replacement["lease"]["lease_id"], lease["lease_id"])

    def test_expired_lease_is_recoverable_after_worker_crash(self) -> None:
        path = OFFICE.dispatch_lease_path(self.root, "run-1")
        path.write_text(
            json.dumps(
                {
                    "version": "1.0.0",
                    "kind": "digital-office-dispatch-lease",
                    "lease_id": "expired-lease",
                    "run_id": "run-1",
                    "owner": "crashed-worker",
                    "status": "active",
                    "acquired_at": "2020-01-01T00:00:00+00:00",
                    "expires_at": "2020-01-01T00:01:00+00:00",
                    "ttl_seconds": 60,
                }
            ),
            encoding="utf-8",
        )
        recovered = OFFICE.acquire_dispatch_lease(self.root, "run-1", owner="worker-c", ttl_seconds=60)
        self.assertTrue(recovered["acquired"])
        self.assertNotEqual(recovered["lease"]["lease_id"], "expired-lease")

    def test_two_processes_cannot_claim_the_same_run(self) -> None:
        context = multiprocessing.get_context("spawn")
        start_event = context.Event()
        result_queue = context.Queue()
        workers = [
            context.Process(
                target=_race_for_dispatch_lease,
                args=(str(self.root), start_event, result_queue, f"worker-{index}"),
            )
            for index in range(2)
        ]
        for worker in workers:
            worker.start()
        start_event.set()
        results = [result_queue.get(timeout=15) for _ in workers]
        for worker in workers:
            worker.join(timeout=15)
            self.assertEqual(worker.exitcode, 0)
        self.assertEqual(sum(bool(result["acquired"]) for result in results), 1)
        self.assertEqual(
            sorted(result["reason"] for result in results),
            ["dispatch_already_leased", "dispatch_lease_acquired"],
        )

    def test_corrupt_or_ambiguous_lease_fails_closed(self) -> None:
        path = OFFICE.dispatch_lease_path(self.root, "run-1")
        path.write_text("{not-json", encoding="utf-8")
        corrupt = OFFICE.acquire_dispatch_lease(self.root, "run-1", owner="worker-d", ttl_seconds=60)
        self.assertFalse(corrupt["acquired"])
        self.assertEqual(corrupt["reason"], "dispatch_lease_corrupt")

        path.write_text(
            json.dumps(
                {
                    "version": "1.0.0",
                    "kind": "digital-office-dispatch-lease",
                    "lease_id": "ambiguous-lease",
                    "run_id": "run-1",
                    "status": "active",
                    "expires_at": "not-a-time",
                }
            ),
            encoding="utf-8",
        )
        ambiguous = OFFICE.acquire_dispatch_lease(self.root, "run-1", owner="worker-e", ttl_seconds=60)
        self.assertFalse(ambiguous["acquired"])
        self.assertEqual(ambiguous["reason"], "dispatch_lease_invalid_expiry")


if __name__ == "__main__":
    unittest.main(verbosity=2)
