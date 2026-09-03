#!/usr/bin/env python3
"""Emit a bounded Coding Team re-anchor after Codex compaction."""

from __future__ import annotations

import json
import sys
from typing import Any


MAX_CONTEXT_BYTES = 5_000

REANCHOR = (
    "Framework re-anchor after host-native compaction. Before any material "
    "action, read the nearest applicable AGENTS.md, reload the global Coding "
    "Team skill and current policy, reload the active role card, and read the "
    "active task handoff. Preserve objective, scope, acceptance, verified "
    "facts, evidence refs, unknowns, last decision, residual limits, and one "
    "next action. A compact summary is continuity context only; it is not "
    "implementation, validation, approval, or release evidence. If the "
    "handoff or policy cannot be reloaded, stop and report BLOCKED."
)


def _output(value: dict[str, Any]) -> int:
    sys.stdout.write(json.dumps(value, separators=(",", ":")) + "\n")
    return 0


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _output({"continue": False, "stopReason": "CODING_TEAM_RELOAD:EVENT_INVALID", "suppressOutput": False})

    if not isinstance(event, dict):
        return _output({"continue": False, "stopReason": "CODING_TEAM_RELOAD:EVENT_INVALID", "suppressOutput": False})

    if event.get("hook_event_name") != "SessionStart" or event.get("source") != "compact":
        return _output({"continue": True, "suppressOutput": True})

    if len(REANCHOR.encode("utf-8")) > MAX_CONTEXT_BYTES:
        return _output({"continue": False, "stopReason": "CODING_TEAM_RELOAD:CONTEXT_TOO_LARGE", "suppressOutput": False})

    return _output(
        {
            "continue": True,
            "suppressOutput": True,
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": REANCHOR,
            },
        }
    )


if __name__ == "__main__":
    raise SystemExit(main())
