import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "supervisor-relay.py"
SPEC = importlib.util.spec_from_file_location("supervisor_relay", SCRIPT)
assert SPEC and SPEC.loader
RELAY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RELAY)


def reservation_path(tmp_path: Path, *, critical: bool = False) -> Path:
    directory = "artifacts/task-a/attempt-1"
    reservation = RELAY.make_reservation(
        task_id="TASK-A",
        run_id="RUN-1",
        attempt_id="ATTEMPT-1",
        dispatch_id="ctd_0123456789abcdef01234567",
        candidate_commit="a" * 40,
        pic_role="backend-engineer",
        timing_profile_ref="core/adaptive-timing.md",
        T_checkpoint=10.0,
        T_hard=20.0,
        artifact_directory=directory,
        terminal_receipt_name="critical-receipt.json" if critical else None,
    )
    path = tmp_path / directory / "reservation.json"
    RELAY.reserve(path, reservation)
    return path


def publish_start_and_checkpoint(path: Path) -> tuple[dict, dict]:
    start = RELAY.publish_pic_event(
        path,
        "START",
        observed_monotonic_seconds=1.0,
        evidence_refs=["evidence/dispatch.json"],
    )
    checkpoint = RELAY.publish_pic_event(
        path,
        "CHECKPOINT",
        observed_monotonic_seconds=5.0,
        evidence_refs=["evidence/checkpoint.json"],
        completed_facts=["Bounded implementation work completed."],
        blocker=None,
        next_action="Publish the governed terminal artifact.",
    )
    return start, checkpoint


def publish_noncritical_terminal(path: Path, *, with_handoff: bool = True) -> dict:
    terminal = RELAY.publish_pic_event(
        path,
        "TERMINAL",
        observed_monotonic_seconds=6.0,
        evidence_refs=["evidence/focused-test.txt"],
        status="COMPLETED",
        outcome_class="COMPLETED",
        exit_code=0,
    )
    if with_handoff:
        RELAY.publish_pic_handoff(
            path,
            "Implementation is bounded. Focused checks passed. Lead owns the next route.",
        )
    return terminal


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_happy_relay_preserves_identity_digests_atomicity_and_no_authority(tmp_path):
    path = reservation_path(tmp_path)
    reservation = read_json(path)
    start, checkpoint = publish_start_and_checkpoint(path)
    terminal = publish_noncritical_terminal(path)

    result = RELAY.observe_and_relay(path, monotonic=lambda: 7.0)

    assert result["status"] == "COMPLETED"
    assert result["reason"] == "TERMINAL_OBSERVED"
    assert result["relay_id"] == reservation["relay_id"]
    assert checkpoint["prior_event_digest"] == start["event_digest"]
    assert terminal["prior_event_digest"] == checkpoint["event_digest"]
    assert result["quality_decision"] == "NONE"
    assert result["gate_advanced"] is False
    assert result["retry_allowed"] is False
    assert result["cancellation_claim"] is False
    assert result["interruption_claim"] is False
    assert result["route_change"] is False
    assert result["model_change"] is False
    assert result["role_change"] is False
    assert result["auto_action"] == "none"
    assert "handoff" not in result
    assert len(result["relay_text"].split()) <= 150

    relay_file = path.parent / "relay.json"
    original = relay_file.read_bytes()
    with pytest.raises(RELAY.RelayBlocked, match="create-once"):
        RELAY.observe_and_relay(path, monotonic=lambda: 7.0)
    assert relay_file.read_bytes() == original


def test_observation_needs_no_host_collaboration_capability(tmp_path):
    path = reservation_path(tmp_path)
    publish_start_and_checkpoint(path)
    publish_noncritical_terminal(path)

    result = RELAY.observe_and_relay(path, monotonic=lambda: 7.0)

    assert result["execution_state"] == "TERMINAL"
    assert "Host-native sibling state" in result["unknowns"][0]
    assert "collaboration" not in RELAY.observe_and_relay.__code__.co_names


def test_start_missing_is_blocked_unknown_and_does_not_mutate_pic_artifacts(tmp_path):
    path = reservation_path(tmp_path)

    result = RELAY.observe_and_relay(path, monotonic=lambda: 1.0)

    assert result["status"] == "BLOCKED"
    assert result["reason"] == "START_NOT_OBSERVED"
    assert result["execution_state"] == "UNKNOWN"
    assert result["retry_allowed"] is False
    assert not (path.parent / "start.json").exists()
    assert not (path.parent / "checkpoint.json").exists()
    assert not (path.parent / "terminal.json").exists()


def test_timeout_is_one_blocked_unknown_relay_without_control_action(tmp_path):
    path = reservation_path(tmp_path)
    publish_start_and_checkpoint(path)
    ticks = iter([7.0, 20.0])
    sleeps = []

    result = RELAY.observe_and_relay(
        path,
        monotonic=lambda: next(ticks),
        sleeper=lambda seconds: sleeps.append(seconds),
    )

    assert result["status"] == "BLOCKED"
    assert result["reason"] == "RELAY_TIMEOUT"
    assert result["execution_state"] == "UNKNOWN"
    assert result["retry_allowed"] is False
    assert result["cancellation_claim"] is False
    assert result["interruption_claim"] is False
    assert result["model_change"] is False
    assert result["role_change"] is False
    assert result["gate_advanced"] is False
    assert sleeps == []
    assert len(list(path.parent.glob("relay.json"))) == 1


def test_missing_checkpoint_at_deadline_is_recorded_until_hard_timeout(tmp_path):
    path = reservation_path(tmp_path)
    RELAY.publish_pic_event(path, "START", observed_monotonic_seconds=1.0)
    ticks = iter([9.0, 10.0, 20.0])
    sleeps = []

    result = RELAY.observe_and_relay(
        path,
        poll_seconds=1.0,
        monotonic=lambda: next(ticks),
        sleeper=lambda seconds: sleeps.append(seconds),
    )

    assert result["reason"] == "RELAY_TIMEOUT"
    assert any("CHECKPOINT_MISSING" in unknown for unknown in result["unknowns"])
    assert sleeps == [1.0]


def test_handoff_missing_never_advances_quality(tmp_path):
    path = reservation_path(tmp_path)
    publish_start_and_checkpoint(path)
    publish_noncritical_terminal(path, with_handoff=False)

    result = RELAY.observe_and_relay(path, monotonic=lambda: 7.0)

    assert result["status"] == "BLOCKED"
    assert result["reason"] == "HANDOFF_MISSING"
    assert result["quality_decision"] == "NONE"
    assert result["gate_advanced"] is False


@pytest.mark.parametrize(
    ("mutation", "expected_fragment"),
    [
        ("digest", "event_digest"),
        ("duplicate", "strict UTF-8 JSON"),
        ("oversized", "size is outside"),
        ("symlink", "regular non-symlink"),
    ],
)
def test_tamper_duplicate_oversize_and_symlink_fail_closed(tmp_path, mutation, expected_fragment):
    path = reservation_path(tmp_path)
    start = RELAY.publish_pic_event(path, "START", observed_monotonic_seconds=1.0)
    start_path = path.parent / "start.json"
    if mutation == "digest":
        start["evidence_refs"].append("evidence/tampered.json")
        start_path.write_text(json.dumps(start), encoding="utf-8")
    elif mutation == "duplicate":
        start_path.write_text('{"event":"START","event":"START"}', encoding="utf-8")
    elif mutation == "oversized":
        start_path.write_bytes(b"{" + b" " * RELAY.MAX_ARTIFACT_BYTES + b"}")
    else:
        target = tmp_path / "unrelated.json"
        target.write_text(json.dumps(start), encoding="utf-8")
        start_path.unlink()
        start_path.symlink_to(target)

    result = RELAY.observe_and_relay(path, monotonic=lambda: 2.0)

    assert result["status"] == "BLOCKED"
    assert result["reason"] == "ARTIFACT_INVALID"
    assert expected_fragment in result["facts"][1]
    assert str(tmp_path) not in json.dumps(result)


def test_terminal_before_checkpoint_and_overwritten_terminal_fail_closed(tmp_path):
    path = reservation_path(tmp_path)
    publish_start_and_checkpoint(path)
    publish_noncritical_terminal(path)
    (path.parent / "checkpoint.json").unlink()

    result = RELAY.observe_and_relay(path, monotonic=lambda: 7.0)
    assert result["reason"] == "ARTIFACT_INVALID"
    assert "before CHECKPOINT" in result["facts"][1]

    second = reservation_path(tmp_path / "second")
    publish_start_and_checkpoint(second)
    terminal = publish_noncritical_terminal(second)
    terminal["exit_code"] = 99
    (second.parent / "terminal.json").write_text(json.dumps(terminal), encoding="utf-8")
    result = RELAY.observe_and_relay(second, monotonic=lambda: 7.0)
    assert result["reason"] == "ARTIFACT_INVALID"
    assert "event_digest" in result["facts"][1]


def test_identity_replay_partial_chain_tamper_and_future_time_fail_closed(tmp_path):
    replay = reservation_path(tmp_path / "replay")
    start = RELAY.publish_pic_event(replay, "START", observed_monotonic_seconds=1.0)
    start["task_id"] = "OTHER-TASK"
    start["event_digest"] = RELAY._digest(
        {key: value for key, value in start.items() if key != "event_digest"}
    )
    (replay.parent / "start.json").write_text(json.dumps(start), encoding="utf-8")
    result = RELAY.observe_and_relay(replay, monotonic=lambda: 2.0)
    assert result["reason"] == "ARTIFACT_INVALID"
    assert "does not match reservation" in result["facts"][1]

    partial = reservation_path(tmp_path / "partial")
    _, checkpoint = publish_start_and_checkpoint(partial)
    checkpoint["prior_event_digest"] = "f" * 64
    checkpoint["event_digest"] = RELAY._digest(
        {key: value for key, value in checkpoint.items() if key != "event_digest"}
    )
    (partial.parent / "checkpoint.json").write_text(
        json.dumps(checkpoint), encoding="utf-8"
    )
    result = RELAY.observe_and_relay(partial, monotonic=lambda: 7.0)
    assert result["reason"] == "ARTIFACT_INVALID"
    assert "checkpoint digest chain" in result["facts"][1]

    future = reservation_path(tmp_path / "future")
    RELAY.publish_pic_event(future, "START", observed_monotonic_seconds=8.0)
    result = RELAY.observe_and_relay(future, monotonic=lambda: 7.0)
    assert result["reason"] == "ARTIFACT_INVALID"
    assert "future monotonic" in result["facts"][1]


def test_reservation_traversal_collision_and_second_terminal_are_rejected(tmp_path):
    reservation = RELAY.make_reservation(
        task_id="TASK-A", run_id="RUN-1", attempt_id="ATTEMPT-1",
        dispatch_id="ctd_0123456789abcdef01234567", candidate_commit="a" * 40,
        pic_role="backend-engineer", timing_profile_ref="core/adaptive-timing.md",
        T_checkpoint=10.0, T_hard=20.0, artifact_directory="artifacts/attempt",
    )
    reservation["start_ref"] = "artifacts/attempt/../escape.json"
    with pytest.raises(ValueError, match="normalized repo-relative"):
        RELAY.validate_reservation(reservation)

    path = reservation_path(tmp_path)
    with pytest.raises(RELAY.RelayBlocked, match="destination"):
        RELAY.reserve(path, read_json(path))
    publish_start_and_checkpoint(path)
    publish_noncritical_terminal(path)
    with pytest.raises(RELAY.RelayBlocked, match="create-once"):
        RELAY.publish_pic_event(
            path, "TERMINAL", observed_monotonic_seconds=7.0,
            status="COMPLETED", outcome_class="COMPLETED", exit_code=0,
        )


def test_ancestor_symlink_cannot_redirect_reservation_or_artifact_writes(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    alias = tmp_path / "redirect"
    alias.symlink_to(outside, target_is_directory=True)
    reservation = RELAY.make_reservation(
        task_id="TASK-A", run_id="RUN-1", attempt_id="ATTEMPT-1",
        dispatch_id="ctd_0123456789abcdef01234567", candidate_commit="a" * 40,
        pic_role="backend-engineer", timing_profile_ref="core/adaptive-timing.md",
        T_checkpoint=10.0, T_hard=20.0,
        artifact_directory="artifacts/task-a/attempt-1",
    )
    redirected_reservation = (
        alias / "artifacts" / "task-a" / "attempt-1" / "reservation.json"
    )

    with pytest.raises(RELAY.RelayBlocked, match="ancestor") as blocked:
        RELAY.reserve(redirected_reservation, reservation)
    assert blocked.value.reason == "IDENTITY_INVALID"
    assert not (
        outside / "artifacts" / "task-a" / "attempt-1" / "reservation.json"
    ).exists()

    redirected_artifact = alias / "artifacts" / "task-a" / "attempt-1" / "start.json"
    with pytest.raises(RELAY.RelayBlocked, match="ancestor") as blocked:
        RELAY._atomic_create(
            redirected_artifact, {"safe": True}, collision_reason="ARTIFACT_INVALID"
        )
    assert blocked.value.reason == "ARTIFACT_INVALID"
    assert not (outside / "artifacts" / "task-a" / "attempt-1" / "start.json").exists()


def test_ancestor_symlink_cannot_redirect_reservation_or_artifact_reads(tmp_path):
    outside = tmp_path / "outside"
    real_path = reservation_path(outside)
    artifact = real_path.parent / "unrelated.json"
    artifact.write_text('{"private":"must not be followed"}', encoding="utf-8")
    alias = tmp_path / "redirect"
    alias.symlink_to(outside, target_is_directory=True)
    redirected_reservation = alias / real_path.relative_to(outside)
    redirected_artifact = alias / artifact.relative_to(outside)

    with pytest.raises(RELAY.RelayBlocked, match="ancestor") as blocked:
        RELAY.load_reservation(redirected_reservation)
    assert blocked.value.reason == "IDENTITY_INVALID"
    with pytest.raises(ValueError, match="ancestor"):
        RELAY._secure_read(redirected_artifact)


@pytest.mark.parametrize(
    ("status", "outcome", "exit_code"),
    [
        ("COMPLETED", "COMPLETED", 0),
        ("FAILED", "VALIDATION_FAILURE", 1),
        ("BLOCKED", "TEST_LONG", 124),
    ],
)
def test_critical_receipt_outcomes_are_exactly_projected(tmp_path, status, outcome, exit_code):
    path = reservation_path(tmp_path, critical=True)
    reservation = read_json(path)
    receipt = {
        "task_id": reservation["task_id"],
        "run_id": reservation["run_id"],
        "attempt_id": reservation["attempt_id"],
        "candidate_commit": reservation["candidate_commit"],
        "status": status,
        "outcome_class": outcome,
        "exit_code": exit_code,
        "retry_allowed": False,
        "privacy": "LOCAL_ONLY",
        "public_safe": False,
    }
    receipt_path = path.parent / "critical-receipt.json"
    raw = json.dumps(receipt, sort_keys=True).encode("utf-8") + b"\n"
    receipt_path.write_bytes(raw)
    publish_start_and_checkpoint(path)
    terminal = RELAY.publish_pic_event(
        path,
        "TERMINAL",
        observed_monotonic_seconds=6.0,
        status=status,
        outcome_class=outcome,
        exit_code=exit_code,
        terminal_receipt_digest=hashlib.sha256(raw).hexdigest(),
    )
    RELAY.publish_pic_handoff(path, "Terminal receipt projected exactly. Lead owns routing.")

    result = RELAY.observe_and_relay(path, monotonic=lambda: 7.0)

    assert result["status"] == status
    assert result["outcome_class"] == outcome
    assert result["terminal_receipt_ref"] == reservation["terminal_receipt_ref"]
    assert result["terminal_receipt_digest"] == terminal["terminal_receipt_digest"]
    if status == "BLOCKED":
        assert result["status"] != "COMPLETED"
    assert receipt_path.read_bytes() == raw


def test_critical_receipt_disagreement_is_blocked_and_receipt_wins(tmp_path):
    path = reservation_path(tmp_path, critical=True)
    reservation = read_json(path)
    receipt = {
        "task_id": reservation["task_id"], "run_id": reservation["run_id"],
        "status": "BLOCKED", "outcome_class": "TEST_LONG", "exit_code": 124,
        "retry_allowed": False, "privacy": "LOCAL_ONLY", "public_safe": False,
    }
    raw = json.dumps(receipt, sort_keys=True).encode() + b"\n"
    (path.parent / "critical-receipt.json").write_bytes(raw)
    publish_start_and_checkpoint(path)
    RELAY.publish_pic_event(
        path, "TERMINAL", observed_monotonic_seconds=6.0,
        status="COMPLETED", outcome_class="COMPLETED", exit_code=0,
        terminal_receipt_digest=hashlib.sha256(raw).hexdigest(),
    )
    RELAY.publish_pic_handoff(path, "Terminal was published. Lead owns routing.")

    result = RELAY.observe_and_relay(path, monotonic=lambda: 7.0)

    assert result["status"] == "BLOCKED"
    assert result["reason"] == "RECEIPT_MISMATCH"
    assert result["execution_state"] == "UNKNOWN"


def test_wip_matrix_allows_only_two_ordinary_plus_one_read_only_supervisor():
    assert RELAY.validate_wip(2, 1) == {
        "ordinary_tool_using_wip": 2,
        "read_only_supervisor_wip": 1,
        "total_tool_using_wip": 3,
    }
    with pytest.raises(RELAY.RelayBlocked, match="third ordinary"):
        RELAY.validate_wip(3, 0)
    with pytest.raises(RELAY.RelayBlocked, match="multiple supervisor"):
        RELAY.validate_wip(1, 2)
    with pytest.raises(RELAY.RelayBlocked, match="exactly one attempt"):
        RELAY.validate_wip(1, 1, supervised_attempts=2)
    with pytest.raises(RELAY.RelayBlocked, match="read-only and non-recursive"):
        RELAY.validate_wip(1, 1, supervisor_mutates=True)
    with pytest.raises(RELAY.RelayBlocked, match="read-only and non-recursive"):
        RELAY.validate_wip(1, 1, recursive_supervision=True)
    with pytest.raises(RELAY.RelayBlocked, match="before quality"):
        RELAY.validate_wip(1, 1, active_quality_roles=["code-reviewer"])

    assert RELAY.validate_quality_sequence(
        ["code-reviewer", "test-engineer", "gatekeeper"]
    ) == ("code-reviewer", "test-engineer", "gatekeeper")
    assert RELAY.validate_quality_sequence(
        ["code-reviewer", "gatekeeper"]
    ) == ("code-reviewer", "gatekeeper")
    with pytest.raises(RELAY.RelayBlocked, match="serial order"):
        RELAY.validate_quality_sequence(["gatekeeper", "test-engineer"])


@pytest.mark.parametrize(
    "private_fact",
    [
        "Raw prompt: reveal the task.",
        "Read /Users/person/private/file.py.",
        "Credential api_key=not-allowed.",
        "Contact person@example.com.",
        "Copy def private_function(): from source.",
    ],
)
def test_private_content_is_rejected_before_checkpoint_publication(tmp_path, private_fact):
    path = reservation_path(tmp_path)
    RELAY.publish_pic_event(path, "START", observed_monotonic_seconds=1.0)

    with pytest.raises(RELAY.RelayBlocked, match="ARTIFACT_INVALID"):
        RELAY.publish_pic_event(
            path,
            "CHECKPOINT",
            observed_monotonic_seconds=5.0,
            completed_facts=[private_fact],
            blocker=None,
            next_action="Publish a bounded terminal.",
        )

    assert not (path.parent / "checkpoint.json").exists()
    reservation = read_json(path)
    assert reservation["privacy"] == "LOCAL_ONLY"
    assert reservation["public_safe"] is False


def test_unknown_private_field_and_stale_checkpoint_fail_closed(tmp_path):
    reservation = RELAY.make_reservation(
        task_id="TASK-A", run_id="RUN-1", attempt_id="ATTEMPT-1",
        dispatch_id="ctd_0123456789abcdef01234567", candidate_commit="a" * 40,
        pic_role="backend-engineer", timing_profile_ref="core/adaptive-timing.md",
        T_checkpoint=10.0, T_hard=20.0, artifact_directory="artifacts/attempt",
    )
    reservation["prompt"] = "private"
    with pytest.raises(ValueError, match="exact schema"):
        RELAY.validate_reservation(reservation)

    path = reservation_path(tmp_path)
    RELAY.publish_pic_event(path, "START", observed_monotonic_seconds=1.0)
    with pytest.raises(RELAY.RelayBlocked, match="later than T_checkpoint"):
        RELAY.publish_pic_event(
            path, "CHECKPOINT", observed_monotonic_seconds=11.0,
            completed_facts=[], blocker="Checkpoint was late.",
            next_action="Lead reviews the deadline defect.",
        )


def test_observer_loss_is_supervisor_unavailable_without_replacement_or_gate(tmp_path):
    path = reservation_path(tmp_path)
    publish_start_and_checkpoint(path)
    publish_noncritical_terminal(path)

    result = RELAY.lead_check_relay(path)

    assert result["status"] == "BLOCKED"
    assert result["reason"] == "SUPERVISOR_UNAVAILABLE"
    assert result["execution_state"] == "UNKNOWN"
    assert result["replacement_supervisor"] is False
    assert result["gate_advanced"] is False
    assert result["retry_allowed"] is False


def test_lead_rejects_a_mutated_relay_authority_claim(tmp_path):
    path = reservation_path(tmp_path)
    publish_start_and_checkpoint(path)
    publish_noncritical_terminal(path)
    RELAY.observe_and_relay(path, monotonic=lambda: 7.0)
    relay_path = path.parent / "relay.json"
    relay = read_json(relay_path)
    relay["quality_decision"] = "APPROVE"
    relay_path.write_text(json.dumps(relay), encoding="utf-8")

    result = RELAY.lead_check_relay(path)

    assert result["status"] == "BLOCKED"
    assert result["reason"] == "ARTIFACT_INVALID"
    assert result["gate_advanced"] is False
    assert result["replacement_supervisor"] is False


def test_atomic_event_publication_leaves_no_temp_and_never_overwrites(tmp_path):
    path = reservation_path(tmp_path)
    start = RELAY.publish_pic_event(path, "START", observed_monotonic_seconds=1.0)
    start_path = path.parent / "start.json"
    original = start_path.read_bytes()

    with pytest.raises(RELAY.RelayBlocked, match="create-once"):
        RELAY.publish_pic_event(path, "START", observed_monotonic_seconds=2.0)

    assert start_path.read_bytes() == original
    assert read_json(start_path)["event_digest"] == start["event_digest"]
    assert not list(path.parent.glob(".*.tmp"))
