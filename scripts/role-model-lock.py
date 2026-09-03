#!/usr/bin/env python3
"""Strict, read-only validation for the Sprint 2 Codex role-model lock.

This module intentionally stops at the DRAFT schema/digest and route-
comparison boundary.  It does not create an authority file, invoke a model,
touch the policy cache or Monitor, or change workflow state.  A DRAFT route
comparison is diagnostic only; it cannot authorize or prevent dispatch.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = 1
LOCK_ID = "wysy-codex-required-seat-lock"
ADAPTER = "codex"
LIFECYCLE_STATE = "DRAFT"
UNLISTED_ROLE_BEHAVIOR = "APPROVED_TIER_MAP"
REPAIR_ACTION = "Restore the approved lock mapping, then retry."
NOT_ACTIVE = "NOT_ACTIVE"
NOT_APPLICABLE_TIER_MAP = "NOT_APPLICABLE_TIER_MAP"
ROUTE_MATCH = "MATCH"
ROUTE_MISMATCH = "MISMATCH"
ROLE_MODEL_LOCK_NOT_ACTIVE = "ROLE_MODEL_LOCK_NOT_ACTIVE"
ROLE_MODEL_LOCK_CACHE_STALE = "ROLE_MODEL_LOCK_CACHE_STALE"
ROLE_MODEL_LOCK_PACKET_MISMATCH = "ROLE_MODEL_LOCK_PACKET_MISMATCH"
ROLE_MODEL_LOCK_CHECK = "ROLE_MODEL_LOCK_CHECK"
HOST_ACTUAL_UNVERIFIED = "UNVERIFIED"
DATA_BOUNDARY_LOCAL_ONLY = "LOCAL_ONLY"
MATCH = "MATCH"
NOT_SUPPLIED = "NOT_SUPPLIED"
POLICY_MANIFEST_SCHEMA_VERSION = 1
ROLE_MODEL_LOCK_MANIFEST_PATH = "adapters/codex/role-model-lock.json"
MANIFEST_ID_RE = re.compile(r"^manifest_[0-9a-f]{16}$")
MANIFEST_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
MANIFEST_SAFE_VALUE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
FILE_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

PROTECTED_ROLES = (
    "lead",
    "product-manager",
    "system-architect",
    "backend-engineer",
    "test-engineer",
    "advisor",
    "contradictor",
)

# The contract deliberately leaves Gatekeeper outside this authority.  Keep
# the exact route table here so a semantically different seven-seat mapping
# cannot be accepted merely because its object shape is correct.
EXPECTED_SEATS: dict[str, dict[str, str]] = {
    "lead": {"model": "gpt-5.6-sol", "effort": "high"},
    "product-manager": {"model": "gpt-5.6-sol", "effort": "high"},
    "system-architect": {"model": "gpt-5.6-sol", "effort": "high"},
    "backend-engineer": {"model": "gpt-5.6-luna", "effort": "max"},
    "test-engineer": {"model": "gpt-5.6-luna", "effort": "max"},
    "advisor": {"model": "claude-opus-5", "effort": "high"},
    "contradictor": {"model": "deepseek-v4-pro", "effort": "xhigh"},
}

TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "lock_id",
        "adapter",
        "revision",
        "lifecycle",
        "approval",
        "seats",
        "unlisted_role_behavior",
        "digest",
    }
)
LIFECYCLE_KEYS = frozenset({"state", "activation"})
APPROVAL_KEYS = frozenset({"status", "approved_by", "approval_ref", "approved_at"})
SEAT_KEYS = frozenset({"model", "effort"})
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
PACKET_IDENTITY_KEYS = frozenset({"revision", "digest"})

DRAFT_EVENT_KEYS = frozenset(
    {
        "event_type",
        "task_id",
        "run_id",
        "canonical_role",
        "authority_revision",
        "authority_digest",
        "lifecycle_state",
        "planned_route",
        "requested_route",
        "host_actual",
        "manifest_binding",
        "packet_status",
        "route_comparison",
        "bootstrap_provenance",
        "lifecycle_outcome",
        "enforcement_status",
        "auto_action",
        "data_boundary",
    }
)
DRAFT_EVENT_BOUNDARY = {
    "storage_scope": DATA_BOUNDARY_LOCAL_ONLY,
    "export_status": "NOT_REQUESTED",
    "public_safe": False,
    "consent_ref": None,
    "redaction_check": "NOT_RUN",
}

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_MANIFEST_BINDING_KEYS = frozenset(
    {
        "status",
        "session_id",
        "context_fingerprint",
        "adapter_policy_scope",
        "manifest_id",
        "manifest_revision",
        "manifest_hash_sha256",
        "root_source",
        "loaded_at",
        "include_learning_policy",
        "path",
        "size",
        "mtime_ns",
        "sha256",
    }
)
_BOOTSTRAP_KEYS = frozenset(
    {
        "mode",
        "task_run_id",
        "canonical_role",
        "approved_map_ref",
        "user_route_approval_ref",
        "planned",
        "requested",
        "host_actual",
        "candidate_revision",
        "candidate_digest",
        "enforcement_status",
    }
)
_PROTECTED_COMPARISON_KEYS = frozenset(
    {
        "canonical_role",
        "status",
        "lifecycle_outcome",
        "enforcement_status",
        "auto_action",
        "lock_id",
        "revision",
        "digest",
        "lifecycle_state",
        "code",
        "comparison_status",
        "match",
        "expected",
        "expected_route",
        "requested",
        "requested_route",
        "requested_match",
        "planned_match",
    }
)
_UNLISTED_COMPARISON_KEYS = frozenset(
    {
        "canonical_role",
        "status",
        "lifecycle_outcome",
        "enforcement_status",
        "auto_action",
        "comparison_status",
    }
)


class RoleModelLockError(ValueError):
    """A safe, stable validation error for the read-only checker."""

    def __init__(
        self,
        code: str,
        reason: str,
        *,
        field: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.reason = reason
        self.field = field
        self.details = dict(details or {})
        detail = f"{field}: {reason}" if field else reason
        super().__init__(detail)


class DuplicateJSONKeyError(ValueError):
    """Raised while parsing an object containing a repeated member name."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKeyError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    # RFC 8259 does not admit NaN or Infinity.  Reject them at parse time so
    # they cannot be hidden in an unknown field or reach canonicalization.
    raise ValueError(f"non-standard JSON number: {value}")


def _schema_error(reason: str, *, field: str | None = None) -> RoleModelLockError:
    return RoleModelLockError("ROLE_MODEL_LOCK_SCHEMA_INVALID", reason, field=field)


def _digest_error(reason: str) -> RoleModelLockError:
    return RoleModelLockError("ROLE_MODEL_LOCK_DIGEST_MISMATCH", reason, field="digest")


def _parse_json_bytes(raw: bytes, *, source: str = "lock") -> dict[str, Any]:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise _schema_error("document is not valid UTF-8") from exc

    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except (DuplicateJSONKeyError, json.JSONDecodeError, ValueError) as exc:
        raise _schema_error(f"invalid JSON in {source}: {exc}") from exc

    if not isinstance(value, dict):
        raise _schema_error("top-level document must be a JSON object")
    return value


def load_json(path: str | Path) -> dict[str, Any]:
    """Read strict UTF-8 JSON without performing any write or side effect."""

    target = Path(path)
    try:
        raw = target.read_bytes()
    except OSError as exc:
        raise RoleModelLockError(
            "ROLE_MODEL_LOCK_MISSING", f"authority file is unreadable: {target}"
        ) from exc
    return _parse_json_bytes(raw, source=str(target))


def _ensure_string(value: Any, field: str, *, nonempty: bool = True) -> str:
    if type(value) is not str:  # bool/int are deliberately not string-like.
        raise _schema_error("must be a string", field=field)
    if nonempty and not value:
        raise _schema_error("must be non-empty", field=field)
    # Lone UTF-16 surrogate code points can be produced by a JSON escape but
    # cannot be represented by the required UTF-8 canonical bytes.
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise _schema_error("must not contain UTF-16 surrogate code points", field=field)
    if any(ord(char) < 0x20 for char in value):
        raise _schema_error("must not contain control characters", field=field)
    return value


def _ensure_opaque(value: Any, field: str) -> str:
    text = _ensure_string(value, field)
    if text.strip() != text:
        raise _schema_error("must not have leading or trailing whitespace", field=field)
    if not text.strip():
        raise _schema_error("must contain a non-whitespace value", field=field)
    return text


def _ensure_exact_keys(value: Any, expected: frozenset[str], field: str) -> None:
    if not isinstance(value, dict):
        raise _schema_error("must be a JSON object", field=field)
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if unknown:
            details.append("unknown " + ", ".join(unknown))
        raise _schema_error("; ".join(details), field=field)


def _validate_rfc3339(value: Any, field: str) -> str:
    text = _ensure_string(value, field)
    # RFC 3339 date-time, including optional fractional seconds and either Z
    # or a numeric UTC offset.  datetime.fromisoformat below checks ranges.
    if not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
        text,
    ):
        raise _schema_error("must be an RFC3339 date-time", field=field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise _schema_error("must be an RFC3339 date-time", field=field) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise _schema_error("must include an RFC3339 timezone", field=field)
    return text


def _validate_schema(document: Mapping[str, Any]) -> None:
    _ensure_exact_keys(document, TOP_LEVEL_KEYS, "document")

    if type(document["schema_version"]) is not int or document["schema_version"] != SCHEMA_VERSION:
        raise _schema_error("must equal 1", field="schema_version")
    if document["lock_id"] != LOCK_ID:
        # Check type separately to keep diagnostics deterministic for arbitrary
        # malformed input instead of relying on an equality coincidence.
        _ensure_string(document["lock_id"], "lock_id")
        raise _schema_error(f"must equal {LOCK_ID!r}", field="lock_id")
    if document["adapter"] != ADAPTER:
        _ensure_string(document["adapter"], "adapter")
        raise _schema_error("must equal 'codex'", field="adapter")
    _ensure_opaque(document["revision"], "revision")

    lifecycle = document["lifecycle"]
    _ensure_exact_keys(lifecycle, LIFECYCLE_KEYS, "lifecycle")
    if lifecycle["state"] != LIFECYCLE_STATE:
        _ensure_string(lifecycle["state"], "lifecycle.state")
        raise _schema_error("must equal 'DRAFT'", field="lifecycle.state")
    if lifecycle["activation"] is not None:
        raise _schema_error("must be null while lifecycle is DRAFT", field="lifecycle.activation")

    approval = document["approval"]
    _ensure_exact_keys(approval, APPROVAL_KEYS, "approval")
    if approval["status"] != "APPROVED":
        _ensure_string(approval["status"], "approval.status")
        raise _schema_error("must equal 'APPROVED'", field="approval.status")
    if approval["approved_by"] != "human":
        _ensure_string(approval["approved_by"], "approval.approved_by")
        raise _schema_error("must equal 'human'", field="approval.approved_by")
    _ensure_opaque(approval["approval_ref"], "approval.approval_ref")
    _validate_rfc3339(approval["approved_at"], "approval.approved_at")

    seats = document["seats"]
    if not isinstance(seats, dict):
        raise _schema_error("must be a JSON object", field="seats")
    actual_roles = set(seats)
    expected_roles = set(PROTECTED_ROLES)
    if actual_roles != expected_roles:
        missing = sorted(expected_roles - actual_roles)
        unknown = sorted(actual_roles - expected_roles)
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if unknown:
            details.append("unknown " + ", ".join(unknown))
        if "gatekeeper" in actual_roles:
            details.append("gatekeeper is unlisted and cannot appear in seats")
        raise _schema_error("; ".join(details), field="seats")
    for role in PROTECTED_ROLES:
        seat = seats[role]
        field = f"seats.{role}"
        _ensure_exact_keys(seat, SEAT_KEYS, field)
        model = _ensure_string(seat["model"], f"{field}.model")
        effort = _ensure_string(seat["effort"], f"{field}.effort")
        expected = EXPECTED_SEATS[role]
        if model != expected["model"] or effort != expected["effort"]:
            raise _schema_error(
                f"must equal model={expected['model']!r}, effort={expected['effort']!r}",
                field=field,
            )

    if document["unlisted_role_behavior"] != UNLISTED_ROLE_BEHAVIOR:
        _ensure_string(document["unlisted_role_behavior"], "unlisted_role_behavior")
        raise _schema_error(
            "must equal 'APPROVED_TIER_MAP'", field="unlisted_role_behavior"
        )
    digest = _ensure_string(document["digest"], "digest")
    if not DIGEST_RE.fullmatch(digest):
        raise _schema_error(
            "must match sha256:<64 lowercase hexadecimal characters>", field="digest"
        )


def canonical_bytes(document: Mapping[str, Any]) -> bytes:
    """Return JCS-equivalent UTF-8 bytes with only top-level ``digest`` omitted.

    The lock schema permits only strings, the integer schema version, and
    JSON null.  For those values Python's compact sorted JSON representation
    has the RFC 8785 member ordering and escaping required by this bounded
    contract.  No caller-visible mapping is mutated.
    """

    if not isinstance(document, Mapping):
        raise TypeError("document must be a mapping")
    without_digest = dict(document)
    without_digest.pop("digest", None)
    try:
        text = json.dumps(
            without_digest,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return text.encode("utf-8", errors="strict")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ValueError(f"document cannot be canonicalized: {exc}") from exc


def compute_digest(document: Mapping[str, Any]) -> str:
    """Compute the lock digest over the object with its top-level digest removed."""

    return "sha256:" + hashlib.sha256(canonical_bytes(document)).hexdigest()


def canonical_digest(document: Mapping[str, Any]) -> str:
    """Alias used by callers that describe the result as a canonical digest."""

    return compute_digest(document)


def verify_digest(document: Mapping[str, Any]) -> bool:
    """Return whether a document's recorded digest matches its canonical bytes."""

    recorded = document.get("digest") if isinstance(document, Mapping) else None
    return isinstance(recorded, str) and bool(DIGEST_RE.fullmatch(recorded)) and recorded == compute_digest(document)


def validate_document(document: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a loaded DRAFT document and return it unchanged.

    ``RoleModelLockError`` is raised for every schema or digest failure.  The
    returned object is the same semantic document supplied by the caller; no
    normalization or mutation is performed.
    """

    if not isinstance(document, dict):
        raise _schema_error("top-level document must be a JSON object")
    _validate_schema(document)
    expected = compute_digest(document)
    if document["digest"] != expected:
        raise _digest_error(f"recorded digest does not match canonical digest {expected}")
    return document


def validate_manifest_binding(
    *,
    manifest: Mapping[str, Any],
    session_id: str,
    context_fingerprint: str,
    lock_path_ref: str,
    lock_bytes: bytes,
) -> dict[str, Any]:
    """Validate the in-memory policy manifest binding for the DRAFT lock.

    This is deliberately a pure boundary check.  It validates only manifest
    metadata and the supplied lock bytes; it does not read a path, inspect a
    packet, or perform any lifecycle, dispatch, or policy-cache action.
    """

    def stale(reason: str, *, field: str | None = None) -> None:
        raise RoleModelLockError(ROLE_MODEL_LOCK_CACHE_STALE, reason, field=field)

    def opaque(value: Any, field: str) -> str:
        try:
            return _ensure_opaque(value, field)
        except RoleModelLockError as exc:
            stale(exc.reason, field=field)
        raise AssertionError("unreachable")

    def safe(value: Any, field: str, pattern: re.Pattern[str]) -> str:
        text = opaque(value, field)
        if not pattern.fullmatch(text):
            stale("must use a safe policy-cache identifier", field=field)
        return text

    def rfc3339(value: Any, field: str) -> str:
        try:
            return _validate_rfc3339(value, field)
        except RoleModelLockError as exc:
            stale(exc.reason, field=field)
        raise AssertionError("unreachable")

    expected_manifest_keys = frozenset(
        {
            "schema_version",
            "session_id",
            "context_fingerprint",
            "adapter_policy_scope",
            "manifest_id",
            "manifest_revision",
            "manifest_hash_sha256",
            "root_source",
            "loaded_at",
            "include_learning_policy",
            "files",
        }
    )
    if not isinstance(manifest, dict):
        stale("manifest must be an object", field="manifest")
    actual_manifest_keys = set(manifest)
    if actual_manifest_keys != expected_manifest_keys:
        missing = sorted(expected_manifest_keys - actual_manifest_keys)
        unknown = sorted(actual_manifest_keys - expected_manifest_keys)
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if unknown:
            details.append("unknown " + ", ".join(unknown))
        stale("; ".join(details), field="manifest")

    if (
        type(manifest["schema_version"]) is not int
        or manifest["schema_version"] != POLICY_MANIFEST_SCHEMA_VERSION
    ):
        stale("must equal 1", field="manifest.schema_version")

    manifest_id = safe(manifest["manifest_id"], "manifest.manifest_id", MANIFEST_ID_RE)
    manifest_revision = safe(
        manifest["manifest_revision"],
        "manifest.manifest_revision",
        MANIFEST_SAFE_VALUE_RE,
    )
    manifest_hash_sha256 = safe(
        manifest["manifest_hash_sha256"],
        "manifest.manifest_hash_sha256",
        MANIFEST_HASH_RE,
    )
    adapter_policy_scope = opaque(
        manifest["adapter_policy_scope"], "manifest.adapter_policy_scope"
    )
    if adapter_policy_scope != "codex-local-policy":
        stale(
            "must equal 'codex-local-policy'", field="manifest.adapter_policy_scope"
        )

    supplied_session_id = safe(session_id, "session_id", MANIFEST_SAFE_VALUE_RE)
    supplied_context = safe(
        context_fingerprint, "context_fingerprint", MANIFEST_SAFE_VALUE_RE
    )
    manifest_session_id = safe(
        manifest["session_id"], "manifest.session_id", MANIFEST_SAFE_VALUE_RE
    )
    manifest_context = safe(
        manifest["context_fingerprint"],
        "manifest.context_fingerprint",
        MANIFEST_SAFE_VALUE_RE,
    )
    if manifest_session_id != supplied_session_id:
        stale("does not equal supplied session_id", field="manifest.session_id")
    if manifest_context != supplied_context:
        stale(
            "does not equal supplied context_fingerprint",
            field="manifest.context_fingerprint",
        )

    root_source = opaque(manifest["root_source"], "manifest.root_source")
    loaded_at = rfc3339(manifest["loaded_at"], "manifest.loaded_at")
    if type(manifest["include_learning_policy"]) is not bool:
        stale("must be a boolean", field="manifest.include_learning_policy")

    supplied_path = opaque(lock_path_ref, "lock_path_ref")
    if supplied_path != ROLE_MODEL_LOCK_MANIFEST_PATH:
        stale(
            f"must equal {ROLE_MODEL_LOCK_MANIFEST_PATH!r}",
            field="lock_path_ref",
        )

    files = manifest["files"]
    if not isinstance(files, list) or not files:
        stale("must be a non-empty array", field="manifest.files")
    expected_file_keys = frozenset({"path", "size", "mtime_ns", "sha256"})
    seen_paths: set[str] = set()
    target_sha: str | None = None
    target_size: int | None = None
    target_mtime_ns: int | None = None
    for index, entry in enumerate(files):
        field = f"manifest.files[{index}]"
        if not isinstance(entry, dict):
            stale("must be an object", field=field)
        actual_file_keys = set(entry)
        if actual_file_keys != expected_file_keys:
            missing = sorted(expected_file_keys - actual_file_keys)
            unknown = sorted(actual_file_keys - expected_file_keys)
            details = []
            if missing:
                details.append("missing " + ", ".join(missing))
            if unknown:
                details.append("unknown " + ", ".join(unknown))
            stale("; ".join(details), field=field)
        path = opaque(entry["path"], f"{field}.path")
        size = entry["size"]
        if type(size) is not int or size < 0:
            stale("must be a nonnegative integer", field=f"{field}.size")
        mtime_ns = entry["mtime_ns"]
        if type(mtime_ns) is not int or mtime_ns < 0:
            stale("must be a nonnegative integer", field=f"{field}.mtime_ns")
        file_sha = safe(entry["sha256"], f"{field}.sha256", FILE_SHA256_RE)
        if path in seen_paths:
            stale("duplicate path", field=f"{field}.path")
        seen_paths.add(path)
        if path == ROLE_MODEL_LOCK_MANIFEST_PATH:
            target_sha = file_sha
            target_size = size
            target_mtime_ns = mtime_ns

    if target_sha is None:
        stale(
            f"must contain exactly one entry for {ROLE_MODEL_LOCK_MANIFEST_PATH!r}",
            field="manifest.files",
        )
    if type(lock_bytes) is not bytes:
        stale("must be bytes", field="lock_bytes")
    expected_sha = hashlib.sha256(lock_bytes).hexdigest()
    if target_sha != expected_sha:
        stale("does not match supplied lock bytes", field="manifest.files.sha256")

    # ``adapter_scope`` is intentionally read and retained to make the
    # binding result self-describing; all lifecycle enforcement remains out of
    # scope for this DRAFT validator.
    return {
        "status": MATCH,
        "session_id": supplied_session_id,
        "context_fingerprint": supplied_context,
        "adapter_policy_scope": adapter_policy_scope,
        "manifest_id": manifest_id,
        "manifest_revision": manifest_revision,
        "manifest_hash_sha256": manifest_hash_sha256,
        "root_source": root_source,
        "loaded_at": loaded_at,
        "include_learning_policy": manifest["include_learning_policy"],
        "path": supplied_path,
        "size": target_size,
        "mtime_ns": target_mtime_ns,
        "sha256": expected_sha,
    }


def validate_packet_binding(
    packet: Mapping[str, Any] | None,
    authority_revision: str,
    authority_digest: str,
) -> str:
    """Validate an optional compact-packet identity against the authority.

    The packet is intentionally limited to the two identity members copied
    from the validated authority.  This is a pure comparison boundary: it
    neither loads the authority nor reads or mutates any packet source.
    """

    def mismatch(reason: str, *, field: str | None = None) -> None:
        raise RoleModelLockError(ROLE_MODEL_LOCK_PACKET_MISMATCH, reason, field=field)

    if packet is None:
        return NOT_SUPPLIED
    if not isinstance(packet, Mapping):
        mismatch("packet identity must be an object", field="packet")

    actual_keys = set(packet)
    if actual_keys != PACKET_IDENTITY_KEYS:
        missing = sorted(PACKET_IDENTITY_KEYS - actual_keys)
        unknown = sorted(actual_keys - PACKET_IDENTITY_KEYS)
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if unknown:
            details.append("unknown " + ", ".join(unknown))
        mismatch("; ".join(details), field="packet")

    try:
        packet_revision = _ensure_opaque(packet["revision"], "packet.revision")
        packet_digest = _ensure_string(packet["digest"], "packet.digest")
    except RoleModelLockError as exc:
        mismatch(exc.reason, field=exc.field)
    if not DIGEST_RE.fullmatch(packet_digest):
        mismatch(
            "must match sha256:<64 lowercase hexadecimal characters>",
            field="packet.digest",
        )

    if type(authority_revision) is not str or type(authority_digest) is not str:
        mismatch("authority identity must contain strings", field="authority")
    if packet_revision != authority_revision:
        mismatch("does not match validated authority revision", field="packet.revision")
    if packet_digest != authority_digest:
        mismatch("does not match validated authority digest", field="packet.digest")
    return MATCH


def validate_lock(document: Mapping[str, Any]) -> dict[str, Any]:
    """Compatibility alias for the pure document validator."""

    return validate_document(document)


def load_lock(path: str | Path) -> dict[str, Any]:
    """Load and fully validate one DRAFT lock without writing anything."""

    return validate_document(load_json(path))


def load_document(path: str | Path) -> dict[str, Any]:
    """Compatibility alias for :func:`load_lock`."""

    return load_lock(path)


def _normalize_route(value: Any, field: str) -> dict[str, str]:
    """Validate and copy one exact model/effort route object."""

    _ensure_exact_keys(value, SEAT_KEYS, field)
    return {
        "model": _ensure_string(value["model"], f"{field}.model"),
        "effort": _ensure_string(value["effort"], f"{field}.effort"),
    }


def _route_result(
    *,
    role: str,
    status: str,
    lifecycle_outcome: str,
    enforcement_status: str,
    auto_action: str = "none",
    **details: Any,
) -> dict[str, Any]:
    """Build a stable, metadata-only route diagnostic."""

    result: dict[str, Any] = {
        "canonical_role": role,
        "status": status,
        "lifecycle_outcome": lifecycle_outcome,
        "enforcement_status": enforcement_status,
        "auto_action": auto_action,
    }
    result.update(details)
    return result


def compare_requested_route(
    document: Mapping[str, Any],
    canonical_role: str,
    requested: Mapping[str, Any] | None = None,
    *,
    planned: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare a requested protected-seat route with the DRAFT authority.

    The comparison is deliberately pure: it validates the supplied document,
    copies route values into a diagnostic result, and performs no dispatch,
    repair, retry, cache/Monitor write, or workflow mutation.  Protected seats
    always report ``NOT_ACTIVE`` while this candidate is DRAFT, even when the
    route differs.  Gatekeeper and every other unlisted role are outside the
    authority and return ``NOT_APPLICABLE_TIER_MAP`` without requiring a route
    identity.

    ``planned`` is optional evidence.  When supplied, it is compared to the
    same exact seat independently from ``requested``; neither value is
    treated as host-actual identity.
    """

    role = _ensure_opaque(canonical_role, "canonical_role")

    # The unlisted exception is intentionally decided before reading the lock:
    # those roles retain the approved tier-map behavior, including its generic
    # missing-identity behavior.
    if role not in PROTECTED_ROLES:
        return _route_result(
            role=role,
            status=NOT_APPLICABLE_TIER_MAP,
            lifecycle_outcome=NOT_APPLICABLE_TIER_MAP,
            enforcement_status=NOT_APPLICABLE_TIER_MAP,
            comparison_status=NOT_APPLICABLE_TIER_MAP,
        )

    validated = validate_document(document)
    expected = dict(EXPECTED_SEATS[role])
    requested_route = (
        _normalize_route(requested, "requested") if requested is not None else None
    )
    planned_route = _normalize_route(planned, "planned") if planned is not None else None

    requested_matches = requested_route == expected
    planned_matches = planned_route == expected if planned is not None else True
    matches = requested_matches and planned_matches
    comparison_status = ROUTE_MATCH if matches else ROUTE_MISMATCH

    details: dict[str, Any] = {
        "lock_id": validated["lock_id"],
        "revision": validated["revision"],
        "digest": validated["digest"],
        "lifecycle_state": validated["lifecycle"]["state"],
        "code": ROLE_MODEL_LOCK_NOT_ACTIVE,
        "comparison_status": comparison_status,
        "match": matches,
        "expected": expected,
        "expected_route": dict(expected),
        "requested": requested_route,
        "requested_route": dict(requested_route) if requested_route is not None else None,
        "requested_match": requested_matches,
        "planned_match": planned_matches,
    }
    if planned is not None:
        details["planned"] = planned_route
        details["planned_route"] = dict(planned_route) if planned_route is not None else None
    return _route_result(
        role=role,
        status=NOT_ACTIVE,
        lifecycle_outcome=NOT_ACTIVE,
        enforcement_status=NOT_ACTIVE,
        **details,
    )


def compare_route(
    document: Mapping[str, Any],
    canonical_role: str,
    requested: Mapping[str, Any] | None = None,
    *,
    planned: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Public short alias for :func:`compare_requested_route`."""

    return compare_requested_route(
        document, canonical_role, requested, planned=planned
    )


def route_comparison(
    document: Mapping[str, Any],
    canonical_role: str,
    requested: Mapping[str, Any] | None = None,
    *,
    planned: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compatibility alias for callers naming the result as a comparison."""

    return compare_requested_route(
        document, canonical_role, requested, planned=planned
    )


def _validate_draft_event(event: Any) -> dict[str, Any]:
    """Validate the terminal shape of one metadata-only DRAFT event."""

    if type(event) is not dict:
        raise _schema_error("event must be a plain dict", field="event")
    actual_keys = set(event)
    if actual_keys != DRAFT_EVENT_KEYS:
        missing = sorted(DRAFT_EVENT_KEYS - actual_keys)
        unknown = sorted(actual_keys - DRAFT_EVENT_KEYS)
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if unknown:
            details.append("unknown " + ", ".join(unknown))
        raise _schema_error("; ".join(details), field="event")
    if event["event_type"] != ROLE_MODEL_LOCK_CHECK:
        raise _schema_error(
            f"must equal {ROLE_MODEL_LOCK_CHECK!r}", field="event.event_type"
        )
    if event["lifecycle_state"] != LIFECYCLE_STATE:
        raise _schema_error(
            f"must equal {LIFECYCLE_STATE!r}", field="event.lifecycle_state"
        )
    if event["host_actual"] != HOST_ACTUAL_UNVERIFIED:
        raise _schema_error(
            f"must equal {HOST_ACTUAL_UNVERIFIED!r}", field="event.host_actual"
        )
    if event["lifecycle_outcome"] != NOT_ACTIVE:
        raise _schema_error(
            f"must equal {NOT_ACTIVE!r}", field="event.lifecycle_outcome"
        )
    if event["enforcement_status"] != NOT_ACTIVE:
        raise _schema_error(
            f"must equal {NOT_ACTIVE!r}", field="event.enforcement_status"
        )
    if event["auto_action"] != "none":
        raise _schema_error("must equal 'none'", field="event.auto_action")

    data_boundary = event["data_boundary"]
    if type(data_boundary) is not dict or data_boundary != DRAFT_EVENT_BOUNDARY:
        raise _schema_error(
            "must be a plain dict equal to the DRAFT data boundary",
            field="event.data_boundary",
        )
    return event


def build_draft_diagnostic(
    *,
    task_id: str,
    run_id: str,
    canonical_role: str,
    authority: Mapping[str, Any],
    planned: Mapping[str, Any] | None,
    requested: Mapping[str, Any] | None,
    manifest_binding: Mapping[str, Any],
    packet_status: str,
    user_route_approval_ref: str,
) -> dict[str, Any]:
    """Assemble one pure, metadata-only DRAFT lock-check event.

    ``authority``, ``manifest_binding`` and ``packet_status`` are the already
    accepted values produced by the corresponding boundary helpers.  This
    assembler deliberately receives no source paths or packet/manifest raw
    objects, and therefore cannot perform I/O or accidentally expose their
    contents.  The route helper remains the single comparison authority.
    """

    task = _ensure_opaque(task_id, "task_id")
    run = _ensure_opaque(run_id, "run_id")
    role = _ensure_opaque(canonical_role, "canonical_role")
    approval_ref = _ensure_opaque(
        user_route_approval_ref, "user_route_approval_ref"
    )

    # Validate the accepted authority again at this pure boundary.  This is
    # inexpensive, keeps the event deterministic, and prevents a caller from
    # smuggling approval internals or an unverified digest into the summary.
    validated = validate_document(authority)

    if packet_status not in {MATCH, NOT_SUPPLIED}:
        raise RoleModelLockError(
            ROLE_MODEL_LOCK_PACKET_MISMATCH,
            "must be MATCH or NOT_SUPPLIED",
            field="packet_status",
        )

    # The helper result has a deliberately fixed metadata shape.  Requiring
    # that shape here means the event cannot become a carrier for a raw
    # manifest or arbitrary approval/policy payload.
    manifest_keys = _MANIFEST_BINDING_KEYS
    if not isinstance(manifest_binding, Mapping):
        raise RoleModelLockError(
            ROLE_MODEL_LOCK_CACHE_STALE,
            "manifest binding must be an object",
            field="manifest_binding",
        )
    if set(manifest_binding) != manifest_keys:
        missing = sorted(manifest_keys - set(manifest_binding))
        unknown = sorted(set(manifest_binding) - manifest_keys)
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if unknown:
            details.append("unknown " + ", ".join(unknown))
        raise RoleModelLockError(
            ROLE_MODEL_LOCK_CACHE_STALE,
            "; ".join(details),
            field="manifest_binding",
        )
    if manifest_binding["status"] != MATCH:
        raise RoleModelLockError(
            ROLE_MODEL_LOCK_CACHE_STALE,
            "must be MATCH",
            field="manifest_binding.status",
        )
    binding = dict(manifest_binding)

    # Keep route values normalized and copied.  In particular, the output
    # never retains a caller-owned mapping that could later be mutated.
    planned_route = _normalize_route(planned, "planned") if planned is not None else None
    requested_route = (
        _normalize_route(requested, "requested") if requested is not None else None
    )
    comparison = compare_requested_route(
        validated,
        role,
        requested_route,
        planned=planned_route,
    )

    # Provenance is intentionally opaque metadata only.  Keep the nested
    # route copies independent from the top-level route fields so mutating a
    # returned event cannot mutate another view of the same caller input.
    bootstrap_provenance = {
        "mode": "DRAFT_BOOTSTRAP",
        "task_run_id": run,
        "canonical_role": role,
        "approved_map_ref": "coding-team/adapters/codex/model-pool.map.md",
        "user_route_approval_ref": approval_ref,
        "planned": dict(planned_route) if planned_route is not None else None,
        "requested": dict(requested_route) if requested_route is not None else None,
        "host_actual": HOST_ACTUAL_UNVERIFIED,
        "candidate_revision": validated["revision"],
        "candidate_digest": validated["digest"],
        "enforcement_status": NOT_ACTIVE,
    }
    event = {
        "event_type": ROLE_MODEL_LOCK_CHECK,
        "task_id": task,
        "run_id": run,
        "canonical_role": role,
        "authority_revision": validated["revision"],
        "authority_digest": validated["digest"],
        "lifecycle_state": LIFECYCLE_STATE,
        "planned_route": dict(planned_route) if planned_route is not None else None,
        "requested_route": dict(requested_route) if requested_route is not None else None,
        "host_actual": HOST_ACTUAL_UNVERIFIED,
        "manifest_binding": binding,
        "packet_status": packet_status,
        "route_comparison": comparison,
        "bootstrap_provenance": bootstrap_provenance,
        "lifecycle_outcome": NOT_ACTIVE,
        "enforcement_status": NOT_ACTIVE,
        "auto_action": "none",
        "data_boundary": dict(DRAFT_EVENT_BOUNDARY),
    }
    return _validate_draft_event(event)


def validate_file(path: str | Path) -> dict[str, Any]:
    """Validate a lock file and return a diagnostic summary."""

    document = load_lock(path)
    return {
        "schema_status": "VALID",
        "digest_status": "MATCH",
        "lifecycle_state": document["lifecycle"]["state"],
        "lifecycle_outcome": "NOT_ACTIVE",
        "enforcement_status": "NOT_ACTIVE",
        "revision": document["revision"],
        "digest": document["digest"],
    }


def _error_summary(error: RoleModelLockError) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "schema_status": "INVALID",
        "digest_status": "UNVERIFIED",
        "lifecycle_outcome": "NOT_ACTIVE",
        "enforcement_status": "NOT_ACTIVE",
        "code": error.code,
        "reason": error.reason,
    }
    if error.field:
        summary["field"] = error.field
    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="read and validate one lock file")
    validate.add_argument("path", type=Path)
    validate.add_argument(
        "--json",
        action="store_true",
        help="accepted for adapter consistency; output is always JSON",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "validate":
        try:
            summary = validate_file(args.path)
        except RoleModelLockError as exc:
            summary = _error_summary(exc)
            print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
            return 1
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
