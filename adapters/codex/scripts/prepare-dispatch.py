#!/usr/bin/env python3
"""Build and validate a plaintext Coding Team Codex dispatch packet.

This is an adapter-local preflight.  It validates the information that the
Codex host is about to receive, but it does not invoke a model or enforce
anything outside this adapter entry point.

Input is a JSON object on stdin (or ``--input``).  A successful invocation
prints a JSON object with a ``spawn`` object whose fields can be passed to the
host spawn call.  Invalid input prints a ``BLOCKED`` result and exits non-zero.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any, Mapping


MAX_MESSAGE_WORDS = 250
MAX_TEXT_LENGTH = 12_000

# Keep this set in lock-step with core/orchestration.md and core/roles/.  A
# role card is resolved from this allow-list; accepting a user-supplied role
# path would reintroduce the context-framing problem at the trust boundary.
CANONICAL_ROLES = frozenset(
    {
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
)

REQUIRED_FIELDS = (
    "role",
    "task_id",
    "objective",
    "acceptance",
    "paths",
    "validation",
    "stop",
    "model",
    "effort",
    "fork_turns",
    "host_binding",
    "allocation",
)
ALLOWED_FIELDS = frozenset((*REQUIRED_FIELDS, "critical", "native_collaboration",
                            "cancellable_pre_start_handle"))
EFFORTS = frozenset({"low", "medium", "high", "xhigh", "max"})
ADMISSION_STATUSES = frozenset({"MEASURED", "ESTIMATED", "UNKNOWN"})
ALLOCATION_MAX_INPUT_REFS = 32
_VALIDATION_PATH_COUNT_RE = re.compile(r"\b([0-9]+)\s+(?:changed\s+)?paths?\b", re.IGNORECASE)

# Canonical Coding Team roles remain authoritative in the plaintext packet.
# This map selects only the closest Codex host execution shape.
HOST_AGENT_TYPES = {
    "lead": "lead",
    "product-manager": "default",
    "system-architect": "system_architecture",
    "advisor": "advisor",
    "contradictor": "contradictor",
    "domain-advisor": "advisor",
    "investigator": "explorer",
    # The supervisor relay is a bounded observer, not an implementation lane.
    "monitor-agent": "explorer",
    "backend-engineer": "worker",
    "frontend-ux-lead": "default",
    "frontend-builder": "worker",
    # Reviewer is read-only and non-final; canonical authority remains in the
    # role card rather than the closest host execution shape.
    "code-reviewer": "advisor",
    "test-engineer": "test_engineer",
    "docs-steward": "worker",
    "gatekeeper": "gatekeeper",
}

_TASK_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]{2,127}$")
_TASK_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
# Host model identifiers may contain spaces, for example `ZM Glm5.3F`.
_MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/ -]{1,127}$")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_OPAQUE_PREFIX_RE = re.compile(
    r"^(?:enc(?:rypted)?|cipher(?:text)?|opaque|sealed|redacted|base64|jwe|kms)"
    r"\s*[:(\[]",
    re.IGNORECASE,
)
_ENCODED_RE = re.compile(r"^(?:[A-Fa-f0-9]{32,}|[A-Za-z0-9+/]{32,}={0,2})$")
_WORD_RE = re.compile(r"\S+")

DIRECT_HOST_BINDING = "collaboration.spawn_agent"
DIRECT_HOST_MODE = "direct_tool_call"
DIRECT_HOST_BINDING_GUIDANCE = (
    "run preflight from a parent context that exposes direct collaboration.spawn_agent, "
    "then invoke it directly; no indirect fallback exists"
)
DIRECT_HOST_INVOCATION = (
    "Invoke the direct collaboration.spawn_agent tool exactly once with READY.spawn; "
    "do not use functions.exec, exec_command, shell, JavaScript, or a nested tool binding."
)
READY_BOUNDARY = (
    "READY proves packet-valid plus direct-binding-attested preflight only; it does not "
    "prove host acceptance, child start, supervision, or completion."
)
MINIMAL_SPECIALIST_FORK_TURNS = "1"
SPECIALIST_EXECUTION_BOUNDARY = (
    "Specialist boundary: you are the sole worker for this Task. Perform the objective "
    "yourself; do not spawn, delegate, orchestrate, or invoke another agent. Do not "
    "call collaboration.spawn_agent, send_message, or followup_task. Write only to "
    "the listed Owned paths; all other paths are read-only. If required work falls "
    "outside them, stop and report BLOCKED. Do not commit, push, deploy, or expand scope."
)


class PacketValidationError(ValueError):
    """A fail-closed packet validation result."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


def _duplicate_key_rejector(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON object members instead of silently overwriting."""

    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PacketValidationError([f"duplicate JSON field: {key}"])
        result[key] = value
    return result


def _load_json(raw: str) -> Any:
    try:
        return json.loads(raw, object_pairs_hook=_duplicate_key_rejector)
    except PacketValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise PacketValidationError([f"invalid JSON: {exc.msg}"]) from exc


def _normalise_text(value: Any, field: str, errors: list[str]) -> str:
    if not isinstance(value, str):
        errors.append(f"{field}: must be a plaintext string")
        return ""
    if _CONTROL_RE.search(value):
        errors.append(f"{field}: contains control characters")
        return ""
    text = " ".join(value.split())
    if not text:
        errors.append(f"{field}: must not be empty")
        return ""
    if len(text) > MAX_TEXT_LENGTH:
        errors.append(f"{field}: exceeds {MAX_TEXT_LENGTH} characters")
    if _is_opaque_only(text):
        errors.append(f"{field}: opaque/encrypted-only values are not accepted")
        return ""
    return text


def _is_opaque_only(value: str) -> bool:
    """Return whether a value carries no usable plaintext framing.

    The check intentionally targets markers and encoded-only values.  It does
    not reject an ordinary sentence that discusses encryption as a subject;
    the packet still has to contain an objective, acceptance, and stop rule.
    """

    text = value.strip()
    lower = text.lower()
    if _OPAQUE_PREFIX_RE.match(text):
        return True
    if lower in {
        "opaque",
        "encrypted",
        "encrypted payload",
        "encrypted brief",
        "encrypted brief blob",
        "ciphertext",
        "ciphertext blob",
        "sealed payload",
        "redacted",
        "redacted payload",
        "blob",
    }:
        return True
    if lower.startswith("-----begin ") and "encrypted" in lower:
        return True
    compact = re.sub(r"\s+", "", text)
    # A long token with no human-readable separators is not a task brief.
    # Do not collapse ordinary prose before this check: a sentence made only
    # of ASCII letters is still valid plaintext.
    if not re.search(r"\s", text) and len(compact) >= 32 and _ENCODED_RE.fullmatch(compact):
        return True
    # Common opaque labels with a short qualifier, e.g. "opaque payload 42".
    marker_words = {"opaque", "encrypted", "ciphertext", "sealed", "redacted"}
    words = set(re.findall(r"[a-z]+", lower))
    if words & marker_words and len(words - marker_words - {"brief", "payload", "blob", "value"}) <= 1:
        return True
    return False


def _normalise_text_list(value: Any, field: str, errors: list[str]) -> list[str]:
    if isinstance(value, str):
        text = _normalise_text(value, field, errors)
        return [text] if text else []
    if not isinstance(value, list) or not value:
        errors.append(f"{field}: must be a non-empty string or list of strings")
        return []
    result: list[str] = []
    for index, item in enumerate(value):
        text = _normalise_text(item, f"{field}[{index}]", errors)
        if text:
            result.append(text)
    return result


def _normalise_paths(value: Any, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or not value:
        errors.append("paths: must be a non-empty list of repository-relative paths")
        return []
    result: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        field = f"paths[{index}]"
        if not isinstance(item, str):
            errors.append(f"{field}: must be a plaintext repository-relative path")
            continue
        if _CONTROL_RE.search(item):
            errors.append(f"{field}: contains control characters")
            continue
        path = item.strip().replace("\\", "/")
        if not path:
            errors.append(f"{field}: must not be empty")
            continue
        if _is_opaque_only(path):
            errors.append(f"{field}: opaque/encrypted-only values are not accepted")
            continue
        parts = path.split("/")
        if path.startswith(("/", "~")) or ".." in parts:
            errors.append(f"{field}: must stay repository-relative and cannot traverse")
            continue
        if any(character in path for character in "*?[]"):
            errors.append(f"{field}: wildcards are not an exclusive owned path")
            continue
        if path in seen:
            errors.append(f"{field}: duplicate owned path")
            continue
        seen.add(path)
        result.append(path)
    return result


def _resolve_role_card(role: str, root: str | os.PathLike[str] | None) -> str:
    if root is None:
        configured_root = os.environ.get("CODING_TEAM_ROOT", "").strip()
        if configured_root:
            root_path = Path(configured_root)
        else:
            # .../coding-team/adapters/codex/scripts/prepare-dispatch.py
            root_path = Path(__file__).resolve().parents[3]
    else:
        root_path = Path(root)
    try:
        root_resolved = root_path.expanduser().resolve(strict=True)
    except OSError as exc:
        raise PacketValidationError([f"coding-team root is not readable: {exc}"]) from exc

    candidate = root_resolved / "core" / "roles" / f"{role}.md"
    try:
        card = candidate.resolve(strict=True)
    except OSError as exc:
        raise PacketValidationError([f"role card is not readable for {role}: {exc}"]) from exc
    try:
        card.relative_to(root_resolved)
    except ValueError as exc:
        raise PacketValidationError(["role card escaped CODING_TEAM_ROOT"]) from exc
    if not card.is_file():
        raise PacketValidationError([f"role card is not a regular file: {card}"])
    return str(card)


def _normalise_fork_turns(value: Any, errors: list[str]) -> str:
    """Normalize the active host's bounded context-depth field."""

    if isinstance(value, bool):
        errors.append("fork_turns: must be a positive base-10 integer, not a boolean")
        return ""
    if isinstance(value, int):
        if value > 0:
            return str(value)
        errors.append("fork_turns: must be a positive base-10 integer")
        return ""
    if not isinstance(value, str):
        errors.append("fork_turns: must be a positive base-10 integer string")
        return ""
    if re.fullmatch(r"[1-9][0-9]*", value):
        return value
    errors.append(
        "fork_turns: require a positive base-10 integer string; "
        "none, all, zero, negative, and malformed depths are unsupported"
    )
    return ""


def _normalise_host_binding(value: Any, errors: list[str]) -> dict[str, Any]:
    """Require the caller to attest the one direct host binding explicitly."""

    expected_keys = {"tool", "mode", "available_to_caller"}
    if not isinstance(value, Mapping):
        errors.append(
            "host_binding: require an exact object with tool, mode, and "
            f"available_to_caller; {DIRECT_HOST_BINDING_GUIDANCE}"
        )
        return {}

    invalid = False
    actual_keys = set(value)
    missing = sorted(expected_keys - actual_keys)
    extra = sorted(actual_keys - expected_keys)
    if missing or extra:
        invalid = True
        detail = []
        if missing:
            detail.append(f"missing keys: {', '.join(missing)}")
        if extra:
            detail.append(f"unexpected keys: {', '.join(extra)}")
        errors.append(
            "host_binding: must contain exactly tool, mode, and "
            f"available_to_caller ({'; '.join(detail)}); "
            f"{DIRECT_HOST_BINDING_GUIDANCE}"
        )

    tool = value.get("tool")
    if tool != DIRECT_HOST_BINDING:
        invalid = True
        errors.append(
            f"host_binding.tool: unsupported binding {tool!r}; expected "
            f"{DIRECT_HOST_BINDING}; {DIRECT_HOST_BINDING_GUIDANCE}"
        )

    mode = value.get("mode")
    if mode != DIRECT_HOST_MODE:
        invalid = True
        errors.append(
            f"host_binding.mode: expected {DIRECT_HOST_MODE!r}; "
            f"{DIRECT_HOST_BINDING_GUIDANCE}"
        )

    available = value.get("available_to_caller")
    if not isinstance(available, bool) or available is not True:
        invalid = True
        errors.append(
            "host_binding.available_to_caller: must be the boolean true; "
            f"{DIRECT_HOST_BINDING_GUIDANCE}"
        )

    if invalid:
        return {}
    return {
        "tool": DIRECT_HOST_BINDING,
        "mode": DIRECT_HOST_MODE,
        "available_to_caller": True,
    }


def _derive_task_name(task_id: str, dispatch_id: str) -> str:
    """Derive the host task name frozen by CT-CODEX-HOST-SCHEMA-V1."""

    task_slug = re.sub(r"[^a-z0-9]+", "_", task_id.lower()).strip("_")
    dispatch_suffix = dispatch_id.removeprefix("ctd_")
    task_name = f"ct_{task_slug}_{dispatch_suffix}"
    if not task_slug or not _TASK_NAME_RE.fullmatch(task_name):
        raise PacketValidationError(
            ["task_id: cannot derive a valid lowercase underscore host task_name"]
        )
    return task_name


def _word_count(text: str) -> int:
    return len(_WORD_RE.findall(text))


def _seconds(value: Any, field: str, errors: list[str]) -> float:
    if (isinstance(value, bool) or not isinstance(value, (int, float)) or
            not math.isfinite(value) or value < 0):
        errors.append(f"{field}: must be a non-negative number of seconds")
        return 0.0
    return float(value)


def _normalise_allocation(value: Any, errors: list[str]) -> dict[str, Any]:
    """Normalize the fail-closed request-to-time admission envelope."""
    if not isinstance(value, Mapping):
        errors.append("allocation: required object")
        return {}
    required = (
        "owner", "concern", "input_refs", "result", "prerequisites",
        "timing_profile", "candidate_changed_paths", "prior_hard_stop",
    )
    for field in required:
        if field not in value:
            errors.append(f"allocation.{field}: required")
    owner = value.get("owner")
    concern = value.get("concern")
    result = value.get("result")
    structural = {"multiple_owner": isinstance(owner, list) and len(owner) != 1,
                  "multiple_concern": isinstance(concern, list) and len(concern) != 1,
                  "multiple_result": isinstance(result, list) and len(result) != 1,
                  "unbounded_input": value.get("input_refs") in ("unbounded", "*", None)
                  or value.get("input_refs") is True}
    if isinstance(owner, list) and len(owner) == 1:
        owner = owner[0]
    elif isinstance(owner, list):
        owner = " | ".join(str(item) for item in owner)
    if isinstance(concern, list) and len(concern) == 1:
        concern = concern[0]
    elif isinstance(concern, list):
        concern = " | ".join(str(item) for item in concern)
    if isinstance(result, list) and len(result) == 1:
        result = result[0]
    elif isinstance(result, list):
        result = " | ".join(str(item) for item in result)
    for field, item in (("owner", owner), ("concern", concern), ("result", result)):
        text = _normalise_text(item, f"allocation.{field}", errors)
        if text:
            if field == "owner": owner = text
            elif field == "concern": concern = text
            else: result = text
    refs = value.get("input_refs")
    normalized_refs: list[str] = []
    if isinstance(refs, list):
        if len(refs) > ALLOCATION_MAX_INPUT_REFS:
            structural["unbounded_input"] = True
        for index, ref in enumerate(refs):
            text = _normalise_text(ref, f"allocation.input_refs[{index}]", errors)
            if text:
                normalized_refs.append(text)
    elif not structural["unbounded_input"]:
        errors.append("allocation.input_refs: must be a bounded list")

    prerequisites = value.get("prerequisites", [])
    if not isinstance(prerequisites, list):
        errors.append("allocation.prerequisites: must be a list")
        prerequisites = []
    normalized_prerequisites = []
    failed_prerequisite = False
    for index, prerequisite in enumerate(prerequisites):
        if isinstance(prerequisite, Mapping):
            name = _normalise_text(prerequisite.get("name", ""), f"allocation.prerequisites[{index}].name", errors)
            state = str(prerequisite.get("status", "passed")).lower()
            passed = prerequisite.get("passed", state not in {"failed", "blocked"})
            failed_prerequisite = failed_prerequisite or passed is False or state in {"failed", "blocked"}
            normalized_prerequisites.append({"name": name, "passed": bool(passed), "status": state})
        else:
            name = _normalise_text(prerequisite, f"allocation.prerequisites[{index}]", errors)
            normalized_prerequisites.append({"name": name, "passed": True, "status": "passed"})

    candidate_changed_paths = value.get("candidate_changed_paths")
    if (isinstance(candidate_changed_paths, bool) or
            not isinstance(candidate_changed_paths, int) or candidate_changed_paths < 0):
        errors.append("allocation.candidate_changed_paths: must be a non-negative integer")
        candidate_changed_paths = 0
    prior_hard_stop = value.get("prior_hard_stop")
    if not isinstance(prior_hard_stop, bool):
        errors.append("allocation.prior_hard_stop: must be true or false")
        prior_hard_stop = False
    profile = value.get("timing_profile", {})
    if not isinstance(profile, Mapping):
        errors.append("allocation.timing_profile: must be an object")
        profile = {}
    normalized_profile = {key: _seconds(profile.get(key), f"allocation.timing_profile.{key}", errors)
                          for key in ("target_s", "checkpoint_s", "hard_stop_s", "reserve_s", "max_hard_cap_s")}
    if normalized_profile["target_s"] < normalized_profile["checkpoint_s"] < normalized_profile["hard_stop_s"]:
        pass
    else:
        errors.append("allocation.timing_profile: require target < checkpoint < hard_stop")
    if normalized_profile["hard_stop_s"] > normalized_profile["max_hard_cap_s"]:
        errors.append("allocation.timing_profile: hard_stop must not exceed max_hard_cap")
    for field in ("target_s", "checkpoint_s", "hard_stop_s", "max_hard_cap_s"):
        if normalized_profile[field] <= 0:
            errors.append(f"allocation.timing_profile.{field}: must be positive")
    if normalized_profile["reserve_s"] >= (
            normalized_profile["hard_stop_s"] - normalized_profile["target_s"]):
        errors.append("allocation.timing_profile: reserve must be less than hard_stop - target")

    raw_units = value.get("priced_units", value.get("units"))
    if not isinstance(raw_units, Mapping):
        errors.append("allocation.priced_units: required setup/work/validation/handoff units")
        raw_units = {}
    units: dict[str, list[dict[str, Any]]] = {}
    unknown_unit = False
    estimated_unit = False
    all_measured = True
    plan = 0.0
    for category in ("setup", "work", "validation", "handoff"):
        entries = raw_units.get(category)
        if not isinstance(entries, list) or not entries:
            errors.append(f"allocation.priced_units.{category}: required non-empty list")
            entries = []
        normalized_entries = []
        for index, entry in enumerate(entries):
            if not isinstance(entry, Mapping):
                errors.append(f"allocation.priced_units.{category}[{index}]: must be an object")
                continue
            status = str(entry.get("status", "")).upper()
            source = _normalise_text(entry.get("source", ""),
                                     f"allocation.priced_units.{category}[{index}].source", errors)
            evidence_ref = entry.get("evidence_ref", "")
            if status == "MEASURED":
                evidence_ref = _normalise_text(
                    evidence_ref,
                    f"allocation.priced_units.{category}[{index}].evidence_ref",
                    errors,
                )
            elif evidence_ref not in ("", None):
                evidence_ref = _normalise_text(
                    evidence_ref,
                    f"allocation.priced_units.{category}[{index}].evidence_ref",
                    errors,
                )
            else:
                evidence_ref = ""
            seconds = 0.0 if status == "UNKNOWN" and "seconds" not in entry else _seconds(
                entry.get("seconds"), f"allocation.priced_units.{category}[{index}].seconds", errors)
            if status not in ADMISSION_STATUSES:
                errors.append(f"allocation.priced_units.{category}[{index}].status: invalid")
            unknown_unit = unknown_unit or status == "UNKNOWN"
            estimated_unit = estimated_unit or status == "ESTIMATED"
            all_measured = all_measured and status == "MEASURED"
            plan += seconds
            normalized_entries.append({
                "status": status, "seconds": seconds, "source": source,
                "evidence_ref": evidence_ref,
            })
        units[category] = normalized_entries
    critical = bool(value.get("critical", False))
    native = bool(value.get("native_collaboration", False))
    cancellable = bool(value.get("cancellable_pre_start_handle", False))
    return {"owner": owner, "concern": concern, "input_refs": normalized_refs, "result": result,
            "prerequisites": normalized_prerequisites, "timing_profile": normalized_profile,
            "priced_units": units, "plan_s": plan, "unknown_unit": unknown_unit,
            "estimated_unit": estimated_unit,
            "all_measured": all_measured, "failed_prerequisite": failed_prerequisite,
            "validation_over_reserve": sum(item["seconds"] for item in units["validation"]) >
            normalized_profile["hard_stop_s"] - normalized_profile["reserve_s"],
            "structural_split": any(structural.values()), "atomic": bool(value.get("atomic", False)),
            "critical": critical, "native_collaboration": native,
            "cancellable_pre_start_handle": cancellable,
            "candidate_changed_paths": candidate_changed_paths,
            "prior_hard_stop": prior_hard_stop,
            "candidate_wide_validation": False, "validation_path_counts": []}


def _admit(normalized: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    allocation = normalized["allocation"]
    if allocation["unknown_unit"]:
        return "MEASURE", allocation
    if allocation["failed_prerequisite"] or allocation["validation_over_reserve"]:
        return "BLOCK", allocation
    if allocation["prior_hard_stop"]:
        return "BLOCK", allocation
    if allocation["candidate_wide_validation"]:
        return "SPLIT", allocation
    if allocation["estimated_unit"]:
        return "MEASURE", allocation
    if allocation["structural_split"]:
        return "SPLIT", allocation
    if allocation["critical"] and allocation["native_collaboration"] and not allocation["cancellable_pre_start_handle"]:
        return "BLOCK", allocation
    profile = allocation["timing_profile"]
    if allocation["plan_s"] <= profile["target_s"]:
        return "ADMIT", allocation
    if (allocation["atomic"] and allocation["all_measured"] and
            allocation["plan_s"] + profile["reserve_s"] < profile["hard_stop_s"] and
            profile["hard_stop_s"] <= profile["max_hard_cap_s"]):
        return "ADMIT", allocation
    return "SPLIT", allocation


def _canonical_dispatch_payload(normalized: Mapping[str, Any]) -> bytes:
    """Canonicalize identity/allocation inputs, excluding derived fields."""
    payload = {
        key: normalized[key]
        for key in (
            "role", "task_id", "objective", "acceptance", "paths",
            "validation", "stop", "model", "effort", "fork_turns",
            "allocation",
        )
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def validate_packet(
    packet: Mapping[str, Any],
    root: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Validate and normalize a structured packet without invoking a host."""

    if not isinstance(packet, Mapping):
        raise PacketValidationError(["packet: top-level JSON value must be an object"])

    errors: list[str] = []
    unknown = sorted(set(packet) - ALLOWED_FIELDS - {"fork_context"})
    for field in unknown:
        if any(marker in field.lower() for marker in ("enc", "cipher", "opaque", "sealed", "blob")):
            errors.append(f"{field}: opaque/encrypted-only payload fields are rejected")
        else:
            errors.append(f"unexpected field: {field}")
    for field in REQUIRED_FIELDS:
        if field not in packet:
            errors.append(f"{field}: required")

    role = ""
    if "role" in packet:
        role = _normalise_text(packet["role"], "role", errors).lower()
        if role and role not in CANONICAL_ROLES:
            errors.append(f"role: unknown canonical role '{role}'")

    task_id = ""
    if "task_id" in packet:
        task_id = _normalise_text(packet["task_id"], "task_id", errors)
        if task_id and not _TASK_ID_RE.fullmatch(task_id):
            errors.append("task_id: must be an explicit identifier without whitespace")

    objective = ""
    if "objective" in packet:
        objective = _normalise_text(packet["objective"], "objective", errors)

    acceptance: list[str] = []
    if "acceptance" in packet:
        acceptance = _normalise_text_list(packet["acceptance"], "acceptance", errors)

    paths: list[str] = []
    if "paths" in packet:
        paths = _normalise_paths(packet["paths"], errors)

    validation: list[str] = []
    if "validation" in packet:
        validation = _normalise_text_list(packet["validation"], "validation", errors)

    stop = ""
    if "stop" in packet:
        stop = _normalise_text(packet["stop"], "stop", errors)

    model = ""
    if "model" in packet:
        model = _normalise_text(packet["model"], "model", errors)
        if model and not _MODEL_RE.fullmatch(model):
            errors.append("model: must be a concrete model slug")

    effort = ""
    if "effort" in packet:
        effort = _normalise_text(packet["effort"], "effort", errors).lower()
        if effort and effort not in EFFORTS:
            errors.append(f"effort: unsupported value '{effort}'")

    allocation = _normalise_allocation(packet.get("allocation"), errors)
    for field in ("critical", "native_collaboration", "cancellable_pre_start_handle"):
        if field in packet:
            allocation[field] = bool(packet[field])
    validation_path_counts = [
        int(match.group(1))
        for item in validation
        for match in _VALIDATION_PATH_COUNT_RE.finditer(item)
    ]
    allocation["validation_path_counts"] = validation_path_counts
    allocation["candidate_wide_validation"] = any(
        count > len(paths) for count in validation_path_counts
    )
    if (validation_path_counts and allocation.get("candidate_changed_paths") not in
            set(validation_path_counts)):
        errors.append(
            "allocation.candidate_changed_paths: conflicts with validation path count"
        )

    if "fork_context" in packet:
        errors.append(
            "fork_context: legacy host field is unsupported; "
            "use fork_turns='1' for single-specialist isolation"
        )
    if "fork_turns" in packet:
        fork_turns = _normalise_fork_turns(packet["fork_turns"], errors)
        if fork_turns and fork_turns != MINIMAL_SPECIALIST_FORK_TURNS:
            errors.append(
                "fork_turns: only '1' is supported for one-specialist isolation; "
                "larger inherited contexts can re-enter Lead routing"
            )
    else:
        fork_turns = ""

    host_binding = _normalise_host_binding(packet.get("host_binding"), errors)

    if errors:
        raise PacketValidationError(errors)

    role_card = _resolve_role_card(role, root)
    return {
        "role": role,
        "task_id": task_id,
        "objective": objective,
        "acceptance": acceptance,
        "paths": paths,
        "validation": validation,
        "stop": stop,
        "model": model,
        "effort": effort,
        "fork_turns": fork_turns,
        "host_binding": host_binding,
        "role_card": role_card,
        "allocation": allocation,
    }


def build_plaintext_message(normalized: Mapping[str, Any]) -> str:
    """Render the bounded plaintext prompt consumed by the worker."""

    acceptance = "; ".join(str(item) for item in normalized["acceptance"])
    validation = "; ".join(str(item) for item in normalized["validation"])
    paths = ", ".join(str(item) for item in normalized["paths"])
    message = "\n".join(
        (
            f"Canonical role: {normalized['role']}",
            f"Task ID: {normalized['task_id']}",
            f"Read the canonical role card first: {normalized['role_card']}",
            f"Objective: {normalized['objective']}",
            f"Acceptance: {acceptance}",
            f"Owned paths: {paths}",
            f"Validation: {validation}",
            f"Stop condition: {normalized['stop']}",
            READY_BOUNDARY,
            SPECIALIST_EXECUTION_BOUNDARY,
            "Return facts, evidence, blockers, and residual risk. Do not commit or push.",
            "Closeout format: `- **Recommended next to-do:** <one action or NONE — objective complete>`; `- **Pending tasks:** <NONE or task ID — owner — prerequisite — state>`."
        )
    )
    count = _word_count(message)
    if count > MAX_MESSAGE_WORDS:
        raise PacketValidationError(
            [f"plaintext message is {count} words; maximum is {MAX_MESSAGE_WORDS}"]
        )
    return message


def prepare_dispatch(
    packet: Mapping[str, Any],
    root: str | os.PathLike[str] | None = None,
    *,
    coding_team_root: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Return a host-ready JSON object, or raise a blocking validation error."""

    if root is not None and coding_team_root is not None:
        raise PacketValidationError(["provide only one of root or coding_team_root"])
    normalized = validate_packet(packet, coding_team_root if coding_team_root is not None else root)
    decision, allocation = _admit(normalized)
    normalized["allocation"] = allocation
    canonical_identity = _canonical_dispatch_payload(normalized)
    admission_digest = hashlib.sha256(canonical_identity).hexdigest()
    dispatch_id = "ctd_" + admission_digest[:24]
    task_name = _derive_task_name(normalized["task_id"], dispatch_id)
    normalized["admission_digest"] = admission_digest
    if decision != "ADMIT":
        return {
            "status": decision,
            "role": normalized["role"],
            "task_id": normalized["task_id"],
            "dispatch_id": dispatch_id,
            "admission": {"decision": decision, "digest": admission_digest, "allocation": allocation},
        }
    message = build_plaintext_message(normalized)

    # Keep the normalized packet visible for audit/debugging while exposing the
    # exact live Codex spawn_agent shape. Canonical role/task IDs stay in the
    # packet and plaintext message; they are not host payload fields.
    packet_out = dict(normalized)
    spawn = {
        "task_name": task_name,
        "agent_type": HOST_AGENT_TYPES[normalized["role"]],
        "fork_turns": normalized["fork_turns"],
        "message": message,
        "model": normalized["model"],
        "reasoning_effort": normalized["effort"],
    }
    return {
        "status": "READY",
        "readiness": READY_BOUNDARY,
        "role": normalized["role"],
        "task_id": normalized["task_id"],
        "dispatch_id": dispatch_id,
        "role_card": normalized["role_card"],
        "message": message,
        "word_count": _word_count(message),
        "packet": packet_out,
        "admission": {"decision": decision, "digest": admission_digest, "allocation": allocation},
        "spawn": spawn,
        "invocation": {
            "tool": DIRECT_HOST_BINDING,
            "mode": DIRECT_HOST_MODE,
            "instruction": DIRECT_HOST_INVOCATION,
        },
    }


def _read_input(path: str | None) -> str:
    if path:
        try:
            return Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            raise PacketValidationError([f"cannot read input: {exc}"]) from exc
    return sys.stdin.read()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="JSON packet file; stdin is used when omitted")
    parser.add_argument(
        "--coding-team-root",
        help="Coding Team root containing core/roles (defaults to CODING_TEAM_ROOT or this checkout)",
    )
    args = parser.parse_args(argv)

    try:
        raw = _read_input(args.input)
        payload = _load_json(raw)
        result = prepare_dispatch(payload, root=args.coding_team_root)
    except PacketValidationError as exc:
        json.dump({"status": "BLOCKED", "errors": exc.errors}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 2

    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
