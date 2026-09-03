"""Frozen S1-S6 acceptance matrix for the supervised critical-task launcher."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "supervised-critical-task.py"
SPEC = importlib.util.spec_from_file_location("supervised_critical_task", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
supervised = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = supervised
SPEC.loader.exec_module(supervised)


BASE_CONTENT = "original candidate content\n"
PROFILE_CONTENT = "private profile raw material\n"
DISPATCH_ID = "ctd_0123456789abcdef01234567"


def _run(*command: str, cwd: Path) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def _new_candidate(root: Path) -> tuple[Path, str, Path, str]:
    candidate = root / "candidate"
    candidate.mkdir()
    _run("git", "init", "--quiet", cwd=candidate)
    _run("git", "config", "user.name", "Critical Runner Test", cwd=candidate)
    _run("git", "config", "user.email", "critical-runner@example.invalid", cwd=candidate)
    (candidate / "owned.txt").write_text(BASE_CONTENT, encoding="utf-8")
    profile = candidate / "private-profile.txt"
    profile.write_text(PROFILE_CONTENT, encoding="utf-8")
    _run("git", "add", "owned.txt", "private-profile.txt", cwd=candidate)
    _run("git", "commit", "--quiet", "-m", "fixture", cwd=candidate)
    commit = _run("git", "rev-parse", "HEAD", cwd=candidate)
    digest = hashlib.sha256(profile.read_bytes()).hexdigest()
    return candidate, commit, profile, digest


def _once_prefix() -> str:
    return (
        "from pathlib import Path; import sys; "
        "marker=Path(sys.argv[1]); "
        "assert not marker.exists(), 'command invoked more than once'; "
        "marker.write_text('1\\n', encoding='utf-8'); "
    )


def _ready_dispatch(**spawn_overrides: object) -> dict[str, object]:
    spawn: dict[str, object] = {
        "agent_type": "worker",
        "task_name": "wysy_critical_runner_be03b1a",
        "fork_turns": "3",
        "message": "Canonical role: backend-engineer\nObjective: load READY dispatch",
        "model": "gpt-5.6-sol",
        "reasoning_effort": "medium",
    }
    spawn.update(spawn_overrides)
    return {"status": "READY", "dispatch_id": DISPATCH_ID, "spawn": spawn}


def _critical_ready_dispatch(
    task_id: str, **run_overrides: object
) -> dict[str, object]:
    supervised_run: dict[str, object] = {
        "role": "code-reviewer",
        "task_id": task_id,
        "message": "Canonical role: code-reviewer\nObjective: review the candidate",
        "model": "OR-Ox",
        "effort": "high",
        "fork_turns": "3",
        "timing": {
            "target": 1,
            "checkpoint": 1.5,
            "hard_stop": 2,
            "max_hard_cap": 3,
            "reserve": 0.5,
            "provenance": "MEASURED",
        },
    }
    supervised_run.update(run_overrides)
    return {
        "status": "READY",
        "dispatch_id": DISPATCH_ID,
        "supervised_run": supervised_run,
    }


def test_load_ready_dispatch_returns_immutable_normalized_value(tmp_path: Path) -> None:
    path = tmp_path / "dispatch.json"
    path.write_text(json.dumps(_ready_dispatch()), encoding="utf-8")

    dispatch = supervised.load_ready_dispatch(path, DISPATCH_ID)

    assert dispatch == supervised.PreparedDispatch(
        dispatch_id=DISPATCH_ID,
        agent_type="worker",
        task_name="wysy_critical_runner_be03b1a",
        fork_turns="3",
        message="Canonical role: backend-engineer Objective: load READY dispatch",
        model="gpt-5.6-sol",
        reasoning_effort="medium",
    )
    with pytest.raises(AttributeError):
        dispatch.model = "changed"


def test_load_ready_dispatch_accepts_supported_underscored_agent_type(
    tmp_path: Path,
) -> None:
    path = tmp_path / "dispatch.json"
    path.write_text(
        json.dumps(_ready_dispatch(agent_type="test_engineer")), encoding="utf-8"
    )

    assert supervised.load_ready_dispatch(path, DISPATCH_ID).agent_type == "test_engineer"


def test_load_ready_dispatch_accepts_identity_bound_supervised_run(
    tmp_path: Path,
) -> None:
    task_id = "WYSY-CRITICAL-REVIEW"
    path = tmp_path / "dispatch.json"
    path.write_text(json.dumps(_critical_ready_dispatch(task_id)), encoding="utf-8")

    dispatch = supervised.load_ready_dispatch(
        path,
        DISPATCH_ID,
        expected_task_id=task_id,
        expected_target_seconds=1,
        expected_hard_stop_seconds=2,
    )

    assert dispatch == supervised.PreparedSupervisedRun(
        dispatch_id=DISPATCH_ID,
        role="code-reviewer",
        task_id=task_id,
        fork_turns="3",
        message="Canonical role: code-reviewer Objective: review the candidate",
        model="OR-Ox",
        reasoning_effort="high",
        timing=supervised.SupervisedTiming(
            target=1,
            checkpoint=1.5,
            hard_stop=2,
            max_hard_cap=3,
            reserve=0.5,
            provenance="MEASURED",
        ),
    )


def test_watchdog_timing_bounds_select_route_specific_values() -> None:
    packet = supervised.OuterAttemptPacket(
        context=supervised.AttemptContext(
            task_id="WYSY-CRITICAL-REVIEW",
            run_id="run",
            attempt_id="attempt",
            join_id="join",
            candidate_root="/tmp/candidate",
            candidate_commit="a" * 40,
            owned_paths=("owned.txt",),
            reserved_artifact="/tmp/handoff.md",
            worker_state_path="/tmp/worker.json",
            profile_path="/tmp/profile.txt",
            profile_version="profile-v1",
            profile_digest="b" * 64,
        ),
        dispatch_ready_path="/tmp/dispatch.json",
        expected_dispatch_id=DISPATCH_ID,
        validation_command=("true",),
        adaptive_target_seconds=1,
        hard_stop_seconds=2,
    )
    critical = supervised.PreparedSupervisedRun(
        dispatch_id=DISPATCH_ID,
        role="code-reviewer",
        task_id="WYSY-CRITICAL-REVIEW",
        fork_turns="3",
        message="Canonical role: code-reviewer",
        model="OR-Ox",
        reasoning_effort="high",
        timing=supervised.SupervisedTiming(
            target=1,
            checkpoint=1.5,
            hard_stop=2,
            max_hard_cap=3,
            reserve=0.5,
            provenance="MEASURED",
        ),
    )
    legacy = supervised.PreparedDispatch(
        dispatch_id=DISPATCH_ID,
        agent_type="worker",
        task_name="wysy_critical_runner_be03b1a",
        fork_turns="3",
        message="Canonical role: backend-engineer",
        model="gpt-5.6-sol",
        reasoning_effort="medium",
    )

    assert supervised.watchdog_timing_bounds(packet, critical) == (1.5, 2)
    assert supervised.watchdog_timing_bounds(packet, legacy) == (1, 2)


def test_outer_preflight_consumes_supervised_run_as_codex_exec(
    tmp_path: Path,
) -> None:
    candidate, commit, profile, profile_digest = _new_candidate(tmp_path)
    artifact = tmp_path / "private" / "handoff.md"
    artifact.parent.mkdir()
    worker_state = tmp_path / "state" / "worker.json"
    worker_state.parent.mkdir()
    task_id = "WYSY-CRITICAL-POSITIVE"
    dispatch_path = tmp_path / "dispatch.json"
    dispatch_path.write_text(
        json.dumps(_critical_ready_dispatch(task_id)), encoding="utf-8"
    )
    packet_value = _outer_packet(
        "POSITIVE",
        candidate,
        commit,
        profile,
        profile_digest,
        artifact,
        worker_state,
        dispatch_path,
        [sys.executable, "-c", "raise AssertionError('not executed by preflight')"],
    )
    packet_value["task_id"] = task_id
    packet_value["join_id"] = supervised.derive_join_id(
        task_id,
        packet_value["run_id"],
        packet_value["attempt_id"],
        str(artifact),
        commit,
    )

    packet, dispatch = supervised.preflight_outer_attempt(
        supervised.validate_outer_attempt_packet(packet_value)
    )
    command = supervised.build_codex_exec(packet.context, dispatch)

    assert isinstance(dispatch, supervised.PreparedSupervisedRun)
    assert command[-1] == dispatch.message
    assert command[command.index("-m") + 1] == "OR-Ox"
    assert 'model_reasoning_effort="high"' in command


@pytest.mark.parametrize(
    "mutation",
    (
        "mixed-shape",
        "missing-field",
        "unknown-field",
        "mismatched-task",
        "mismatched-target",
        "mismatched-hard-stop",
        "unsupported-role",
        "non-positive-fork",
        "invalid-timing",
        "unbounded-timing",
    ),
)
def test_outer_attempt_rejects_invalid_supervised_run_before_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    candidate, commit, profile, profile_digest = _new_candidate(tmp_path)
    artifact = tmp_path / "private" / "handoff.md"
    artifact.parent.mkdir()
    worker_state = tmp_path / "state" / "worker.json"
    worker_state.parent.mkdir()
    task_id = "WYSY-CRITICAL-FAIL-CLOSED"
    document = _critical_ready_dispatch(task_id)
    run = document["supervised_run"]
    assert isinstance(run, dict)
    timing = run["timing"]
    assert isinstance(timing, dict)
    if mutation == "mixed-shape":
        document["spawn"] = _ready_dispatch()["spawn"]
    elif mutation == "missing-field":
        del run["message"]
    elif mutation == "unknown-field":
        run["extra"] = "unknown"
    elif mutation == "mismatched-task":
        run["task_id"] = "WYSY-CRITICAL-OTHER"
    elif mutation == "mismatched-target":
        timing["target"] = 0.75
    elif mutation == "mismatched-hard-stop":
        timing["hard_stop"] = 2.5
    elif mutation == "unsupported-role":
        run["role"] = "backend-engineer"
    elif mutation == "non-positive-fork":
        run["fork_turns"] = "0"
    elif mutation == "invalid-timing":
        timing["checkpoint"] = 3
    elif mutation == "unbounded-timing":
        del timing["max_hard_cap"]

    dispatch_path = tmp_path / "dispatch.json"
    dispatch_path.write_text(json.dumps(document), encoding="utf-8")
    packet = _outer_packet(
        "FAIL-CLOSED",
        candidate,
        commit,
        profile,
        profile_digest,
        artifact,
        worker_state,
        dispatch_path,
        [sys.executable, "-c", "raise AssertionError('must not validate')"],
    )
    packet["task_id"] = task_id
    packet["join_id"] = supervised.derive_join_id(
        task_id, packet["run_id"], packet["attempt_id"], str(artifact), commit
    )
    attempt = tmp_path / "attempt.json"
    attempt.write_text(json.dumps(packet), encoding="utf-8")
    receipt = tmp_path / "receipt.json"
    monkeypatch.setattr(
        supervised.watchdog,
        "supervise",
        lambda *args, **kwargs: pytest.fail("watchdog must not execute"),
    )

    with pytest.raises(ValueError):
        supervised.run_outer_attempt(attempt, receipt)

    assert not receipt.exists()
    assert not worker_state.exists()


@pytest.mark.parametrize(
    ("document", "expected_id"),
    (
        (None, "ctd_aaaaaaaaaaaaaaaaaaaaaaaa"),
        ({"status": "BLOCKED", "dispatch_id": DISPATCH_ID, "spawn": {}}, DISPATCH_ID),
        (_ready_dispatch(), "ctd_aaaaaaaaaaaaaaaaaaaaaaaa"),
        (_ready_dispatch(message="opaque:abc123"), DISPATCH_ID),
        (_ready_dispatch(model=""), DISPATCH_ID),
        (_ready_dispatch(reasoning_effort="ultra"), DISPATCH_ID),
        (_ready_dispatch(fork_turns="all"), DISPATCH_ID),
        (_ready_dispatch(extra="unknown"), DISPATCH_ID),
    ),
    ids=(
        "missing",
        "blocked",
        "mismatched-id",
        "opaque-message",
        "empty-model",
        "unknown-effort",
        "unsupported-full-history",
        "unknown-spawn-shape",
    ),
)
def test_load_ready_dispatch_rejects_untrusted_documents(
    tmp_path: Path, document: dict[str, object] | None, expected_id: str
) -> None:
    path = tmp_path / "dispatch.json"
    if document is not None:
        path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError):
        supervised.load_ready_dispatch(path, expected_id)


@pytest.mark.parametrize(
    "raw",
    (
        "{not-json",
        '{"status":"READY","status":"BLOCKED","dispatch_id":"ctd_0123456789abcdef01234567","spawn":{}}',
    ),
    ids=("malformed", "duplicate-key"),
)
def test_load_ready_dispatch_rejects_malformed_or_duplicate_json(
    tmp_path: Path, raw: str
) -> None:
    path = tmp_path / "dispatch.json"
    path.write_text(raw, encoding="utf-8")

    with pytest.raises(ValueError):
        supervised.load_ready_dispatch(path, DISPATCH_ID)


def test_load_ready_dispatch_rejects_symlink_and_oversized_file(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_text(json.dumps(_ready_dispatch()), encoding="utf-8")
    link = tmp_path / "dispatch-link.json"
    link.symlink_to(target)
    oversized = tmp_path / "oversized.json"
    oversized.write_bytes(b" " * (supervised._MAX_PREPARED_DISPATCH_BYTES + 1))

    with pytest.raises(ValueError):
        supervised.load_ready_dispatch(link, DISPATCH_ID)
    with pytest.raises(ValueError):
        supervised.load_ready_dispatch(oversized, DISPATCH_ID)


def _install_fake_codex(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    codex = fake_bin / "codex"
    codex.write_text(
        """#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys
import time

args = sys.argv[1:]
assert len(args) == 13
assert args[:5] == ["exec", "--ephemeral", "-s", "workspace-write", "-C"]
assert args[6] == "-o"
assert args[8] == "-m"
assert args[10] == "-c"
assert args[11] == 'model_reasoning_effort="medium"'
assert args[12] == os.environ["FAKE_CODEX_MESSAGE"]
marker = Path(os.environ["FAKE_CODEX_MARKER"])
assert not marker.exists(), "codex invoked more than once"
marker.write_text("1\\n", encoding="utf-8")
Path(os.environ["FAKE_CODEX_INVOCATION"]).write_text(
    json.dumps(args), encoding="utf-8"
)
if os.environ["FAKE_CODEX_MUTATION"] == "1":
    (Path(args[5]) / "owned.txt").write_text(
        os.environ["FAKE_CODEX_CONTENT"], encoding="utf-8"
    )
if os.environ["FAKE_CODEX_HANDOFF"] == "1":
    Path(args[7]).write_text(
        "handoff for " + os.environ["FAKE_CODEX_CONTENT"], encoding="utf-8"
    )
if os.environ["FAKE_CODEX_SLEEP"] == "1":
    time.sleep(10)
raise SystemExit(int(os.environ["FAKE_CODEX_EXIT"]))
""",
        encoding="utf-8",
    )
    codex.chmod(0o755)
    monkeypatch.setenv("PATH", str(fake_bin) + os.pathsep + os.environ["PATH"])


def _outer_packet(
    scenario: str,
    candidate: Path,
    commit: str,
    profile: Path,
    profile_digest: str,
    artifact: Path,
    worker_state: Path,
    dispatch_path: Path,
    validation_command: list[str],
) -> dict[str, object]:
    task_id = f"WYSY-CRITICAL-{scenario}"
    run_id = f"private-sol-{scenario}"
    return {
        "task_id": task_id,
        "run_id": run_id,
        "attempt_id": "attempt-1",
        "join_id": supervised.derive_join_id(
            task_id, run_id, "attempt-1", str(artifact), commit
        ),
        "candidate_root": str(candidate),
        "candidate_commit": commit,
        "owned_paths": ["owned.txt"],
        "reserved_artifact": str(artifact),
        "worker_state_path": str(worker_state),
        "profile_path": str(profile),
        "profile_version": "private-sol-carry-forward-v1",
        "profile_digest": profile_digest,
        "dispatch_ready_path": str(dispatch_path),
        "expected_dispatch_id": DISPATCH_ID,
        "validation_command": validation_command,
        "adaptive_target_seconds": 1,
        "hard_stop_seconds": 2,
    }


def _validation_command(marker: Path, *, sleep: bool = False, exit_code: int = 0) -> list[str]:
    code = _once_prefix()
    if sleep:
        code += "import time; time.sleep(10); "
    if exit_code:
        code += f"raise SystemExit({exit_code}); "
    return [sys.executable, "-c", code, str(marker)]


SCENARIOS = (
    pytest.param("S1", "TRANSPORT_FAILURE", False, False, True, False, False, 0, id="S1-codex-exit-before-mutation"),
    pytest.param("S2", "TEST_LONG", False, False, False, True, False, 0, id="S2-silent-hard-stop"),
    pytest.param("S3", "TEST_LONG", True, True, False, False, True, 0, id="S3-mutation-then-long-validation"),
    pytest.param("S4", "UNHANDED_MUTATION", True, False, False, False, False, 0, id="S4-mutation-without-handoff"),
    pytest.param("S5", "COMPLETED", True, True, False, False, False, 0, id="S5-successful-completion"),
    pytest.param("S6", "VALIDATION_FAILURE", True, True, False, False, False, 9, id="S6-focused-validation-failure"),
)


@pytest.mark.parametrize(
    (
        "scenario",
        "expected_outcome",
        "mutation",
        "handoff",
        "task_failure",
        "task_sleep",
        "validation_sleep",
        "validation_exit",
    ),
    SCENARIOS,
)
def test_frozen_supervised_launcher_matrix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    scenario: str,
    expected_outcome: str,
    mutation: bool,
    handoff: bool,
    task_failure: bool,
    task_sleep: bool,
    validation_sleep: bool,
    validation_exit: int,
) -> None:
    candidate, commit, profile, profile_digest = _new_candidate(tmp_path)
    artifact = tmp_path / "private" / f"{scenario}.handoff"
    artifact.parent.mkdir()
    worker_state = tmp_path / "state" / f"{scenario}.json"
    worker_state.parent.mkdir()
    task_marker = tmp_path / f"{scenario}.task-once"
    validation_marker = tmp_path / f"{scenario}.validation-once"
    receipt_dir = tmp_path / "receipts"
    receipt = receipt_dir / f"{scenario}.json"
    attempt = tmp_path / f"{scenario}.attempt.json"
    dispatch_path = tmp_path / f"{scenario}.dispatch.json"
    message = f"Canonical role backend-engineer scenario {scenario}"
    dispatch_path.write_text(
        json.dumps(_ready_dispatch(message=message)), encoding="utf-8"
    )
    changed_content = f"{scenario} exact changed content\n"
    _install_fake_codex(tmp_path, monkeypatch)
    for name, value in {
        "FAKE_CODEX_MARKER": str(task_marker),
        "FAKE_CODEX_INVOCATION": str(tmp_path / f"{scenario}.invocation.json"),
        "FAKE_CODEX_MESSAGE": message,
        "FAKE_CODEX_CONTENT": changed_content,
        "FAKE_CODEX_MUTATION": "1" if mutation else "0",
        "FAKE_CODEX_HANDOFF": "1" if handoff else "0",
        "FAKE_CODEX_SLEEP": "1" if task_sleep else "0",
        "FAKE_CODEX_EXIT": "17" if task_failure else "0",
    }.items():
        monkeypatch.setenv(name, value)

    packet = _outer_packet(
        scenario,
        candidate,
        commit,
        profile,
        profile_digest,
        artifact,
        worker_state,
        dispatch_path,
        _validation_command(
            validation_marker,
            sleep=validation_sleep,
            exit_code=validation_exit,
        ),
    )
    attempt.write_text(json.dumps(packet), encoding="utf-8")

    status = supervised.run_outer_attempt(attempt, receipt)

    assert receipt_dir.glob("*.json")
    assert list(receipt_dir.glob("*.json")) == [receipt]
    receipt_text = receipt.read_text(encoding="utf-8")
    assert receipt_text.count("\n") == 1
    result = json.loads(receipt_text)
    assert result["outcome_class"] == expected_outcome
    assert result["retry_allowed"] is False
    assert result["reserved_artifact"] == str(artifact)
    assert result["changed_paths"] == (["owned.txt"] if mutation else [])
    assert result["unhanded_paths"] == (["owned.txt"] if mutation and not handoff else [])
    assert result["worktree_mutated"] is mutation
    assert result["artifact_present"] is handoff
    assert result["next_action"] == {
        "S1": "INVESTIGATE_TRANSPORT_FAILURE",
        "S2": "REVIEW_STUCK_CHECKPOINT",
        "S3": "REVIEW_STUCK_CHECKPOINT",
        "S4": "REVIEW_UNHANDED_MUTATION",
        "S5": "HAND_OFF_TO_TEST_ENGINEER",
        "S6": "REMEDIATE_VALIDATION_FAILURE",
    }[scenario]
    assert result["preflight_clean"] is True
    assert result["checkout_root_digest"] == hashlib.sha256(
        str(candidate.resolve()).encode("utf-8")
    ).hexdigest()

    assert task_marker.read_text(encoding="utf-8") == "1\n"
    assert validation_marker.exists() is (not task_failure and not task_sleep)
    if validation_marker.exists():
        assert validation_marker.read_text(encoding="utf-8") == "1\n"
    invocation = json.loads(
        (tmp_path / f"{scenario}.invocation.json").read_text(encoding="utf-8")
    )
    assert invocation.count(message) == 1
    assert invocation[5] == str(candidate)
    assert invocation[7] == str(artifact)
    assert invocation[9] == "gpt-5.6-sol"
    assert (candidate / "owned.txt").read_text(encoding="utf-8") == (
        changed_content if mutation else BASE_CONTENT
    )
    assert artifact.exists() is handoff
    if handoff:
        assert artifact.read_text(encoding="utf-8") == f"handoff for {changed_content}"
    assert profile.read_text(encoding="utf-8") == PROFILE_CONTENT

    if expected_outcome == "COMPLETED":
        assert status == 0
        assert result["status"] == "COMPLETED"
        assert result["exit_code"] == 0
    else:
        assert status != 0
        assert result["status"] == "BLOCKED"
        assert result["exit_code"] != 0
    if scenario == "S1":
        assert result["task_exit"] == 17
        assert result["validation_exit"] is None

    assert "candidate_root" not in result
    assert "profile_path" not in result
    assert str(candidate) not in receipt_text
    assert str(profile) not in receipt_text
    assert PROFILE_CONTENT.strip() not in receipt_text
    assert changed_content.strip() not in receipt_text


def test_no_artifact_next_action_opens_new_attempt_identity() -> None:
    assert (
        supervised._NEXT_ACTION[supervised.Outcome.NO_ARTIFACT]
        == "OPEN_NEW_ATTEMPT_IDENTITY"
    )


def test_external_profile_is_digest_bound_without_candidate_mutation(
    tmp_path: Path,
) -> None:
    candidate, commit, _profile, _digest = _new_candidate(tmp_path)
    external_profile = tmp_path / "external-profile.json"
    external_profile.write_text(PROFILE_CONTENT, encoding="utf-8")
    profile_digest = hashlib.sha256(external_profile.read_bytes()).hexdigest()
    artifact = tmp_path / "private" / "handoff.md"
    artifact.parent.mkdir()
    worker_state = tmp_path / "state" / "worker.json"
    worker_state.parent.mkdir()
    dispatch_path = tmp_path / "dispatch.json"
    dispatch_path.write_text(json.dumps(_ready_dispatch()), encoding="utf-8")
    packet = supervised.validate_outer_attempt_packet(
        _outer_packet(
            "EXTERNAL-PROFILE",
            candidate,
            commit,
            external_profile,
            profile_digest,
            artifact,
            worker_state,
            dispatch_path,
            [sys.executable, "-c", "raise AssertionError('not executed')"],
        )
    )

    observation = supervised.observe_preflight(packet.context)
    assert observation.tracked_profile_digest == profile_digest
    assert observation.git_changes == ()

    external_profile.write_text("drifted\n", encoding="utf-8")
    with pytest.raises(ValueError, match="profile SHA-256 drifted"):
        supervised.observe_terminal(packet.context, "CLEAR")


@pytest.mark.parametrize("failure", ("blocked", "mismatched"))
def test_outer_attempt_rejects_untrusted_dispatch_before_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    candidate, commit, profile, profile_digest = _new_candidate(tmp_path)
    artifact = tmp_path / "private" / "handoff.md"
    artifact.parent.mkdir()
    worker_state = tmp_path / "state" / "worker.json"
    worker_state.parent.mkdir()
    dispatch_path = tmp_path / "dispatch.json"
    dispatch_document = _ready_dispatch()
    if failure == "blocked":
        dispatch_document["status"] = "BLOCKED"
    else:
        dispatch_document["dispatch_id"] = "ctd_aaaaaaaaaaaaaaaaaaaaaaaa"
    dispatch_path.write_text(json.dumps(dispatch_document), encoding="utf-8")
    packet = _outer_packet(
        "DISPATCH-PREFLIGHT",
        candidate,
        commit,
        profile,
        profile_digest,
        artifact,
        worker_state,
        dispatch_path,
        [sys.executable, "-c", "raise AssertionError('must not validate')"],
    )
    attempt = tmp_path / "attempt.json"
    attempt.write_text(json.dumps(packet), encoding="utf-8")
    receipt = tmp_path / "receipt.json"
    monkeypatch.setattr(
        supervised.watchdog,
        "supervise",
        lambda *args, **kwargs: pytest.fail("watchdog must not execute"),
    )

    with pytest.raises(ValueError):
        supervised.run_outer_attempt(attempt, receipt)

    assert not receipt.exists()
    assert not worker_state.exists()

@pytest.mark.parametrize("precondition", ("dirty", "artifact-exists"))
def test_outer_attempt_rejects_failed_checkout_preflight_before_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, precondition: str
) -> None:
    candidate, commit, profile, profile_digest = _new_candidate(tmp_path)
    artifact = tmp_path / "private" / "handoff.md"
    artifact.parent.mkdir()
    worker_state = tmp_path / "state" / "worker.json"
    worker_state.parent.mkdir()
    dispatch_path = tmp_path / "dispatch.json"
    dispatch_path.write_text(json.dumps(_ready_dispatch()), encoding="utf-8")
    if precondition == "dirty":
        (candidate / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    else:
        artifact.write_text("pre-existing\n", encoding="utf-8")
    packet = _outer_packet(
        "CHECKOUT-PREFLIGHT",
        candidate,
        commit,
        profile,
        profile_digest,
        artifact,
        worker_state,
        dispatch_path,
        [sys.executable, "-c", "raise AssertionError('must not validate')"],
    )
    attempt = tmp_path / "attempt.json"
    attempt.write_text(json.dumps(packet), encoding="utf-8")
    receipt = tmp_path / "receipt.json"
    monkeypatch.setattr(
        supervised.watchdog,
        "supervise",
        lambda *args, **kwargs: pytest.fail("watchdog must not execute"),
    )

    with pytest.raises(supervised.PreflightError):
        supervised.run_outer_attempt(attempt, receipt)

    assert not receipt.exists()
    assert not worker_state.exists()
