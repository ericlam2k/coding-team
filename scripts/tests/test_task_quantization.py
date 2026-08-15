import hashlib
import json
import unittest

from core.routing.context_budgeter import ContextBudgetError, budget_context


class ContextBudgeterTests(unittest.TestCase):
    def test_exact_context_matrix(self) -> None:
        cases = (
            ("Q0", "NONE", "C0", 0),
            ("Q1", "BOUNDED", "C1", 4_000),
            ("Q2", "NONE", "C2", 12_000),
            ("Q2", "BOUNDED", "C2", 12_000),
            ("Q2", "INTEGRATION", "C3", 24_000),
            ("Q2", "RELEASE", "C3", 24_000),
            ("Q3", "NONE", "C4", 48_000),
            ("Q4", "RELEASE", "C5", 96_000),
        )
        for quantized_class, validation_need, level, tokens in cases:
            with self.subTest(quantized_class=quantized_class, validation_need=validation_need):
                self.assertEqual(
                    budget_context(quantized_class, validation_need),
                    {
                        "quantized_class": quantized_class,
                        "context_level": level,
                        "context_budget_tokens": tokens,
                        "status": "ROUTED",
                    },
                )

    def test_invalid_quantized_class_is_schema_error_without_payload(self) -> None:
        with self.assertRaises(ContextBudgetError) as raised:
            budget_context("Q9", "NONE")
        self.assertEqual(raised.exception.code, "QRT-SCHEMA")
        self.assertEqual(raised.exception.field, "quantized_class")
        self.assertNotIn("Q9", str(raised.exception))

    def test_invalid_validation_need_is_schema_error_without_payload(self) -> None:
        with self.assertRaises(ContextBudgetError) as raised:
            budget_context("Q2", "FULL")
        self.assertEqual(raised.exception.code, "QRT-SCHEMA")
        self.assertEqual(raised.exception.field, "validation_need")
        self.assertNotIn("FULL", str(raised.exception))


if __name__ == "__main__":
    unittest.main()


from core.routing.quantizer import QuantizationError, quantize_task


class QuantizerTests(unittest.TestCase):
    def _build_request(self, **overrides):
        """Build a valid baseline request with optional overrides."""
        base = {
            "schema_version": "quant-route/v1",
            "task_id": "TEST-001",
            "run_id": "test-run/01",
            "nature": "N1_BOUNDED_WORKER",
            "role_id": "backend-engineer",
            "minimum_model_tier": "0",
            "no_model_eligible": False,
            "execution_scope": "SCOPED_WRITE",
            "reasoning_depth": "MECHANICAL",
            "enumeration_required": False,
            "synthesis_input_ref": None,
            "estimated_input_tokens": {"value": 1500, "provenance": "MEASURED"},
            "estimated_files_touched": {"value": 1, "provenance": "MEASURED"},
            "validation_need": "NONE",
            "architecture_impact": "NONE",
            "risks": [],
            "evidence_refs": ["contract-v1"],
        }
        base.update(overrides)
        return base

    def test_q0_deterministic_template(self) -> None:
        """Q0: no-model template with MECHANICAL reasoning and no risks."""
        request = self._build_request(
            no_model_eligible=True,
            minimum_model_tier="NONE",
            reasoning_depth="MECHANICAL",
            validation_need="NONE",
            risks=[],
        )
        result = quantize_task(request)
        
        self.assertEqual(result["quantized_class"], "Q0")
        self.assertEqual(result["model_tier"], "NONE")
        self.assertEqual(result["precedence_rule"], "P2_DETERMINISTIC_TEMPLATE")
        self.assertFalse(result["human_gate_required"])
        self.assertEqual(result["status"], "ROUTED")
        self.assertEqual(result["confidence"], "HIGH")

    def test_q1_low_score(self) -> None:
        """Q1: score 0-2, simple bounded task."""
        request = self._build_request(
            estimated_input_tokens={"value": 1500, "provenance": "MEASURED"},
            estimated_files_touched={"value": 1, "provenance": "MEASURED"},
            reasoning_depth="MECHANICAL",
            validation_need="NONE",
            architecture_impact="NONE",
            risks=[],
        )
        result = quantize_task(request)
        
        self.assertEqual(result["quantized_class"], "Q1")
        self.assertEqual(result["model_tier"], "0")
        self.assertEqual(result["precedence_rule"], "P3_SCORE_0_2")
        self.assertEqual(result["score"], 1)  # tokens=0, files=1
        self.assertEqual(result["status"], "ROUTED")

    def test_q2_mid_score_with_c3_validation(self) -> None:
        """Q2: score 3-7, 12k tokens, C2→C3 with INTEGRATION validation."""
        request = self._build_request(
            estimated_input_tokens={"value": 12000, "provenance": "MEASURED"},
            estimated_files_touched={"value": 2, "provenance": "MEASURED"},
            reasoning_depth="RECONCILE",
            validation_need="INTEGRATION",
            architecture_impact="NONE",
            risks=[],
        )
        result = quantize_task(request)
        
        self.assertEqual(result["quantized_class"], "Q2")
        self.assertEqual(result["model_tier"], "1-build")
        self.assertEqual(result["precedence_rule"], "P3_SCORE_3_7")
        # score: tokens=2, files=2, reasoning=1, validation=2, arch=0, risk=0 = 7
        self.assertEqual(result["score"], 7)
        self.assertEqual(result["context_level"], "C3")
        self.assertEqual(result["context_budget_tokens"], 24_000)
        self.assertEqual(result["status"], "ROUTED")

    def test_q3_high_score(self) -> None:
        """Q3: score ≥8, complex multi-file task."""
        request = self._build_request(
            estimated_input_tokens={"value": 25000, "provenance": "MEASURED"},
            estimated_files_touched={"value": 5, "provenance": "MEASURED"},
            reasoning_depth="JUDGMENT",
            validation_need="RELEASE",
            architecture_impact="SHARED",
            risks=["PUBLIC_CONTRACT", "MIGRATION"],
        )
        result = quantize_task(request)
        
        self.assertEqual(result["quantized_class"], "Q3")
        self.assertEqual(result["model_tier"], "2")
        self.assertEqual(result["precedence_rule"], "P3_SCORE_8_PLUS")
        # score: tokens=3, files=3, reasoning=3, validation=3, arch=3, risk=4 = 19
        self.assertEqual(result["score"], 19)
        self.assertEqual(result["status"], "ROUTED")

    def test_q4_security_gate_blocked(self) -> None:
        """Q4: SECURITY risk triggers human gate and BLOCKED status."""
        request = self._build_request(
            risks=["SECURITY"],
        )
        result = quantize_task(request)
        
        self.assertEqual(result["quantized_class"], "Q4")
        self.assertEqual(result["model_tier"], "3")
        self.assertEqual(result["precedence_rule"], "P1_HIGH_RISK_OR_GATE")
        self.assertTrue(result["human_gate_required"])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["failure_code"], "QRT-HUMAN-GATE")

    def test_nature_role_and_execution_scope_are_nonempty_pass_through(self) -> None:
        request = self._build_request(
            nature="future-nature",
            role_id="future-role",
            execution_scope="future-scope",
        )
        self.assertEqual(quantize_task(request)["status"], "ROUTED")

        for field in ("nature", "role_id", "execution_scope"):
            with self.subTest(field=field):
                with self.assertRaises(QuantizationError) as raised:
                    quantize_task(self._build_request(**{field: ""}))
                self.assertEqual(raised.exception.code, "QRT-SCHEMA")
                self.assertEqual(raised.exception.field, field)

    def test_low_confidence_blocks(self) -> None:
        """UNKNOWN provenance causes LOW confidence and BLOCKED status."""
        request = self._build_request(
            estimated_input_tokens={"value": None, "provenance": "UNKNOWN"},
        )
        result = quantize_task(request)
        
        self.assertEqual(result["confidence"], "LOW")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["failure_code"], "QRT-LOW-CONFIDENCE")

    def test_unknown_estimates_score_maximum_buckets_and_block(self) -> None:
        result = quantize_task(self._build_request(
            estimated_input_tokens={"value": None, "provenance": "UNKNOWN"},
            estimated_files_touched={"value": None, "provenance": "UNKNOWN"},
        ))
        self.assertEqual(result["score_breakdown"]["input_tokens"], 3)
        self.assertEqual(result["score_breakdown"]["files_touched"], 3)
        self.assertEqual(result["confidence"], "LOW")
        self.assertEqual(result["status"], "BLOCKED")

    def test_duplicate_valid_risks_are_deduplicated_for_scoring(self) -> None:
        result = quantize_task(self._build_request(
            risks=["PUBLIC_CONTRACT", "PUBLIC_CONTRACT"],
        ))
        self.assertEqual(result["score_breakdown"]["risks"], 2)

    def test_input_digest_is_canonical_utf8_json_sha256(self) -> None:
        request = self._build_request(nature="Náture")
        expected = hashlib.sha256(json.dumps(
            request,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")).hexdigest()
        self.assertEqual(quantize_task(request)["input_digest"], expected)

    def test_unknown_key_is_payload_free_schema_error(self) -> None:
        secret = "do-not-echo-this-key"
        request = self._build_request()
        request[secret] = "do-not-echo-this-value"
        with self.assertRaises(QuantizationError) as raised:
            quantize_task(request)
        self.assertEqual(raised.exception.code, "QRT-SCHEMA")
        self.assertEqual(raised.exception.field, "request")
        self.assertNotIn(secret, str(raised.exception))
        self.assertNotIn(request[secret], str(raised.exception))

    def test_equal_rank_preserves_lead_tier_floor(self) -> None:
        result = quantize_task(self._build_request(
            minimum_model_tier="1-validate",
            estimated_input_tokens={"value": 4000, "provenance": "MEASURED"},
            estimated_files_touched={"value": 2, "provenance": "MEASURED"},
        ))
        self.assertEqual(result["quantized_class"], "Q2")
        self.assertEqual(result["model_tier"], "1-validate")

    def test_confidence_requires_exact_provenance_matrix(self) -> None:
        one_estimated = quantize_task(self._build_request(
            estimated_input_tokens={"value": 1500, "provenance": "ESTIMATED"},
        ))
        both_estimated = quantize_task(self._build_request(
            estimated_input_tokens={"value": 1500, "provenance": "ESTIMATED"},
            estimated_files_touched={"value": 1, "provenance": "ESTIMATED"},
        ))
        self.assertEqual(one_estimated["confidence"], "MEDIUM")
        self.assertEqual(both_estimated["confidence"], "LOW")
        self.assertEqual(both_estimated["status"], "BLOCKED")

    def test_escalation_rules_are_the_frozen_six(self) -> None:
        result = quantize_task(self._build_request())
        self.assertEqual(result["escalation_rules"], [
            "NEW_RISK",
            "EVIDENCE_CONFLICT",
            "CROSS_MODULE_DISCOVERY",
            "TIER_1_FAILURE_TWICE",
            "HIGH_RISK_ADVISOR_CONTRADICTOR_DEADLOCK",
            "CONTEXT_OVERFLOW",
        ])
