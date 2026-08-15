#!/usr/bin/env python3
"""Regression tests for the Codex adapter role-card handoff boundary."""

from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[2]
SKILL = (ROOT / "adapters/codex/SKILL.md").read_text(encoding="utf-8")
RUNTIME = (ROOT / "adapters/codex/runtime.md").read_text(encoding="utf-8")
ORCHESTRATION = (ROOT / "core/orchestration.md").read_text(encoding="utf-8")
MODEL_ROUTING = (ROOT / "core/model-routing.md").read_text(encoding="utf-8")
TASK_BRIEF = (ROOT / "core/templates/task-brief.md").read_text(encoding="utf-8")
HANDOFF = (ROOT / "core/templates/handoff.md").read_text(encoding="utf-8")
ADAPTIVE_TIMING = (ROOT / "core/adaptive-timing.md").read_text(encoding="utf-8")
QA_OPERATING_MODEL = (ROOT / "core/qa-operating-model.md").read_text(encoding="utf-8")
TEST_ENGINEER = (ROOT / "core/roles/test-engineer.md").read_text(encoding="utf-8")
QA_EVIDENCE = json.loads((ROOT / "core/templates/qa-evidence.json").read_text(encoding="utf-8"))
SKILL_FLAT = " ".join(SKILL.split())
RUNTIME_FLAT = " ".join(RUNTIME.split())
ORCHESTRATION_FLAT = " ".join(ORCHESTRATION.split())
MODEL_ROUTING_FLAT = " ".join(MODEL_ROUTING.split())
TASK_BRIEF_FLAT = " ".join(TASK_BRIEF.split())
HANDOFF_FLAT = " ".join(HANDOFF.split())
ADAPTIVE_TIMING_FLAT = " ".join(ADAPTIVE_TIMING.split())
QA_OPERATING_MODEL_FLAT = " ".join(QA_OPERATING_MODEL.split())
TEST_ENGINEER_FLAT = " ".join(TEST_ENGINEER.split())


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

    def test_task_fields_and_legacy_readability_are_explicit(self) -> None:
        for field in (
            "`execution_scope`",
            "`reasoning_depth`",
            "`enumeration_required`",
            "`synthesis_input_ref`",
        ):
            self.assertIn(field, TASK_BRIEF_FLAT)
            self.assertIn(field, ORCHESTRATION_FLAT)
            self.assertIn(field, MODEL_ROUTING_FLAT)
        self.assertIn("`MECHANICAL` | `RECONCILE` | `JUDGMENT`", TASK_BRIEF_FLAT)
        self.assertIn("Legacy briefs without them remain readable as `UNSPECIFIED`", TASK_BRIEF_FLAT)
        self.assertIn("Block new policy-sensitive enumeration", MODEL_ROUTING_FLAT)

    def test_enumeration_has_investigator_and_manager_boundary(self) -> None:
        self.assertIn("`enumeration_required=true` requires a separate `investigator` Task", MODEL_ROUTING_FLAT)
        self.assertIn("Managers (`lead`, `product-manager`, `system-architect`, `advisor`, `contradictor`, and `{domain}-advisor`)", MODEL_ROUTING_FLAT)
        self.assertIn("must stop before locating, listing, counting, copying, or normalizing source facts", MODEL_ROUTING_FLAT)
        self.assertIn("Lead alone reconciles role outputs", ORCHESTRATION_FLAT)
        self.assertIn("Investigator supplies facts and conflicts", ORCHESTRATION_FLAT)

    def test_synthetic_lookup_scenarios_keep_one_owner_and_one_next_action(self) -> None:
        scenarios = (
            ("pure judgment", "Split a mixed execution and synthesis task"),
            ("bounded enumeration", "`enumeration_required=true` requires a separate `investigator` Task"),
            ("conflicting evidence", "Return to Lead for a corrected Investigator / Tier 1 brief"),
            ("missing receipt", "`TELEMETRY_UNAVAILABLE`"),
        )
        policy = f"{ORCHESTRATION_FLAT} {MODEL_ROUTING_FLAT} {HANDOFF_FLAT}"
        for name, expected_rule in scenarios:
            with self.subTest(name=name):
                self.assertIn(expected_rule, policy)
        self.assertIn("one unresolved item, and exactly one next Task", policy)

    def test_checkpoint_and_unavailable_telemetry_are_not_model_hops(self) -> None:
        for document in (ORCHESTRATION_FLAT, MODEL_ROUTING_FLAT, TASK_BRIEF_FLAT, HANDOFF_FLAT):
            self.assertIn("TELEMETRY_UNAVAILABLE", document)
            self.assertIn("second lookup session", document)
            self.assertIn("second follow-up", document)
        self.assertIn("do not trigger a model hop", MODEL_ROUTING_FLAT)
        self.assertIn("Monitor receives these fields as passive evidence", MODEL_ROUTING_FLAT)
        self.assertIn("parent and worker task/role IDs", ORCHESTRATION_FLAT)
        self.assertIn("stateful trace", ORCHESTRATION_FLAT)

    def test_handoff_carries_assignment_and_observation_fields(self) -> None:
        for field in (
            "Assignment fields",
            "Bounded evidence",
            "inspected-source count",
            "lookup-session count",
            "Checkpoint / escalation reason",
            "Receipt",
        ):
            self.assertIn(field, HANDOFF_FLAT)
        self.assertIn("exactly one next Task", HANDOFF_FLAT)

    def test_existing_role_routes_and_concurrency_remain_named(self) -> None:
        self.assertIn("| **N0** Map/fact | Investigator | 0 (1 if cross-file)", MODEL_ROUTING_FLAT)
        self.assertIn("| **N1** Bounded build | Backend / Frontend Builder / TE if test-heavy | 1 build", MODEL_ROUTING_FLAT)
        self.assertIn("WIP ≤2", ORCHESTRATION_FLAT)
        self.assertIn("Test Engineer → Gatekeeper sequential", ORCHESTRATION_FLAT)

    def test_adaptive_timing_policy_covers_profile_calc_and_governance(self) -> None:
        self.assertIn(
            "Bounds must be positive, `target < checkpoint < hard_stop`, `hard_stop_s <= max_hard_cap_s`, and `reserve < hard_stop-target`; `max_hard_cap_s` is required.",
            ADAPTIVE_TIMING_FLAT,
        )
        self.assertIn(
            "Defaults are recommendations, not invariants: `initial_target_s=90`, `min_success_samples=5`, `alpha=0.3`, `blend_weight=0.5`, `margin=1.25`, and `max_step_ratio=0.2`. Every value remains app-configurable.",
            ADAPTIVE_TIMING_FLAT,
        )
        self.assertIn("`active_cap_s = min(hard_stop_s, max_hard_cap_s) - reserve_s`", ADAPTIVE_TIMING_FLAT)
        self.assertIn("`E_n = alpha*d_n + (1-alpha)*E_(n-1)`", ADAPTIVE_TIMING_FLAT)
        self.assertIn(
            "`R_raw = min(active_cap_s, ceil(blend_weight*target_s + (1-blend_weight)*margin*E_n))`",
            ADAPTIVE_TIMING_FLAT,
        )
        self.assertIn(
            "Rate-limit `R_raw` to the configurable `max_step_ratio` interval around the prior approved recommendation, then cap it at `active_cap_s`.",
            ADAPTIVE_TIMING_FLAT,
        )
        self.assertIn(
            "so right-censored outcomes must remain separate",
            ADAPTIVE_TIMING_FLAT,
        )
        self.assertIn("Monitor may observe and propose only.", ADAPTIVE_TIMING_FLAT)
        self.assertIn("The app owner must approve any durable profile change.", ADAPTIVE_TIMING_FLAT)
        self.assertIn(
            "This policy is independent of operating system, runtime, or provider.",
            ADAPTIVE_TIMING_FLAT,
        )

    def test_adaptive_timing_reference_is_flattened_and_time_free(self) -> None:
        for document in (ORCHESTRATION_FLAT, TASK_BRIEF_FLAT):
            self.assertIn("adaptive-timing.md", document)
            self.assertIn("T_target", document)
            self.assertIn("T_checkpoint", document)
            self.assertIn("T_hard", document)
            self.assertIn("T_reserve", document)
        self.assertIn("adaptive-timing.md", MODEL_ROUTING_FLAT)
        self.assertIn("T_checkpoint", MODEL_ROUTING_FLAT)
        self.assertNotIn("T_target", MODEL_ROUTING_FLAT)
        self.assertNotIn("T_hard", MODEL_ROUTING_FLAT)
        self.assertNotIn("T_reserve", MODEL_ROUTING_FLAT)
        for document in (ORCHESTRATION_FLAT, MODEL_ROUTING_FLAT, TASK_BRIEF_FLAT):
            self.assertNotIn("120-second target", document)
            self.assertNotIn("180 seconds without", document)
            self.assertNotIn("240 seconds", document)

    def test_qa_role_adapters_carry_adaptive_timing_reference(self) -> None:
        for token in ("adaptive-timing.md", "T_target", "T_checkpoint", "T_hard", "T_reserve"):
            self.assertIn(token, QA_OPERATING_MODEL_FLAT)
        for document in (TEST_ENGINEER_FLAT, SKILL_FLAT):
            for token in ("adaptive-timing.md", "T_target", "T_checkpoint", "T_hard"):
                self.assertIn(token, document)
        for document in (QA_OPERATING_MODEL_FLAT, TEST_ENGINEER_FLAT, SKILL_FLAT):
            self.assertNotIn("120-second target", document)
            self.assertNotIn("240-second hard stop", document)

    def test_qa_evidence_template_keeps_adaptive_timing_editable_until_resolved(self) -> None:
        timebox = QA_EVIDENCE["timebox"]
        self.assertEqual(timebox["profile_status"], "UNRESOLVED")
        self.assertEqual(timebox["profile_provenance"], "UNRESOLVED")
        for field in (
            "resolved_target_seconds",
            "resolved_checkpoint_seconds",
            "resolved_hard_seconds",
            "resolved_reserve_seconds",
            "resolved_max_hard_cap_seconds",
        ):
            self.assertIsNone(timebox[field])
        self.assertEqual(timebox["recommended_target_seconds"], 90)
        self.assertEqual(timebox["recommendation_status"], "EDITABLE")


if __name__ == "__main__":
    unittest.main()
