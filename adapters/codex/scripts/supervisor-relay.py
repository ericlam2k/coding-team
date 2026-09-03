#!/usr/bin/env python3
"""Artifact-first, non-authoritative supervisor relay for the Codex adapter.

The module deliberately has no collaboration, process-control, routing, or
quality-gate integration.  It persists a single-writer event chain and lets one
read-only observer publish one bounded relay for Lead.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import time
from typing import Any, Callable, Iterable, Mapping, Sequence


SCHEMA_VERSION = "1"
CONTRACT_ID = "WYSY-CODING-TEAM-SUPERVISOR-RELAY-001"
MAX_ARTIFACT_BYTES = 64 * 1024
MAX_HANDOFF_BYTES = 8 * 1024
MAX_RELAY_WORDS = 150
NONE = "NONE"

_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_GIT_ID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_DISPATCH_ID = re.compile(r"^ctd_[0-9a-f]{24}$")
_OPAQUE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_OUTCOME = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
_ABSOLUTE_PRIVATE_PATH = re.compile(
    r"(?:^|[\s'\"])(?:/Users/|/home/|/private/|[A-Za-z]:\\)"
)
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_SECRET = re.compile(
    r"\b(?:api[_-]?key|password|passwd|bearer|access[_-]?token|secret)\b\s*[:=]",
    re.I,
)
_SOURCE = re.compile(r"(?:^|\s)(?:def|class|function)\s+[A-Za-z_]\w*\s*[(:]", re.I)

_RESERVATION_FIELDS = {
    "schema_version", "contract_id", "relay_id", "task_id", "run_id",
    "attempt_id", "dispatch_id", "candidate_commit", "pic_role",
    "supervisor_role", "timing_profile_ref", "T_checkpoint", "T_hard",
    "clock_source", "start_ref", "checkpoint_ref", "terminal_ref",
    "handoff_ref", "relay_ref", "terminal_receipt_ref", "privacy",
    "public_safe", "auto_action",
}
_EVENT_BASE_FIELDS = {
    "schema_version", "contract_id", "relay_id", "task_id", "run_id",
    "attempt_id", "candidate_commit", "event", "sequence",
    "observed_monotonic_seconds", "written_at_utc", "writer_role", "status",
    "evidence_refs", "prior_event_digest", "event_digest",
}
_CHECKPOINT_FIELDS = {"completed_facts", "blocker", "next_action"}
_TERMINAL_FIELDS = {
    "outcome_class", "exit_code", "retry_allowed", "terminal_receipt_ref",
    "terminal_receipt_digest",
}
_HANDOFF_FIELDS = {
    "schema_version", "contract_id", "relay_id", "task_id", "run_id",
    "attempt_id", "candidate_commit", "writer_role", "terminal_event_digest",
    "handoff", "privacy", "public_safe",
}
_RELAY_BASE_FIELDS = {
    "schema_version", "contract_id", "relay_id", "task_id", "run_id",
    "attempt_id", "candidate_commit", "observer_role", "status", "reason",
    "execution_state", "outcome_class", "evidence_refs", "facts", "unknowns",
    "next_action", "retry_allowed", "cancellation_claim", "interruption_claim",
    "route_change", "model_change", "role_change", "quality_decision",
    "gate_advanced", "auto_action", "privacy", "public_safe",
    "emitted_monotonic_seconds", "relay_text",
}
_RELAY_TERMINAL_FIELDS = {"terminal_receipt_ref", "terminal_receipt_digest"}
_EVENT_SHAPES = {
    "START": (1, "RUNNING", _EVENT_BASE_FIELDS),
    "CHECKPOINT": (2, "CHECKPOINT", _EVENT_BASE_FIELDS | _CHECKPOINT_FIELDS),
    "TERMINAL": (3, None, _EVENT_BASE_FIELDS | _TERMINAL_FIELDS),
}


class RelayBlocked(ValueError):
    """A fail-closed relay classification with an optional artifact ref."""

    def __init__(self, reason: str, detail: str, ref: str | None = None) -> None:
        self.reason = reason
        self.detail = detail
        self.ref = ref
        super().__init__(f"{reason}: {detail}" + (f" [{ref}]" if ref else ""))


def _strict_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def derive_relay_id(
    contract_id: str,
    task_id: str,
    run_id: str,
    attempt_id: str,
    candidate_commit: str,
    terminal_receipt_ref: str,
) -> str:
    """Derive the exact immutable join key frozen by the contract."""

    joined = (
        contract_id + task_id + run_id + attempt_id + candidate_commit
        + terminal_receipt_ref
    )
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _required_string(value: Any, name: str, *, maximum: int = 500) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    if value != value.strip() or len(value) > maximum or any(ord(c) < 32 for c in value):
        raise ValueError(f"{name} is not a bounded plain string")
    return value


def _identifier(value: Any, name: str) -> str:
    result = _required_string(value, name, maximum=128)
    if not _OPAQUE_ID.fullmatch(result):
        raise ValueError(f"{name} has an invalid format")
    return result


def _repo_ref(value: Any, name: str) -> str:
    ref = _required_string(value, name, maximum=300)
    path = PurePosixPath(ref)
    if (
        path.is_absolute() or ref != path.as_posix() or ref in {".", ".."}
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError(f"{name} must be a normalized repo-relative ref")
    return ref


def _event_ref(reservation: Mapping[str, Any], event: str) -> str:
    return str(reservation[f"{event.casefold()}_ref"])


def _artifact_directory(reservation: Mapping[str, Any]) -> PurePosixPath:
    refs = [
        reservation["start_ref"], reservation["checkpoint_ref"],
        reservation["terminal_ref"], reservation["handoff_ref"],
        reservation["relay_ref"],
    ]
    parents = {PurePosixPath(str(ref)).parent for ref in refs}
    if len(parents) != 1 or next(iter(parents)) == PurePosixPath("."):
        raise ValueError("artifact refs must share one non-root reserved directory")
    return next(iter(parents))


def _privacy_scan(value: Any, name: str = "artifact") -> None:
    if isinstance(value, Mapping):
        forbidden_names = {
            "prompt", "raw_prompt", "transcript", "source", "source_content",
            "password", "secret", "api_key", "access_token", "provider_token",
            "pii", "commercial_fact",
        }
        for key, item in value.items():
            if str(key).casefold() in forbidden_names:
                raise ValueError(f"{name} contains forbidden private field {key}")
            _privacy_scan(item, f"{name}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _privacy_scan(item, f"{name}[{index}]")
    elif isinstance(value, str):
        if "\n" in value or "\r" in value:
            raise ValueError(f"{name} contains multiline content")
        if _ABSOLUTE_PRIVATE_PATH.search(value):
            raise ValueError(f"{name} contains an absolute private path")
        if _EMAIL.search(value):
            raise ValueError(f"{name} contains PII-like email content")
        if _SECRET.search(value):
            raise ValueError(f"{name} contains secret-like content")
        if _SOURCE.search(value):
            raise ValueError(f"{name} contains source-like content")
        if "raw prompt" in value.casefold() or "transcript:" in value.casefold():
            raise ValueError(f"{name} contains prompt or transcript content")


def validate_reservation(value: Any) -> dict[str, Any]:
    """Validate one exact, privacy-bounded Lead reservation."""

    if not isinstance(value, dict) or set(value) != _RESERVATION_FIELDS:
        raise ValueError("reservation has an invalid exact schema")
    if value["schema_version"] != SCHEMA_VERSION or value["contract_id"] != CONTRACT_ID:
        raise ValueError("reservation contract identity is invalid")
    for name in ("task_id", "run_id", "attempt_id", "dispatch_id", "pic_role"):
        _identifier(value[name], name)
    if not _DISPATCH_ID.fullmatch(value["dispatch_id"]):
        raise ValueError("dispatch_id must come from prepare-dispatch.py")
    if value["supervisor_role"] != "monitor-agent":
        raise ValueError("supervisor_role must be the canonical monitor-agent role")
    commit = _required_string(value["candidate_commit"], "candidate_commit")
    if not _GIT_ID.fullmatch(commit):
        raise ValueError("candidate_commit must be a lowercase Git object ID")
    _repo_ref(value["timing_profile_ref"], "timing_profile_ref")
    checkpoint = value["T_checkpoint"]
    hard = value["T_hard"]
    if isinstance(checkpoint, bool) or not isinstance(checkpoint, (int, float)) or checkpoint < 0:
        raise ValueError("T_checkpoint must be a non-negative monotonic time")
    if isinstance(hard, bool) or not isinstance(hard, (int, float)) or hard <= checkpoint:
        raise ValueError("T_hard must be greater than T_checkpoint")
    if value["clock_source"] not in {"time.monotonic", "CLOCK_MONOTONIC"}:
        raise ValueError("clock_source must name a monotonic clock")

    artifact_refs = []
    for name in ("start_ref", "checkpoint_ref", "terminal_ref", "handoff_ref", "relay_ref"):
        artifact_refs.append(_repo_ref(value[name], name))
    directory = _artifact_directory(value)
    if len(set(artifact_refs)) != len(artifact_refs):
        raise ValueError("artifact refs must be unique")
    receipt_ref = value["terminal_receipt_ref"]
    if receipt_ref != NONE:
        receipt_ref = _repo_ref(receipt_ref, "terminal_receipt_ref")
        if PurePosixPath(receipt_ref).parent != directory or receipt_ref in artifact_refs:
            raise ValueError("terminal_receipt_ref must be unique under the reserved directory")
    if value["privacy"] != "LOCAL_ONLY" or value["public_safe"] is not False:
        raise ValueError("reservation must remain LOCAL_ONLY and not public safe")
    if value["auto_action"] != "none":
        raise ValueError("reservation auto_action must be none")
    expected = derive_relay_id(
        CONTRACT_ID, value["task_id"], value["run_id"], value["attempt_id"],
        commit, receipt_ref,
    )
    if value["relay_id"] != expected:
        raise ValueError("relay_id does not match immutable reservation identity")
    _privacy_scan(value)
    return dict(value)


def make_reservation(
    *, task_id: str, run_id: str, attempt_id: str, dispatch_id: str,
    candidate_commit: str, pic_role: str, timing_profile_ref: str,
    T_checkpoint: float, T_hard: float, artifact_directory: str,
    terminal_receipt_name: str | None = None,
) -> dict[str, Any]:
    """Build, but do not persist, one exact Lead reservation."""

    directory = _repo_ref(artifact_directory, "artifact_directory")
    receipt_ref = (
        f"{directory}/{terminal_receipt_name}" if terminal_receipt_name else NONE
    )
    reservation: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "relay_id": derive_relay_id(
            CONTRACT_ID, task_id, run_id, attempt_id, candidate_commit, receipt_ref
        ),
        "task_id": task_id, "run_id": run_id, "attempt_id": attempt_id,
        "dispatch_id": dispatch_id, "candidate_commit": candidate_commit,
        "pic_role": pic_role, "supervisor_role": "monitor-agent",
        "timing_profile_ref": timing_profile_ref, "T_checkpoint": T_checkpoint,
        "T_hard": T_hard, "clock_source": "time.monotonic",
        "start_ref": f"{directory}/start.json",
        "checkpoint_ref": f"{directory}/checkpoint.json",
        "terminal_ref": f"{directory}/terminal.json",
        "handoff_ref": f"{directory}/handoff.json",
        "relay_ref": f"{directory}/relay.json",
        "terminal_receipt_ref": receipt_ref,
        "privacy": "LOCAL_ONLY", "public_safe": False, "auto_action": "none",
    }
    return validate_reservation(reservation)


def _open_parent_directory(path: Path, *, create: bool) -> tuple[int, str]:
    """Open every ancestor without following links and return the parent dirfd."""

    absolute = Path(os.path.abspath(os.fspath(path)))
    if not absolute.is_absolute() or not absolute.name or "\x00" in os.fspath(path):
        raise ValueError("artifact path is invalid")
    directory_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_DIRECTORY"):
        directory_flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW
    current_fd = os.open(absolute.anchor, directory_flags)
    try:
        for component in absolute.parent.parts[1:]:
            try:
                before = os.stat(component, dir_fd=current_fd, follow_symlinks=False)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(component, 0o700, dir_fd=current_fd)
                except FileExistsError:
                    pass
                before = os.stat(component, dir_fd=current_fd, follow_symlinks=False)
            if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
                raise ValueError(
                    "artifact ancestor is not a regular non-symlink directory"
                )
            next_fd = os.open(component, directory_flags, dir_fd=current_fd)
            opened = os.fstat(next_fd)
            if (
                not stat.S_ISDIR(opened.st_mode)
                or (before.st_dev, before.st_ino)
                != (opened.st_dev, opened.st_ino)
            ):
                os.close(next_fd)
                raise ValueError(
                    "artifact ancestor changed during no-follow traversal"
                )
            os.close(current_fd)
            current_fd = next_fd
        return current_fd, absolute.name
    except Exception:
        os.close(current_fd)
        raise


def _atomic_create(path: Path, value: Mapping[str, Any], *, collision_reason: str) -> None:
    document = _canonical(value) + b"\n"
    if len(document) > MAX_ARTIFACT_BYTES:
        raise RelayBlocked("ARTIFACT_INVALID", "artifact exceeds the size bound")
    try:
        directory_fd, destination = _open_parent_directory(path, create=True)
    except (OSError, ValueError) as error:
        raise RelayBlocked(collision_reason, str(error)) from error
    try:
        os.stat(destination, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        pass
    else:
        os.close(directory_fd)
        raise RelayBlocked(
            collision_reason, "create-once destination already exists"
        )

    temporary = f".{destination}.{os.getpid()}.{time.time_ns()}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = -1
    try:
        fd = os.open(temporary, flags, 0o600, dir_fd=directory_fd)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            fd = -1
            handle.write(document)
            handle.flush()
            os.fsync(handle.fileno())
        # Both names are bound to the verified directory handle.
        os.link(
            temporary,
            destination,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
            follow_symlinks=False,
        )
        os.fsync(directory_fd)
    except FileExistsError as error:
        raise RelayBlocked(
            collision_reason, "create-once destination collision"
        ) from error
    finally:
        if fd >= 0:
            os.close(fd)
        try:
            os.unlink(temporary, dir_fd=directory_fd)
        except FileNotFoundError:
            pass
        os.close(directory_fd)


def _validate_reservation_location(path: Path, reservation: Mapping[str, Any]) -> None:
    directory_parts = _artifact_directory(reservation).parts
    if len(path.parent.parts) < len(directory_parts) or path.parent.parts[-len(directory_parts):] != directory_parts:
        raise ValueError("reservation location does not match its reserved directory refs")


def reserve(reservation_path: str | os.PathLike[str], value: Mapping[str, Any]) -> dict[str, Any]:
    """Lead-only create-once reservation publication."""

    path = Path(reservation_path)
    if path.name != "reservation.json":
        raise RelayBlocked("IDENTITY_INVALID", "reservation filename must be reservation.json")
    validated = validate_reservation(dict(value))
    try:
        _validate_reservation_location(path, validated)
    except ValueError as error:
        raise RelayBlocked("IDENTITY_INVALID", str(error)) from error
    _atomic_create(path, validated, collision_reason="IDENTITY_INVALID")
    return validated


def _secure_read(path: Path, *, maximum: int = MAX_ARTIFACT_BYTES) -> bytes:
    try:
        directory_fd, name = _open_parent_directory(path, create=False)
    except FileNotFoundError as error:
        raise FileNotFoundError("artifact does not exist") from error
    try:
        before = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError as error:
        os.close(directory_fd)
        raise FileNotFoundError("artifact does not exist") from error
    if not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode):
        os.close(directory_fd)
        raise ValueError("artifact is not a regular non-symlink file")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(name, flags, dir_fd=directory_fd)
    except OSError:
        os.close(directory_fd)
        raise
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise ValueError("artifact changed before open")
        if opened.st_size <= 0 or opened.st_size > maximum:
            raise ValueError("artifact size is outside the allowed bound")
        chunks: list[bytes] = []
        remaining = maximum + 1
        while remaining:
            chunk = os.read(fd, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        document = b"".join(chunks)
        after = os.fstat(fd)
        if len(document) != opened.st_size or (after.st_size, after.st_mtime_ns) != (opened.st_size, opened.st_mtime_ns):
            raise ValueError("artifact changed while being read")
        return document
    finally:
        os.close(fd)
        os.close(directory_fd)


def _read_json(path: Path, *, maximum: int = MAX_ARTIFACT_BYTES) -> dict[str, Any]:
    document = _secure_read(path, maximum=maximum)
    try:
        value = json.loads(document.decode("utf-8"), object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError("artifact is not strict UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ValueError("artifact JSON must be an object")
    return value


def load_reservation(reservation_path: str | os.PathLike[str]) -> dict[str, Any]:
    try:
        path = Path(reservation_path)
        reservation = validate_reservation(_read_json(path))
        _validate_reservation_location(path, reservation)
        return reservation
    except (FileNotFoundError, OSError, ValueError) as error:
        raise RelayBlocked("IDENTITY_INVALID", str(error)) from error


def _local_artifact_path(reservation_path: Path, ref: str) -> Path:
    reservation = load_reservation(reservation_path)
    directory = _artifact_directory(reservation)
    parsed = PurePosixPath(ref)
    if parsed.parent != directory:
        raise RelayBlocked("ARTIFACT_INVALID", "ref escapes the reserved directory", ref)
    target = reservation_path.parent / parsed.name
    if target.parent != reservation_path.parent:
        raise RelayBlocked("ARTIFACT_INVALID", "ref resolves outside reservation directory", ref)
    return target


def _identity_fields(reservation: Mapping[str, Any]) -> dict[str, Any]:
    return {name: reservation[name] for name in (
        "schema_version", "contract_id", "relay_id", "task_id", "run_id",
        "attempt_id", "candidate_commit",
    )}


def _validate_text_list(value: Any, name: str, *, maximum_items: int = 16) -> list[str]:
    if not isinstance(value, list) or len(value) > maximum_items:
        raise ValueError(f"{name} must be a bounded array")
    result = [_required_string(item, f"{name} item", maximum=240) for item in value]
    if len(set(result)) != len(result):
        raise ValueError(f"{name} must not contain duplicates")
    _privacy_scan(result, name)
    return result


def validate_event(value: Any, reservation: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("event") not in _EVENT_SHAPES:
        raise ValueError("event has an invalid type")
    sequence, required_status, fields = _EVENT_SHAPES[value["event"]]
    if set(value) != fields:
        raise ValueError("event has an invalid exact schema")
    for name, expected in _identity_fields(reservation).items():
        if value[name] != expected:
            raise ValueError(f"event {name} does not match reservation")
    if value["sequence"] != sequence:
        raise ValueError("event sequence is invalid")
    if value["writer_role"] != reservation["pic_role"]:
        raise ValueError("event writer_role is not the reserved PIC")
    if required_status is not None and value["status"] != required_status:
        raise ValueError("event status is invalid")
    if value["event"] == "TERMINAL" and value["status"] not in {"COMPLETED", "FAILED", "BLOCKED"}:
        raise ValueError("terminal status is invalid")
    observed = value["observed_monotonic_seconds"]
    if isinstance(observed, bool) or not isinstance(observed, (int, float)) or observed < 0:
        raise ValueError("observed monotonic time is invalid")
    if observed > reservation["T_hard"]:
        raise ValueError("event is later than the reserved hard bound")
    if not isinstance(value["written_at_utc"], str) or not _UTC.fullmatch(value["written_at_utc"]):
        raise ValueError("written_at_utc is invalid")
    refs = _validate_text_list(value["evidence_refs"], "evidence_refs")
    for ref in refs:
        _repo_ref(ref, "evidence_ref")
    if value["event"] == "START":
        if value["prior_event_digest"] != NONE:
            raise ValueError("START prior_event_digest must be NONE")
    elif not _HEX_64.fullmatch(str(value["prior_event_digest"])):
        raise ValueError("prior_event_digest must be SHA-256")
    if value["event"] == "CHECKPOINT":
        if observed > reservation["T_checkpoint"]:
            raise ValueError("checkpoint is later than T_checkpoint")
        _validate_text_list(value["completed_facts"], "completed_facts", maximum_items=12)
        blocker = value["blocker"]
        if blocker is not None:
            _required_string(blocker, "blocker", maximum=240)
            _privacy_scan(blocker, "blocker")
        _required_string(value["next_action"], "next_action", maximum=240)
        _privacy_scan(value["next_action"], "next_action")
    if value["event"] == "TERMINAL":
        if not _OUTCOME.fullmatch(str(value["outcome_class"])):
            raise ValueError("terminal outcome_class is invalid")
        if type(value["exit_code"]) is not int:
            raise ValueError("terminal exit_code must be an integer")
        if value["retry_allowed"] is not False:
            raise ValueError("terminal retry_allowed must be false")
        receipt_ref = value["terminal_receipt_ref"]
        receipt_digest = value["terminal_receipt_digest"]
        if receipt_ref != reservation["terminal_receipt_ref"]:
            raise ValueError("terminal receipt ref does not match reservation")
        if receipt_ref == NONE:
            if receipt_digest != NONE:
                raise ValueError("non-critical terminal receipt digest must be NONE")
        elif not _HEX_64.fullmatch(str(receipt_digest)):
            raise ValueError("terminal receipt digest must be SHA-256")
    claimed = value["event_digest"]
    without_digest = {key: item for key, item in value.items() if key != "event_digest"}
    if not isinstance(claimed, str) or claimed != _digest(without_digest):
        raise ValueError("event_digest does not match event content")
    _privacy_scan(value)
    return dict(value)


def _read_event(reservation_path: Path, event: str, *, required: bool = True) -> dict[str, Any] | None:
    reservation = load_reservation(reservation_path)
    ref = _event_ref(reservation, event)
    path = _local_artifact_path(reservation_path, ref)
    try:
        return validate_event(_read_json(path), reservation)
    except FileNotFoundError as error:
        if required:
            raise RelayBlocked(
                "ARTIFACT_INVALID", f"{event} artifact is missing", ref
            ) from error
        return None
    except (OSError, ValueError) as error:
        raise RelayBlocked("ARTIFACT_INVALID", str(error), ref) from error


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def publish_pic_event(
    reservation_path: str | os.PathLike[str], event: str, *,
    observed_monotonic_seconds: float, evidence_refs: Iterable[str] = (),
    written_at_utc: str | None = None, completed_facts: Iterable[str] = (),
    blocker: str | None = None, next_action: str | None = None,
    status: str | None = None, outcome_class: str | None = None,
    exit_code: int | None = None, terminal_receipt_digest: str | None = None,
) -> dict[str, Any]:
    """PIC-only atomic publication of START, CHECKPOINT, or TERMINAL."""

    reservation_file = Path(reservation_path)
    reservation = load_reservation(reservation_file)
    if event not in _EVENT_SHAPES:
        raise RelayBlocked("ARTIFACT_INVALID", "unknown event type")
    sequence, default_status, _ = _EVENT_SHAPES[event]
    prior = NONE
    if event == "CHECKPOINT":
        prior = _read_event(reservation_file, "START")["event_digest"]
    elif event == "TERMINAL":
        prior = _read_event(reservation_file, "CHECKPOINT")["event_digest"]
    value: dict[str, Any] = {
        **_identity_fields(reservation), "event": event, "sequence": sequence,
        "observed_monotonic_seconds": observed_monotonic_seconds,
        "written_at_utc": written_at_utc or _utc_now(),
        "writer_role": reservation["pic_role"],
        "status": status or default_status,
        "evidence_refs": list(evidence_refs), "prior_event_digest": prior,
    }
    if event == "CHECKPOINT":
        value.update(
            completed_facts=list(completed_facts), blocker=blocker,
            next_action=next_action,
        )
    elif event == "TERMINAL":
        value.update(
            outcome_class=outcome_class, exit_code=exit_code,
            retry_allowed=False,
            terminal_receipt_ref=reservation["terminal_receipt_ref"],
            terminal_receipt_digest=(
                NONE if reservation["terminal_receipt_ref"] == NONE
                else terminal_receipt_digest
            ),
        )
    value["event_digest"] = _digest(value)
    try:
        validated = validate_event(value, reservation)
    except ValueError as error:
        raise RelayBlocked("ARTIFACT_INVALID", str(error), _event_ref(reservation, event)) from error
    target = _local_artifact_path(reservation_file, _event_ref(reservation, event))
    _atomic_create(target, validated, collision_reason="ARTIFACT_INVALID")
    return validated


def validate_handoff(value: Any, reservation: Mapping[str, Any], terminal: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _HANDOFF_FIELDS:
        raise ValueError("handoff has an invalid exact schema")
    for name, expected in _identity_fields(reservation).items():
        if value[name] != expected:
            raise ValueError(f"handoff {name} does not match reservation")
    if value["writer_role"] != reservation["pic_role"]:
        raise ValueError("handoff writer_role is not the reserved PIC")
    if value["terminal_event_digest"] != terminal["event_digest"]:
        raise ValueError("handoff is not bound to the terminal digest")
    handoff = _required_string(value["handoff"], "handoff", maximum=4000)
    if len(handoff.split()) > MAX_RELAY_WORDS:
        raise ValueError("handoff exceeds 150 words")
    if value["privacy"] != "LOCAL_ONLY" or value["public_safe"] is not False:
        raise ValueError("handoff privacy boundary is invalid")
    _privacy_scan(value)
    return dict(value)


def publish_pic_handoff(reservation_path: str | os.PathLike[str], handoff: str) -> dict[str, Any]:
    reservation_file = Path(reservation_path)
    reservation = load_reservation(reservation_file)
    terminal = _read_event(reservation_file, "TERMINAL")
    value = {
        **_identity_fields(reservation), "writer_role": reservation["pic_role"],
        "terminal_event_digest": terminal["event_digest"], "handoff": handoff,
        "privacy": "LOCAL_ONLY", "public_safe": False,
    }
    try:
        validated = validate_handoff(value, reservation, terminal)
    except ValueError as error:
        raise RelayBlocked("HANDOFF_MISSING", str(error), reservation["handoff_ref"]) from error
    target = _local_artifact_path(reservation_file, reservation["handoff_ref"])
    _atomic_create(target, validated, collision_reason="ARTIFACT_INVALID")
    return validated


def _validate_chain(start: Mapping[str, Any], checkpoint: Mapping[str, Any], terminal: Mapping[str, Any]) -> None:
    if checkpoint["prior_event_digest"] != start["event_digest"]:
        raise RelayBlocked("ARTIFACT_INVALID", "checkpoint digest chain is broken")
    if terminal["prior_event_digest"] != checkpoint["event_digest"]:
        raise RelayBlocked("ARTIFACT_INVALID", "terminal digest chain is broken")
    times = [item["observed_monotonic_seconds"] for item in (start, checkpoint, terminal)]
    if times != sorted(times):
        raise RelayBlocked("ARTIFACT_INVALID", "event monotonic order is invalid")


def _validate_partial_chain(start: Mapping[str, Any], checkpoint: Mapping[str, Any]) -> None:
    if checkpoint["prior_event_digest"] != start["event_digest"]:
        raise RelayBlocked("ARTIFACT_INVALID", "checkpoint digest chain is broken")
    if checkpoint["observed_monotonic_seconds"] < start["observed_monotonic_seconds"]:
        raise RelayBlocked("ARTIFACT_INVALID", "checkpoint precedes START monotonic time")


def _validate_critical_receipt(
    reservation_path: Path, reservation: Mapping[str, Any], terminal: Mapping[str, Any]
) -> None:
    ref = reservation["terminal_receipt_ref"]
    if ref == NONE:
        return
    path = _local_artifact_path(reservation_path, ref)
    try:
        raw = _secure_read(path)
        receipt = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_object)
        if not isinstance(receipt, dict):
            raise ValueError("terminal receipt must be an object")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise RelayBlocked("RECEIPT_MISMATCH", str(error), ref) from error
    if hashlib.sha256(raw).hexdigest() != terminal["terminal_receipt_digest"]:
        raise RelayBlocked("RECEIPT_MISMATCH", "terminal receipt digest differs", ref)
    for name in ("task_id", "run_id"):
        if receipt.get(name) != reservation[name]:
            raise RelayBlocked("RECEIPT_MISMATCH", f"receipt {name} differs", ref)
    for name in ("attempt_id", "candidate_commit"):
        if name in receipt and receipt[name] != reservation[name]:
            raise RelayBlocked("RECEIPT_MISMATCH", f"receipt {name} differs", ref)
    projected = {
        "status": terminal["status"], "outcome_class": terminal["outcome_class"],
        "exit_code": terminal["exit_code"], "retry_allowed": False,
    }
    if any(receipt.get(name) != expected for name, expected in projected.items()):
        raise RelayBlocked("RECEIPT_MISMATCH", "terminal does not exactly project receipt outcome", ref)
    if receipt.get("privacy") != "LOCAL_ONLY" or receipt.get("public_safe") is not False:
        raise RelayBlocked("RECEIPT_MISMATCH", "receipt privacy boundary differs", ref)


def _relay_document(
    reservation: Mapping[str, Any], *, status: str, reason: str,
    execution_state: str, outcome_class: str | None, evidence_refs: list[str],
    facts: list[str], unknowns: list[str], now: float,
) -> dict[str, Any]:
    next_action = "Lead inspects this relay and chooses the governed next route."
    text = " ".join(facts + [f"Unknown: {item}" for item in unknowns] + [next_action])
    if len(text.split()) > MAX_RELAY_WORDS:
        raise RelayBlocked("ARTIFACT_INVALID", "relay exceeds 150 words")
    return {
        **_identity_fields(reservation), "observer_role": reservation["supervisor_role"],
        "status": status, "reason": reason, "execution_state": execution_state,
        "outcome_class": outcome_class, "evidence_refs": evidence_refs,
        "facts": facts, "unknowns": unknowns, "next_action": next_action,
        "retry_allowed": False, "cancellation_claim": False,
        "interruption_claim": False, "route_change": False, "model_change": False,
        "role_change": False, "quality_decision": "NONE", "gate_advanced": False,
        "auto_action": "none", "privacy": "LOCAL_ONLY", "public_safe": False,
        "emitted_monotonic_seconds": now, "relay_text": text,
    }


def _publish_relay(reservation_path: Path, reservation: Mapping[str, Any], relay: dict[str, Any]) -> dict[str, Any]:
    _privacy_scan(relay)
    target = _local_artifact_path(reservation_path, reservation["relay_ref"])
    _atomic_create(target, relay, collision_reason="ARTIFACT_INVALID")
    return relay


def validate_relay(value: Any, reservation: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the supervisor's non-authoritative relay before Lead consumes it."""

    if not isinstance(value, dict) or frozenset(value) not in {
        frozenset(_RELAY_BASE_FIELDS),
        frozenset(_RELAY_BASE_FIELDS | _RELAY_TERMINAL_FIELDS),
    }:
        raise ValueError("relay has an invalid exact schema")
    for name, expected in _identity_fields(reservation).items():
        if value[name] != expected:
            raise ValueError(f"relay {name} does not match reservation")
    if value["observer_role"] != reservation["supervisor_role"]:
        raise ValueError("relay observer_role does not match reservation")
    if value["status"] not in {"COMPLETED", "FAILED", "BLOCKED"}:
        raise ValueError("relay status is invalid")
    if value["execution_state"] not in {"TERMINAL", "UNKNOWN"}:
        raise ValueError("relay execution_state is invalid")
    for name in (
        "retry_allowed", "cancellation_claim", "interruption_claim", "route_change",
        "model_change", "role_change", "gate_advanced",
    ):
        if value[name] is not False:
            raise ValueError(f"relay {name} exceeds observer authority")
    if value["quality_decision"] != NONE or value["auto_action"] != "none":
        raise ValueError("relay contains a quality decision or automatic action")
    if value["privacy"] != "LOCAL_ONLY" or value["public_safe"] is not False:
        raise ValueError("relay privacy boundary is invalid")
    relay_refs = _validate_text_list(value["evidence_refs"], "relay evidence_refs")
    for ref in relay_refs:
        _repo_ref(ref, "relay evidence_ref")
    _validate_text_list(value["facts"], "relay facts")
    _validate_text_list(value["unknowns"], "relay unknowns")
    if value["next_action"] != "Lead inspects this relay and chooses the governed next route.":
        raise ValueError("relay next action exceeds observer authority")
    text = _required_string(value["relay_text"], "relay_text", maximum=4000)
    if len(text.split()) > MAX_RELAY_WORDS:
        raise ValueError("relay exceeds 150 words")
    emitted = value["emitted_monotonic_seconds"]
    if isinstance(emitted, bool) or not isinstance(emitted, (int, float)) or emitted < 0:
        raise ValueError("relay monotonic time is invalid")
    terminal_shape = set(value) == (_RELAY_BASE_FIELDS | _RELAY_TERMINAL_FIELDS)
    if value["execution_state"] == "TERMINAL":
        if not terminal_shape or not _OUTCOME.fullmatch(str(value["outcome_class"])):
            raise ValueError("terminal relay must preserve terminal outcome fields")
    elif terminal_shape or value["outcome_class"] is not None:
        raise ValueError("unknown-state relay must not claim a terminal outcome")
    if terminal_shape:
        if value["execution_state"] != "TERMINAL":
            raise ValueError("only a terminal relay may carry terminal receipt fields")
        if value["terminal_receipt_ref"] != reservation["terminal_receipt_ref"]:
            raise ValueError("relay terminal receipt ref differs")
        digest = value["terminal_receipt_digest"]
        if reservation["terminal_receipt_ref"] == NONE:
            if digest != NONE:
                raise ValueError("non-critical relay receipt digest must be NONE")
        elif not _HEX_64.fullmatch(str(digest)):
            raise ValueError("relay terminal receipt digest is invalid")
    _privacy_scan(value)
    return dict(value)


def _blocked_relay(
    reservation_path: Path, reservation: Mapping[str, Any], reason: str,
    detail: str, ref: str | None, now: float, *, defects: Iterable[str] = (),
) -> dict[str, Any]:
    facts = [f"Relay stopped: {reason}."]
    if detail:
        facts.append(f"Evidence defect: {detail[:240]}.")
    unknowns = ["PIC and host execution state remain UNKNOWN."]
    if defects:
        unknowns.append("Pending defects: " + ", ".join(defects) + ".")
    return _publish_relay(
        reservation_path, reservation,
        _relay_document(
            reservation, status="BLOCKED", reason=reason,
            execution_state="UNKNOWN", outcome_class=None,
            evidence_refs=[ref] if ref else [], facts=facts, unknowns=unknowns, now=now,
        ),
    )


def observe_and_relay(
    reservation_path: str | os.PathLike[str], *, poll_seconds: float = 0.05,
    monotonic: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Observe declared artifacts only and create exactly one relay output."""

    if poll_seconds <= 0 or poll_seconds > 5:
        raise ValueError("poll_seconds must be within (0, 5]")
    reservation_file = Path(reservation_path)
    reservation = load_reservation(reservation_file)
    now = monotonic()
    try:
        start = _read_event(reservation_file, "START", required=False)
    except RelayBlocked as error:
        return _blocked_relay(
            reservation_file, reservation, error.reason, error.detail, error.ref, now,
        )
    if start is None:
        return _blocked_relay(
            reservation_file, reservation, "START_NOT_OBSERVED",
            "START artifact was absent at admitted observation", reservation["start_ref"], now,
        )

    defects: list[str] = []
    while True:
        now = monotonic()
        if now > reservation["T_hard"]:
            return _blocked_relay(
                reservation_file, reservation, "RELAY_TIMEOUT",
                "observation resumed after T_hard", reservation["terminal_ref"],
                now, defects=defects,
            )
        try:
            start = _read_event(reservation_file, "START")
            checkpoint = _read_event(reservation_file, "CHECKPOINT", required=False)
            terminal = _read_event(reservation_file, "TERMINAL", required=False)
            if start["observed_monotonic_seconds"] > now:
                raise RelayBlocked("ARTIFACT_INVALID", "START claims a future monotonic time", reservation["start_ref"])
            if checkpoint is not None:
                _validate_partial_chain(start, checkpoint)
                if checkpoint["observed_monotonic_seconds"] > now:
                    raise RelayBlocked("ARTIFACT_INVALID", "CHECKPOINT claims a future monotonic time", reservation["checkpoint_ref"])
            if checkpoint is None and now >= reservation["T_checkpoint"] and "CHECKPOINT_MISSING" not in defects:
                defects.append("CHECKPOINT_MISSING")
            if terminal is not None:
                if checkpoint is None:
                    raise RelayBlocked("ARTIFACT_INVALID", "TERMINAL exists before CHECKPOINT", reservation["terminal_ref"])
                _validate_chain(start, checkpoint, terminal)
                if terminal["observed_monotonic_seconds"] > now:
                    raise RelayBlocked("ARTIFACT_INVALID", "TERMINAL claims a future monotonic time", reservation["terminal_ref"])
                _validate_critical_receipt(reservation_file, reservation, terminal)
                handoff_path = _local_artifact_path(reservation_file, reservation["handoff_ref"])
                try:
                    handoff = validate_handoff(_read_json(handoff_path, maximum=MAX_HANDOFF_BYTES), reservation, terminal)
                except FileNotFoundError:
                    return _blocked_relay(
                        reservation_file, reservation, "HANDOFF_MISSING",
                        "valid terminal has no bound handoff",
                        reservation["handoff_ref"], now,
                    )
                except (OSError, ValueError) as error:
                    return _blocked_relay(
                        reservation_file, reservation, "HANDOFF_MISSING", str(error),
                        reservation["handoff_ref"], now,
                    )
                if defects:
                    return _blocked_relay(
                        reservation_file, reservation, "ARTIFACT_INVALID",
                        "terminal chain completed after a required checkpoint defect",
                        reservation["checkpoint_ref"], now, defects=defects,
                    )
                relay = _relay_document(
                    reservation, status=terminal["status"], reason="TERMINAL_OBSERVED",
                    execution_state="TERMINAL", outcome_class=terminal["outcome_class"],
                    evidence_refs=[reservation["start_ref"], reservation["checkpoint_ref"],
                                   reservation["terminal_ref"], reservation["handoff_ref"]],
                    facts=["The complete PIC event digest chain is valid.",
                           "The PIC handoff is bound to the terminal digest."],
                    unknowns=["Host-native sibling state and cancellation are not observed."],
                    now=now,
                )
                relay["terminal_receipt_ref"] = terminal["terminal_receipt_ref"]
                relay["terminal_receipt_digest"] = terminal["terminal_receipt_digest"]
                return _publish_relay(reservation_file, reservation, relay)
        except RelayBlocked as error:
            return _blocked_relay(
                reservation_file, reservation, error.reason, error.detail, error.ref, now,
                defects=defects,
            )
        if now >= reservation["T_hard"]:
            return _blocked_relay(
                reservation_file, reservation, "RELAY_TIMEOUT",
                "no valid terminal was observed by T_hard", reservation["terminal_ref"],
                now, defects=defects,
            )
        sleeper(min(poll_seconds, max(0.0, reservation["T_hard"] - now)))


def lead_check_relay(reservation_path: str | os.PathLike[str]) -> dict[str, Any]:
    """Lead's bounded check when the observer emitted no relay artifact."""

    reservation_file = Path(reservation_path)
    reservation = load_reservation(reservation_file)
    relay_path = _local_artifact_path(reservation_file, reservation["relay_ref"])
    try:
        relay = _read_json(relay_path)
    except FileNotFoundError:
        return {
            **_identity_fields(reservation), "status": "BLOCKED",
            "reason": "SUPERVISOR_UNAVAILABLE", "execution_state": "UNKNOWN",
            "retry_allowed": False, "replacement_supervisor": False,
            "gate_advanced": False, "auto_action": "none",
            "privacy": "LOCAL_ONLY", "public_safe": False,
        }
    except (OSError, ValueError) as error:
        return {
            **_identity_fields(reservation), "status": "BLOCKED",
            "reason": "ARTIFACT_INVALID", "execution_state": "UNKNOWN",
            "detail": str(error), "retry_allowed": False,
            "replacement_supervisor": False, "gate_advanced": False,
            "auto_action": "none", "privacy": "LOCAL_ONLY", "public_safe": False,
        }
    try:
        return validate_relay(relay, reservation)
    except ValueError as error:
        return {
            **_identity_fields(reservation), "status": "BLOCKED",
            "reason": "ARTIFACT_INVALID", "execution_state": "UNKNOWN",
            "detail": str(error), "retry_allowed": False,
            "replacement_supervisor": False, "gate_advanced": False,
            "auto_action": "none", "privacy": "LOCAL_ONLY", "public_safe": False,
        }


def validate_wip(
    ordinary_tool_using_wip: int, read_only_supervisor_wip: int, *,
    supervised_attempts: int = 1, supervisor_mutates: bool = False,
    recursive_supervision: bool = False, active_quality_roles: Iterable[str] = (),
) -> dict[str, int]:
    """Apply the typed 2 ordinary + optional 1 read-only supervisor limit."""

    counts = (ordinary_tool_using_wip, read_only_supervisor_wip, supervised_attempts)
    if any(type(count) is not int or count < 0 for count in counts):
        raise RelayBlocked("WIP_INVALID", "WIP counts must be non-negative integers")
    if ordinary_tool_using_wip > 2:
        raise RelayBlocked("WIP_INVALID", "a third ordinary tool-using lane is forbidden")
    if read_only_supervisor_wip > 1:
        raise RelayBlocked("WIP_INVALID", "multiple supervisor lanes are forbidden")
    if read_only_supervisor_wip and supervised_attempts != 1:
        raise RelayBlocked("WIP_INVALID", "the supervisor must observe exactly one attempt")
    if read_only_supervisor_wip and (supervisor_mutates or recursive_supervision):
        raise RelayBlocked("WIP_INVALID", "the extra lane must remain read-only and non-recursive")
    roles = list(active_quality_roles)
    allowed = {"code-reviewer", "test-engineer", "gatekeeper"}
    if any(role not in allowed for role in roles) or len(roles) > 1:
        raise RelayBlocked("WIP_INVALID", "quality roles must remain canonical and serial")
    if read_only_supervisor_wip and roles:
        raise RelayBlocked("WIP_INVALID", "supervisor must end before quality review begins")
    total = ordinary_tool_using_wip + read_only_supervisor_wip
    if total > 3 or (total == 3 and read_only_supervisor_wip != 1):
        raise RelayBlocked("WIP_INVALID", "total WIP 3 is allowed only for the supervisor lane")
    return {
        "ordinary_tool_using_wip": ordinary_tool_using_wip,
        "read_only_supervisor_wip": read_only_supervisor_wip,
        "total_tool_using_wip": total,
    }


def validate_quality_sequence(sequence: Iterable[str]) -> tuple[str, ...]:
    """Preserve Reviewer -> optional TE -> Gatekeeper sequencing."""

    result = tuple(sequence)
    if result not in {
        (), ("code-reviewer",), ("code-reviewer", "gatekeeper"),
        ("code-reviewer", "test-engineer"),
        ("code-reviewer", "test-engineer", "gatekeeper"),
    }:
        raise RelayBlocked("WIP_INVALID", "quality sequence is not governed serial order")
    return result


# Short aliases expose the contract vocabulary without duplicating behavior.
create_reservation = reserve
write_event = publish_pic_event
write_handoff = publish_pic_handoff
observe = observe_and_relay
check_wip = validate_wip


def _load_input(path: Path) -> dict[str, Any]:
    return _read_json(path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Artifact-first supervisor relay")
    subparsers = parser.add_subparsers(dest="command", required=True)
    reserve_parser = subparsers.add_parser("reserve")
    reserve_parser.add_argument("reservation", type=Path)
    reserve_parser.add_argument("input", type=Path)
    observe_parser = subparsers.add_parser("observe")
    observe_parser.add_argument("reservation", type=Path)
    observe_parser.add_argument("--poll-seconds", type=float, default=0.05)
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("reservation", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "reserve":
            result = reserve(args.reservation, _load_input(args.input))
        elif args.command == "observe":
            result = observe_and_relay(args.reservation, poll_seconds=args.poll_seconds)
        else:
            result = lead_check_relay(args.reservation)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result.get("status") not in {"BLOCKED", "FAILED"} else 2
    except (OSError, ValueError, RelayBlocked) as error:
        reason = error.reason if isinstance(error, RelayBlocked) else "IDENTITY_INVALID"
        print(json.dumps({"status": "BLOCKED", "reason": reason, "error": str(error),
                          "retry_allowed": False, "auto_action": "none"}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
