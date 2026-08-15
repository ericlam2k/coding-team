"""Deterministic task quantization and abstract model-tier selection."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Final, Mapping

from core.routing.context_budgeter import budget_context


class QuantizationError(ValueError):
    """Raised when quantization input violates the frozen contract."""

    def __init__(self, code: str, field: str) -> None:
        self.code = code
        self.field = field
        super().__init__(code)


_VALID_TIERS: Final[frozenset[str]] = frozenset({
    "NONE", "0", "1-build", "1-validate", "2", "3"
})

_TIER_RANK: Final[dict[str, int]] = {
    "NONE": 0, "0": 1, "1-build": 2, "1-validate": 2, "2": 3, "3": 4
}

_VALID_REASONING: Final[frozenset[str]] = frozenset({
    "MECHANICAL", "RECONCILE", "JUDGMENT"
})

_VALID_VALIDATION: Final[frozenset[str]] = frozenset({
    "NONE", "BOUNDED", "INTEGRATION", "RELEASE"
})

_VALID_ARCH_IMPACT: Final[frozenset[str]] = frozenset({
    "NONE", "LOCAL", "SHARED"
})

_HIGH_RISK_SET: Final[frozenset[str]] = frozenset({
    "SECURITY", "PRIVACY", "DATA_LOSS", "PRODUCTION",
    "IRREVERSIBLE", "DESTRUCTIVE", "EXTERNAL_PROVIDER", "REAL_PERSONAL_DATA"
})

_SCORED_RISKS: Final[frozenset[str]] = frozenset({
    "PUBLIC_CONTRACT", "MIGRATION", "AUTH"
})

_ALL_RISKS: Final[frozenset[str]] = _HIGH_RISK_SET | _SCORED_RISKS

_VALID_PROVENANCE: Final[frozenset[str]] = frozenset({
    "MEASURED", "ESTIMATED", "UNKNOWN"
})

_REQUEST_FIELDS: Final[frozenset[str]] = frozenset({
    "schema_version", "task_id", "run_id", "nature", "role_id",
    "minimum_model_tier", "no_model_eligible", "execution_scope",
    "reasoning_depth", "enumeration_required", "synthesis_input_ref",
    "estimated_input_tokens", "estimated_files_touched", "validation_need",
    "architecture_impact", "risks", "evidence_refs",
})

_ESCALATION_RULES: Final[tuple[str, ...]] = (
    "NEW_RISK",
    "EVIDENCE_CONFLICT",
    "CROSS_MODULE_DISCOVERY",
    "TIER_1_FAILURE_TWICE",
    "HIGH_RISK_ADVISOR_CONTRADICTOR_DEADLOCK",
    "CONTEXT_OVERFLOW",
)


def _validate_estimate(
    field_name: str, estimate: Any
) -> tuple[int | None, str]:
    """Validate and extract estimate structure."""
    if not isinstance(estimate, Mapping):
        raise QuantizationError("QRT-SCHEMA", field_name)
    
    if set(estimate.keys()) != {"value", "provenance"}:
        raise QuantizationError("QRT-SCHEMA", field_name)
    
    value = estimate["value"]
    provenance = estimate["provenance"]
    
    if not isinstance(provenance, str) or provenance not in _VALID_PROVENANCE:
        raise QuantizationError("QRT-SCHEMA", f"{field_name}.provenance")
    
    if provenance == "UNKNOWN":
        if value is not None:
            raise QuantizationError("QRT-SCHEMA", f"{field_name}.value")
        return None, provenance
    
    if not isinstance(value, int) or value < 0:
        raise QuantizationError("QRT-SCHEMA", f"{field_name}.value")
    
    return value, provenance


def _compute_score(
    input_tokens: int | None,
    files_touched: int | None,
    reasoning_depth: str,
    validation_need: str,
    architecture_impact: str,
    risks: frozenset[str],
) -> tuple[int, dict[str, int]]:
    """Compute deterministic quantization score and breakdown."""
    
    if input_tokens is None:
        token_score = 3
    elif input_tokens <= 2000:
        token_score = 0
    elif input_tokens <= 8000:
        token_score = 1
    elif input_tokens <= 20000:
        token_score = 2
    else:
        token_score = 3
    
    if files_touched is None:
        file_score = 3
    elif files_touched == 0:
        file_score = 0
    elif files_touched == 1:
        file_score = 1
    elif files_touched <= 3:
        file_score = 2
    else:
        file_score = 3
    
    reasoning_map = {"MECHANICAL": 0, "RECONCILE": 1, "JUDGMENT": 3}
    reasoning_score = reasoning_map[reasoning_depth]
    
    validation_map = {"NONE": 0, "BOUNDED": 1, "INTEGRATION": 2, "RELEASE": 3}
    validation_score = validation_map[validation_need]
    
    arch_score = 0
    if architecture_impact == "LOCAL":
        arch_score = 1
    elif architecture_impact == "SHARED":
        arch_score = 3
    
    scored_risk_count = len(risks & _SCORED_RISKS)
    risk_score = scored_risk_count * 2
    
    total = (
        token_score + file_score + reasoning_score +
        validation_score + arch_score + risk_score
    )
    
    breakdown = {
        "input_tokens": token_score,
        "files_touched": file_score,
        "reasoning_depth": reasoning_score,
        "validation_need": validation_score,
        "architecture_impact": arch_score,
        "risks": risk_score,
    }
    
    return total, breakdown


def _select_quantized_class_and_tier(
    score: int,
    no_model_eligible: bool,
    minimum_model_tier: str,
    reasoning_depth: str,
    validation_need: str,
    risks: frozenset[str],
    has_human_gate: bool,
) -> tuple[str, str, str, bool]:
    """Apply precedence rules to determine Q-class and abstract tier."""
    
    has_high_risk = bool(risks & _HIGH_RISK_SET)
    
    # Precedence 1: High risk or existing gate → Q4
    if has_human_gate or has_high_risk:
        return "Q4", "3", "P1_HIGH_RISK_OR_GATE", True
    
    # Precedence 2: Q0 special case
    if (no_model_eligible and
        minimum_model_tier == "NONE" and
        reasoning_depth == "MECHANICAL" and
        validation_need == "NONE" and
        len(risks) == 0):
        return "Q0", "NONE", "P2_DETERMINISTIC_TEMPLATE", False
    
    # Precedence 3: Score-based mapping
    if score <= 2:
        quantized_class = "Q1"
        model_tier = "0"
        precedence = "P3_SCORE_0_2"
    elif score <= 7:
        quantized_class = "Q2"
        # Q2 uses Lead floor to pick 1-build vs 1-validate
        if minimum_model_tier in {"1-validate", "2", "3"}:
            model_tier = "1-validate"
        else:
            model_tier = "1-build"
        precedence = "P3_SCORE_3_7"
    else:
        quantized_class = "Q3"
        model_tier = "2"
        precedence = "P3_SCORE_8_PLUS"
    
    # Compare quantized tier with Lead floor; higher rank wins
    lead_rank = _TIER_RANK[minimum_model_tier]
    quant_rank = _TIER_RANK[model_tier]
    
    if lead_rank > quant_rank:
        model_tier = minimum_model_tier
    elif lead_rank == quant_rank and minimum_model_tier != model_tier:
        # Equal rank: preserve Lead value (e.g., 1-build vs 1-validate)
        model_tier = minimum_model_tier
    
    return quantized_class, model_tier, precedence, False


def _determine_confidence(
    input_prov: str,
    files_prov: str,
) -> str:
    """Determine confidence level from estimate provenance."""
    if input_prov == "MEASURED" and files_prov == "MEASURED":
        return "HIGH"
    elif (
        "UNKNOWN" not in {input_prov, files_prov}
        and (input_prov, files_prov).count("ESTIMATED") == 1
    ):
        return "MEDIUM"
    else:
        return "LOW"


def quantize_task(request: Mapping[str, object]) -> dict[str, object]:
    """Quantize a task into deterministic Q-class, context level, and abstract tier.
    
    Returns complete output schema with status ROUTED or BLOCKED.
    Raises QuantizationError for schema violations or contract conflicts.
    """
    
    if set(request) != _REQUEST_FIELDS:
        # Keep rejected key names and values out of the exception surface.
        raise QuantizationError("QRT-SCHEMA", "request")

    # Required field extraction with type validation
    try:
        schema_version = request["schema_version"]
        task_id = request["task_id"]
        run_id = request["run_id"]
        nature = request["nature"]
        role_id = request["role_id"]
        minimum_model_tier = request["minimum_model_tier"]
        no_model_eligible = request["no_model_eligible"]
        execution_scope = request["execution_scope"]
        reasoning_depth = request["reasoning_depth"]
        enumeration_required = request["enumeration_required"]
        synthesis_input_ref = request["synthesis_input_ref"]
        estimated_input_tokens = request["estimated_input_tokens"]
        estimated_files_touched = request["estimated_files_touched"]
        validation_need = request["validation_need"]
        architecture_impact = request["architecture_impact"]
        risks = request["risks"]
        evidence_refs = request["evidence_refs"]
    except KeyError as exc:
        raise QuantizationError("QRT-SCHEMA", str(exc.args[0]))
    
    # Schema version check
    if schema_version != "quant-route/v1":
        raise QuantizationError("QRT-SCHEMA", "schema_version")
    
    # Type and value validations
    if not isinstance(task_id, str):
        raise QuantizationError("QRT-SCHEMA", "task_id")
    if not isinstance(run_id, str):
        raise QuantizationError("QRT-SCHEMA", "run_id")
    
    if not isinstance(nature, str) or not nature:
        raise QuantizationError("QRT-SCHEMA", "nature")
    
    if not isinstance(role_id, str) or not role_id:
        raise QuantizationError("QRT-SCHEMA", "role_id")
    
    if not isinstance(minimum_model_tier, str) or minimum_model_tier not in _VALID_TIERS:
        raise QuantizationError("QRT-SCHEMA", "minimum_model_tier")
    
    if not isinstance(no_model_eligible, bool):
        raise QuantizationError("QRT-SCHEMA", "no_model_eligible")
    
    if not isinstance(execution_scope, str) or not execution_scope:
        raise QuantizationError("QRT-SCHEMA", "execution_scope")
    
    if not isinstance(reasoning_depth, str) or reasoning_depth not in _VALID_REASONING:
        raise QuantizationError("QRT-SCHEMA", "reasoning_depth")
    
    if not isinstance(enumeration_required, bool):
        raise QuantizationError("QRT-SCHEMA", "enumeration_required")
    
    if not isinstance(synthesis_input_ref, (str, type(None))):
        raise QuantizationError("QRT-SCHEMA", "synthesis_input_ref")
    
    # Validate estimates
    input_tokens, input_prov = _validate_estimate(
        "estimated_input_tokens", estimated_input_tokens
    )
    files_touched, files_prov = _validate_estimate(
        "estimated_files_touched", estimated_files_touched
    )
    
    if not isinstance(validation_need, str) or validation_need not in _VALID_VALIDATION:
        raise QuantizationError("QRT-SCHEMA", "validation_need")
    
    if not isinstance(architecture_impact, str) or architecture_impact not in _VALID_ARCH_IMPACT:
        raise QuantizationError("QRT-SCHEMA", "architecture_impact")
    
    # Validate risks
    if not isinstance(risks, list):
        raise QuantizationError("QRT-SCHEMA", "risks")
    
    for risk in risks:
        if not isinstance(risk, str) or risk not in _ALL_RISKS:
            raise QuantizationError("QRT-SCHEMA", "risks")
    risk_set = frozenset(risks)
    
    if not isinstance(evidence_refs, list):
        raise QuantizationError("QRT-SCHEMA", "evidence_refs")
    
    for ref in evidence_refs:
        if not isinstance(ref, str):
            raise QuantizationError("QRT-SCHEMA", "evidence_refs")
    
    # Compute score
    score, breakdown = _compute_score(
        input_tokens,
        files_touched,
        reasoning_depth,
        validation_need,
        architecture_impact,
        risk_set,
    )
    
    # Select Q-class and tier
    quantized_class, model_tier, precedence, human_gate = _select_quantized_class_and_tier(
        score,
        no_model_eligible,
        minimum_model_tier,
        reasoning_depth,
        validation_need,
        risk_set,
        False,  # has_human_gate from external trigger (not in this input)
    )
    
    # Determine confidence
    confidence = _determine_confidence(input_prov, files_prov)

    context = budget_context(quantized_class, validation_need)
    
    # Check blocking conditions
    status = "ROUTED"
    failure_code = None
    
    if confidence == "LOW":
        status = "BLOCKED"
        failure_code = "QRT-LOW-CONFIDENCE"
    elif human_gate:
        status = "BLOCKED"
        failure_code = "QRT-HUMAN-GATE"
    
    canonical_input = json.dumps(
        request,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    input_digest = hashlib.sha256(canonical_input).hexdigest()
    
    # Construct output
    return {
        "schema_version": "quant-route/v1",
        "input_digest": input_digest,
        "task_id": task_id,
        "run_id": run_id,
        "quantized_class": quantized_class,
        "context_level": context["context_level"],
        "context_budget_tokens": context["context_budget_tokens"],
        "model_tier": model_tier,
        "human_gate_required": human_gate,
        "score": score,
        "score_breakdown": breakdown,
        "precedence_rule": precedence,
        "confidence": confidence,
        "escalation_rules": list(_ESCALATION_RULES),
        "evidence_refs": list(evidence_refs),
        "status": status,
        "failure_code": failure_code,
    }
