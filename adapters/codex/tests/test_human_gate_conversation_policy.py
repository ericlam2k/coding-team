#!/usr/bin/env python3
"""Focused checks for scoped human gates."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CORE = " ".join((ROOT / "core/human-gates.md").read_text(encoding="utf-8").split())
ADAPTER = " ".join((ROOT / "adapters/codex/SKILL.md").read_text(encoding="utf-8").split())


def test_gates_cover_external_and_irreversible_actions() -> None:
    for phrase in ("destructive operations", "production deployment", "secrets", "material scope expansion"):
        assert phrase in CORE


def test_questions_remain_available_without_mutating_a_pending_gate() -> None:
    assert "Questions and explanations remain available" in CORE
    assert "Silence is never approval" in CORE
    assert "human gate" in CORE


if __name__ == "__main__":
    test_gates_cover_external_and_irreversible_actions()
    test_questions_remain_available_without_mutating_a_pending_gate()
    print("PASS: human gate consistency")
