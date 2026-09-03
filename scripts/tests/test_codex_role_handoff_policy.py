#!/usr/bin/env python3
"""Regression tests for the Codex adapter role-card handoff boundary."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SKILL = (ROOT / "adapters/codex/SKILL.md").read_text(encoding="utf-8")
RUNTIME = (ROOT / "adapters/codex/runtime.md").read_text(encoding="utf-8")
SKILL_FLAT = " ".join(SKILL.split())
RUNTIME_FLAT = " ".join(RUNTIME.split())


class CodexRoleHandoffPolicyTest(unittest.TestCase):
    def test_missing_host_receipt_is_not_an_ordinary_dispatch_gate(self) -> None:
        self.assertIn("that absence is not a dispatch gate", SKILL_FLAT)
        self.assertIn("consumption_status: UNVERIFIED", SKILL_FLAT)
        self.assertIn("must not stop unrelated work", RUNTIME_FLAT)

    def test_consumed_remains_host_attested(self) -> None:
        self.assertIn("`CONSUMED` is reserved for an approved same-task host-runtime receipt", SKILL_FLAT)
        self.assertIn("Only an approved host runtime event for the same task may set `CONSUMED`", RUNTIME_FLAT)
        self.assertIn("never mints, repairs, or infers a host receipt", RUNTIME_FLAT)

    def test_project_local_handoff_is_auditable(self) -> None:
        for field in (
            "task/run ID",
            "canonical role ID",
            "matching card hash",
            "exclusive scope",
            "planned → actual",
            "artifact/evidence references",
        ):
            self.assertIn(field, SKILL_FLAT)

    def test_docs_steward_gate_is_preserved(self) -> None:
        self.assertIn(
            "Named path + fresh TE PASS + sequential GK APPROVE/APPROVE_WITH_NOTES",
            RUNTIME_FLAT,
        )
        self.assertIn("Ordinary handoffs never route through Docs Steward", RUNTIME_FLAT)


if __name__ == "__main__":
    unittest.main()
