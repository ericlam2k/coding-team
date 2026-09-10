#!/usr/bin/env python3
"""Focused consistency checks for the canonical Lead workflow."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORCHESTRATION = (ROOT / "core/orchestration.md").read_text(encoding="utf-8")
LEAD = (ROOT / "core/roles/lead.md").read_text(encoding="utf-8")
TASK = (ROOT / "core/templates/task-brief.md").read_text(encoding="utf-8")
ROLES = {
    path.stem for path in (ROOT / "core/roles").glob("*.md")
}


def test_canonical_flow_and_single_record() -> None:
    assert "Input → Process → Handoff → related role" in ORCHESTRATION
    assert "The handoff is the task record" in ORCHESTRATION
    concurrency = (ROOT / "core/concurrency.md").read_text(encoding="utf-8")
    assert "There is no supervisor lane" in concurrency
    assert "Code Reviewer, Test Engineer, and Gatekeeper are independent" in ORCHESTRATION


def test_role_index_matches_role_cards() -> None:
    table = set(re.findall(r"^\| [^|]+ \| `([^`]+)` \|", ORCHESTRATION, re.MULTILINE))
    assert table == ROLES - {"lead", "domain-advisor"}
    assert "monitor-agent" not in table


def test_task_brief_has_only_optional_risk_support() -> None:
    assert "Optional risk support" in TASK
    assert "Watchdog for a background or long-running command" in TASK
    assert "Unneeded controls remain blank" in TASK
    assert "prepare-dispatch.py" not in TASK
    assert "terminal_closeout" not in (LEAD + TASK)


if __name__ == "__main__":
    for test in (test_canonical_flow_and_single_record, test_role_index_matches_role_cards,
                 test_task_brief_has_only_optional_risk_support):
        test()
    print("PASS: Lead canonical workflow consistency")
