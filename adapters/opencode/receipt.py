"""Hermetic, evidence-only receipts for the OpenCode adapter.

This module deliberately does not inspect provider state, retry a failed write,
or project a receipt into any WYSY state.  The only filesystem mutation it
performs is the adapter-local receipt path below the validated ``root``.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Mapping, Optional, Sequence


UNAVAILABLE = "UNAVAILABLE"
TRUSTED_RUNTIME_RECEIPT = "TRUSTED_RUNTIME_RECEIPT"
RECORD_REVISION = 1
AUTO_ACTION = "none"

_STATUSES = frozenset({"MEASURED", "ESTIMATED", UNAVAILABLE})
_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:@+-]{0,127}\Z")
_HEX_RE = re.compile(r"[0-9A-Fa-f]+\Z")
_SAFE_ARTIFACT_RE = re.compile(r"[A-Za-z0-9._@+-]+\Z")
_SECRET_RE = re.compile(
    r"(?:api[_-]?key|secret|password|passwd|authorization|bearer|"
    r"private[_-]?key|access[_-]?token|raw[_-]?(?:prompt|output))",
    re.IGNORECASE,
)
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?:api[\W_]*key|secret|password|passwd|authorization|bearer|"
    r"private[\W_]*key|access[\W_]*token|token)[\W_]*[:=]",
    re.IGNORECASE,
)
_TOKEN_ASSIGNMENT_RE = re.compile(
    r"t[\W_]*o[\W_]*k[\W_]*e[\W_]*n[\W_]*[:=]",
    re.IGNORECASE,
)
_SECRET_VALUE_RE = re.compile(
    r"(?:sk|rk|pk)-[A-Za-z0-9_-]{8,}|-----BEGIN[ A-Z0-9_-]*KEY-----",
    re.IGNORECASE,
)
_COMPACT_SENSITIVE_TERMS = frozenset(
    {
        "apikey",
        "secret",
        "password",
        "passwd",
        "authorization",
        "bearer",
        "privatekey",
        "accesstoken",
        "rawprompt",
        "rawoutput",
    }
)
_TRUSTED_MODEL_SOURCES = frozenset(
    {
        TRUSTED_RUNTIME_RECEIPT,
        "trusted_runtime_receipt",
        "trusted-runtime-receipt",
        "runtime_receipt",
        "runtime-receipt",
    }
)

_BASE_INPUT_FIELDS = frozenset(
    {
        "schema_version",
        "task_id",
        "run_id",
        "attempt_id",
        "role_id",
        "planned_model",
        "planned_tier",
        "map_ref",
        "map_revision",
        "map_digest",
        "exit_state",
        "source_sha",
        "actual_model",
        "actual_model_source",
        "usage",
        "cost",
        "performance",
        "artifact_refs",
    }
)

_METRIC_FIELDS = {
    "usage": frozenset(
        {
            "status",
            "source",
            "basis",
            "input_tokens",
            "output_tokens",
            "cached_input_tokens",
            "total_tokens",
            "units",
        }
    ),
    "cost": frozenset({"status", "source", "basis", "amount", "currency", "units"}),
    "performance": frozenset(
        {"status", "source", "basis", "latency_ms", "duration_ms", "units"}
    ),
}

_METRIC_FLAT_FIELDS = frozenset(
    field
    for metric in _METRIC_FIELDS
    for field in (
        f"{metric}_status",
        f"{metric}_source",
        f"{metric}_basis",
    )
)

_INPUT_FIELDS = _BASE_INPUT_FIELDS | _METRIC_FLAT_FIELDS
_REQUIRED_FIELDS = frozenset(
    {
        "task_id",
        "run_id",
        "attempt_id",
        "role_id",
        "planned_model",
        "planned_tier",
        "map_ref",
        "map_revision",
        "map_digest",
        "exit_state",
        "source_sha",
        "artifact_refs",
        "usage",
        "cost",
        "performance",
    }
)


class ReceiptError(Exception):
    """Base class for handled receipt failures."""


class ReceiptValidationError(ReceiptError, ValueError):
    """The requested receipt does not satisfy the evidence contract."""


class RootValidationError(ReceiptError, ValueError):
    """The supplied root is not the validated nested coding-team checkout."""


class ReceiptConflict(ReceiptError):
    """A final receipt already exists with different content."""


class PendingReceipt(ReceiptError):
    """A pending receipt exists and is observable rather than retried."""


def _error(message: str) -> ReceiptValidationError:
    return ReceiptValidationError(message)


def _contains_sensitive_material(value: str) -> bool:
    compact = re.sub(r"[^a-z0-9]+", "", value.casefold())
    return bool(
        _SECRET_ASSIGNMENT_RE.search(value)
        or _TOKEN_ASSIGNMENT_RE.search(value)
        or _SECRET_RE.search(value)
        or _SECRET_VALUE_RE.search(value)
        or any(term in compact for term in _COMPACT_SENSITIVE_TERMS)
    )


def _validate_text(name: str, value: Any, *, max_length: int = 1024) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise _error(f"{name} must be a non-empty string")
    if len(value) > max_length:
        raise _error(f"{name} is too long")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise _error(f"{name} contains control characters")
    if _contains_sensitive_material(value):
        raise _error(f"{name} contains secret-like material")
    return value


def _validate_id(name: str, value: Any) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise _error(f"{name} must be a non-empty safe opaque ID")
    if value in {".", ".."} or ".." in value.split("/"):
        raise _error(f"{name} contains path traversal")
    return value


def _validate_reference(name: str, value: Any) -> str:
    value = _validate_text(name, value, max_length=1024)
    if (
        os.path.isabs(value)
        or PurePosixPath(value).is_absolute()
        or PureWindowsPath(value).is_absolute()
        or PureWindowsPath(value).drive
    ):
        raise _error(f"{name} must not be absolute")
    if "\\" in value or "\x00" in value or "://" in value:
        raise _error(f"{name} is not a safe local reference")
    if any(part in {"", ".", ".."} for part in value.split("/")):
        raise _error(f"{name} contains path traversal")
    if _contains_sensitive_material(value):
        raise _error(f"{name} contains secret-like material")
    return value


def _validate_digest(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value or not _HEX_RE.fullmatch(value):
        raise _error(f"{name} must be a non-empty hexadecimal digest")
    return value


def _validate_revision(value: Any) -> Any:
    if isinstance(value, bool):
        raise _error("map_revision must be a string or integer")
    if isinstance(value, int):
        if value < 0:
            raise _error("map_revision must not be negative")
        return value
    return _validate_text("map_revision", value, max_length=256)


def _validate_model(name: str, value: Any) -> str:
    value = _validate_text(name, value, max_length=256)
    if _contains_sensitive_material(value):
        raise _error(f"{name} contains secret-like material")
    return value


def _validate_provenance_text(name: str, value: Any, *, max_length: int) -> str:
    value = _validate_text(name, value, max_length=max_length)
    if _contains_sensitive_material(value):
        raise _error(f"{name} contains raw or secret-like material")
    return value


def _validate_artifact_refs(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        raise _error("artifact_refs must be an array of relative paths")

    refs: list[str] = []
    for index, reference in enumerate(value):
        if not isinstance(reference, str) or not reference:
            raise _error(f"artifact_refs[{index}] must be a relative path")
        if not all(_SAFE_ARTIFACT_RE.fullmatch(part) for part in reference.split("/")):
            raise _error(f"artifact_refs[{index}] is not a safe path reference")
        reference = _validate_reference(f"artifact_refs[{index}]", reference)
        if _contains_sensitive_material(reference) or any(
            part.lower() in {".env", "credentials", "credential", "secrets", "secret", "id_rsa"}
            for part in reference.split("/")
        ):
            raise _error(f"artifact_refs[{index}] contains secret-like material")
        if re.search(r"(?:^|/)(?:raw[-_.]?(?:prompt|output))(?:$|[._-])", reference, re.I):
            raise _error(f"artifact_refs[{index}] must not reference raw prompt/output")
        if reference in refs:
            raise _error(f"artifact_refs contains duplicate reference: {index}")
        refs.append(reference)
    return refs


def _validate_nonnegative_number(name: str, value: Any, *, integer: bool = False) -> Any:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _error(f"{name} must be a non-negative number")
    if isinstance(value, float) and not math.isfinite(value):
        raise _error(f"{name} must be finite")
    if value < 0:
        raise _error(f"{name} must be non-negative")
    if integer and not isinstance(value, int):
        raise _error(f"{name} must be a non-negative integer")
    return value


def _validate_metric(metric_name: str, metric: Any) -> dict[str, Any]:
    if not isinstance(metric, Mapping):
        raise _error(f"{metric_name} must be an object")
    unknown = set(metric) - _METRIC_FIELDS[metric_name]
    if unknown:
        raise _error(f"{metric_name} contains unknown field(s)")
    for field in ("status", "source", "basis"):
        if field not in metric:
            raise _error(f"{metric_name}.{field} is required")

    status = metric["status"]
    if not isinstance(status, str) or status not in _STATUSES:
        raise _error(f"{metric_name}.status must be MEASURED, ESTIMATED, or UNAVAILABLE")
    source = _validate_provenance_text(
        f"{metric_name}.source", metric["source"], max_length=512
    )
    basis = _validate_provenance_text(
        f"{metric_name}.basis", metric["basis"], max_length=2048
    )

    result: dict[str, Any] = {"status": status, "source": source, "basis": basis}
    integer_fields = {
        "input_tokens",
        "output_tokens",
        "cached_input_tokens",
        "total_tokens",
        "latency_ms",
        "duration_ms",
    }
    for field, value in metric.items():
        if field in {"status", "source", "basis"}:
            continue
        if field in integer_fields:
            if value is not None:
                value = _validate_nonnegative_number(
                    f"{metric_name}.{field}", value, integer=True
                )
        elif field == "amount":
            if value is not None:
                value = _validate_nonnegative_number(f"{metric_name}.amount", value)
        elif field == "currency":
            if value is not None:
                value = _validate_text(f"{metric_name}.currency", value, max_length=16)
        elif field == "units":
            if value is not None:
                value = _validate_text(f"{metric_name}.units", value, max_length=32)
        result[field] = value

    if status == UNAVAILABLE:
        measured_values = [
            value
            for field, value in result.items()
            if field not in {"status", "source", "basis"} and value is not None
        ]
        if measured_values:
            raise _error(f"{metric_name} cannot include values when status is UNAVAILABLE")
    return result


def _metric_from_payload(metric_name: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    nested = payload.get(metric_name)
    flat_names = {
        "status": f"{metric_name}_status",
        "source": f"{metric_name}_source",
        "basis": f"{metric_name}_basis",
    }
    flat_present = [name for name in flat_names.values() if name in payload]
    if nested is not None:
        if flat_present:
            raise _error(f"use either {metric_name} or flattened metric fields")
        return _validate_metric(metric_name, nested)
    if not flat_present:
        raise _error(f"{metric_name} status/source/basis are required")
    if len(flat_present) != len(flat_names):
        raise _error(f"{metric_name} status, source, and basis are all required")
    return _validate_metric(
        metric_name,
        {field: payload[name] for field, name in flat_names.items()},
    )


def _normalise_payload(receipt: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(receipt, Mapping):
        raise _error("receipt input must be an object")
    unknown = set(receipt) - _INPUT_FIELDS
    if unknown:
        raise _error("receipt contains unknown top-level field(s)")
    missing = set(_REQUIRED_FIELDS - set(receipt))
    # Nested metrics can be supplied using their flattened equivalents.
    for metric_name in ("usage", "cost", "performance"):
        missing.discard(metric_name)
        if not (
            metric_name in receipt
            or f"{metric_name}_status" in receipt
            or f"{metric_name}_source" in receipt
            or f"{metric_name}_basis" in receipt
        ):
            missing.add(metric_name)
    if missing:
        raise _error("receipt is missing required field(s)")

    if "schema_version" in receipt and receipt["schema_version"] != 1:
        raise _error("schema_version must be 1")

    result: dict[str, Any] = {
        "task_id": _validate_id("task_id", receipt["task_id"]),
        "run_id": _validate_id("run_id", receipt["run_id"]),
        "attempt_id": _validate_id("attempt_id", receipt["attempt_id"]),
        "role_id": _validate_id("role_id", receipt["role_id"]),
        "planned_model": _validate_model("planned_model", receipt["planned_model"]),
        "planned_tier": _validate_text("planned_tier", receipt["planned_tier"], max_length=256),
        "map_ref": _validate_reference("map_ref", receipt["map_ref"]),
        "map_revision": _validate_revision(receipt["map_revision"]),
        "map_digest": _validate_digest("map_digest", receipt["map_digest"]),
        "exit_state": _validate_text("exit_state", receipt["exit_state"], max_length=128),
        "source_sha": _validate_digest("source_sha", receipt["source_sha"]),
        "artifact_refs": _validate_artifact_refs(receipt["artifact_refs"]),
        "usage": _metric_from_payload("usage", receipt),
        "cost": _metric_from_payload("cost", receipt),
        "performance": _metric_from_payload("performance", receipt),
    }

    actual_model = receipt.get("actual_model")
    actual_model_source = receipt.get("actual_model_source")
    if actual_model is not None:
        _validate_model("actual_model", actual_model)
    if actual_model_source is not None:
        actual_model_source = _validate_provenance_text(
            "actual_model_source", actual_model_source, max_length=256
        )

    trusted = (
        isinstance(actual_model_source, str)
        and actual_model_source in _TRUSTED_MODEL_SOURCES
        and isinstance(actual_model, str)
        and actual_model != UNAVAILABLE
    )
    if trusted:
        result.update(
            {
                "actual_model": actual_model,
                "actual_model_source": actual_model_source,
                "actual_model_status": "TRUSTED",
            }
        )
    else:
        result.update(
            {
                "actual_model": UNAVAILABLE,
                "actual_model_source": UNAVAILABLE,
                "actual_model_status": UNAVAILABLE,
            }
        )
    return result


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    try:
        text = json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise ReceiptValidationError("receipt contains a non-canonical value") from exc
    return (text + "\n").encode("ascii")


def _utc_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _lstat(path: Path) -> Optional[os.stat_result]:
    try:
        return os.lstat(path)
    except FileNotFoundError:
        return None


def _real_directory(path: Path) -> bool:
    info = _lstat(path)
    return info is not None and stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode)


def _git_root(path: Path) -> Optional[Path]:
    try:
        result = subprocess.run(
            ["git", "-C", os.fspath(path), "rev-parse", "--show-toplevel"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    output = result.stdout.strip()
    if not output or "\n" in output or "\x00" in output:
        return None
    try:
        return Path(output).resolve(strict=True)
    except (OSError, RuntimeError):
        return None


def _resolve_root(root: os.PathLike[str] | str) -> Path:
    try:
        raw_root = os.fspath(root)
    except TypeError as exc:
        raise RootValidationError("root must be a filesystem path") from exc
    if not isinstance(raw_root, str) or not raw_root or "\x00" in raw_root:
        raise RootValidationError("root must be a non-empty filesystem path")

    supplied = Path(raw_root)
    if not supplied.is_absolute():
        supplied = Path.cwd() / supplied
    if supplied.is_symlink():
        raise RootValidationError("root symlinks are not accepted")
    try:
        resolved = supplied.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise RootValidationError("root does not exist") from exc
    if not _real_directory(resolved):
        raise RootValidationError("root must be a directory")

    repository_root = _git_root(resolved)
    if repository_root is None or repository_root != resolved:
        raise RootValidationError("root must be the git repository top level")

    # The parent WYSY checkout is also a git repository.  A disposable fixture
    # may only have the conventional checkout name; a real checkout also has
    # these adapter-local markers.
    named_checkout = resolved.name == "coding-team"
    marked_checkout = _real_directory(resolved / "core") and _real_directory(
        resolved / "adapters" / "opencode"
    )
    if not (named_checkout or marked_checkout):
        raise RootValidationError("root is not the nested coding-team checkout")
    nested_candidate = resolved / "coding-team"
    if _real_directory(nested_candidate) and _git_root(nested_candidate) == nested_candidate.resolve():
        raise RootValidationError("parent WYSY root is not an accepted receipt root")
    return resolved


def _ensure_directory_chain(root: Path, components: Sequence[str]) -> Path:
    current = root
    for component in components:
        if component in {"", ".", ".."} or "/" in component or "\\" in component:
            raise ReceiptValidationError("unsafe receipt directory component")
        next_path = current / component
        info = _lstat(next_path)
        if info is None:
            try:
                os.mkdir(next_path, 0o700)
            except FileExistsError:
                info = _lstat(next_path)
            except OSError as exc:
                raise ReceiptError("could not create receipt directory") from exc
            else:
                info = _lstat(next_path)
        if info is None or stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise ReceiptError("receipt path contains a symlink or non-directory")
        current = next_path
    return current


def _read_existing_json(path: Path) -> dict[str, Any]:
    info = _lstat(path)
    if info is None:
        raise FileNotFoundError(path)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ReceiptConflict("final receipt path is not a regular file")
    try:
        with open(path, "rb") as stream:
            raw = stream.read()
        value = json.loads(
            raw.decode("utf-8"),
            parse_constant=lambda constant: (_ for _ in ()).throw(
                ValueError(f"invalid JSON constant: {constant}")
            ),
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise ReceiptConflict("existing receipt is not valid JSON") from exc
    if not isinstance(value, dict):
        raise ReceiptConflict("existing receipt is not an object")
    return value


def _same_record_ignoring_timestamps(
    existing: Mapping[str, Any], candidate: Mapping[str, Any]
) -> bool:
    if set(existing) != set(candidate):
        return False
    existing_without_time = dict(existing)
    candidate_without_time = dict(candidate)
    existing_without_time.pop("created_at", None)
    existing_without_time.pop("finalized_at", None)
    candidate_without_time.pop("created_at", None)
    candidate_without_time.pop("finalized_at", None)
    return _canonical_json(existing_without_time) == _canonical_json(candidate_without_time)


def _cleanup_pending(path: Path) -> None:
    info = _lstat(path)
    if info is None or stat.S_ISLNK(info.st_mode):
        return
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass
    except OSError:
        # A failed cleanup leaves the pending file observable for a human.
        pass


def record_receipt(
    root: os.PathLike[str] | str,
    receipt: Optional[Mapping[str, Any]] = None,
    **fields: Any,
) -> Path:
    """Validate and atomically record one adapter-local receipt.

    ``receipt`` may be a mapping, or the input fields may be passed as keyword
    arguments.  The returned path is the final receipt path.  An identical
    existing record is a no-op; a conflicting record raises
    :class:`ReceiptConflict`.
    """

    aliases = [name for name in ("record", "data", "payload") if name in fields]
    if aliases:
        if receipt is not None or len(aliases) != 1:
            raise ReceiptValidationError("receipt mapping supplied more than once")
        receipt = fields.pop(aliases[0])
    if receipt is None:
        receipt = fields
        fields = {}
    elif fields:
        raise ReceiptValidationError("receipt mapping cannot be combined with fields")
    if not isinstance(receipt, Mapping):
        raise ReceiptValidationError("receipt input must be an object")

    normalized = _normalise_payload(receipt)
    validated_root = _resolve_root(root)
    receipt_relative = Path(
        ".coding-team",
        "receipts",
        "opencode",
        normalized["task_id"],
        normalized["run_id"],
        normalized["attempt_id"],
        f"{normalized['attempt_id']}.json",
    )
    attempt_directory = _ensure_directory_chain(
        validated_root, receipt_relative.parts[:-1]
    )
    final_path = attempt_directory / receipt_relative.name
    pending_path = attempt_directory / f"{receipt_relative.name}.pending"
    alternate_pending_path = attempt_directory / f"{normalized['attempt_id']}.pending"

    final_info = _lstat(final_path)
    if _lstat(pending_path) is not None or _lstat(alternate_pending_path) is not None:
        raise PendingReceipt("pending receipt is orphaned; manual inspection is required")

    record = {
        "schema_version": 1,
        **normalized,
        "record_ref": receipt_relative.as_posix(),
        "record_revision": RECORD_REVISION,
        "auto_action": AUTO_ACTION,
        "created_at": _utc_timestamp(),
        "finalized_at": _utc_timestamp(),
    }
    canonical = _canonical_json(record)

    if final_info is not None:
        existing = _read_existing_json(final_path)
        if _same_record_ignoring_timestamps(existing, record):
            return final_path
        raise ReceiptConflict("final receipt already exists with different content")

    pending_created = False
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(pending_path, flags, 0o600)
        pending_created = True
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical)
            stream.flush()
            os.fsync(stream.fileno())

        # The pending file is also the single-writer reservation for other
        # instances of this writer.
        try:
            # A hard link creates the final name atomically without replacing
            # a final receipt another writer may have published in the race.
            os.link(pending_path, final_path)
        except FileExistsError:
            try:
                existing = _read_existing_json(final_path)
            except FileNotFoundError as exc:
                raise ReceiptConflict("final receipt changed during atomic finalize") from exc
            if _same_record_ignoring_timestamps(existing, record):
                _cleanup_pending(pending_path)
                if _lstat(pending_path) is not None:
                    raise ReceiptError("final receipt published but pending cleanup failed")
                pending_created = False
                return final_path
            raise ReceiptConflict("final receipt already exists with different content")
        os.unlink(pending_path)
        pending_created = False
    except ReceiptError:
        if pending_created:
            _cleanup_pending(pending_path)
        raise
    except OSError as exc:
        if pending_created:
            _cleanup_pending(pending_path)
        raise ReceiptError("receipt write failed; no retry was attempted") from exc
    except Exception:
        if pending_created:
            _cleanup_pending(pending_path)
        raise
    return final_path


def write_receipt(
    root: os.PathLike[str] | str,
    receipt: Optional[Mapping[str, Any]] = None,
    **fields: Any,
) -> Path:
    """Alias for callers that prefer the persistence-oriented name."""

    return record_receipt(root, receipt, **fields)


def record(
    root: os.PathLike[str] | str,
    receipt: Optional[Mapping[str, Any]] = None,
    **fields: Any,
) -> Path:
    """Callable counterpart of the CLI ``record`` operation."""

    return record_receipt(root, receipt, **fields)


def _number_argument(value: str) -> Any:
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("must be a finite non-negative number")
    return int(number) if number.is_integer() else number


def _integer_argument(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if number < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return number


def _add_metric_arguments(parser: argparse.ArgumentParser, metric_name: str) -> None:
    parser.add_argument(f"--{metric_name}-status", choices=sorted(_STATUSES), required=True)
    parser.add_argument(f"--{metric_name}-source", required=True)
    parser.add_argument(f"--{metric_name}-basis", required=True)
    if metric_name == "usage":
        parser.add_argument("--usage-input-tokens", type=_integer_argument)
        parser.add_argument("--usage-output-tokens", type=_integer_argument)
        parser.add_argument("--usage-cached-input-tokens", type=_integer_argument)
        parser.add_argument("--usage-total-tokens", type=_integer_argument)
        parser.add_argument("--usage-units")
    elif metric_name == "cost":
        parser.add_argument("--cost-amount", type=_number_argument)
        parser.add_argument("--cost-currency")
        parser.add_argument("--cost-units")
    else:
        parser.add_argument("--performance-latency-ms", type=_integer_argument)
        parser.add_argument("--performance-duration-ms", type=_integer_argument)
        parser.add_argument("--performance-units")


def _build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write an OpenCode adapter receipt")
    operations = parser.add_subparsers(dest="operation", required=True)
    record_parser = operations.add_parser("record", help="record one evidence-only receipt")
    record_parser.add_argument("--root", required=True)
    for name in (
        "task-id",
        "run-id",
        "attempt-id",
        "role-id",
        "planned-model",
        "planned-tier",
        "map-ref",
        "map-revision",
        "map-digest",
        "exit-state",
        "source-sha",
    ):
        record_parser.add_argument(f"--{name}", required=True)
    record_parser.add_argument("--actual-model")
    record_parser.add_argument("--actual-model-source")
    record_parser.add_argument("--artifact-ref", action="append", default=[])
    _add_metric_arguments(record_parser, "usage")
    _add_metric_arguments(record_parser, "cost")
    _add_metric_arguments(record_parser, "performance")
    return parser


def _cli_payload(arguments: argparse.Namespace) -> dict[str, Any]:
    usage = {
        "status": arguments.usage_status,
        "source": arguments.usage_source,
        "basis": arguments.usage_basis,
    }
    for field in (
        "input_tokens",
        "output_tokens",
        "cached_input_tokens",
        "total_tokens",
        "units",
    ):
        value = getattr(arguments, f"usage_{field}")
        if value is not None:
            usage[field] = value

    cost = {
        "status": arguments.cost_status,
        "source": arguments.cost_source,
        "basis": arguments.cost_basis,
    }
    for field in ("amount", "currency", "units"):
        value = getattr(arguments, f"cost_{field}")
        if value is not None:
            cost[field] = value

    performance = {
        "status": arguments.performance_status,
        "source": arguments.performance_source,
        "basis": arguments.performance_basis,
    }
    for field in ("latency_ms", "duration_ms", "units"):
        value = getattr(arguments, f"performance_{field}")
        if value is not None:
            performance[field] = value

    payload: dict[str, Any] = {
        "task_id": arguments.task_id,
        "run_id": arguments.run_id,
        "attempt_id": arguments.attempt_id,
        "role_id": arguments.role_id,
        "planned_model": arguments.planned_model,
        "planned_tier": arguments.planned_tier,
        "map_ref": arguments.map_ref,
        "map_revision": arguments.map_revision,
        "map_digest": arguments.map_digest,
        "exit_state": arguments.exit_state,
        "source_sha": arguments.source_sha,
        "usage": usage,
        "cost": cost,
        "performance": performance,
        "artifact_refs": arguments.artifact_ref,
    }
    if arguments.actual_model is not None:
        payload["actual_model"] = arguments.actual_model
    if arguments.actual_model_source is not None:
        payload["actual_model_source"] = arguments.actual_model_source
    return payload


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_cli_parser()
    arguments = parser.parse_args(argv)
    if arguments.operation != "record":
        parser.error("an operation is required")
    try:
        path = record_receipt(arguments.root, _cli_payload(arguments))
    except ReceiptError as exc:
        print(f"receipt error: {exc}", file=sys.stderr)
        return 1
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
