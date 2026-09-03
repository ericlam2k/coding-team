"""Deterministic context-budget selection for quantized task classes."""

from __future__ import annotations

from typing import Final


class ContextBudgetError(ValueError):
    """Raised when a context-budget callable argument is outside the contract."""

    def __init__(self, field: str) -> None:
        self.code = "QRT-SCHEMA"
        self.field = field
        # Do not include the rejected value: exception data must not carry a
        # task payload or other unbounded input.
        super().__init__(self.code)


_BASE_CONTEXT: Final[dict[str, tuple[str, int]]] = {
    "Q0": ("C0", 0),
    "Q1": ("C1", 4_000),
    "Q2": ("C2", 12_000),
    "Q3": ("C4", 48_000),
    "Q4": ("C5", 96_000),
}
_VALIDATION_NEEDS: Final[frozenset[str]] = frozenset(
    {"NONE", "BOUNDED", "INTEGRATION", "RELEASE"}
)


def budget_context(
    quantized_class: str, validation_need: str
) -> dict[str, object]:
    """Return the contract context packet for a quantized task class.

    ``INTEGRATION`` and ``RELEASE`` validation increase only Q2 from C2 to
    C3.  The quantized class is returned unchanged so callers can preserve
    the originating Q/tier while composing the complete routing result.
    """

    if not isinstance(quantized_class, str) or quantized_class not in _BASE_CONTEXT:
        raise ContextBudgetError("quantized_class")
    if not isinstance(validation_need, str) or validation_need not in _VALIDATION_NEEDS:
        raise ContextBudgetError("validation_need")

    context_level, context_budget_tokens = _BASE_CONTEXT[quantized_class]
    if quantized_class == "Q2" and validation_need in {"INTEGRATION", "RELEASE"}:
        context_level, context_budget_tokens = "C3", 24_000

    return {
        "quantized_class": quantized_class,
        "context_level": context_level,
        "context_budget_tokens": context_budget_tokens,
        "status": "ROUTED",
    }
