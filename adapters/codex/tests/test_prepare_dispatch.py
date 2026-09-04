#!/usr/bin/env python3
"""Focused tests for the optional native Codex payload formatter."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare-dispatch.py"
SPEC = importlib.util.spec_from_file_location("prepare_dispatch", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class NativePayloadTests(unittest.TestCase):
    def test_role_message_is_minimal_native_payload(self) -> None:
        result = MODULE.format_native_payload(
            {"role": "backend-engineer", "message": "Run one focused check."}
        )
        self.assertEqual(result["agent_type"], "worker")
        self.assertRegex(result["task_name"], r"^worker_[0-9a-f]{8}$")
        self.assertEqual(result["fork_turns"], "1")
        self.assertEqual(result["message"], "Run one focused check.")

    def test_explicit_model_and_effort_are_preserved(self) -> None:
        result = MODULE.prepare_dispatch({
            "agent_type": "worker", "message": "Build the bounded change.",
            "model": "gpt-5.6-sol", "reasoning_effort": "high",
        })
        self.assertEqual(result["model"], "gpt-5.6-sol")
        self.assertEqual(result["reasoning_effort"], "high")
        self.assertEqual(
            set(result),
            {"agent_type", "task_name", "fork_turns", "message", "model", "reasoning_effort"},
        )

    def test_direct_payload_can_skip_formatter_fields(self) -> None:
        self.assertEqual(MODULE.format_native_payload({
            "agent_type": "explorer", "task_name": "inspect_one", "fork_turns": "all",
            "message": "Inspect one file."
        }), {
            "agent_type": "explorer", "task_name": "inspect_one", "fork_turns": "all",
            "message": "Inspect one file."
        })

    def test_removed_controls_are_rejected(self) -> None:
        for field in ("host_binding", "allocation", "dispatch_id", "receipt"):
            with self.subTest(field=field), self.assertRaises(MODULE.PacketValidationError) as raised:
                MODULE.format_native_payload({"agent_type": "worker", "message": "x", field: "legacy"})
            self.assertIn("removed workflow field", str(raised.exception))

    def test_active_host_identity_and_context_fields_are_validated(self) -> None:
        for packet in (
            {"agent_type": "worker", "message": "x", "fork_context": False},
            {"agent_type": "worker", "message": "x", "task_name": "Bad-Name"},
            {"agent_type": "worker", "message": "x", "fork_turns": "none"},
            {"agent_type": "worker", "message": "x", "fork_turns": 0},
        ):
            with self.subTest(packet=packet), self.assertRaises(MODULE.PacketValidationError):
                MODULE.format_native_payload(packet)

        result = MODULE.format_native_payload({
            "agent_type": "worker", "message": "x", "task_name": "bounded_task",
            "fork_turns": 2,
        })
        self.assertEqual(result["task_name"], "bounded_task")
        self.assertEqual(result["fork_turns"], "2")

    def test_invalid_role_and_message_fail_closed(self) -> None:
        for packet in ({"role": "monitor-agent", "message": "x"}, {"agent_type": "worker"}):
            with self.assertRaises(MODULE.PacketValidationError):
                MODULE.format_native_payload(packet)


if __name__ == "__main__":
    unittest.main()
