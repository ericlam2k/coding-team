import importlib.util, json, sys
from pathlib import Path
import pytest
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "stuck-watchdog.py"
SPEC = importlib.util.spec_from_file_location("stuck_watchdog", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC); assert SPEC and SPEC.loader; SPEC.loader.exec_module(MODULE)

def test_fast_command_completes(tmp_path):
    receipt = tmp_path / "receipt.json"
    code = MODULE.supervise([sys.executable, "-c", "print('ok')"], task_id="T-fast", run_id="R1", target_seconds=.2, hard_stop_seconds=1, receipt_path=receipt, poll_seconds=.01)
    assert code == 0; data = json.loads(receipt.read_text()); assert data["event"] == "COMPLETED"

def test_hard_stop_is_blocked_without_retry(tmp_path, monkeypatch):
    receipt = tmp_path / "receipt.json"
    monkeypatch.setattr(MODULE, "_observe_process_group", lambda pgid: MODULE._GroupObservation.QUIESCENT)
    code = MODULE.supervise([sys.executable, "-c", "import time; time.sleep(2)"], task_id="T-stuck", run_id="R2", target_seconds=.05, hard_stop_seconds=.15, receipt_path=receipt, poll_seconds=.01)
    assert code == 124; data = json.loads(receipt.read_text())
    assert data["event"] == "STUCK_REPORT" and data["status"] == "BLOCKED" and data["retry_allowed"] is False and data["receipt_id"]

def test_process_group_observer_distinguishes_quiescent_and_unavailable(monkeypatch):
    commands = []
    probes = []

    def observe(command, **kwargs):
        commands.append((command, kwargs))
        return MODULE.subprocess.CompletedProcess(command, 0, " 42 Z\n 42 Z+\n 17 S\n", "")

    monkeypatch.setattr(MODULE.subprocess, "run", observe)
    assert MODULE._observe_process_group(42) is MODULE._GroupObservation.QUIESCENT
    assert commands == [
        (["ps", "-axo", "pgid=,stat="], {"check": True, "capture_output": True, "text": True})
    ]

    def ps_denied(*args, **kwargs):
        raise OSError("ps failed")

    def probe(pgid, sig):
        probes.append((pgid, sig))
        raise ProcessLookupError

    monkeypatch.setattr(MODULE.subprocess, "run", ps_denied)
    monkeypatch.setattr(MODULE.os, "killpg", probe)
    assert MODULE._observe_process_group(42) is MODULE._GroupObservation.QUIESCENT
    assert probes == [(42, 0)]

    monkeypatch.setattr(MODULE.os, "killpg", lambda pgid, sig: None)
    assert MODULE._observe_process_group(42) is MODULE._GroupObservation.UNAVAILABLE

    def deny_probe(pgid, sig):
        raise PermissionError

    monkeypatch.setattr(MODULE.os, "killpg", deny_probe)
    assert MODULE._observe_process_group(42) is MODULE._GroupObservation.UNAVAILABLE

def test_exited_leader_live_group_is_killed_before_transform_and_one_receipt(monkeypatch):
    calls = []
    states = iter([True, True, False])

    class Process:
        pid = 42

        def poll(self):
            return 7

        def wait(self, timeout=None):
            calls.append(("wait", timeout))
            return -MODULE.signal.SIGKILL

    ticks = iter([0.0, 2.0, 2.0, 2.0])
    monkeypatch.setattr(MODULE.subprocess, "Popen", lambda *args, **kwargs: Process())
    monkeypatch.setattr(MODULE.time, "monotonic", lambda: next(ticks, 2.0))
    monkeypatch.setattr(MODULE, "_TERMINATION_GRACE_SECONDS", 0.0)
    monkeypatch.setattr(MODULE, "_observe_process_group", lambda pgid: MODULE._GroupObservation.LIVE if next(states) else MODULE._GroupObservation.QUIESCENT)
    monkeypatch.setattr(MODULE.os, "killpg", lambda pgid, sig: calls.append(("signal", sig)))
    monkeypatch.setattr(MODULE, "_write_receipt", lambda path, receipt: calls.append(("receipt", receipt)))

    def transform(observation):
        calls.append(("transform", observation))
        return {"status": "BLOCKED", "retry_allowed": False}

    code = MODULE.supervise(
        ["command"],
        task_id="T-group",
        run_id="R-group",
        target_seconds=1.0,
        hard_stop_seconds=1.5,
        receipt_path=Path("unused"),
        terminal_transform=transform,
    )

    assert code == 124
    assert [kind for kind, *_ in calls] == ["signal", "signal", "wait", "transform", "receipt"]
    assert [value for kind, value in calls if kind == "signal"] == [MODULE.signal.SIGTERM, MODULE.signal.SIGKILL]
    assert len([call for call in calls if call[0] == "transform"]) == 1
    receipts = [receipt for kind, receipt in calls if kind == "receipt"]
    assert len(receipts) == 1
    assert receipts[0]["retry_allowed"] is False

def test_exited_leader_waits_for_live_descendant_before_transform_and_receipt(monkeypatch):
    calls = []
    observations = iter([
        MODULE._GroupObservation.LIVE,
        MODULE._GroupObservation.QUIESCENT,
    ])

    class Process:
        pid = 42

        def poll(self):
            calls.append(("poll", 7))
            return 7

        def wait(self, timeout=None):
            raise AssertionError("saved direct-child exit code must be preserved")

    ticks = iter([0.0, 0.1, 0.2])
    monkeypatch.setattr(MODULE.subprocess, "Popen", lambda *args, **kwargs: Process())
    monkeypatch.setattr(MODULE.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(MODULE.time, "sleep", lambda seconds: calls.append(("sleep", seconds)))

    def observe(pgid):
        observation = next(observations)
        calls.append(("observe", observation))
        return observation

    monkeypatch.setattr(MODULE, "_observe_process_group", observe)
    monkeypatch.setattr(MODULE, "_write_receipt", lambda path, receipt: calls.append(("receipt", receipt)))

    def transform(observation):
        calls.append(("transform", observation))
        return {"status": "FAILED", "retry_allowed": False}

    code = MODULE.supervise(
        ["command"],
        task_id="T-descendant",
        run_id="R-descendant",
        target_seconds=1.0,
        hard_stop_seconds=2.0,
        receipt_path=Path("unused"),
        poll_seconds=0.01,
        terminal_transform=transform,
    )

    assert code == 7
    assert [kind for kind, *_ in calls] == [
        "poll", "observe", "sleep", "observe", "transform", "receipt"
    ]
    receipts = [receipt for kind, receipt in calls if kind == "receipt"]
    assert len(receipts) == 1
    assert receipts[0]["exit_code"] == 7
    assert receipts[0]["retry_allowed"] is False

def test_exited_leader_with_unavailable_group_is_cancelled_without_transform(monkeypatch):
    calls = []

    class Process:
        pid = 42

        def poll(self):
            return 7

        def wait(self, timeout=None):
            calls.append(("wait", timeout))
            return -MODULE.signal.SIGKILL

    ticks = iter([0.0, 2.0, 2.0, 2.0])
    observations = iter([
        MODULE._GroupObservation.UNAVAILABLE,
        MODULE._GroupObservation.UNAVAILABLE,
        MODULE._GroupObservation.UNAVAILABLE,
    ])
    monkeypatch.setattr(MODULE.subprocess, "Popen", lambda *args, **kwargs: Process())
    monkeypatch.setattr(MODULE.time, "monotonic", lambda: next(ticks, 2.0))
    monkeypatch.setattr(MODULE, "_TERMINATION_GRACE_SECONDS", 0.0)
    monkeypatch.setattr(MODULE, "_observe_process_group", lambda pgid: next(observations))
    monkeypatch.setattr(MODULE.os, "killpg", lambda pgid, sig: calls.append(("signal", sig)))
    monkeypatch.setattr(MODULE, "_write_receipt", lambda path, receipt: calls.append(("receipt", receipt)))

    def transform(observation):
        calls.append(("transform", observation))
        return {"status": "BLOCKED", "retry_allowed": False}

    code = MODULE.supervise(
        ["command"],
        task_id="T-observer-unavailable",
        run_id="R-observer-unavailable",
        target_seconds=1.0,
        hard_stop_seconds=1.5,
        receipt_path=Path("unused"),
        terminal_transform=transform,
    )

    assert code == 124
    assert [kind for kind, *_ in calls] == ["signal", "signal", "wait", "receipt"]
    assert [value for kind, value in calls if kind == "signal"] == [MODULE.signal.SIGTERM, MODULE.signal.SIGKILL]
    receipts = [receipt for kind, receipt in calls if kind == "receipt"]
    assert len(receipts) == 1
    assert receipts[0]["event"] == "BLOCKED"
    assert receipts[0]["status"] == "BLOCKED"
    assert receipts[0]["outcome_class"] == "TRANSPORT_FAILURE"
    assert receipts[0]["retry_allowed"] is False

def test_invalid_deadline_fails_closed():
    try: MODULE.supervise([sys.executable, "-c", "pass"], task_id="T", run_id="R", target_seconds=1, hard_stop_seconds=1)
    except ValueError as exc: assert "target_seconds" in str(exc)
    else: raise AssertionError("invalid deadline was accepted")

def test_receipt_publication_is_atomic_and_does_not_overwrite(tmp_path):
    receipt = tmp_path / "receipt.json"
    MODULE._write_receipt(receipt, {"event": "FIRST"})
    original = receipt.read_bytes()

    with pytest.raises(OSError):
        MODULE._write_receipt(receipt, {"event": "SECOND"})

    assert receipt.read_bytes() == original
    assert not list(tmp_path.glob(f".{receipt.name}.*.tmp"))

def test_terminal_transform_runs_once_before_receipt_and_preserves_identity(monkeypatch):
    calls = []
    receipts = []

    def transform(observation):
        calls.append(("transform", observation))
        return {
            "status": "COMPLETED",
            "outcome_class": "COMPLETED",
            "task_id": "overridden-task",
            "run_id": "overridden-run",
        }

    def write_receipt(path, receipt):
        calls.append(("write", receipt))
        receipts.append(receipt)

    monkeypatch.setattr(MODULE, "_write_receipt", write_receipt)
    code = MODULE.supervise(
        [sys.executable, "-c", "pass"],
        task_id="T-transform",
        run_id="R-transform",
        terminal_transform=transform,
    )

    assert code == 0
    assert [kind for kind, _ in calls] == ["transform", "write"]
    assert len(receipts) == 1
    observation = calls[0][1]
    assert observation["exit_code"] == 0
    assert isinstance(observation["elapsed_seconds"], float)
    assert observation["checkpoint"] is False
    assert receipts[0]["outcome_class"] == "COMPLETED"
    assert receipts[0]["task_id"] == "T-transform"
    assert receipts[0]["run_id"] == "R-transform"

def test_raised_terminal_transform_writes_transport_failure_once(monkeypatch):
    receipts = []

    def transform(observation):
        raise RuntimeError("transport unavailable")

    monkeypatch.setattr(MODULE, "_write_receipt", lambda path, receipt: receipts.append(receipt))
    code = MODULE.supervise(
        [sys.executable, "-c", "pass"],
        task_id="T-transform-error",
        run_id="R-transform-error",
        terminal_transform=transform,
    )

    assert code != 0
    assert len(receipts) == 1
    assert receipts[0]["event"] == "BLOCKED"
    assert receipts[0]["status"] == "BLOCKED"
    assert receipts[0]["outcome_class"] == "TRANSPORT_FAILURE"
    assert receipts[0]["retry_allowed"] is False
