#!/usr/bin/env python3
"""Focused checks for the host-neutral Lead request-shaping rule."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ORCHESTRATION = (ROOT / "core/orchestration.md").read_text(encoding="utf-8")
LEAD = (ROOT / "core/roles/lead.md").read_text(encoding="utf-8")
TASK = (ROOT / "core/templates/task-brief.md").read_text(encoding="utf-8")

DISPOSITIONS = ("SINGLE", "SPLIT", "CLARIFY", "MEASURE", "BLOCK")
CANONICAL_ROLES = {
    "lead",
    "product-manager",
    "system-architect",
    "advisor",
    "contradictor",
    "domain-advisor",
    "investigator",
    "monitor-agent",
    "backend-engineer",
    "frontend-ux-lead",
    "frontend-builder",
    "code-reviewer",
    "test-engineer",
    "docs-steward",
    "gatekeeper",
}


def _fail(message: str) -> None:
    raise AssertionError(message)


def _section(text: str, heading: str, next_heading: str) -> str:
    start = text.find(heading)
    if start < 0:
        _fail(f"missing section: {heading}")
    end = text.find(next_heading, start + len(heading))
    if end < 0:
        _fail(f"missing section boundary: {next_heading}")
    return text[start:end]


def _assert_contains(text: str, *needles: str) -> None:
    compact = " ".join(text.split())
    for needle in needles:
        if " ".join(needle.split()) not in compact:
            _fail(f"missing required text: {needle}")


def _assert_no_forbidden_additions(text: str) -> None:
    forbidden = (
        "questionnaire",
        "issue automation",
        "story points",
        "universal qa target",
        "new role",
        "new stage",
        "80%",
        "90%",
        "100%",
    )
    lowered = text.casefold()
    for term in forbidden:
        if term in lowered:
            _fail(f"forbidden addition in shaping rule: {term}")


def test_rule_defines_one_slice_and_all_dispositions() -> None:
    section = _section(
        ORCHESTRATION,
        "### Lead request shaping — one feasible slice",
        "### Lead cost discipline",
    )
    _assert_contains(
        section,
        "one bounded shaping decision",
        "Read current briefs",
        "one selected slice",
        "queue the remainder",
        "dependency-safe slice",
        "Ask a human only when",
        "Ask at most one plain-language question",
        "before `prepare-dispatch.py`",
        "prepare-dispatch.py` validates packet identity and shape",
        "Supervision starts only after Lead admission",
    )
    for disposition in DISPOSITIONS:
        if f"**`{disposition}`**" not in section:
            _fail(f"missing disposition: {disposition}")
    _assert_no_forbidden_additions(section)


def test_existing_roles_and_stages_are_not_extended() -> None:
    role_ids = set(re.findall(r"^\| `([^`]+)` \|", ORCHESTRATION, re.MULTILINE))
    if role_ids != CANONICAL_ROLES:
        _fail(f"canonical role set changed: {sorted(role_ids ^ CANONICAL_ROLES)}")

    stage_line = next(
        (line for line in TASK.splitlines() if line.startswith("- **Stage:**")),
        "",
    )
    expected = "- **Stage:** pre-build | build | code-review | targeted-TE | gatekeeper | docs"
    if stage_line != expected:
        _fail(f"stage vocabulary changed: {stage_line!r}")

    _assert_no_forbidden_additions(LEAD + "\n" + TASK)


def test_note_is_conditional_and_admission_remains_separate() -> None:
    section = _section(
        TASK,
        "## Lead request-shaping note (use only when needed)",
        "## Skills (named or none)",
    )
    _assert_contains(
        section,
        "when the request is broad, ambiguous, or needs",
        "omit it for an already spec-ready Task",
        "does not change the existing Sprint → Batch → Task flow",
        "exactly one dependency-safe slice",
        "Queued remainder",
        "Human question",
    )
    selected_slice = re.search(
        r"- \*\*Selected slice:\*\* (?P<value>.+?)(?=\n- \*\*Queued remainder)",
        section,
        re.DOTALL,
    )
    if selected_slice is None:
        _fail("missing Selected slice invariant")
    selected_value = " ".join(selected_slice.group("value").split())
    expected_slice = (
        "`SINGLE` / `SPLIT`: exactly one dependency-safe slice for this brief; "
        "`CLARIFY` / `MEASURE` / `BLOCK`: `NONE`"
    )
    if selected_value != expected_slice:
        _fail(f"Selected slice invariant changed: {selected_value!r}")
    if "ADMIT" not in ORCHESTRATION or "admission" not in ORCHESTRATION:
        _fail("existing admission route is not visible")
    _assert_no_forbidden_additions(section)


if __name__ == "__main__":
    tests = (
        test_rule_defines_one_slice_and_all_dispositions,
        test_existing_roles_and_stages_are_not_extended,
        test_note_is_conditional_and_admission_remains_separate,
    )
    for test in tests:
        test()
    print(f"PASS: {len(tests)} Lead request-shaping consistency checks")
