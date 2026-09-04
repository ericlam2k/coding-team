#!/usr/bin/env python3
"""Bound a real background command and write one internal status record."""
from __future__ import annotations
import argparse, hashlib, json, os, signal, subprocess, sys, time
from enum import Enum
from pathlib import Path
from typing import Any, Callable

_TERMINATION_GRACE_SECONDS = 2.0

class _GroupObservation(Enum):
    LIVE = "live"
    QUIESCENT = "quiescent"
    UNAVAILABLE = "unavailable"

def _event(kind: str, **fields: Any) -> dict[str, Any]:
    return {"event": kind, "timestamp": time.time(), **fields}

def _observe_process_group(pgid: int) -> _GroupObservation:
    """Observe whether *pgid* is live, quiescent, or unavailable."""
    try:
        observed = subprocess.run(
            ["ps", "-axo", "pgid=,stat="],
            check=True,
            capture_output=True,
            text=True,
        )
        for line in observed.stdout.splitlines():
            fields = line.split(None, 1)
            if len(fields) != 2:
                raise ValueError("malformed ps process-group observation")
            observed_pgid, state = fields
            if int(observed_pgid) == pgid and not state.startswith("Z"):
                return _GroupObservation.LIVE
        return _GroupObservation.QUIESCENT
    except (OSError, subprocess.SubprocessError, ValueError):
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return _GroupObservation.QUIESCENT
        except PermissionError:
            return _GroupObservation.UNAVAILABLE
        except OSError:
            return _GroupObservation.UNAVAILABLE
        return _GroupObservation.UNAVAILABLE

def _write_status(path: Path | None, receipt: dict[str, Any]) -> None:
    if path is None: return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(receipt, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.link(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)

# Private compatibility alias for existing watchdog callers. The file remains
# an internal status record; this alias does not create workflow authority.
_write_receipt = _write_status

def supervise(command: list[str], *, task_id: str, run_id: str, target_seconds: float = 120.0,
              hard_stop_seconds: float = 240.0, receipt_path: Path | None = None,
              poll_seconds: float = 0.05,
              terminal_transform: Callable[[dict[str, Any]], dict[str, Any]] | None = None) -> int:
    """Run one command. 0=completed, child code=failure, 124=blocked."""
    if not command or not task_id or not run_id: raise ValueError("command, task_id, and run_id are required")
    if target_seconds <= 0 or hard_stop_seconds <= target_seconds: raise ValueError("require 0 < target_seconds < hard_stop_seconds")
    if poll_seconds <= 0: raise ValueError("poll_seconds must be positive")
    proc = subprocess.Popen(command, start_new_session=(os.name == "posix")); started = time.monotonic(); checkpoint_sent = False; terminal_sent = False
    def emit(payload: dict[str, Any]) -> None:
        nonlocal terminal_sent
        if payload["event"] in {"COMPLETED", "FAILED", "STUCK_REPORT"}:
            if terminal_sent: return
            terminal_sent = True
        print(json.dumps(payload, sort_keys=True), file=sys.stderr, flush=True)
    def finish(receipt: dict[str, Any], default_code: int, *, allow_transform: bool = True) -> int:
        if allow_transform and terminal_transform is not None:
            observation = {**receipt, "checkpoint": checkpoint_sent}
            identity = {key: observation[key] for key in ("task_id", "run_id")}
            if "receipt_id" in observation:
                identity["receipt_id"] = observation["receipt_id"]
            try:
                transformed = terminal_transform(observation)
                if not isinstance(transformed, dict):
                    raise TypeError("terminal transform must return a dict")
                receipt = {**observation, **transformed, **identity}
                status = receipt.get("status")
                if status not in {"COMPLETED", "FAILED", "BLOCKED"}:
                    raise ValueError("terminal transform returned an invalid outcome")
                if status == "COMPLETED" and not receipt.get("outcome_class"):
                    raise ValueError("COMPLETED terminal transform requires outcome_class")
                if status == "BLOCKED":
                    receipt["event"] = "BLOCKED"
                    default_code = default_code or 124
            except Exception as exc:
                receipt = {**observation, **identity, "event": "BLOCKED", "status": "BLOCKED",
                    "outcome_class": "TRANSPORT_FAILURE", "retry_allowed": False,
                    "error": f"terminal transform failed: {exc}"}
                default_code = default_code or 124
        _write_receipt(receipt_path, receipt); emit(receipt); return default_code
    child_exit_code: int | None = None
    while True:
        if child_exit_code is None:
            child_exit_code = proc.poll()
        elapsed = time.monotonic() - started
        if child_exit_code is not None and (
            os.name != "posix"
            or _observe_process_group(proc.pid) is _GroupObservation.QUIESCENT
        ):
            code = child_exit_code
            receipt = _event("COMPLETED" if code == 0 else "FAILED", task_id=task_id, run_id=run_id,
                status="COMPLETED" if code == 0 else "FAILED", exit_code=code, elapsed_seconds=round(elapsed, 3))
            return finish(receipt, code)
        if not checkpoint_sent and elapsed >= target_seconds:
            checkpoint_sent = True; emit(_event("CHECKPOINT", task_id=task_id, run_id=run_id,
                status="CHECKPOINT", elapsed_seconds=round(elapsed, 3), next_action="stop at hard_stop; do not retry unchanged task"))
        if elapsed >= hard_stop_seconds:
            if os.name == "posix":
                os.killpg(proc.pid, signal.SIGTERM)
                deadline = time.monotonic() + _TERMINATION_GRACE_SECONDS
                group_observation = _observe_process_group(proc.pid)
                while group_observation is not _GroupObservation.QUIESCENT and time.monotonic() < deadline:
                    time.sleep(poll_seconds)
                    proc.poll()
                    group_observation = _observe_process_group(proc.pid)
                if group_observation is not _GroupObservation.QUIESCENT:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                while True:
                    group_observation = _observe_process_group(proc.pid)
                    if group_observation is _GroupObservation.QUIESCENT:
                        break
                    if group_observation is _GroupObservation.UNAVAILABLE:
                        proc.wait()
                        receipt = _event("BLOCKED", task_id=task_id, run_id=run_id,
                            status="BLOCKED", outcome_class="TRANSPORT_FAILURE",
                            stop_reason="process_group_observation_unavailable",
                            elapsed_seconds=round(time.monotonic() - started, 3), exit_code=124,
                            retry_allowed=False,
                            next_action="Lead must inspect transport availability before any new bounded task")
                        return finish(receipt, 124, allow_transform=False)
                    time.sleep(poll_seconds)
                proc.wait()
            else:
                proc.terminate()
                try: proc.wait(timeout=_TERMINATION_GRACE_SECONDS)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            receipt = _event("STUCK_REPORT", task_id=task_id, run_id=run_id,
                receipt_id=hashlib.sha256(f"{task_id}:{run_id}:STUCK_REPORT".encode()).hexdigest(), status="BLOCKED",
                stop_reason="hard_stop_exceeded", elapsed_seconds=round(time.monotonic() - started, 3), exit_code=124,
                retry_allowed=False, next_action="Lead must create one smaller bounded task or ask the human")
            return finish(receipt, 124)
        time.sleep(poll_seconds)

def main() -> int:
    p = argparse.ArgumentParser(description="Fail-closed STUCK hard stop")
    p.add_argument("--task-id", required=True); p.add_argument("--run-id", required=True)
    p.add_argument("--target-seconds", type=float, default=120.0); p.add_argument("--hard-stop-seconds", type=float, default=240.0)
    p.add_argument("--receipt-path", type=Path); p.add_argument("command", nargs=argparse.REMAINDER); a = p.parse_args()
    command = a.command[1:] if a.command[:1] == ["--"] else a.command
    try: return supervise(command, task_id=a.task_id, run_id=a.run_id, target_seconds=a.target_seconds, hard_stop_seconds=a.hard_stop_seconds, receipt_path=a.receipt_path)
    except (ValueError, OSError) as exc:
        print(json.dumps({"event":"BLOCKED", "status":"BLOCKED", "error":str(exc)}), file=sys.stderr); return 2
if __name__ == "__main__": raise SystemExit(main())
