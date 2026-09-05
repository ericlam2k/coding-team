#!/usr/bin/env python3
"""Prepare a validated native Codex dispatch payload.

The formatter validates the caller's direct-host attestation and returns a
READY wrapper around the exact native spawn shape. It does not invoke a host,
admit work, or prove that a host call was made.
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

ROUTE_PROFILES = {
    "frontend-builder": ("OR-Laguna", "medium"),
    "backend-engineer": ("gpt-5.6-luna", "medium"),
    "system-architect": ("claude-fable-5.1", "high"),
    "code-reviewer": ("gpt-5.6-luna", "high"),
    "test-engineer:design": ("claude-sonnet-5", "high"),
    "test-engineer:implement": ("gpt-5.6-luna", "medium"),
    "gatekeeper:frontend": ("gpt-6-astra", "high"),
    "gatekeeper:backend": ("claude-fable-5.1", "high"),
}

V1_HOST_BINDING = "collaboration.spawn_agent"
V2_HOST_BINDING = "multi_agent_v1__spawn_agent"
SUPPORTED_HOST_BINDINGS = frozenset({V1_HOST_BINDING, V2_HOST_BINDING})
DIRECT_HOST_MODE = "direct_tool_call"
DIRECT_HOST_BINDING_GUIDANCE = (
    "run preflight from a parent context that exposes one supported direct spawn binding, "
    "attest its exact tool name, then invoke that selected binding directly; "
    "no indirect fallback or cross-binding translation exists"
)
V1_HOST_INVOCATION = (
    "Invoke the direct collaboration.spawn_agent tool exactly once with READY.spawn; "
    "do not use functions.exec, exec_command, shell, JavaScript, or a nested tool binding."
)
V2_HOST_INVOCATION = (
    "Invoke the direct multi_agent_v1__spawn_agent tool exactly once with READY.spawn; "
    "do not translate fields, retry, or use functions.exec, exec_command, shell, "
    "JavaScript, or a nested tool binding."
)
READY_BOUNDARY = (
    "READY proves packet-valid plus selected direct-binding-attested preflight only; "
    "it does not prove host acceptance, child start, supervision, or completion."
)

# These fields belonged to the removed admission/receipt contract. Silently
# carrying them forward would recreate a second workflow authority.
REMOVED_FIELDS = frozenset({
    "task_id", "allocation", "admission",
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


def _normalise_host_binding(value: Any) -> dict[str, Any]:
    """Require the caller to attest one supported direct host binding exactly."""

    expected_keys = {"tool", "mode", "available_to_caller"}
    if not isinstance(value, Mapping):
        raise PacketValidationError([
            "host_binding: require an exact object with tool, mode, and "
            f"available_to_caller; {DIRECT_HOST_BINDING_GUIDANCE}"
        ])

    actual_keys = set(value)
    if any(not isinstance(key, str) for key in actual_keys):
        raise PacketValidationError([
            "host_binding: keys must be strings and must be exactly tool, mode, "
            f"and available_to_caller; {DIRECT_HOST_BINDING_GUIDANCE}"
        ])
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        extra = sorted(actual_keys - expected_keys)
        details = []
        if missing:
            details.append(f"missing keys: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected keys: {', '.join(extra)}")
        raise PacketValidationError([
            "host_binding: must contain exactly tool, mode, and "
            f"available_to_caller ({'; '.join(details)}); {DIRECT_HOST_BINDING_GUIDANCE}"
        ])

    errors = []
    tool = value["tool"]
    if not isinstance(tool, str) or tool not in SUPPORTED_HOST_BINDINGS:
        errors.append(
            f"host_binding.tool: unsupported binding {tool!r}; expected one of "
            f"{sorted(SUPPORTED_HOST_BINDINGS)!r}; {DIRECT_HOST_BINDING_GUIDANCE}"
        )
    if value["mode"] != DIRECT_HOST_MODE:
        errors.append(
            f"host_binding.mode: expected {DIRECT_HOST_MODE!r}; "
            f"{DIRECT_HOST_BINDING_GUIDANCE}"
        )
    if value["available_to_caller"] is not True or not isinstance(value["available_to_caller"], bool):
        errors.append(
            "host_binding.available_to_caller: must be the boolean true; "
            f"{DIRECT_HOST_BINDING_GUIDANCE}"
        )
    if errors:
        raise PacketValidationError(errors)
    return {
        "tool": value["tool"],
        "mode": DIRECT_HOST_MODE,
        "available_to_caller": True,
    }


def _required_model(packet: Mapping[str, Any]) -> str:
    value = packet.get("model")
    if value in (None, ""):
        raise PacketValidationError(["model: required to populate READY.spawn"])
    model = _text(value, "model")
    if not _MODEL_RE.fullmatch(model):
        raise PacketValidationError(["model: must be a concrete model slug"])
    return model


def _required_effort(packet: Mapping[str, Any]) -> str:
    if "reasoning_effort" in packet and "effort" in packet:
        raise PacketValidationError([
            "reasoning_effort: do not combine with the legacy effort alias"
        ])
    key = "reasoning_effort" if "reasoning_effort" in packet else "effort"
    value = packet.get(key)
    if value in (None, ""):
        raise PacketValidationError([
            "reasoning_effort: required to populate READY.spawn"
        ])
    effort = _text(value, key).lower()
    if effort not in _EFFORTS:
        raise PacketValidationError([f"{key}: unsupported value '{effort}'"])
    return effort


def _optional_model(packet: Mapping[str, Any]) -> str | None:
    value = _optional_text(packet, "model")
    if value is not None and not _MODEL_RE.fullmatch(value):
        raise PacketValidationError(["model: must be a concrete model slug"])
    return value


def _optional_effort(packet: Mapping[str, Any]) -> str | None:
    if "effort" in packet:
        raise PacketValidationError([
            f"effort: unsupported for {V2_HOST_BINDING}; supply reasoning_effort explicitly"
        ])
    value = _optional_text(packet, "reasoning_effort")
    if value is None:
        return None
    value = value.lower()
    if value not in _EFFORTS:
        raise PacketValidationError([f"reasoning_effort: unsupported value '{value}'"])
    return value


def _route_profile(packet: Mapping[str, Any]) -> tuple[str, str] | None:
    role = _optional_text(packet, "role")
    if role is None:
        return None
    role = role.lower()
    if role not in ROUTE_PROFILES and role not in {"test-engineer", "gatekeeper"}:
        return None
    route = _optional_text(packet, "model_route")
    if role == "test-engineer":
        if route not in {"design", "implement"}:
            raise PacketValidationError(["model_route: test-engineer requires design or implement"])
        return ROUTE_PROFILES[f"{role}:{route}"]
    if role == "gatekeeper":
        if route not in {"frontend", "backend"}:
            raise PacketValidationError(["model_route: gatekeeper requires frontend or backend"])
        return ROUTE_PROFILES[f"{role}:{route}"]
    if route is not None:
        raise PacketValidationError([f"model_route: unsupported for {role}"])
    return ROUTE_PROFILES[role]


def _routed_model_and_effort(packet: Mapping[str, Any]) -> tuple[str | None, str | None]:
    profile = _route_profile(packet)
    model = _optional_model(packet)
    effort = _optional_effort(packet)
    if profile is None:
        return model, effort
    expected_model, expected_effort = profile
    if model is not None and model != expected_model:
        raise PacketValidationError([f"model: {model!r} conflicts with selected route {expected_model!r}"])
    if effort is not None and effort != expected_effort:
        raise PacketValidationError([f"reasoning_effort: {effort!r} conflicts with selected route {expected_effort!r}"])
    return expected_model, expected_effort


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
    if "fork_turns" not in packet:
        raise PacketValidationError([
            "fork_turns: required positive base-10 integer string"
        ])
    value = packet["fork_turns"]
    if isinstance(value, int) and value > 0:
        value = str(value)
    if isinstance(value, str) and re.fullmatch(r"[1-9][0-9]*", value):
        return value
    raise PacketValidationError([
        "fork_turns: require a positive base-10 integer string; "
        "omitted, all, zero, negative, and malformed depths are unsupported"
    ])


def format_native_payload(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Return the exact payload for the explicitly selected native host."""

    if not isinstance(packet, Mapping):
        raise PacketValidationError(["packet: top-level JSON value must be an object"])
    removed = sorted(REMOVED_FIELDS.intersection(packet))
    errors = [f"{field}: removed workflow field is unsupported" for field in removed]
    if errors:
        raise PacketValidationError(errors)

    binding = _normalise_host_binding(packet.get("host_binding"))["tool"]
    agent_type = _role_agent_type(packet)
    message_value = packet.get("message", packet.get("objective"))
    if message_value is None:
        raise PacketValidationError(["message: required plaintext task message"])
    message = _text(message_value, "message")
    if binding == V1_HOST_BINDING:
        model = _required_model(packet)
        effort = _required_effort(packet)
        profile = _route_profile(packet)
        if profile is not None and (model, effort) != profile:
            raise PacketValidationError(["model/reasoning_effort: conflicts with selected route"])
        return {
            "task_name": _task_name(packet, agent_type, message),
            "agent_type": agent_type,
            "fork_turns": _fork_turns(packet),
            "message": message,
            "model": model,
            "reasoning_effort": effort,
        }

    cross_binding = [field for field in ("task_name", "fork_turns") if field in packet]
    if cross_binding:
        raise PacketValidationError([
            f"{field}: unsupported for {V2_HOST_BINDING}; do not translate V1 fields"
            for field in cross_binding
        ])
    payload: dict[str, Any] = {
        "agent_type": agent_type,
        "fork_context": False,
        "message": message,
    }
    model, effort = _routed_model_and_effort(packet)
    if model is not None:
        payload["model"] = model
    if effort is not None:
        payload["reasoning_effort"] = effort
    return payload


def prepare_dispatch(packet: Mapping[str, Any], root: str | Path | None = None, *,
                     coding_team_root: str | Path | None = None) -> dict[str, Any]:
    """Return READY preflight evidence and the unchanged native spawn payload."""
    if root is not None and coding_team_root is not None:
        raise PacketValidationError(["provide only one of root or coding_team_root"])
    if not isinstance(packet, Mapping):
        raise PacketValidationError(["packet: top-level JSON value must be an object"])
    binding = _normalise_host_binding(packet.get("host_binding"))["tool"]
    spawn = format_native_payload(packet)
    dispatch_material = json.dumps(
        {"binding": binding, "spawn": spawn},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    dispatch_id = "ctd_" + hashlib.sha256(dispatch_material).hexdigest()[:24]
    instruction = (
        V1_HOST_INVOCATION if binding == V1_HOST_BINDING else V2_HOST_INVOCATION
    )
    return {
        "status": "READY",
        "readiness": READY_BOUNDARY,
        "binding": binding,
        "dispatch_id": dispatch_id,
        "spawn": spawn,
        "invocation": {
            "tool": binding,
            "mode": DIRECT_HOST_MODE,
            "instruction": instruction,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="JSON payload file; stdin is used when omitted")
    parser.add_argument("--coding-team-root", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
        result = prepare_dispatch(json.loads(raw))
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
