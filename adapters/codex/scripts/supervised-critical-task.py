"""Preflight, terminal classification, and the isolated internal worker."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from enum import Enum
from types import ModuleType
from typing import Iterable, Sequence


def _import_watchdog() -> ModuleType:
    """Import the hyphenated sibling without introducing another supervisor."""

    path = Path(__file__).with_name("stuck-watchdog.py")
    spec = importlib.util.spec_from_file_location("_critical_task_stuck_watchdog", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import watchdog: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


watchdog = _import_watchdog()


class PreflightError(ValueError):
    """Raised when an attempt cannot safely start."""

    def __init__(self, violations: Iterable[str]) -> None:
        self.violations = tuple(violations)
        super().__init__("; ".join(self.violations))


class Outcome(str, Enum):
    UNHANDED_MUTATION = "UNHANDED_MUTATION"
    TRANSPORT_FAILURE = "TRANSPORT_FAILURE"
    TEST_LONG = "TEST_LONG"
    VALIDATION_FAILURE = "VALIDATION_FAILURE"
    NO_ARTIFACT = "NO_ARTIFACT"
    COMPLETED = "COMPLETED"


class WatchdogObservation(str, Enum):
    CLEAR = "CLEAR"
    TRANSPORT_FAILURE = "TRANSPORT_FAILURE"
    TEST_LONG = "TEST_LONG"


@dataclass(frozen=True)
class AttemptContext:
    """Immutable identity and trust boundary for exactly one attempt."""

    task_id: str
    run_id: str
    attempt_id: str
    join_id: str
    candidate_root: str
    candidate_commit: str
    owned_paths: tuple[str, ...]
    reserved_artifact: str
    worker_state_path: str
    profile_path: str
    profile_version: str
    profile_digest: str

    def __post_init__(self) -> None:
        required = {
            "task_id": self.task_id,
            "run_id": self.run_id,
            "attempt_id": self.attempt_id,
            "join_id": self.join_id,
            "candidate_root": self.candidate_root,
            "candidate_commit": self.candidate_commit,
            "reserved_artifact": self.reserved_artifact,
            "worker_state_path": self.worker_state_path,
            "profile_path": self.profile_path,
            "profile_version": self.profile_version,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"empty attempt-context fields: {', '.join(missing)}")
        digest = self.profile_digest.lower()
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError("profile_digest must be a 64-character SHA-256 hex digest")
        object.__setattr__(self, "profile_digest", digest)
        object.__setattr__(self, "owned_paths", tuple(self.owned_paths))


@dataclass(frozen=True)
class PreflightObservation:
    head_commit: str
    git_changes: tuple[str, ...]
    artifact_exists: bool
    tracked_profile_digest: str


@dataclass(frozen=True)
class OuterAttemptPacket:
    """Strictly validated inputs needed before an outer attempt may start."""

    context: AttemptContext
    dispatch_ready_path: str
    expected_dispatch_id: str
    validation_command: tuple[str, ...]
    adaptive_target_seconds: int
    hard_stop_seconds: int


@dataclass(frozen=True)
class PreparedDispatch:
    """Immutable, explicitly routed host dispatch loaded from trusted JSON."""

    dispatch_id: str
    agent_type: str
    task_name: str
    fork_turns: str
    message: str
    model: str
    reasoning_effort: str


@dataclass(frozen=True)
class SupervisedTiming:
    """Normalized adaptive bounds carried by a critical READY result."""

    target: int | float
    checkpoint: int | float
    hard_stop: int | float
    max_hard_cap: int | float
    reserve: int | float
    provenance: str


@dataclass(frozen=True)
class PreparedSupervisedRun:
    """Immutable critical route bound to one outer task and timing profile."""

    dispatch_id: str
    role: str
    task_id: str
    fork_turns: str
    message: str
    model: str
    reasoning_effort: str
    timing: SupervisedTiming


def watchdog_timing_bounds(
    packet: OuterAttemptPacket,
    dispatch: PreparedDispatch | PreparedSupervisedRun,
) -> tuple[int | float, int | float]:
    """Select the checkpoint and terminal bounds for one supervised run."""

    if isinstance(dispatch, PreparedSupervisedRun):
        return dispatch.timing.checkpoint, dispatch.timing.hard_stop
    return packet.adaptive_target_seconds, packet.hard_stop_seconds


_MAX_PREPARED_DISPATCH_BYTES = 64 * 1024
_PREPARED_SPAWN_FIELDS = {
    "agent_type",
    "task_name",
    "fork_turns",
    "message",
    "model",
    "reasoning_effort",
}
_PREPARED_SUPERVISED_RUN_FIELDS = {
    "role",
    "task_id",
    "message",
    "model",
    "effort",
    "fork_turns",
    "timing",
}
_SUPERVISED_TIMING_FIELDS = {
    "target",
    "checkpoint",
    "hard_stop",
    "max_hard_cap",
    "reserve",
    "provenance",
}
_CRITICAL_ROLES = {"code-reviewer", "test-engineer", "gatekeeper"}
_TIMING_PROVENANCES = {"MEASURED", "ESTIMATED"}
_DISPATCH_ID_RE = re.compile(r"^ctd_[0-9a-f]{24}$")
_ROUTE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{1,127}$")
_TASK_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_OPAQUE_PREFIX_RE = re.compile(
    r"^(?:enc(?:rypted)?|cipher(?:text)?|opaque|sealed|redacted|base64|jwe|kms)"
    r"\s*[:(\[]",
    re.IGNORECASE,
)
_ENCODED_RE = re.compile(r"^(?:[A-Fa-f0-9]{32,}|[A-Za-z0-9+/]{32,}={0,2})$")
_REASONING_EFFORTS = {"low", "medium", "high", "xhigh", "max"}
_HOST_AGENT_TYPES = {
    "lead",
    "default",
    "system_architecture",
    "advisor",
    "contradictor",
    "explorer",
    "worker",
    "test_engineer",
    "gatekeeper",
}


def _dispatch_plaintext(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"prepared dispatch {field} must be a non-empty plaintext string")
    if _CONTROL_RE.search(value):
        raise ValueError(f"prepared dispatch {field} contains control characters")
    normalized = " ".join(value.split())
    lowered = normalized.casefold()
    opaque_words = {
        "opaque",
        "encrypted",
        "encrypted payload",
        "encrypted brief",
        "ciphertext",
        "ciphertext blob",
        "sealed payload",
        "redacted",
        "redacted payload",
        "blob",
    }
    if (
        lowered in opaque_words
        or _OPAQUE_PREFIX_RE.match(normalized)
        or (
            " " not in normalized
            and len(normalized) >= 32
            and _ENCODED_RE.fullmatch(normalized)
        )
    ):
        raise ValueError(f"prepared dispatch {field} is opaque or encoded-only")
    return normalized


def load_ready_dispatch(
    path: str | os.PathLike[str],
    expected_dispatch_id: str,
    *,
    expected_task_id: str | None = None,
    expected_target_seconds: int | None = None,
    expected_hard_stop_seconds: int | None = None,
) -> PreparedDispatch | PreparedSupervisedRun:
    """Load one bounded READY result without following a dispatch-file symlink."""

    expected = _required_string(expected_dispatch_id, "expected_dispatch_id")
    if not _DISPATCH_ID_RE.fullmatch(expected):
        raise ValueError("expected_dispatch_id has an invalid format")

    dispatch_path = Path(path)
    try:
        path_status = dispatch_path.lstat()
    except OSError as error:
        raise ValueError("prepared dispatch is not a readable regular file") from error
    if not stat.S_ISREG(path_status.st_mode):
        raise ValueError("prepared dispatch is not a regular non-symlink file")

    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(dispatch_path, flags)
    except OSError as error:
        raise ValueError("prepared dispatch is not a readable regular file") from error
    try:
        opened_status = os.fstat(fd)
        if (
            not stat.S_ISREG(opened_status.st_mode)
            or (opened_status.st_dev, opened_status.st_ino)
            != (path_status.st_dev, path_status.st_ino)
        ):
            raise ValueError("prepared dispatch changed before it was opened")
        size = opened_status.st_size
        if size <= 0 or size > _MAX_PREPARED_DISPATCH_BYTES:
            raise ValueError("prepared dispatch size is outside the allowed bound")
        document = os.read(fd, _MAX_PREPARED_DISPATCH_BYTES + 1)
        if len(document) != size:
            raise ValueError("prepared dispatch changed while being read")
    finally:
        os.close(fd)

    try:
        value = json.loads(
            document.decode("utf-8"), object_pairs_hook=_object_without_duplicate_keys
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("prepared dispatch is not valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ValueError("prepared dispatch JSON must be an object")
    if value.get("status") != "READY":
        raise ValueError("prepared dispatch status must be READY")
    dispatch_id = value.get("dispatch_id")
    if dispatch_id != expected:
        raise ValueError("prepared dispatch_id does not match the expected identity")

    has_spawn = "spawn" in value
    has_supervised_run = "supervised_run" in value
    if has_spawn == has_supervised_run:
        raise ValueError(
            "prepared dispatch must contain exactly one execution shape: "
            "spawn or supervised_run"
        )

    if has_supervised_run:
        supervised_run = value["supervised_run"]
        if (
            not isinstance(supervised_run, dict)
            or set(supervised_run) != _PREPARED_SUPERVISED_RUN_FIELDS
        ):
            raise ValueError(
                "prepared dispatch supervised_run has an unknown execution shape"
            )
        if (
            expected_task_id is None
            or expected_target_seconds is None
            or expected_hard_stop_seconds is None
        ):
            raise ValueError(
                "prepared dispatch supervised_run requires outer task and timing identity"
            )

        role = _dispatch_plaintext(supervised_run["role"], "supervised_run.role")
        task_id = _dispatch_plaintext(
            supervised_run["task_id"], "supervised_run.task_id"
        )
        message = _dispatch_plaintext(
            supervised_run["message"], "supervised_run.message"
        )
        model = _dispatch_plaintext(
            supervised_run["model"], "supervised_run.model"
        )
        effort = _dispatch_plaintext(
            supervised_run["effort"], "supervised_run.effort"
        ).casefold()
        fork_turns = supervised_run["fork_turns"]

        if role not in _CRITICAL_ROLES:
            raise ValueError("prepared dispatch supervised_run.role is unsupported")
        if task_id != expected_task_id:
            raise ValueError(
                "prepared dispatch supervised_run.task_id does not match outer attempt"
            )
        if not _ROUTE_NAME_RE.fullmatch(model):
            raise ValueError("prepared dispatch supervised_run.model is invalid")
        if len(message.split()) > 250:
            raise ValueError("prepared dispatch supervised_run.message exceeds 250 words")
        if effort not in _REASONING_EFFORTS:
            raise ValueError("prepared dispatch supervised_run.effort is unsupported")
        if not isinstance(fork_turns, str) or not re.fullmatch(
            r"[1-9][0-9]*", fork_turns
        ):
            raise ValueError(
                "prepared dispatch supervised_run.fork_turns is unsupported"
            )

        timing_value = supervised_run["timing"]
        if (
            not isinstance(timing_value, dict)
            or set(timing_value) != _SUPERVISED_TIMING_FIELDS
        ):
            raise ValueError("prepared dispatch supervised_run.timing has invalid fields")
        numbers: dict[str, int | float] = {}
        for field in (
            "target",
            "checkpoint",
            "hard_stop",
            "max_hard_cap",
            "reserve",
        ):
            item = timing_value[field]
            if (
                isinstance(item, bool)
                or not isinstance(item, (int, float))
                or not math.isfinite(item)
                or item <= 0
            ):
                raise ValueError(
                    f"prepared dispatch supervised_run.timing.{field} "
                    "must be a finite positive number"
                )
            numbers[field] = item
        provenance = timing_value["provenance"]
        if not isinstance(provenance, str) or provenance not in _TIMING_PROVENANCES:
            raise ValueError(
                "prepared dispatch supervised_run.timing.provenance is unsupported"
            )
        if not (
            numbers["target"]
            < numbers["checkpoint"]
            < numbers["hard_stop"]
            <= numbers["max_hard_cap"]
        ):
            raise ValueError(
                "prepared dispatch supervised_run.timing must satisfy "
                "target < checkpoint < hard_stop <= max_hard_cap"
            )
        if not numbers["reserve"] < numbers["hard_stop"] - numbers["target"]:
            raise ValueError(
                "prepared dispatch supervised_run.timing.reserve must be less than "
                "hard_stop minus target"
            )
        if numbers["target"] != expected_target_seconds:
            raise ValueError(
                "prepared dispatch supervised_run.timing.target does not match "
                "outer attempt"
            )
        if numbers["hard_stop"] != expected_hard_stop_seconds:
            raise ValueError(
                "prepared dispatch supervised_run.timing.hard_stop does not match "
                "outer attempt"
            )

        return PreparedSupervisedRun(
            dispatch_id=dispatch_id,
            role=role,
            task_id=task_id,
            fork_turns=fork_turns,
            message=message,
            model=model,
            reasoning_effort=effort,
            timing=SupervisedTiming(
                target=numbers["target"],
                checkpoint=numbers["checkpoint"],
                hard_stop=numbers["hard_stop"],
                max_hard_cap=numbers["max_hard_cap"],
                reserve=numbers["reserve"],
                provenance=provenance,
            ),
        )

    spawn = value["spawn"]
    if not isinstance(spawn, dict) or set(spawn) != _PREPARED_SPAWN_FIELDS:
        raise ValueError("prepared dispatch spawn has an unknown execution shape")

    agent_type = _dispatch_plaintext(spawn["agent_type"], "spawn.agent_type")
    task_name = _dispatch_plaintext(spawn["task_name"], "spawn.task_name")
    message = _dispatch_plaintext(spawn["message"], "spawn.message")
    model = _dispatch_plaintext(spawn["model"], "spawn.model")
    effort = _dispatch_plaintext(
        spawn["reasoning_effort"], "spawn.reasoning_effort"
    ).casefold()
    fork_turns = spawn["fork_turns"]

    if agent_type not in _HOST_AGENT_TYPES:
        raise ValueError("prepared dispatch spawn.agent_type is unsupported")
    if not _TASK_NAME_RE.fullmatch(task_name):
        raise ValueError("prepared dispatch spawn.task_name is invalid")
    if not _ROUTE_NAME_RE.fullmatch(model):
        raise ValueError("prepared dispatch spawn.model is invalid")
    if len(message.split()) > 250:
        raise ValueError("prepared dispatch spawn.message exceeds 250 words")
    if effort not in _REASONING_EFFORTS:
        raise ValueError("prepared dispatch spawn.reasoning_effort is unsupported")
    if not isinstance(fork_turns, str) or not re.fullmatch(r"[1-9][0-9]*", fork_turns):
        raise ValueError("prepared dispatch spawn.fork_turns is unsupported")

    return PreparedDispatch(
        dispatch_id=dispatch_id,
        agent_type=agent_type,
        task_name=task_name,
        fork_turns=fork_turns,
        message=message,
        model=model,
        reasoning_effort=effort,
    )


_OUTER_ATTEMPT_FIELDS = {
    "task_id",
    "run_id",
    "attempt_id",
    "join_id",
    "candidate_root",
    "candidate_commit",
    "owned_paths",
    "reserved_artifact",
    "worker_state_path",
    "profile_path",
    "profile_version",
    "profile_digest",
    "dispatch_ready_path",
    "expected_dispatch_id",
    "validation_command",
    "adaptive_target_seconds",
    "hard_stop_seconds",
}


def derive_join_id(
    task_id: str,
    run_id: str,
    attempt_id: str,
    reserved_artifact: str,
    candidate_commit: str,
) -> str:
    """Derive a collision-resistant join identity from immutable attempt inputs."""

    identity = json.dumps(
        {
            "artifact": reserved_artifact,
            "attempt": attempt_id,
            "commit": candidate_commit,
            "run": run_id,
            "task": task_id,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(identity).hexdigest()


def _required_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or value.isspace():
        raise ValueError(f"{name} must be a non-empty string")
    if "\x00" in value:
        raise ValueError(f"{name} must not contain NUL")
    return value


def _absolute_normal_path(value: object, name: str) -> str:
    path = _required_string(value, name)
    if not os.path.isabs(path):
        raise ValueError(f"{name} must be absolute")
    if os.path.normpath(path) != path or path == os.path.sep:
        raise ValueError(f"{name} must be a normalized, non-root path")
    return path


def _command_array(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{name} must be a non-empty array of strings")
    result = tuple(_required_string(part, f"{name} element") for part in value)
    return result


def validate_outer_attempt_packet(value: object) -> OuterAttemptPacket:
    """Validate the complete outer-attempt packet without observing the host."""

    if not isinstance(value, dict):
        raise ValueError("outer-attempt JSON must be an object")
    actual = set(value)
    if actual != _OUTER_ATTEMPT_FIELDS:
        missing = sorted(_OUTER_ATTEMPT_FIELDS - actual)
        unknown = sorted(actual - _OUTER_ATTEMPT_FIELDS)
        details = []
        if missing:
            details.append(f"missing fields: {', '.join(missing)}")
        if unknown:
            details.append(f"unknown fields: {', '.join(unknown)}")
        raise ValueError("outer-attempt JSON has " + "; ".join(details))

    task_id = _required_string(value["task_id"], "task_id")
    run_id = _required_string(value["run_id"], "run_id")
    attempt_id = _required_string(value["attempt_id"], "attempt_id")
    candidate_root = _absolute_normal_path(value["candidate_root"], "candidate_root")
    reserved_artifact = _absolute_normal_path(
        value["reserved_artifact"], "reserved_artifact"
    )
    worker_state_path = _absolute_normal_path(
        value["worker_state_path"], "worker_state_path"
    )
    profile_path = _absolute_normal_path(value["profile_path"], "profile_path")
    dispatch_ready_path = _absolute_normal_path(
        value["dispatch_ready_path"], "dispatch_ready_path"
    )
    if len(
        {reserved_artifact, worker_state_path, profile_path, dispatch_ready_path}
    ) != 4:
        raise ValueError(
            "artifact, worker state, profile, and dispatch paths must be distinct"
        )

    candidate_commit = _required_string(value["candidate_commit"], "candidate_commit")
    if len(candidate_commit) not in (40, 64) or any(
        char not in "0123456789abcdef" for char in candidate_commit
    ):
        raise ValueError("candidate_commit must be a lowercase Git object ID")
    profile_digest = _required_string(value["profile_digest"], "profile_digest")
    if len(profile_digest) != 64 or any(
        char not in "0123456789abcdef" for char in profile_digest
    ):
        raise ValueError("profile_digest must be a lowercase SHA-256 hex digest")

    owned = value["owned_paths"]
    if not isinstance(owned, list) or not owned:
        raise ValueError("owned_paths must be a non-empty array")
    owned_paths: list[str] = []
    for raw_path in owned:
        path = _required_string(raw_path, "owned_paths element")
        if os.path.isabs(path) or os.path.normpath(path) != path or path in (".", ".."):
            raise ValueError("owned_paths entries must be normalized relative paths")
        if any(part == ".." for part in Path(path).parts):
            raise ValueError("owned_paths entries must not traverse candidate_root")
        owned_paths.append(path)
    if len(set(owned_paths)) != len(owned_paths):
        raise ValueError("owned_paths must not contain duplicates")

    adaptive_target = value["adaptive_target_seconds"]
    hard_stop = value["hard_stop_seconds"]
    if type(adaptive_target) is not int or adaptive_target <= 0:
        raise ValueError("adaptive_target_seconds must be a positive integer")
    if type(hard_stop) is not int or hard_stop <= adaptive_target:
        raise ValueError(
            "hard_stop_seconds must be an integer greater than adaptive_target_seconds"
        )

    join_id = _required_string(value["join_id"], "join_id")
    expected_join = derive_join_id(
        task_id, run_id, attempt_id, reserved_artifact, candidate_commit
    )
    if join_id != expected_join:
        raise ValueError("join_id does not match the immutable attempt identity")

    context = AttemptContext(
        task_id=task_id,
        run_id=run_id,
        attempt_id=attempt_id,
        join_id=join_id,
        candidate_root=candidate_root,
        candidate_commit=candidate_commit,
        owned_paths=tuple(owned_paths),
        reserved_artifact=reserved_artifact,
        worker_state_path=worker_state_path,
        profile_path=profile_path,
        profile_version=_required_string(value["profile_version"], "profile_version"),
        profile_digest=profile_digest,
    )
    return OuterAttemptPacket(
        context=context,
        dispatch_ready_path=dispatch_ready_path,
        expected_dispatch_id=_required_string(
            value["expected_dispatch_id"], "expected_dispatch_id"
        ),
        validation_command=_command_array(
            value["validation_command"], "validation_command"
        ),
        adaptive_target_seconds=adaptive_target,
        hard_stop_seconds=hard_stop,
    )


def parse_outer_attempt_packet(document: str | bytes | bytearray) -> OuterAttemptPacket:
    """Decode strict JSON, including duplicate-key rejection, then validate it."""

    value = json.loads(document, object_pairs_hook=_object_without_duplicate_keys)
    return validate_outer_attempt_packet(value)


def _git_output(candidate_root: str, *arguments: str) -> bytes:
    completed = subprocess.run(
        ("git", "-C", candidate_root, *arguments),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise PreflightError((f"Git observation failed: {detail or arguments[0]}",))
    return completed.stdout


def observe_preflight(context: AttemptContext) -> PreflightObservation:
    """Capture the exact candidate and tracked-profile preflight snapshot."""

    root = Path(context.candidate_root)
    profile = Path(context.profile_path)
    if not root.is_dir():
        raise PreflightError(("candidate_root is not a directory",))
    if profile.is_symlink() or not profile.is_file():
        raise PreflightError(("profile is not a regular file",))

    head = _git_output(context.candidate_root, "rev-parse", "--verify", "HEAD^{commit}")
    head_commit = head.decode("ascii", "strict").strip()
    status = _git_output(
        context.candidate_root,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignored=no",
    )
    git_changes = tuple(
        item.decode("utf-8", "surrogateescape") for item in status.split(b"\0") if item
    )
    try:
        relative_profile = profile.relative_to(root)
    except ValueError:
        relative_profile = None
    if relative_profile is not None:
        _git_output(
            context.candidate_root,
            "ls-files",
            "--error-unmatch",
            "--",
            relative_profile.as_posix(),
        )
    digest = hashlib.sha256(profile.read_bytes()).hexdigest()
    return PreflightObservation(
        head_commit=head_commit,
        git_changes=git_changes,
        artifact_exists=os.path.lexists(context.reserved_artifact),
        tracked_profile_digest=digest,
    )


def preflight_outer_attempt(
    packet: OuterAttemptPacket,
) -> tuple[OuterAttemptPacket, PreparedDispatch | PreparedSupervisedRun]:
    """Validate the persisted route and candidate before any worker starts."""

    dispatch = load_ready_dispatch(
        packet.dispatch_ready_path,
        packet.expected_dispatch_id,
        expected_task_id=packet.context.task_id,
        expected_target_seconds=packet.adaptive_target_seconds,
        expected_hard_stop_seconds=packet.hard_stop_seconds,
    )
    preflight_attempt(packet.context, observe_preflight(packet.context))
    return packet, dispatch


def build_codex_exec(
    context: AttemptContext, dispatch: PreparedDispatch | PreparedSupervisedRun
) -> tuple[str, ...]:
    """Build the only supported outer task command from the READY route."""

    return (
        "codex",
        "exec",
        "--ephemeral",
        "-s",
        "workspace-write",
        "-C",
        context.candidate_root,
        "-o",
        context.reserved_artifact,
        "-m",
        dispatch.model,
        "-c",
        f'model_reasoning_effort="{dispatch.reasoning_effort}"',
        dispatch.message,
    )


@dataclass(frozen=True)
class TerminalObservation:
    git_changes: tuple[str, ...]
    unhanded_paths: tuple[str, ...]
    artifact_exists: bool
    worker_phase: str
    worker_exits: tuple[tuple[str, int | None], ...]
    watchdog: WatchdogObservation


@dataclass(frozen=True)
class TerminalResult:
    task_id: str
    run_id: str
    attempt_id: str
    join_id: str
    outcome: Outcome
    retry_allowed: bool
    worker_phase: str
    unhanded_paths: tuple[str, ...]


_MAX_WORKER_STATE_BYTES = 4096
_WORKER_STATE_FIELDS = {"phase", "task_exit", "validation_exit"}


def _git_changed_paths(candidate_root: str) -> tuple[str, ...]:
    """Return every path named by porcelain status, including rename sources."""

    status = _git_output(
        candidate_root,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignored=no",
    )
    records = status.split(b"\0")
    if records[-1:] == [b""]:
        records.pop()

    paths: list[str] = []
    index = 0
    while index < len(records):
        record = records[index]
        if len(record) < 4 or record[2:3] != b" ":
            raise ValueError("malformed Git porcelain status record")
        status_code = record[:2]
        path = record[3:]
        if not path:
            raise ValueError("Git porcelain status record has an empty path")
        paths.append(path.decode("utf-8", "surrogateescape"))
        index += 1

        # In porcelain v1 -z output, rename/copy destinations are in the
        # status record and the source is the following NUL-delimited field.
        if b"R" in status_code or b"C" in status_code:
            if index >= len(records) or not records[index]:
                raise ValueError("Git rename/copy record has no source path")
            # A rename mutates both names; a copy only mutates its destination.
            if b"R" in status_code:
                paths.append(records[index].decode("utf-8", "surrogateescape"))
            index += 1
    return tuple(paths)


def _open_regular(path: Path, description: str) -> int:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as error:
        raise ValueError(f"{description} is not a readable regular file") from error
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise ValueError(f"{description} is not a regular file")
    return fd


def _read_worker_state(path: Path) -> tuple[str, tuple[tuple[str, int | None], ...]]:
    """Read and strictly validate the worker's small, atomic state document."""

    if not os.path.lexists(path):
        return "NOT_STARTED", ()

    fd = _open_regular(path, "worker state")
    try:
        size = os.fstat(fd).st_size
        if size <= 0 or size > _MAX_WORKER_STATE_BYTES:
            raise ValueError("worker state size is outside the allowed bound")
        document = os.read(fd, _MAX_WORKER_STATE_BYTES + 1)
        if len(document) != size:
            raise ValueError("worker state changed while being observed")
    finally:
        os.close(fd)

    try:
        value = json.loads(
            document.decode("utf-8"), object_pairs_hook=_object_without_duplicate_keys
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("worker state is not valid UTF-8 JSON") from error
    if not isinstance(value, dict) or set(value) != _WORKER_STATE_FIELDS:
        raise ValueError("worker state has an invalid schema")

    phase = value["phase"]
    task_exit = value["task_exit"]
    validation_exit = value["validation_exit"]
    if phase not in {"TASK_RUNNING", "VALIDATION_RUNNING", "FINISHED"}:
        raise ValueError("worker state has an invalid phase")
    for name, exit_code in (
        ("task_exit", task_exit),
        ("validation_exit", validation_exit),
    ):
        if exit_code is not None and type(exit_code) is not int:
            raise ValueError(f"worker state {name} must be an integer or null")

    consistent = (
        phase == "TASK_RUNNING"
        and task_exit is None
        and validation_exit is None
    ) or (
        phase == "VALIDATION_RUNNING"
        and task_exit == 0
        and validation_exit is None
    ) or (
        phase == "FINISHED"
        and (
            (type(task_exit) is int and task_exit != 0 and validation_exit is None)
            or (task_exit == 0 and type(validation_exit) is int)
        )
    )
    if not consistent:
        raise ValueError("worker phase and exit codes are inconsistent")
    return phase, (("task", task_exit), ("validation", validation_exit))


def _profile_digest(context: AttemptContext) -> str:
    profile = Path(context.profile_path)
    root = Path(context.candidate_root)
    try:
        relative_profile = profile.relative_to(root)
    except ValueError:
        relative_profile = None
    if relative_profile is not None:
        _git_output(
            context.candidate_root,
            "ls-files",
            "--error-unmatch",
            "--",
            relative_profile.as_posix(),
        )
    fd = _open_regular(profile, "profile")
    try:
        digest = hashlib.sha256()
        while chunk := os.read(fd, 1024 * 1024):
            digest.update(chunk)
    finally:
        os.close(fd)
    return digest.hexdigest()


def _watchdog_observation(event: object, worker_phase: str) -> WatchdogObservation:
    if type(event) is not str or event not in {"CLEAR", "FAILED", "STUCK_REPORT"}:
        raise ValueError("malformed watchdog event")
    if event == "STUCK_REPORT":
        return WatchdogObservation.TEST_LONG
    if worker_phase == "FINISHED":
        return WatchdogObservation.CLEAR
    return WatchdogObservation.TRANSPORT_FAILURE


def _path_is_owned(path: str, owned_paths: tuple[str, ...]) -> bool:
    return any(path == owned or path.startswith(f"{owned}/") for owned in owned_paths)


def observe_terminal(
    context: AttemptContext, watchdog_event: object
) -> TerminalObservation:
    """Capture and validate one quiescent terminal attempt snapshot."""

    git_changes = _git_changed_paths(context.candidate_root)
    worker_phase, worker_exits = _read_worker_state(Path(context.worker_state_path))
    artifact = Path(context.reserved_artifact)
    try:
        artifact_status = artifact.lstat()
    except FileNotFoundError:
        artifact_exists = False
    else:
        artifact_exists = stat.S_ISREG(artifact_status.st_mode) and artifact_status.st_size > 0

    if _profile_digest(context) != context.profile_digest:
        raise ValueError("profile SHA-256 drifted during the attempt")
    watchdog = _watchdog_observation(watchdog_event, worker_phase)
    unhanded_paths = tuple(
        path
        for path in git_changes
        if not _path_is_owned(path, context.owned_paths) or not artifact_exists
    )
    return TerminalObservation(
        git_changes=git_changes,
        unhanded_paths=unhanded_paths,
        artifact_exists=artifact_exists,
        worker_phase=worker_phase,
        worker_exits=worker_exits,
        watchdog=watchdog,
    )


def preflight_attempt(
    context: AttemptContext, observation: PreflightObservation
) -> AttemptContext:
    """Return the validated context, or fail closed with all violations."""

    violations: list[str] = []
    if observation.git_changes:
        violations.append("candidate is not clean")
    if observation.head_commit != context.candidate_commit:
        violations.append("candidate HEAD is not pinned to candidate_commit")
    if observation.artifact_exists:
        violations.append("reserved artifact already exists")
    if observation.tracked_profile_digest.lower() != context.profile_digest:
        violations.append("tracked profile SHA-256 does not match attempt context")
    if violations:
        raise PreflightError(violations)
    return context


def classify_terminal(
    context: AttemptContext, observation: TerminalObservation
) -> TerminalResult:
    """Classify one terminal snapshot using the contract's strict precedence."""

    worker_exits = dict(observation.worker_exits)
    if observation.unhanded_paths:
        outcome = Outcome.UNHANDED_MUTATION
    elif observation.watchdog is WatchdogObservation.TRANSPORT_FAILURE:
        outcome = Outcome.TRANSPORT_FAILURE
    elif observation.watchdog is WatchdogObservation.TEST_LONG:
        outcome = Outcome.TEST_LONG
    elif (
        worker_exits.get("task") not in (None, 0)
        and not observation.artifact_exists
        and not observation.git_changes
    ):
        outcome = Outcome.TRANSPORT_FAILURE
    elif any(code not in (None, 0) for code in worker_exits.values()):
        outcome = Outcome.VALIDATION_FAILURE
    elif not observation.artifact_exists:
        outcome = Outcome.NO_ARTIFACT
    else:
        outcome = Outcome.COMPLETED

    return TerminalResult(
        task_id=context.task_id,
        run_id=context.run_id,
        attempt_id=context.attempt_id,
        join_id=context.join_id,
        outcome=outcome,
        retry_allowed=False,
        worker_phase=observation.worker_phase,
        unhanded_paths=observation.unhanded_paths,
    )


_NEXT_ACTION = {
    Outcome.UNHANDED_MUTATION: "REVIEW_UNHANDED_MUTATION",
    Outcome.TRANSPORT_FAILURE: "INVESTIGATE_TRANSPORT_FAILURE",
    Outcome.TEST_LONG: "REVIEW_STUCK_CHECKPOINT",
    Outcome.VALIDATION_FAILURE: "REMEDIATE_VALIDATION_FAILURE",
    Outcome.NO_ARTIFACT: "OPEN_NEW_ATTEMPT_IDENTITY",
    Outcome.COMPLETED: "HAND_OFF_TO_TEST_ENGINEER",
}


def project_terminal_receipt(
    context: AttemptContext,
    observation: TerminalObservation,
    watchdog_terminal_event: dict[str, object],
) -> dict[str, object]:
    """Project a privacy-bounded receipt for the watchdog terminal transform."""

    if not isinstance(watchdog_terminal_event, dict):
        raise ValueError("watchdog terminal event must be an object")
    for name, expected in (("task_id", context.task_id), ("run_id", context.run_id)):
        actual = _required_string(watchdog_terminal_event.get(name), name)
        if actual != expected:
            raise ValueError(f"watchdog terminal event {name} does not match attempt")

    watchdog_exit = watchdog_terminal_event.get("exit_code")
    if type(watchdog_exit) is not int:
        raise ValueError("watchdog terminal event exit_code must be an integer")

    result = classify_terminal(context, observation)
    completed = result.outcome is Outcome.COMPLETED and watchdog_exit == 0
    worker_exits = dict(observation.worker_exits)
    receipt: dict[str, object] = {
        "task_id": result.task_id,
        "run_id": result.run_id,
        "attempt_id": result.attempt_id,
        "join_id": result.join_id,
        "candidate_commit": context.candidate_commit,
        "checkout_root_digest": hashlib.sha256(
            os.path.realpath(context.candidate_root).encode("utf-8")
        ).hexdigest(),
        "preflight_clean": True,
        "profile_version": context.profile_version,
        "profile_digest": context.profile_digest,
        "reserved_artifact": context.reserved_artifact,
        "artifact_present": observation.artifact_exists,
        "worktree_mutated": bool(observation.git_changes),
        "changed_paths": list(observation.git_changes),
        "unhanded_paths": list(result.unhanded_paths),
        "worker_phase": result.worker_phase,
        "task_exit": worker_exits.get("task"),
        "validation_exit": worker_exits.get("validation"),
        "outcome_class": result.outcome.value,
        "status": "COMPLETED" if completed else "BLOCKED",
        "exit_code": 0 if completed else (watchdog_exit or 1),
        "retry_allowed": False,
        "privacy": "LOCAL_ONLY",
        "public_safe": False,
        "next_action": _NEXT_ACTION[result.outcome],
    }
    for optional in ("elapsed", "elapsed_seconds", "checkpoint"):
        if optional in watchdog_terminal_event:
            receipt[optional] = watchdog_terminal_event[optional]
    return receipt


# Short aliases keep the public vocabulary convenient without duplicating logic.
preflight = preflight_attempt
classify = classify_terminal


@dataclass(frozen=True)
class InternalWorkerSpec:
    """Validated commands and the unique state destination for one worker."""

    state_path: Path
    command: tuple[str, ...]
    validation_command: tuple[str, ...]


def validate_internal_worker(value: object) -> InternalWorkerSpec:
    """Validate the complete, deliberately small internal-worker contract."""

    if not isinstance(value, dict):
        raise ValueError("internal-worker JSON must be an object")
    expected = {"state_path", "command", "validation_command"}
    if set(value) != expected:
        raise ValueError(
            "internal-worker JSON must contain exactly state_path, command, "
            "and validation_command"
        )

    state_path = value["state_path"]
    if not isinstance(state_path, str) or not state_path:
        raise ValueError("state_path must be a non-empty string")

    def command_array(name: str) -> tuple[str, ...]:
        raw = value[name]
        if (
            not isinstance(raw, list)
            or not raw
            or any(not isinstance(part, str) for part in raw)
            or not raw[0]
        ):
            raise ValueError(f"{name} must be a non-empty array of strings")
        return tuple(raw)

    return InternalWorkerSpec(
        state_path=Path(state_path),
        command=command_array("command"),
        validation_command=command_array("validation_command"),
    )


class _StatePublisher:
    """Atomically publish state without replacing a pre-existing identity."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._claimed = False

    def publish(
        self, phase: str, task_exit: int | None, validation_exit: int | None
    ) -> None:
        payload = json.dumps(
            {
                "phase": phase,
                "task_exit": task_exit,
                "validation_exit": validation_exit,
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8") + b"\n"
        fd, temporary = tempfile.mkstemp(
            dir=self.path.parent, prefix=f".{self.path.name}."
        )
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            if self._claimed:
                os.replace(temporary, self.path)
            else:
                # link(2) fails rather than replacing a state identity won by
                # another process between the absence check and publication.
                os.link(temporary, self.path)
                os.unlink(temporary)
                self._claimed = True
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def run_internal_worker(value: object) -> int:
    """Run each declared command at most once and publish observable phases."""

    spec = validate_internal_worker(value)
    if os.path.lexists(spec.state_path):
        raise FileExistsError(f"state path already exists: {spec.state_path}")
    if not spec.state_path.parent.is_dir():
        raise ValueError(f"state path parent is not a directory: {spec.state_path.parent}")

    publisher = _StatePublisher(spec.state_path)
    publisher.publish("TASK_RUNNING", None, None)
    task_exit = subprocess.run(spec.command, check=False).returncode
    if task_exit != 0:
        publisher.publish("FINISHED", task_exit, None)
        return task_exit

    publisher.publish("VALIDATION_RUNNING", task_exit, None)
    validation_exit = subprocess.run(spec.validation_command, check=False).returncode
    publisher.publish("FINISHED", task_exit, validation_exit)
    return validation_exit


def run_outer_attempt(
    attempt_path: Path,
    receipt_path: Path,
) -> int:
    """Preflight and supervise exactly one isolated internal worker."""

    if os.path.lexists(receipt_path):
        raise FileExistsError(f"receipt path already exists: {receipt_path}")

    packet, dispatch = preflight_outer_attempt(
        parse_outer_attempt_packet(attempt_path.read_bytes())
    )
    protected_paths = {
        Path(packet.context.reserved_artifact),
        Path(packet.context.worker_state_path),
        Path(packet.context.profile_path),
        Path(packet.dispatch_ready_path),
        attempt_path,
    }
    if receipt_path in protected_paths:
        raise ValueError("receipt path must be unique from attempt-controlled paths")

    worker = {
        "state_path": packet.context.worker_state_path,
        "command": list(build_codex_exec(packet.context, dispatch)),
        "validation_command": list(packet.validation_command),
    }
    worker_command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "internal-worker",
        json.dumps(worker, separators=(",", ":"), sort_keys=True),
    ]
    projected: dict[str, object] | None = None

    def terminal_transform(event: dict[str, object]) -> dict[str, object]:
        nonlocal projected
        watchdog_event = "CLEAR" if event.get("event") == "COMPLETED" else event.get("event")
        observation = observe_terminal(packet.context, watchdog_event)
        projected = project_terminal_receipt(packet.context, observation, event)
        return projected

    target_seconds, hard_stop_seconds = watchdog_timing_bounds(packet, dispatch)
    status = watchdog.supervise(
        worker_command,
        task_id=packet.context.task_id,
        run_id=packet.context.run_id,
        target_seconds=target_seconds,
        hard_stop_seconds=hard_stop_seconds,
        receipt_path=receipt_path,
        terminal_transform=terminal_transform,
    )
    completed = (
        status == 0
        and projected is not None
        and projected.get("status") == "COMPLETED"
        and projected.get("outcome_class") == Outcome.COMPLETED.value
    )
    return 0 if completed else (status if type(status) is int and status != 0 else 1)


def _object_without_duplicate_keys(pairs: Sequence[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="subcommand", required=True)
    worker_parser = subparsers.add_parser("internal-worker")
    worker_parser.add_argument("worker_json", help="internal-worker JSON object")
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("attempt_json", type=Path, help="outer-attempt JSON file")
    run_parser.add_argument("receipt_path", type=Path, help="new terminal receipt path")
    args = parser.parse_args(argv)

    if args.subcommand == "internal-worker":
        try:
            worker = json.loads(
                args.worker_json, object_pairs_hook=_object_without_duplicate_keys
            )
            status = run_internal_worker(worker)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            worker_parser.error(str(error))
        return status if 0 <= status <= 255 else 1
    if args.subcommand == "run":
        try:
            return run_outer_attempt(args.attempt_json, args.receipt_path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            run_parser.error(str(error))
    raise AssertionError("unreachable subcommand")


if __name__ == "__main__":
    raise SystemExit(main())
