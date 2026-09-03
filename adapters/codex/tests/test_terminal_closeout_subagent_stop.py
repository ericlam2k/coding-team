#!/usr/bin/env python3
"""Focused tests for the Codex SubagentStop closeout guard."""

from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "terminal-closeout-subagent-stop.py"
SPEC = importlib.util.spec_from_file_location("terminal_closeout_subagent_stop", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TerminalCloseoutSubagentStopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project = Path(self.temp_dir.name) / "project"
        (self.project / "nested").mkdir(parents=True)
        (self.project / "AGENTS.md").write_text("<!-- coding-team:begin -->\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_hook(self, event: object) -> tuple[int, dict[str, object]]:
        output = io.StringIO()
        with patch("sys.stdin", io.StringIO(json.dumps(event))), redirect_stdout(output):
            code = MODULE.main()
        return code, json.loads(output.getvalue())

    def valid_message(self) -> str:
        return (
            "- **Recommended next to-do:** CT-42 — Lead prepares the next bounded task\n"
            "- **Pending tasks:** NONE\n"
        )

    def event(self, message: object, **extra: object) -> dict[str, object]:
        return {
            "hook_event_name": "SubagentStop",
            "cwd": str(self.project / "nested"),
            "last_assistant_message": message,
            "stop_hook_active": False,
            "agent_transcript_path": str(self.project / "missing-transcript.jsonl"),
            **extra,
        }

    def test_valid_closeout_is_allowed_without_reading_transcript(self) -> None:
        code, result = self.run_hook(self.event(self.valid_message()))
        self.assertEqual(code, 0)
        self.assertTrue(result["continue"])
        self.assertNotIn("decision", result)

    def test_first_invalid_closeout_requests_one_continuation(self) -> None:
        code, result = self.run_hook(self.event("- **Recommended next to-do:** TBD\n- **Pending tasks:** NONE"))
        self.assertEqual(code, 0)
        self.assertEqual(result["decision"], "block")
        self.assertIn("CODING_TEAM_CLOSEOUT", result["reason"])

    def test_repeated_invalid_closeout_stops_without_a_loop(self) -> None:
        code, result = self.run_hook(self.event("", stop_hook_active=True))
        self.assertEqual(code, 0)
        self.assertFalse(result["continue"])
        self.assertEqual(result["stopReason"], "CODING_TEAM_CLOSEOUT:BLOCKED")

    def test_ordinary_project_is_ignored(self) -> None:
        ordinary = Path(self.temp_dir.name) / "ordinary"
        ordinary.mkdir()
        code, result = self.run_hook({**self.event(""), "cwd": str(ordinary)})
        self.assertEqual(code, 0)
        self.assertTrue(result["continue"])
        self.assertNotIn("decision", result)

    def test_unmarked_nearest_project_is_not_inherited_from_marked_parent(self) -> None:
        nested = self.project / "ordinary-child"
        (nested / "deep").mkdir(parents=True)
        (nested / "AGENTS.md").write_text("ordinary project\n", encoding="utf-8")
        code, result = self.run_hook({**self.event(""), "cwd": str(nested / "deep")})
        self.assertEqual(code, 0)
        self.assertTrue(result["continue"])
        self.assertNotIn("decision", result)

    def test_non_subagent_event_is_ignored(self) -> None:
        code, result = self.run_hook({"hook_event_name": "Stop", "cwd": str(self.project), "last_assistant_message": ""})
        self.assertEqual(code, 0)
        self.assertTrue(result["continue"])

    def test_invalid_event_fails_closed(self) -> None:
        output = io.StringIO()
        with patch("sys.stdin", io.StringIO("not-json")), redirect_stdout(output):
            code = MODULE.main()
        result = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertFalse(result["continue"])
        self.assertIn("EVENT_INVALID", result["stopReason"])

    def test_scope_without_cwd_fails_closed(self) -> None:
        code, result = self.run_hook({"hook_event_name": "SubagentStop", "last_assistant_message": self.valid_message()})
        self.assertEqual(code, 0)
        self.assertFalse(result["continue"])
        self.assertIn("project-scope-unavailable", result["stopReason"])

    def test_invalid_stop_hook_state_fails_closed(self) -> None:
        code, result = self.run_hook(self.event(self.valid_message(), stop_hook_active="false"))
        self.assertEqual(code, 0)
        self.assertFalse(result["continue"])
        self.assertIn("stop-hook-state-invalid", result["stopReason"])


if __name__ == "__main__":
    unittest.main()
