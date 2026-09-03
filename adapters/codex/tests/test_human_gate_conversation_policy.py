from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CORE_POLICY = ROOT / "core" / "human-gates.md"
CODEX_ADAPTER = ROOT / "adapters" / "codex" / "SKILL.md"


class HumanGateConversationPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.core = " ".join(
            CORE_POLICY.read_text(encoding="utf-8").split()
        ).replace("**", "")
        cls.adapter = " ".join(
            CODEX_ADAPTER.read_text(encoding="utf-8").split()
        ).replace("**", "")

    def test_core_keeps_natural_language_questions_available(self) -> None:
        self.assertIn("it does not pause conversation", self.core)
        self.assertIn("Do not require the human to know or type command keywords", self.core)
        self.assertIn("question or request for an example or explanation", self.core)
        self.assertIn("zero workflow mutation", self.core)
        self.assertIn("the gate remains pending", self.core)

    def test_core_requires_semantic_scope_bound_approval(self) -> None:
        self.assertIn("Interpret the semantic intent of natural language", self.core)
        self.assertIn("current task, gated action, and scope", self.core)
        self.assertIn("Resume only the approved action", self.core)

    def test_core_limits_revise_cancel_and_clarifies_ambiguity(self) -> None:
        self.assertIn("revise or cancel changes only the named current decision", self.core)
        self.assertIn("Ambiguous input receives a concise clarification question", self.core)
        self.assertIn("alter unrelated tasks, scope, gates, or release state", self.core)

    def test_core_rejects_quoted_or_example_approval_wording(self) -> None:
        self.assertIn("Quoted approval wording", self.core)
        self.assertIn("request for an approval example, is not approval", self.core)

    def test_adapter_keeps_a_short_always_loaded_anchor(self) -> None:
        self.assertIn("Pending-gate conversation", self.adapter)
        self.assertIn("users need no keyword", self.adapter)
        self.assertIn("zero workflow mutation and keep the gate pending", self.adapter)
        self.assertIn("task/action/scope-bound approval resumes", self.adapter)
        self.assertIn("Clarify ambiguous input without mutation", self.adapter)
        self.assertIn("quoted or example approval wording is not approval", self.adapter)
        self.assertIn("`core/human-gates.md` is the source of truth", self.adapter)


if __name__ == "__main__":
    unittest.main()
