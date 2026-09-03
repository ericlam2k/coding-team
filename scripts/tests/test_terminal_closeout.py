#!/usr/bin/env python3
"""Focused tests for the terminal-handoff closeout validator."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "core" / "tools" / "validate_terminal_closeout.py"
SPEC = importlib.util.spec_from_file_location("terminal_closeout", SCRIPT)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - test bootstrap
    raise RuntimeError(f"cannot load {SCRIPT}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TerminalCloseoutTests(unittest.TestCase):
    def handoff(self, next_to_do: str, pending: str) -> str:
        return (
            "- **Status:** DONE\n"
            f"- **Recommended next to-do:** {next_to_do}\n"
            f"- **Pending tasks:** {pending}\n"
        )

    def test_objective_complete_with_no_pending_tasks_is_valid(self) -> None:
        self.assertEqual(MODULE.validate(self.handoff("NONE — objective complete", "NONE")), [])

    def test_one_next_task_and_compact_queue_is_valid(self) -> None:
        text = self.handoff(
            "CT-42 — Lead prepares a bounded fix brief",
            "CT-43 — test-engineer — candidate frozen — QUEUED; CT-44 — gatekeeper — TE PASS — QUEUED",
        )
        self.assertEqual(MODULE.validate(text), [])

    def test_inline_code_queue_fields_are_valid(self) -> None:
        text = self.handoff(
            "Route the human-requested TE pass",
            "`TE pass` — `test-engineer` — `review PASS + evidence` — `queued`.",
        )
        self.assertEqual(MODULE.validate(text), [])

    def test_missing_or_placeholder_fields_are_rejected(self) -> None:
        errors = MODULE.validate(self.handoff("", "(NONE, or task list)"))
        self.assertEqual(len(errors), 2)

    def test_queue_larger_than_three_is_rejected(self) -> None:
        text = self.handoff(
            "CT-42 — Lead makes the next brief",
            "CT-43 — Lead — no gate — READY; CT-44 — Lead — no gate — READY; CT-45 — Lead — no gate — READY; CT-46 — Lead — no gate — READY",
        )
        self.assertIn("at most three", MODULE.validate(text)[0])

    def test_punctuation_duplicates_and_malformed_queue_are_rejected(self) -> None:
        text = (
            "- **Recommended next to-do:** - / -\n"
            "- **Recommended next to-do:** CT-42 — Lead makes a brief\n"
            "- **Pending tasks:** orphan-item\n"
        )
        errors = MODULE.validate(text)
        self.assertTrue(any("exactly once" in error for error in errors))
        self.assertTrue(any("placeholder" in error for error in errors))
        self.assertTrue(any("task ID" in error for error in errors))

    def test_generic_placeholders_overlong_actions_and_complete_queue_conflict_fail(self) -> None:
        for next_to_do, pending, expected in (
            ("TBD.", "NONE", "placeholder"),
            ("<next task>", "NONE", "placeholder"),
            (" ".join(["action"] * 61), "NONE", "at most 60 words"),
            ("NONE — objective complete", "CT-43 — Lead — no gate — READY", "requires Pending tasks: NONE"),
        ):
            with self.subTest(next_to_do=next_to_do):
                self.assertTrue(any(expected in error for error in MODULE.validate(self.handoff(next_to_do, pending))))

    def test_cli_accepts_valid_text_and_rejects_missing_closeout(self) -> None:
        with tempfile.TemporaryDirectory() as cache:
            env = {**os.environ, "PYTHONPYCACHEPREFIX": cache}
            valid = subprocess.run(
                [sys.executable, str(SCRIPT), "--stdin"],
                input=self.handoff("NONE — objective complete", "NONE"),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            invalid = subprocess.run(
                [sys.executable, str(SCRIPT), "--stdin"],
                input=self.handoff("", "NONE"),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertEqual(invalid.returncode, 1)
        self.assertIn("Recommended next to-do", invalid.stderr)


if __name__ == "__main__":
    unittest.main()
