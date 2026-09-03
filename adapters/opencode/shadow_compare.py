"""Read-only comparison of OpenCode receipts with optional WYSY flow fixtures.

This is an observation-only shadow.  It is not a flow authority, does not
reconcile records, and never writes to either input root.  Callers must pass a
receipt root explicitly.  A flow record is joinable only when the same object
contains ``task_id``, ``run_id``, and ``attempt_id``.  For disposable fixtures,
the same complete triple may be placed in a ``shadow_projection``,
``projection``, ``canonical_record``, or ``record`` object; this is the only
documented nested equivalent.  ``flow_id`` and WYSY's nested ``docs.run_id``
are deliberately ignored.

The CLI emits one canonical JSON report to stdout.  Pending files are not
parsed or retried; they are listed separately as ``ORPHANED`` observations.
All other malformed input, unsafe roots, symlinks, and duplicate canonical
records are contract errors and produce a non-zero CLI exit without a report.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import sys
from typing import Any, Optional


CLASSIFICATIONS = ("MATCH", "MISSING", "MISMATCH", "STALE", "UNJOINABLE")
ORPHANED = "ORPHANED"
REPORT_SCHEMA_VERSION = 1
CONTRACT_NAME = "opencode-shadow-compare-v1"

_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:@+-]{0,127}\Z")
_HEX_RE = re.compile(r"[0-9A-Fa-f]+\Z")
_SAFE_TEXT_RE = re.compile(r"[^\x00-\x1f\x7f]+\Z")
_SENSITIVE_RE = re.compile(
    r"(?:api[_ -]?key|secret|password|passwd|authorization|bearer|"
    r"private[_ -]?key|access[_ -]?token|raw[_ -]?(?:prompt|output))",
    re.IGNORECASE,
)
_SENSITIVE_VALUE_RE = re.compile(
    r"(?:sk|rk|pk)-[A-Za-z0-9_-]{8,}|-----BEGIN[ A-Z0-9_-]*KEY-----",
    re.IGNORECASE,
)
_SENSITIVE_PATH_PARTS = frozenset(
    {".env", "credentials", "credential", "secrets", "secret", "id_rsa"}
)
_CANONICAL_IDS = ("task_id", "run_id", "attempt_id")
_CONSISTENCY_FIELDS = (
    "map_ref",
    "map_revision",
    "map_digest",
    "source_sha",
)
_OPTIONAL_SHARED_FIELDS = ("role_id",)
_FLOW_PROJECTION_KEYS = (
    "shadow_projection",
    "projection",
    "canonical_record",
    "record",
)
_TIMESTAMP_KEYS = ("updated_at", "finalized_at", "created_at", "timestamp", "at")
_MAX_JSON_BYTES = 8 * 1024 * 1024


class ShadowCompareError(Exception):
    """Base class for malformed, unsafe, or contract-invalid input."""


class RootValidationError(ShadowCompareError, ValueError):
    """A supplied root is not a safe, existing directory."""


class InputValidationError(ShadowCompareError, ValueError):
    """A JSON record cannot be safely interpreted by the comparator."""


class DuplicateRecordError(ShadowCompareError):
    """More than one record claims one canonical identity."""


class _DuplicateJSONKey(ValueError):
    pass


@dataclass(frozen=True)
class _Record:
    side: str
    ref: str
    values: Mapping[str, Any]
    present: frozenset[str]
    key: Optional[tuple[str, str, str]]
    missing_ids: tuple[str, ...]


@dataclass(frozen=True)
class _Scan:
    records: tuple[_Record, ...]
    orphans: tuple[str, ...]


@dataclass(frozen=True)
class _Reference:
    kind: str
    revision: Any = None
    timestamp: Optional[datetime] = None


def _sensitive(value: str) -> bool:
    compact = re.sub(r"[^a-z0-9]+", "", value.casefold())
    return bool(
        _SENSITIVE_RE.search(value)
        or _SENSITIVE_VALUE_RE.search(value)
        or any(term in compact for term in ("rawprompt", "rawoutput", "apikey"))
    )


def _text(name: str, value: Any, *, max_length: int = 1024) -> str:
    if not isinstance(value, str) or not value or len(value) > max_length:
        raise InputValidationError(f"{name} is not a safe string")
    if not _SAFE_TEXT_RE.fullmatch(value):
        raise InputValidationError(f"{name} contains control characters")
    if _sensitive(value):
        raise InputValidationError(f"{name} contains sensitive material")
    return value


def _optional_id(name: str, value: Any) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise InputValidationError(f"{name} is not a safe opaque ID")
    return value


def _optional_model(name: str, value: Any) -> Optional[str]:
    if value is None:
        return None
    value = _text(name, value, max_length=256)
    if (
        os.path.isabs(value)
        or PurePosixPath(value).is_absolute()
        or PureWindowsPath(value).is_absolute()
        or PureWindowsPath(value).drive
    ):
        raise InputValidationError(f"{name} is an absolute path")
    return value


def _optional_reference(name: str, value: Any) -> Optional[str]:
    if value is None:
        return None
    value = _text(name, value)
    if (
        os.path.isabs(value)
        or PurePosixPath(value).is_absolute()
        or PureWindowsPath(value).is_absolute()
        or PureWindowsPath(value).drive
        or "\\" in value
        or "://" in value
    ):
        raise InputValidationError(f"{name} is not a relative local reference")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise InputValidationError(f"{name} contains path traversal")
    if any(part.casefold() in _SENSITIVE_PATH_PARTS for part in parts):
        raise InputValidationError(f"{name} contains sensitive material")
    return value


def _optional_digest(name: str, value: Any) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not value or not _HEX_RE.fullmatch(value):
        raise InputValidationError(f"{name} is not a hexadecimal digest")
    return value.casefold()


def _optional_revision(name: str, value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise InputValidationError(f"{name} is not a revision")
    if isinstance(value, int):
        if value < 0:
            raise InputValidationError(f"{name} is negative")
        return value
    return _text(name, value, max_length=256)


def _parse_timestamp(name: str, value: Any) -> datetime:
    value = _text(name, value, max_length=128)
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise InputValidationError(f"{name} is not an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise InputValidationError(f"{name} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJSONKey(key)
        result[key] = value
    return result


def _load_json(path: Path, ref: str) -> Any:
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(os.fspath(path), flags)
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode):
                raise InputValidationError(f"non-regular JSON input: {ref}")
            with os.fdopen(descriptor, "rb") as stream:
                descriptor = -1
                raw = stream.read(_MAX_JSON_BYTES + 1)
        finally:
            if descriptor != -1:
                os.close(descriptor)
    except InputValidationError:
        raise
    except (OSError, UnicodeError) as exc:
        raise InputValidationError(f"could not read JSON input: {ref}") from exc
    if len(raw) > _MAX_JSON_BYTES:
        raise InputValidationError(f"JSON input is too large: {ref}")
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_json_object,
            parse_constant=lambda constant: (_ for _ in ()).throw(
                ValueError(f"invalid JSON constant: {constant}")
            ),
        )
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise InputValidationError(f"malformed JSON input: {ref}") from exc


def _lstat(path: Path) -> Optional[os.stat_result]:
    try:
        return os.lstat(path)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise RootValidationError("could not inspect input root") from exc


def _reject_symlink_components(path: Path) -> None:
    current = Path(path.anchor)
    components = path.parts[1:]
    for index, component in enumerate(components):
        current /= component
        info = _lstat(current)
        if info is not None and stat.S_ISLNK(info.st_mode):
            if index < len(components) - 1 and current.as_posix() in {"/var", "/tmp"}:
                # macOS commonly exposes temporary directories through these
                # aliases.  They are platform roots, not fixture-controlled
                # traversal links; the supplied root itself is still checked.
                continue
            raise RootValidationError("symlink path components are not accepted")


def _validate_root(root: os.PathLike[str] | str, label: str) -> Path:
    try:
        raw = os.fspath(root)
    except TypeError as exc:
        raise RootValidationError(f"{label} must be a filesystem path") from exc
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        raise RootValidationError(f"{label} must be a non-empty filesystem path")
    supplied = Path(raw)
    if not supplied.is_absolute():
        supplied = Path.cwd() / supplied
    supplied = Path(os.path.abspath(os.fspath(supplied)))
    _reject_symlink_components(supplied)
    try:
        resolved = supplied.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise RootValidationError(f"{label} does not exist") from exc
    # Resolve ordinary platform aliases such as macOS /var first.  The final
    # root itself and every child visited below are still checked with lstat.
    _reject_symlink_components(resolved)
    info = _lstat(resolved)
    if info is None or stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise RootValidationError(f"{label} must be a directory")
    return resolved


def _relative_ref(path: Path, root: Path) -> str:
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise RootValidationError("input traversal escaped its root") from exc
    parts = relative.split("/")
    if not relative or any(part in {"", ".", ".."} for part in parts):
        raise RootValidationError("input traversal produced an unsafe reference")
    if any(_sensitive(part) or part.casefold() in _SENSITIVE_PATH_PARTS for part in parts):
        return "/".join(
            "[redacted]"
            if _sensitive(part) or part.casefold() in _SENSITIVE_PATH_PARTS
            else part
            for part in parts
        )
    return relative


def _walk_json(root: Path, side: str) -> _Scan:
    records: list[_Record] = []
    orphans: list[str] = []

    def visit(directory: Path) -> None:
        info = _lstat(directory)
        if info is None or stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise RootValidationError("input traversal encountered an unsafe directory")
        try:
            children = sorted(directory.iterdir(), key=lambda item: item.name)
        except OSError as exc:
            raise RootValidationError("could not traverse input root") from exc
        for child in children:
            child_info = _lstat(child)
            if child_info is None:
                raise RootValidationError("input changed during traversal")
            if stat.S_ISLNK(child_info.st_mode):
                raise RootValidationError("symlinks are not accepted during traversal")
            ref = _relative_ref(child, root)
            if child.name.endswith(".pending"):
                orphans.append(ref)
                continue
            if stat.S_ISDIR(child_info.st_mode):
                visit(child)
                continue
            if not stat.S_ISREG(child_info.st_mode):
                raise RootValidationError("non-regular input encountered during traversal")
            if child.suffix.casefold() != ".json":
                continue
            document = _load_json(child, ref)
            if isinstance(document, list):
                documents = [(f"{ref}#{index}", value) for index, value in enumerate(document)]
            else:
                documents = [(ref, document)]
            for document_ref, value in documents:
                if not isinstance(value, Mapping):
                    raise InputValidationError(f"JSON record is not an object: {document_ref}")
                records.append(_normalise_record(side, document_ref, value))

    visit(root)
    return _Scan(tuple(records), tuple(sorted(orphans)))


def _flow_source(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    if any(key in payload for key in _CANONICAL_IDS):
        return payload
    for key in _FLOW_PROJECTION_KEYS:
        candidate = payload.get(key)
        if isinstance(candidate, Mapping) and any(
            name in candidate for name in _CANONICAL_IDS
        ):
            return candidate
    return payload


def _value(source: Mapping[str, Any], payload: Mapping[str, Any], name: str) -> tuple[bool, Any]:
    if name in source:
        return True, source[name]
    if source is not payload and name in payload:
        return True, payload[name]
    return False, None


def _normalise_record(side: str, ref: str, payload: Mapping[str, Any]) -> _Record:
    source = payload if side == "receipt" else _flow_source(payload)
    values: dict[str, Any] = {}
    present: set[str] = set()

    for field in _CANONICAL_IDS:
        found, value = _value(source, payload, field)
        if found and value is not None:
            values[field] = _optional_id(field, value)
            present.add(field)

    found, value = _value(source, payload, "role_id")
    if found and value is not None:
        values["role_id"] = _optional_id("role_id", value)
        present.add("role_id")

    for field in ("planned_model", "actual_model", "actual_model_status"):
        found, value = _value(source, payload, field)
        if found and value is not None:
            if field == "actual_model_status":
                values[field] = _text(field, value, max_length=128)
            else:
                values[field] = _optional_model(field, value)
            present.add(field)

    for field in ("map_ref",):
        found, value = _value(source, payload, field)
        if found and value is not None:
            values[field] = _optional_reference(field, value)
            present.add(field)
    for field in ("map_digest", "source_sha"):
        found, value = _value(source, payload, field)
        if found and value is not None:
            values[field] = _optional_digest(field, value)
            present.add(field)
    found, value = _value(source, payload, "map_revision")
    if found and value is not None:
        values["map_revision"] = _optional_revision("map_revision", value)
        present.add("map_revision")

    revision_found = False
    for field in ("record_revision", "revision"):
        found, value = _value(source, payload, field)
        if found and value is not None:
            values["revision"] = _optional_revision(field, value)
            present.add("revision")
            revision_found = True
            break
    if not revision_found:
        values["revision"] = None

    timestamp_found = False
    for field in _TIMESTAMP_KEYS:
        found, value = _value(source, payload, field)
        if found and value is not None:
            values["timestamp"] = _parse_timestamp(field, value)
            present.add("timestamp")
            timestamp_found = True
            break
    if not timestamp_found:
        values["timestamp"] = None

    missing_ids = tuple(field for field in _CANONICAL_IDS if field not in values)
    key = None if missing_ids else tuple(values[field] for field in _CANONICAL_IDS)  # type: ignore[assignment]
    return _Record(side, ref, values, frozenset(present), key, missing_ids)


def _record_maps(records: Sequence[_Record], side: str) -> dict[tuple[str, str, str], _Record]:
    result: dict[tuple[str, str, str], _Record] = {}
    for record in records:
        if record.side != side or record.key is None:
            continue
        if record.key in result:
            raise DuplicateRecordError(f"duplicate {side} canonical record")
        result[record.key] = record
    return result


def _equal(field: str, left: Any, right: Any) -> bool:
    if field in {"map_digest", "source_sha"}:
        return isinstance(left, str) and isinstance(right, str) and left.casefold() == right.casefold()
    if field == "map_revision":
        left_number = _number(left)
        right_number = _number(right)
        if left_number is not None and right_number is not None:
            return left_number == right_number
    return left == right


def _differences(receipt: _Record, flow: _Record) -> tuple[str, ...]:
    differences: list[str] = []
    for field in _CANONICAL_IDS:
        if not _equal(field, receipt.values.get(field), flow.values.get(field)):
            differences.append(field)
    for field in _CONSISTENCY_FIELDS:
        if field not in flow.present:
            differences.append(f"{field} missing on flow")
        elif field not in receipt.present or not _equal(
            field, receipt.values.get(field), flow.values.get(field)
        ):
            differences.append(field)
    for field in _OPTIONAL_SHARED_FIELDS:
        if field in flow.present and field in receipt.present and not _equal(
            field, receipt.values.get(field), flow.values.get(field)
        ):
            differences.append(field)
    return tuple(sorted(set(differences)))


def _number(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdecimal():
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _older(candidate: _Record, reference: _Record | _Reference) -> tuple[str, ...]:
    if isinstance(reference, _Record):
        reference_revision = reference.values.get("revision")
        reference_timestamp = reference.values.get("timestamp")
    else:
        reference_revision = reference.revision
        reference_timestamp = reference.timestamp
    reasons: list[str] = []
    candidate_revision = candidate.values.get("revision")
    if candidate_revision is not None and reference_revision is not None:
        candidate_number = _number(candidate_revision)
        reference_number = _number(reference_revision)
        if candidate_number is not None and reference_number is not None:
            if candidate_number < reference_number:
                reasons.append("revision")
    candidate_timestamp = candidate.values.get("timestamp")
    if isinstance(candidate_timestamp, datetime) and isinstance(reference_timestamp, datetime):
        if candidate_timestamp < reference_timestamp:
            reasons.append("timestamp")
    return tuple(reasons)


def _reference(
    reference: Optional[str],
    *,
    selected_reference: Optional[str],
    reference_revision: Any,
    reference_timestamp: Optional[str],
) -> Optional[_Reference]:
    if reference is not None and selected_reference is not None:
        raise ShadowCompareError("reference was supplied more than once")
    kind = reference or selected_reference
    if kind is not None:
        if not isinstance(kind, str):
            raise ShadowCompareError("reference must be receipt, flow, or newest")
        kind = kind.casefold()
        aliases = {"current": "flow", "fixture": "receipt"}
        kind = aliases.get(kind, kind)
        if kind not in {"receipt", "flow", "newest", "external"}:
            raise ShadowCompareError("reference must be receipt, flow, newest, or external")
    if reference_revision is not None or reference_timestamp is not None:
        if kind in {"receipt", "flow", "newest"}:
            raise ShadowCompareError("external reference values cannot use a side reference")
        kind = "external"
    if kind is None:
        return None
    revision = _optional_revision("reference_revision", reference_revision)
    timestamp = (
        _parse_timestamp("reference_timestamp", reference_timestamp)
        if reference_timestamp is not None
        else None
    )
    if kind == "external" and revision is None and timestamp is None:
        raise ShadowCompareError("an external reference needs a revision or timestamp")
    return _Reference(kind, revision, timestamp)


def _stale_reason(
    receipt: _Record, flow: _Record, reference: Optional[_Reference]
) -> Optional[str]:
    if reference is None:
        return None
    stale_side: Optional[str] = None
    dimensions: tuple[str, ...] = ()
    if reference.kind == "receipt":
        dimensions = _older(flow, receipt)
        if dimensions:
            stale_side = "flow"
    elif reference.kind == "flow":
        dimensions = _older(receipt, flow)
        if dimensions:
            stale_side = "receipt"
    elif reference.kind == "external":
        receipt_dimensions = _older(receipt, reference)
        flow_dimensions = _older(flow, reference)
        if receipt_dimensions and flow_dimensions:
            # Both sides are older than an external reference.  Keep the
            # reason deterministic without selecting an authority.
            return "receipt and flow revision/timestamp are older than selected reference"
        if receipt_dimensions:
            stale_side, dimensions = "receipt", receipt_dimensions
        elif flow_dimensions:
            stale_side, dimensions = "flow", flow_dimensions
    else:  # newest
        receipt_dimensions = _older(receipt, flow)
        flow_dimensions = _older(flow, receipt)
        if receipt_dimensions and not flow_dimensions:
            stale_side, dimensions = "receipt", receipt_dimensions
        elif flow_dimensions and not receipt_dimensions:
            stale_side, dimensions = "flow", flow_dimensions
        elif receipt_dimensions and flow_dimensions:
            return "receipt and flow have conflicting older revision/timestamp signals"
    if stale_side is None:
        return None
    return f"{stale_side} {','.join(dimensions)} is older than selected reference"


def _output_ref(ref: Optional[str]) -> Optional[str]:
    return ref


def _entry(
    classification: str,
    *,
    receipt: Optional[_Record] = None,
    flow: Optional[_Record] = None,
    reason: str,
) -> dict[str, Any]:
    source = receipt or flow
    receipt_values = receipt.values if receipt is not None else {}
    return {
        "classification": classification,
        "receipt_ref": _output_ref(receipt.ref) if receipt is not None else None,
        "flow_ref": _output_ref(flow.ref) if flow is not None else None,
        "role_id": receipt_values.get("role_id"),
        "planned_model": receipt_values.get("planned_model"),
        "actual_model": receipt_values.get("actual_model"),
        "actual_model_status": receipt_values.get("actual_model_status"),
        "task_id": source.values.get("task_id") if source is not None else None,
        "run_id": source.values.get("run_id") if source is not None else None,
        "attempt_id": source.values.get("attempt_id") if source is not None else None,
        "reason": reason,
    }


def _entry_sort_key(entry: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(str(entry.get(field) or "") for field in (
        "task_id",
        "run_id",
        "attempt_id",
        "receipt_ref",
        "flow_ref",
        "classification",
    ))


def compare(
    receipt_root: os.PathLike[str] | str,
    flow_root: os.PathLike[str] | str | None = None,
    *,
    reference: Optional[str] = None,
    selected_reference: Optional[str] = None,
    reference_revision: Any = None,
    reference_timestamp: Optional[str] = None,
) -> dict[str, Any]:
    """Return a deterministic, read-only comparison report.

    ``reference``/``selected_reference`` may be ``receipt``, ``flow``, or
    ``newest``.  Without one, currentness is not guessed and no ``STALE``
    result is produced.  ``reference_revision`` and/or
    ``reference_timestamp`` provide an explicit external reference instead.
    """

    validated_receipt_root = _validate_root(receipt_root, "receipt root")
    validated_flow_root = (
        _validate_root(flow_root, "flow root") if flow_root is not None else None
    )
    receipt_scan = _walk_json(validated_receipt_root, "receipt")
    flow_scan = (
        _walk_json(validated_flow_root, "flow")
        if validated_flow_root is not None
        else _Scan((), ())
    )
    selected = _reference(
        reference,
        selected_reference=selected_reference,
        reference_revision=reference_revision,
        reference_timestamp=reference_timestamp,
    )
    receipt_records = _record_maps(receipt_scan.records, "receipt")
    flow_records = _record_maps(flow_scan.records, "flow")

    entries: list[dict[str, Any]] = []
    for key in sorted(set(receipt_records) | set(flow_records)):
        receipt = receipt_records.get(key)
        flow = flow_records.get(key)
        if receipt is None:
            entries.append(
                _entry(
                    "MISSING",
                    flow=flow,
                    reason="expected receipt record is absent for canonical key",
                )
            )
            continue
        if flow is None:
            entries.append(
                _entry(
                    "MISSING",
                    receipt=receipt,
                    reason="expected flow record is absent for canonical key",
                )
            )
            continue
        differences = _differences(receipt, flow)
        stale_reason = _stale_reason(receipt, flow, selected)
        if differences:
            reason = "trusted shared field differs: " + ", ".join(differences)
            classification = "MISMATCH"
        elif stale_reason is not None:
            reason = stale_reason
            classification = "STALE"
        else:
            reason = "canonical IDs and trusted shared fields agree"
            classification = "MATCH"
        entries.append(
            _entry(classification, receipt=receipt, flow=flow, reason=reason)
        )

    for record in (*receipt_scan.records, *flow_scan.records):
        if record.key is not None:
            continue
        missing = ", ".join(record.missing_ids) or "task_id, run_id, attempt_id"
        entries.append(
            _entry(
                "UNJOINABLE",
                receipt=record if record.side == "receipt" else None,
                flow=record if record.side == "flow" else None,
                reason=f"canonical task_id/run_id/attempt_id is incomplete: {missing}",
            )
        )

    entries.sort(key=_entry_sort_key)
    summary = {classification: 0 for classification in CLASSIFICATIONS}
    for entry in entries:
        summary[entry["classification"]] += 1
    orphans = [
        {"classification": ORPHANED, "side": side, "ref": ref, "reason": "pending input ignored"}
        for side, scan in (("receipt", receipt_scan), ("flow", flow_scan))
        for ref in scan.orphans
    ]
    orphans.sort(key=lambda item: (str(item["side"]), str(item["ref"])))
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "contract": CONTRACT_NAME,
        "mode": "read-only-shadow",
        "reference": selected.kind if selected is not None else None,
        "summary": summary,
        "entries": entries,
        "orphans": orphans,
    }


def compare_records(
    receipt_root: os.PathLike[str] | str,
    flow_root: os.PathLike[str] | str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Callable alias for integrations that use record-oriented naming."""

    return compare(receipt_root, flow_root, **kwargs)


def canonical_json(report: Mapping[str, Any]) -> str:
    """Serialize a report without timestamps, paths, or environment data."""

    try:
        return json.dumps(
            report,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ) + "\n"
    except (TypeError, ValueError) as exc:
        raise ShadowCompareError("report is not canonical JSON") from exc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shadow_compare",
        description="Compare OpenCode receipts without writing",
    )
    parser.add_argument(
        "--receipt-root",
        "--receipts-root",
        dest="receipt_root",
        required=True,
        help="explicit nested receipt directory",
    )
    parser.add_argument(
        "--flow-root",
        "--wysy-flow-root",
        dest="flow_root",
        help="optional explicit read-only WYSY flow directory",
    )
    parser.add_argument(
        "--reference",
        "--reference-side",
        dest="reference",
        choices=("receipt", "flow", "newest", "current", "fixture", "external"),
        help="explicit side used for stale checks; omitted means no freshness claim",
    )
    parser.add_argument("--reference-revision", dest="reference_revision")
    parser.add_argument("--reference-timestamp", dest="reference_timestamp")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    try:
        arguments = parser.parse_args(argv)
        report = compare(
            arguments.receipt_root,
            arguments.flow_root,
            reference=arguments.reference,
            reference_revision=arguments.reference_revision,
            reference_timestamp=arguments.reference_timestamp,
        )
        sys.stdout.write(canonical_json(report))
        return 0
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else 1
    except (ShadowCompareError, OSError, ValueError) as exc:
        print(f"shadow compare error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
