"""Explicit command-line activation for the retained compact-terminal tool."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from adapters.codex import compact_terminal  # noqa: E402


CLI_ARGUMENT = "CTERM-CLI-ARGV"
UNSUPPORTED_PLATFORM = "CTERM-UNSUPPORTED-PLATFORM"


def _compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _error(code: str) -> int:
    sys.stderr.write(_compact_json({"error": code}) + "\n")
    return 2


def _terminal(args: list[str]) -> int:
    if os.name != "posix" or not hasattr(os, "killpg"):
        return _error(UNSUPPORTED_PLATFORM)
    if len(args) < 4 or args[0] != "--timeout-s" or args[2] != "--":
        return _error(CLI_ARGUMENT)
    try:
        timeout_s = float(args[1])
    except (TypeError, ValueError):
        return _error(CLI_ARGUMENT)
    try:
        result = compact_terminal.execute_terminal_command(args[3:], timeout_s=timeout_s)
    except compact_terminal.CompactTerminalError as exc:
        return _error(exc.code)
    except Exception:
        return _error("CTERM-INTERNAL")
    if result["exit_code"] is None and compact_terminal._PROCESS_GROUP_CLEANUP_CAPABILITY is not True:
        return _error(UNSUPPORTED_PLATFORM)
    sys.stdout.write(_compact_json(result) + "\n")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args.pop(0) != "terminal":
        return _error("TOKEN-TOOLS-DISPOSED")
    return _terminal(args)


if __name__ == "__main__":
    raise SystemExit(main())
