"""Explicit command-line activation for bounded adapter tools."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from adapters.codex import compact_terminal  # noqa: E402
from core.tools.ast_file_skeleton import FileSkeletonError, get_file_skeleton  # noqa: E402
from core.routing.quantizer import QuantizationError, quantize_task  # noqa: E402
from adapters.codex.message_guard import (  # noqa: E402
    DispatchGuardError,
    build_guarded_messages,
)
from adapters.codex.integration import IntegrationError, integrate_token_tools  # noqa: E402

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
    command_argv = args[3:]
    try:
        result = compact_terminal.execute_terminal_command(
            command_argv, timeout_s=timeout_s
        )
    except compact_terminal.CompactTerminalError as exc:
        return _error(exc.code)
    except Exception:
        return _error("CTERM-INTERNAL")
    if (
        result["exit_code"] is None
        and compact_terminal._PROCESS_GROUP_CLEANUP_CAPABILITY is not True
    ):
        return _error(UNSUPPORTED_PLATFORM)
    sys.stdout.write(_compact_json(result) + "\n")
    return 0


def _skeleton(args: list[str]) -> int:
    # No supported platform currently has a verified hard memory-containment
    # implementation. Fail before inspecting arguments or touching a path.
    return _error("AST-MEMORY-UNSUPPORTED")


def _quantize(args: list[str]) -> int:
    if len(args) != 2 or args[0] != "--request-file":
        return _error("QRT-CLI-ARGV")
    try:
        if args[1] == "-":
            request = json.load(sys.stdin)
        else:
            with open(args[1], encoding="utf-8") as handle:
                request = json.load(handle)
    except (OSError, UnicodeError):
        return _error("QRT-CLI-IO")
    except (json.JSONDecodeError, ValueError):
        return _error("QRT-CLI-JSON")
    if not isinstance(request, dict):
        return _error("QRT-CLI-JSON")
    try:
        result = quantize_task(request)
    except QuantizationError as exc:
        return _error(exc.code)
    except Exception:
        return _error("QRT-CLI-INTERNAL")
    sys.stdout.write(_compact_json(result) + "\n")
    return 0


def _guard(args: list[str]) -> int:
    if "--authoritative-token-count" not in args:
        return _error("DMG-COUNTER-MISSING")
    if (
        len(args) != 4
        or args[0] != "--request-file"
        or args[2] != "--authoritative-token-count"
    ):
        return _error("DMG-SCHEMA")
    if re.fullmatch(r"[0-9]+", args[3]) is None:
        return _error("DMG-COUNTER-INVALID")
    token_count = int(args[3])
    try:
        if args[1] == "-":
            request = json.load(sys.stdin)
        else:
            with open(args[1], encoding="utf-8") as handle:
                request = json.load(handle)
    except (OSError, UnicodeError):
        return _error("DMG-SCHEMA")
    except (json.JSONDecodeError, ValueError):
        return _error("DMG-SCHEMA")
    if not isinstance(request, dict):
        return _error("DMG-SCHEMA")
    allowed_keys = {
        "static_system_prompt",
        "codebase_structure",
        "chat_history",
        "active_request",
        "prefix_template_version",
        "platform_context_window",
        "reserve_tokens",
        "max_tokens",
    }
    required_keys = {
        "static_system_prompt",
        "codebase_structure",
        "chat_history",
        "active_request",
    }
    if not required_keys.issubset(request) or not set(request).issubset(allowed_keys):
        return _error("DMG-SCHEMA")

    counter_calls = 0

    def caller_attested_counter(_messages: object) -> int:
        nonlocal counter_calls
        counter_calls += 1
        if counter_calls != 1:
            raise RuntimeError
        return token_count

    optional: dict[str, object] = {}
    if "prefix_template_version" in request:
        optional["prefix_template_version"] = request["prefix_template_version"]
    for key in (
        "platform_context_window", "reserve_tokens", "max_tokens"
    ):
        if key in request:
            optional[key] = request[key]
    try:
        result = build_guarded_messages(
            request["static_system_prompt"],
            request["codebase_structure"],
            request["chat_history"],
            request["active_request"],
            caller_attested_counter,
            **optional,
        )
    except DispatchGuardError as exc:
        return _error(exc.code)
    except Exception:
        return _error("DMG-SCHEMA")
    sys.stdout.write(_compact_json(result) + "\n")
    return 0


def _integrate(args: list[str]) -> int:
    """Run quantizer + guard as one checkpointed local candidate update."""
    if "--authoritative-token-count" not in args:
        return _error("DMG-COUNTER-MISSING")
    if len(args) not in {4, 6} or args[0] != "--request-file" or args[2] != "--authoritative-token-count":
        return _error("CTI-CLI-ARGV")
    if re.fullmatch(r"[0-9]+", args[3]) is None:
        return _error("CTI-COUNTER-INVALID")
    state_path = ".coding-team/checkpoints/token-tools/runtime-state.json"
    if len(args) == 6:
        if args[4] != "--state-file" or not args[5]:
            return _error("CTI-CLI-ARGV")
        state_path = args[5]
    try:
        if args[1] == "-":
            request = json.load(sys.stdin)
        else:
            with open(args[1], encoding="utf-8") as handle:
                request = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return _error("CTI-SCHEMA")
    try:
        result = integrate_token_tools(
            request,
            authoritative_token_count=int(args[3]),
            state_path=state_path,
        )
    except IntegrationError as exc:
        return _error(exc.code)
    sys.stdout.write(_compact_json(result) + "\n")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        return _error("AST-ARGUMENT")
    action = args.pop(0)
    if action == "terminal":
        return _terminal(args)
    if action == "skeleton":
        return _skeleton(args)
    if action == "quantize":
        return _quantize(args)
    if action == "guard":
        return _guard(args)
    if action == "integrate":
        return _integrate(args)
    return _error("AST-ARGUMENT")


if __name__ == "__main__":
    raise SystemExit(main())
