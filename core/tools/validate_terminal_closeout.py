#!/usr/bin/env python3
"""Fail closed when a terminal Coding Team handoff lacks a useful closeout.

The tool validates text only. It does not dispatch work, approve a gate, or
decide whether the proposed next task is product-correct. Lead runs it before
treating a handoff as closed.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


FIELD_RE = re.compile(r"^[ \t]*-[ \t]*\*\*(?P<name>[^*]+):\*\*[ \t]*(?P<value>.*)$", re.MULTILINE)
NONE_COMPLETE = {"none — objective complete", "none - objective complete"}
PLACEHOLDER_VALUES = frozenset({"", "todo", "tbd", "n/a", "na", "none", "next task", "next step", "task", "action"})
QUEUE_STATES = frozenset({"READY", "QUEUED", "DEFERRED", "BLOCKED", "HUMAN_APPROVAL_REQUIRED"})
MAX_NEXT_WORDS = 60


def _fields(text: str) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    for match in FIELD_RE.finditer(text):
        fields.setdefault(match.group("name").strip().casefold(), []).append(
            match.group("value").strip()
        )
    return fields


def _single_field(fields: dict[str, list[str]], name: str, errors: list[str]) -> str:
    values = fields.get(name, [])
    label = name.capitalize()
    if not values:
        errors.append(f"{label} is missing")
        return ""
    if len(values) != 1:
        errors.append(f"{label} must appear exactly once")
        return ""
    return values[0]


def _meaningful(value: str) -> bool:
    return bool(value) and any(character.isalnum() for character in value)


def _is_placeholder(value: str) -> bool:
    compact = value.strip().casefold().strip(" \t.!?;:,<>[]{}()")
    return compact in PLACEHOLDER_VALUES


def validate(text: str) -> list[str]:
    """Return all closeout defects; an empty list means the text is valid."""

    fields = _fields(text)
    errors: list[str] = []
    next_to_do = _single_field(fields, "recommended next to-do", errors)
    pending = _single_field(fields, "pending tasks", errors)

    next_is_complete = next_to_do.casefold() in NONE_COMPLETE
    if not _meaningful(next_to_do) or _is_placeholder(next_to_do):
        errors.append("Recommended next to-do is missing or a placeholder")
    elif next_is_complete:
        pass
    elif ";" in next_to_do:
        errors.append("Recommended next to-do must name exactly one action")
    elif len(next_to_do.split()) > MAX_NEXT_WORDS:
        errors.append(f"Recommended next to-do must be at most {MAX_NEXT_WORDS} words")

    if pending.casefold() == "none":
        pass
    elif not _meaningful(pending) or _is_placeholder(pending):
        errors.append("Pending tasks must be NONE or a compact queue")
    else:
        items = [item.strip() for item in pending.split(";") if item.strip()]
        if not items:
            errors.append("Pending tasks must be NONE or a compact queue")
        elif len(items) > 3:
            errors.append("Pending tasks may contain at most three queued items")
        for item in items:
            parts = [part.strip().rstrip(".").strip("`") for part in re.split(r"\s+[—-]\s+", item)]
            if len(parts) != 4 or any(not _meaningful(part) for part in parts):
                errors.append("Each pending task needs task ID — owner — prerequisite — state")
                continue
            if parts[3].upper() not in QUEUE_STATES:
                errors.append("Each pending task must use a supported state")

    if next_is_complete and pending.casefold() != "none":
        errors.append("Objective-complete closeout requires Pending tasks: NONE")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--handoff", type=Path, help="Markdown handoff to validate")
    group.add_argument("--stdin", action="store_true", help="Read handoff text from stdin")
    args = parser.parse_args()

    if args.stdin:
        text = sys.stdin.read()
    else:
        try:
            text = args.handoff.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"BLOCKED: cannot read handoff: {exc}", file=sys.stderr)
            return 2

    errors = validate(text)
    if errors:
        for error in errors:
            print(f"BLOCKED: {error}", file=sys.stderr)
        return 1
    print("READY: terminal closeout is present and well formed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
