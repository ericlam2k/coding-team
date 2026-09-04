#!/usr/bin/env python3
"""Format a small native Codex payload.

The formatter is optional convenience code. It does not admit work, create
task identity, select a workflow, or prove that a host call was made. A
caller may pass the returned object directly to the native host API instead.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping


class PacketValidationError(ValueError):
    """A fail-closed native-payload formatting error."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


CANONICAL_ROLES = frozenset({
    "lead", "product-manager", "system-architect", "advisor", "contradictor",
    "domain-advisor", "investigator", "backend-engineer", "frontend-ux-lead",
    "frontend-builder", "code-reviewer", "test-engineer", "docs-steward", "gatekeeper",
})

HOST_AGENT_TYPES = {
    "lead": "lead", "product-manager": "default", "system-architect": "system_architecture",
    "advisor": "advisor", "contradictor": "contradictor", "domain-advisor": "advisor",
    "investigator": "explorer", "backend-engineer": "worker", "frontend-ux-lead": "default",
    "frontend-builder": "worker", "code-reviewer": "advisor", "test-engineer": "test_engineer",
    "docs-steward": "worker", "gatekeeper": "gatekeeper",
}
VALID_AGENT_TYPES = frozenset(HOST_AGENT_TYPES.values())
MAX_TEXT_LENGTH = 12_000
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/ -]{1,127}$")
_TASK_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_EFFORTS = frozenset({"low", "medium", "high", "xhigh", "max"})

# These fields belonged to the removed admission/receipt contract. Silently
# carrying them forward would recreate a second workflow authority.
REMOVED_FIELDS = frozenset({
    "task_id", "host_binding", "allocation", "admission",
    "dispatch_id", "receipt", "receipt_id", "prior_hard_stop", "candidate_changed_paths",
    "critical", "native_collaboration", "fork_context",
})


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise PacketValidationError([f"{field}: must be a plaintext string"])
    if _CONTROL_RE.search(value):
        raise PacketValidationError([f"{field}: contains control characters"])
    value = " ".join(value.split())
    if not value:
        raise PacketValidationError([f"{field}: must not be empty"])
    if len(value) > MAX_TEXT_LENGTH:
        raise PacketValidationError([f"{field}: exceeds {MAX_TEXT_LENGTH} characters"])
    return value


def _optional_text(packet: Mapping[str, Any], key: str) -> str | None:
    if key not in packet or packet[key] in (None, ""):
        return None
    return _text(packet[key], key)


def _role_agent_type(packet: Mapping[str, Any]) -> str:
    if "agent_type" in packet:
        agent_type = _text(packet["agent_type"], "agent_type")
        if agent_type not in VALID_AGENT_TYPES:
            raise PacketValidationError([f"agent_type: unsupported value '{agent_type}'"])
        return agent_type
    role = _text(packet.get("role", ""), "role").lower()
    if role not in CANONICAL_ROLES:
        raise PacketValidationError([f"role: unknown canonical role '{role}'"])
    return HOST_AGENT_TYPES[role]


def _task_name(packet: Mapping[str, Any], agent_type: str, message: str) -> str:
    supplied = _optional_text(packet, "task_name")
    if supplied is not None:
        if not _TASK_NAME_RE.fullmatch(supplied):
            raise PacketValidationError([
                "task_name: use lowercase letters, digits, or underscores; start with a letter"
            ])
        return supplied
    prefix = agent_type.replace("-", "_")[:48].rstrip("_") or "worker"
    suffix = hashlib.sha256(message.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{suffix}"


def _fork_turns(packet: Mapping[str, Any]) -> str:
    value = packet.get("fork_turns", "1")
    if isinstance(value, int) and value > 0:
        value = str(value)
    if value == "all" or (isinstance(value, str) and value.isdigit() and int(value) > 0):
        return value
    raise PacketValidationError(["fork_turns: must be 'all' or a positive integer"])


def format_native_payload(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Return only fields understood by the native host spawn call."""

    if not isinstance(packet, Mapping):
        raise PacketValidationError(["packet: top-level JSON value must be an object"])
    removed = sorted(REMOVED_FIELDS.intersection(packet))
    errors = [f"{field}: removed workflow field is unsupported" for field in removed]
    if errors:
        raise PacketValidationError(errors)

    agent_type = _role_agent_type(packet)
    message_value = packet.get("message", packet.get("objective"))
    if message_value is None:
        raise PacketValidationError(["message: required plaintext task message"])
    message = _text(message_value, "message")
    payload: dict[str, Any] = {
        "agent_type": agent_type,
        "task_name": _task_name(packet, agent_type, message),
        "fork_turns": _fork_turns(packet),
        "message": message,
    }

    model = _optional_text(packet, "model")
    if model is not None:
        if not _MODEL_RE.fullmatch(model):
            raise PacketValidationError(["model: must be a concrete model slug"])
        payload["model"] = model

    effort_key = "reasoning_effort" if "reasoning_effort" in packet else "effort"
    if effort_key in packet and packet[effort_key] not in (None, ""):
        effort = _text(packet[effort_key], effort_key).lower()
        if effort not in _EFFORTS:
            raise PacketValidationError([f"{effort_key}: unsupported value '{effort}'"])
        payload["reasoning_effort"] = effort
    return payload


def prepare_dispatch(packet: Mapping[str, Any], root: str | Path | None = None, *,
                     coding_team_root: str | Path | None = None) -> dict[str, Any]:
    """Backward-compatible function name for the optional formatter."""
    if root is not None and coding_team_root is not None:
        raise PacketValidationError(["provide only one of root or coding_team_root"])
    return format_native_payload(packet)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="JSON payload file; stdin is used when omitted")
    parser.add_argument("--coding-team-root", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
        result = format_native_payload(json.loads(raw))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BLOCKED", "errors": [f"invalid JSON input: {exc}"]}, indent=2))
        return 2
    except PacketValidationError as exc:
        print(json.dumps({"status": "BLOCKED", "errors": exc.errors}, indent=2))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
