from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ADAPTIVE = ROOT / "core" / "adaptive-timing.md"
ORCHESTRATION = ROOT / "core" / "orchestration.md"
QA_POLICY = ROOT / "core" / "qa-operating-model.md"
TASK_BRIEF = ROOT / "core" / "templates" / "task-brief.md"
CODEX_SKILL = ROOT / "adapters" / "codex" / "SKILL.md"
CODEX_RUNTIME = ROOT / "adapters" / "codex" / "runtime.md"


def normalized(path: Path) -> str:
    return (
        " ".join(path.read_text(encoding="utf-8").split())
        .replace("**", "")
        .replace("`", "")
    )


class AdaptiveTaskAdmissionPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.adaptive = normalized(ADAPTIVE)
        cls.orchestration = normalized(ORCHESTRATION)
        cls.qa = normalized(QA_POLICY)
        cls.brief = normalized(TASK_BRIEF)
        cls.codex_skill = normalized(CODEX_SKILL)
        cls.codex_runtime = normalized(CODEX_RUNTIME)

    def test_profile_defines_symbolic_bounds_and_no_universal_cap(self) -> None:
        for name in ("T_target", "T_checkpoint", "T_hard", "T_reserve"):
            self.assertIn(name, self.adaptive)
            self.assertIn(name, self.orchestration)
            self.assertIn(name, self.qa)
            self.assertIn(name, self.brief)
        self.assertIn("no cap is a universal constant", self.adaptive)

    def test_plan_prices_setup_mutation_validation_and_handoff(self) -> None:
        self.assertIn("T_policy,p95 + T_memory,p95 + T_migration,p95", self.adaptive)
        self.assertIn("T_repo-bootstrap,p95", self.adaptive)
        self.assertIn("T_plan = T_setup,p95", self.adaptive)
        self.assertIn("T_mutation-unit,p95", self.adaptive)
        self.assertIn("T_validation-command,p95", self.adaptive)
        self.assertIn("T_handoff,p95", self.adaptive)
        self.assertIn("repository-bootstrap=", self.brief)

    def test_unknown_inputs_measure_before_dispatch(self) -> None:
        self.assertIn("Any mandatory UNKNOWN input returns MEASURE", self.adaptive)
        self.assertIn("do not dispatch", self.adaptive)
        self.assertIn("Mandatory UNKNOWN returns MEASURE without dispatch", self.orchestration)
        self.assertIn("mandatory UNKNOWN → MEASURE and no dispatch", self.brief)

    def test_fresh_bootstrap_waste_is_blocked_without_retry_or_hop(self) -> None:
        self.assertIn("After that condition, an unchanged fresh route is BLOCK", self.adaptive)
        self.assertIn("do not retry it or hop models", self.adaptive)
        self.assertIn("reuse valid same-task context with a material delta", self.adaptive)
        self.assertIn("pre-resolve required setup", self.adaptive)
        self.assertIn("Never retry or model-hop to reset the clock", self.brief)

    def test_timeout_is_excluded_from_success_ewma(self) -> None:
        self.assertIn("timed-out runs never enter the successful-duration EWMA", self.adaptive)
        self.assertIn("At T_hard, stop safely without automatic retry", self.adaptive)

    def test_codex_resolves_admit_before_preflight_without_universal_time(self) -> None:
        self.assertIn("Adaptive admission is always loaded", self.codex_skill)
        self.assertIn("before prepare-dispatch.py, resolve ADMIT", self.codex_skill)
        self.assertIn("Resolve ADMIT from core/adaptive-timing.md before running prepare-dispatch.py", self.codex_runtime)
        self.assertIn("no fixed time is universal", self.codex_skill)
        self.assertIn("No fixed target, checkpoint, hard stop, or reserve is universal", self.codex_runtime)

    def test_codex_prices_reload_validation_and_handoff_before_mutation(self) -> None:
        for required in ("context reload", "every validation command", "checkpoint/handoff"):
            self.assertIn(required, self.codex_runtime)
        self.assertIn("pre-resolve each named contract, test, evidence reference, and dependency", self.codex_runtime)
        self.assertIn("Reserve and publish the checkpoint or handoff identity before mutation", self.codex_runtime)

    def test_codex_blocks_repeat_bootstrap_and_allows_one_material_delta(self) -> None:
        self.assertIn("unchanged fresh route is BLOCK", self.codex_runtime)
        self.assertIn("do not retry it or hop models", self.codex_runtime)
        self.assertIn("safe same-task context continuation with exactly one material plaintext delta", self.codex_runtime)
        self.assertIn("Do not mirror the initial packet", self.codex_runtime)
        self.assertIn("shrink the Task and pre-resolve its setup", self.codex_runtime)

    def test_native_critical_continuation_is_accepted_risk_and_keeps_gates(self) -> None:
        self.assertIn("human-approved one-off ACCEPTED_RISK", self.codex_runtime)
        self.assertIn("supervised bootstrap, rather than mutation or validation, is the blocker", self.codex_runtime)
        self.assertIn("not a default critical runner", self.codex_runtime)
        self.assertIn("Test Engineer → bounded QA evidence validator when triggered → Gatekeeper", self.codex_runtime)


if __name__ == "__main__":
    unittest.main()
