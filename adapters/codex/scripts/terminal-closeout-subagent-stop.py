#!/usr/bin/env python3
"""Keep Coding Team subagents from closing without a terminal closeout."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


PROJECT_MARKER = "coding-team:begin"
MAX_AGENTS_BYTES = 128_000


def _emit(payload: dict[str, Any]) -> int:
    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
    return 0


def _scope(cwd: Any) -> str:
    """Return whether cwd belongs to a project that declares Coding Team."""

    if not isinstance(cwd, str) or not cwd.strip():
        return "unknown"
    try:
        path = Path(cwd).expanduser().resolve(strict=False)
    except (OSError, RuntimeError):
        return "unknown"
    # The nearest AGENTS.md defines the current repository boundary.  Do not
    # inherit a parent's marker through an ordinary nested project.
    for directory in (path, *path.parents):
        agents = directory / "AGENTS.md"
        try:
            if not agents.is_file():
                continue
            with agents.open("r", encoding="utf-8") as handle:
                text = handle.read(MAX_AGENTS_BYTES)
        except (OSError, UnicodeError):
            return "unknown"
        return "coding-team" if PROJECT_MARKER in text.casefold() else "ordinary"
    return "ordinary"


def _event_error(reason: str) -> int:
    return _emit(
        {
            "continue": False,
            "stopReason": f"CODING_TEAM_CLOSEOUT:EVENT_INVALID:{reason}",
            "suppressOutput": False,
        }
    )


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _event_error("invalid-json")
    if not isinstance(event, dict):
        return _event_error("object-required")
    if event.get("hook_event_name") != "SubagentStop":
        return _emit({"continue": True, "suppressOutput": True})

    scope = _scope(event.get("cwd"))
    if scope == "ordinary":
        return _emit({"continue": True, "suppressOutput": True})
    if scope == "unknown":
        return _event_error("project-scope-unavailable")

    if "stop_hook_active" in event and not isinstance(event["stop_hook_active"], bool):
        return _event_error("stop-hook-state-invalid")

    message = event.get("last_assistant_message")
    if isinstance(message, str):
        validator_path = Path(__file__).resolve().parents[3] / "core" / "tools" / "validate_terminal_closeout.py"
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location("terminal_closeout", validator_path)
            if spec is None or spec.loader is None:
                errors = ["terminal closeout validator is unavailable"]
            else:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                errors = module.validate(message)
        except Exception as exc:
            errors = [f"terminal closeout validator failed: {exc.__class__.__name__}"]
    else:
        errors = ["last_assistant_message must be a plaintext string"]

    if not errors:
        return _emit({"continue": True, "suppressOutput": True})

    detail = "; ".join(errors[:2])
    if bool(event.get("stop_hook_active", False)):
        return _emit(
            {
                "continue": False,
                "stopReason": "CODING_TEAM_CLOSEOUT:BLOCKED",
                "systemMessage": f"Terminal closeout is still invalid after one correction: {detail}",
                "suppressOutput": False,
            }
        )
    return _emit(
        {
            "decision": "block",
            "reason": (
                "CODING_TEAM_CLOSEOUT: add exactly one Recommended next to-do and "
                f"Pending tasks (NONE or a compact queue). {detail}"
            ),
        }
    )


if __name__ == "__main__":
    raise SystemExit(main())
