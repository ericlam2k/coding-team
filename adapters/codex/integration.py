"""Small, reversible integration seam for quantization and dispatch guarding.

The seam writes only a local candidate state.  It never selects a vendor,
dispatches a task, or treats a missing authoritative token count as safe.
Before the candidate state changes, the previous bytes are recorded in a
content-addressed checkpoint.  A failed run restores them with compare-and-
swap semantics so a concurrent writer is never silently overwritten.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from adapters.codex.message_guard import DispatchGuardError, build_guarded_messages
from core.routing.quantizer import QuantizationError, quantize_task


class IntegrationError(ValueError):
    """Stable, privacy-safe integration failure."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, RecursionError):
        raise IntegrationError("CTI-SCHEMA") from None


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_state(path: Path) -> tuple[bytes, str, bool]:
    exists = path.exists()
    try:
        raw = path.read_bytes() if exists else b""
    except OSError:
        raise IntegrationError("CTI-STATE-READ") from None
    return raw, _digest(raw), exists


def _atomic_write(path: Path, raw: bytes) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    except OSError:
        raise IntegrationError("CTI-STATE-WRITE") from None


def _checkpoint(path: Path, prior: bytes, prior_digest: str, prior_exists: bool) -> tuple[Path, str]:
    record = {"schema": "ct-integrated-checkpoint/1", "state_path": str(path),
              "prior_digest": prior_digest, "prior_exists": prior_exists,
              "prior_state": prior.decode("utf-8")}
    raw = _canonical(record)
    checkpoint_id = _digest(raw)
    checkpoint_path = path.parent / "checkpoints" / f"{checkpoint_id}.json"
    _atomic_write(checkpoint_path, raw)
    return checkpoint_path, checkpoint_id


def _restore(path: Path, expected_digest: str, prior: bytes, prior_exists: bool) -> str:
    current, current_digest, _ = _read_state(path)
    if current_digest != expected_digest:
        return "NOT_RESTORED_CONCURRENT_CHANGE"
    if prior_exists:
        _atomic_write(path, prior)
    elif path.exists():
        try:
            path.unlink()
        except OSError:
            raise IntegrationError("CTI-STATE-WRITE") from None
    return "RESTORED"


def integrate_token_tools(
    request: Mapping[str, object],
    *,
    authoritative_token_count: int,
    state_path: str | os.PathLike[str],
) -> dict[str, object]:
    """Run quantizer then guard and commit one local candidate state.

    The request must contain ``quantize`` and ``guard`` objects.  The caller
    supplies the authoritative count exactly once to the guard.
    """
    if not isinstance(request, Mapping) or set(request) != {"quantize", "guard"}:
        raise IntegrationError("CTI-SCHEMA")
    if (isinstance(authoritative_token_count, bool)
            or not isinstance(authoritative_token_count, int)
            or authoritative_token_count < 0):
        raise IntegrationError("CTI-COUNTER-INVALID")
    if not isinstance(state_path, (str, os.PathLike)):
        raise IntegrationError("CTI-SCHEMA")
    path = Path(state_path)
    prior, prior_digest, prior_exists = _read_state(path)
    checkpoint_path, checkpoint_id = _checkpoint(path, prior, prior_digest, prior_exists)

    try:
        quantized = quantize_task(request["quantize"])
        if quantized.get("status") != "ROUTED":
            raise IntegrationError(str(quantized.get("failure_code") or "CTI-QUANTIZE-BLOCKED"))
        guard_request = request["guard"]
        if not isinstance(guard_request, Mapping):
            raise IntegrationError("CTI-SCHEMA")
        required = {"static_system_prompt", "codebase_structure", "chat_history", "active_request"}
        if set(guard_request) - required - {"prefix_template_version", "platform_context_window", "reserve_tokens", "max_tokens"} or not required.issubset(guard_request):
            raise IntegrationError("CTI-SCHEMA")
        calls = 0

        def counter(_messages: object) -> int:
            nonlocal calls
            calls += 1
            if calls != 1:
                raise RuntimeError("counter called more than once")
            return authoritative_token_count

        optional = {key: guard_request[key] for key in
                    ("prefix_template_version", "platform_context_window", "reserve_tokens", "max_tokens")
                    if key in guard_request}
        guarded = build_guarded_messages(
            guard_request["static_system_prompt"], guard_request["codebase_structure"],
            guard_request["chat_history"], guard_request["active_request"], counter,
            **optional,
        )
        candidate = _canonical({"schema": "ct-integrated-state/1", "quantized": quantized,
                                "guard": guarded, "checkpoint_id": checkpoint_id})
        _atomic_write(path, candidate)
        return {"status": "COMMITTED", "checkpoint_id": checkpoint_id,
                "checkpoint_path": str(checkpoint_path), "state_digest": _digest(candidate),
                "quantized_class": quantized["quantized_class"],
                "context_level": quantized["context_level"],
                "guard_decision": guarded["decision"], "rollback": "AVAILABLE"}
    except QuantizationError as exc:
        rollback = _restore(path, prior_digest, prior, prior_exists)
        return {"status": "BLOCKED", "failure_code": exc.code,
                "checkpoint_id": checkpoint_id, "rollback": rollback}
    except DispatchGuardError as exc:
        rollback = _restore(path, prior_digest, prior, prior_exists)
        return {"status": "BLOCKED", "failure_code": exc.code,
                "checkpoint_id": checkpoint_id, "rollback": rollback}
    except IntegrationError as exc:
        rollback = _restore(path, prior_digest, prior, prior_exists)
        return {"status": "BLOCKED", "failure_code": exc.code,
                "checkpoint_id": checkpoint_id, "rollback": rollback}
    except Exception:
        rollback = _restore(path, prior_digest, prior, prior_exists)
        return {"status": "BLOCKED", "failure_code": "CTI-INTERNAL",
                "checkpoint_id": checkpoint_id, "rollback": rollback}
