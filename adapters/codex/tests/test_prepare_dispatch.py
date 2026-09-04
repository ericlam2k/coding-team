#!/usr/bin/env python3
"""Focused tests for the Codex adapter dispatch preflight."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare-dispatch.py"
RUNTIME = Path(__file__).resolve().parents[1] / "runtime.md"
SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"
SPEC = importlib.util.spec_from_file_location("prepare_dispatch", SCRIPT)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - test bootstrap
    raise RuntimeError(f"cannot load {SCRIPT}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PrepareDispatchTests(unittest.TestCase):
    def packet(self) -> dict[str, object]:
        return {
            "role": "backend-engineer",
            "task_id": "CT-DISPATCH-RCA-B01",
            "objective": "Build the fail-closed dispatch packet validator.",
            "acceptance": [
                "Plaintext message names the absolute backend role card.",
                "Invalid packets return BLOCKED without a spawn shape.",
            ],
            "paths": [
                "coding-team/adapters/codex/scripts/prepare-dispatch.py",
                "coding-team/adapters/codex/tests/test_prepare_dispatch.py",
            ],
            "validation": ["python3 -m unittest coding-team/adapters/codex/tests/test_prepare_dispatch.py"],
            "stop": "Stop on scope conflict; do not commit or push.",
            "model": "gpt-5.6-luna",
            "effort": "max",
            "fork_turns": "3",
            "host_binding": {
                "tool": "collaboration.spawn_agent",
                "mode": "direct_tool_call",
                "available_to_caller": True,
            },
            "allocation": self.allocation(),
        }

    def allocation(self) -> dict[str, object]:
        unit = {
            "status": "MEASURED", "seconds": 1, "source": "test-fixture",
            "evidence_ref": "evidence:test-duration",
        }
        return {
            "owner": "backend-engineer",
            "concern": "dispatch admission",
            "input_refs": ["adapters/codex/scripts/prepare-dispatch.py"],
            "result": "one bounded dispatch decision",
            "prerequisites": [{"name": "packet normalized", "status": "passed"}],
            "candidate_changed_paths": 2,
            "prior_hard_stop": False,
            "timing_profile": {
                "target_s": 10, "checkpoint_s": 20, "hard_stop_s": 30,
                "reserve_s": 5, "max_hard_cap_s": 30,
            },
            "priced_units": {
                "setup": [unit], "work": [unit], "validation": [unit], "handoff": [unit],
            },
        }

    def test_valid_packet_is_spawn_ready_and_plaintext(self) -> None:
        result = MODULE.prepare_dispatch(self.packet())

        self.assertEqual(result["status"], "READY")
        self.assertEqual(
            set(result["spawn"]),
            {
                "task_name", "agent_type", "fork_turns", "message", "model",
                "reasoning_effort",
            },
        )
        self.assertEqual(result["spawn"]["fork_turns"], "3")
        self.assertEqual(result["spawn"]["agent_type"], "worker")
        self.assertEqual(result["spawn"]["model"], "gpt-5.6-luna")
        self.assertEqual(result["spawn"]["reasoning_effort"], "max")
        self.assertRegex(result["dispatch_id"], r"^ctd_[0-9a-f]{24}$")
        self.assertEqual(
            result["spawn"]["task_name"],
            "ct_ct_dispatch_rca_b01_" + result["dispatch_id"].removeprefix("ctd_"),
        )
        self.assertRegex(result["spawn"]["task_name"], r"^[a-z][a-z0-9_]*$")
        self.assertNotIn("role", result["spawn"])
        self.assertNotIn("task_id", result["spawn"])
        self.assertNotIn("dispatch_id", result["spawn"])
        self.assertNotIn("fork_context", result["spawn"])
        self.assertNotIn("host_binding", result["spawn"])
        self.assertNotIn("invocation", result["spawn"])
        self.assertEqual(
            result["invocation"],
            {
                "tool": "collaboration.spawn_agent",
                "mode": "direct_tool_call",
                "instruction": MODULE.DIRECT_HOST_INVOCATION,
            },
        )
        self.assertEqual(result["packet"]["host_binding"], {
            "tool": "collaboration.spawn_agent",
            "mode": "direct_tool_call",
            "available_to_caller": True,
        })
        role_card = Path(result["role_card"])
        self.assertTrue(role_card.is_absolute())
        self.assertTrue(role_card.is_file())
        self.assertIn(str(role_card), result["message"])
        self.assertLessEqual(result["word_count"], MODULE.MAX_MESSAGE_WORDS)
        self.assertNotIn("encrypted", result["message"].lower())
        self.assertIn("- **Recommended next to-do:**", result["message"])
        self.assertIn("- **Pending tasks:**", result["message"])
        self.assertIn("task ID — owner — prerequisite — state", result["message"])

    def test_runtime_documents_the_live_explicit_role_spawn_contract(self) -> None:
        runtime = RUNTIME.read_text(encoding="utf-8")
        skill = SKILL.read_text(encoding="utf-8")
        expected = (
            "`task_name`, `agent_type`, `fork_turns`, `message`, `model`, and "
            "`reasoning_effort`"
        )
        self.assertIn("set `fork_turns` to a positive bounded context depth", runtime)
        self.assertIn(expected, " ".join(runtime.split()))
        self.assertIn(expected, " ".join(skill.split()))
        self.assertIn("Legacy `fork_context`", skill)
        self.assertNotIn("set `fork_context=false`", runtime)
        runtime_prose = " ".join(runtime.split())
        self.assertIn(
            "Prefer `dispatch_id + agent_thread_id + call_id` as the evidence identity",
            runtime_prose,
        )
        self.assertIn(
            "`dispatch_id + deterministic task_name + the authoritative single spawn response`",
            runtime_prose,
        )
        self.assertIn(
            "explicitly record each unavailable thread/call identifier",
            runtime_prose,
        )
        self.assertIn(
            "Never use Codex UI activity rows as run, retry, token, cost, model, or identity evidence",
            runtime_prose,
        )
        for prose in (runtime_prose, " ".join(skill.split())):
            self.assertIn("host_binding", prose)
            self.assertIn("direct collaboration.spawn_agent", prose)
            self.assertIn("no indirect fallback exists", prose)
            self.assertIn("Invoke the direct collaboration.spawn_agent tool exactly once", prose)

    def test_dispatch_id_is_stable_and_changes_with_material_delta(self) -> None:
        first = MODULE.prepare_dispatch(self.packet())
        second = MODULE.prepare_dispatch(self.packet())

        self.assertEqual(first["dispatch_id"], second["dispatch_id"])
        for field, value in (
            ("objective", "Build a corrected fail-closed dispatch packet validator."),
            ("paths", ["adapters/codex/scripts/other.py"]),
        ):
            changed_packet = self.packet()
            changed_packet[field] = value
            changed = MODULE.prepare_dispatch(changed_packet)
            self.assertNotEqual(first["admission"]["digest"], changed["admission"]["digest"])
            self.assertNotEqual(first["dispatch_id"], changed["dispatch_id"])

    def test_task_name_is_stable_and_changes_with_material_delta(self) -> None:
        first = MODULE.prepare_dispatch(self.packet())
        second = MODULE.prepare_dispatch(self.packet())
        changed_packet = self.packet()
        changed_packet["objective"] = "Build a materially changed dispatch validator."
        changed = MODULE.prepare_dispatch(changed_packet)

        self.assertEqual(first["spawn"]["task_name"], second["spawn"]["task_name"])
        self.assertNotEqual(first["dispatch_id"], changed["dispatch_id"])
        self.assertNotEqual(first["spawn"]["task_name"], changed["spawn"]["task_name"])

    def test_positive_fork_depth_integer_and_string_are_normalized(self) -> None:
        for value, expected in ((1, "1"), (7, "7"), ("1", "1"), ("42", "42")):
            packet = self.packet()
            packet["fork_turns"] = value

            with self.subTest(value=value):
                result = MODULE.prepare_dispatch(packet)
                self.assertEqual(result["spawn"]["fork_turns"], expected)
                self.assertIn(f"fork_turns={expected}", result["message"])

    def test_omitted_fork_turns_is_blocked(self) -> None:
        packet = self.packet()
        packet.pop("fork_turns")

        with self.assertRaises(MODULE.PacketValidationError) as raised:
            MODULE.prepare_dispatch(packet)

        self.assertTrue(any("fork_turns" in item and "required" in item for item in raised.exception.errors))

    def test_unsupported_fork_depth_is_blocked(self) -> None:
        for value in (
            None, False, True, 0, -1, "0", "-1", "none", "all", "1.5",
            "01", "+3", " 3 ", "abc",
        ):
            packet = self.packet()
            packet["fork_turns"] = value

            with self.subTest(value=value), self.assertRaises(MODULE.PacketValidationError) as raised:
                MODULE.prepare_dispatch(packet)

            self.assertTrue(any("fork_turns" in item for item in raised.exception.errors))

    def test_legacy_fork_context_is_always_blocked(self) -> None:
        for keep_fork_turns in (False, True):
            packet = self.packet()
            if not keep_fork_turns:
                packet.pop("fork_turns")
            packet["fork_context"] = False

            with self.subTest(keep_fork_turns=keep_fork_turns), self.assertRaises(
                MODULE.PacketValidationError
            ) as raised:
                MODULE.prepare_dispatch(packet)

            self.assertTrue(
                any("fork_context" in item and "unsupported" in item for item in raised.exception.errors)
            )

    def test_missing_host_binding_is_blocked_with_direct_route_guidance(self) -> None:
        packet = self.packet()
        packet.pop("host_binding")

        with self.assertRaises(MODULE.PacketValidationError) as raised:
            MODULE.prepare_dispatch(packet)

        errors = " ".join(raised.exception.errors)
        self.assertIn("host_binding: required", errors)
        self.assertIn(MODULE.DIRECT_HOST_BINDING_GUIDANCE, errors)

    def test_invalid_host_binding_is_blocked_without_a_spawn(self) -> None:
        variants = (
            None,
            {"tool": "collaboration.spawn_agent", "mode": "direct_tool_call", "available_to_caller": False},
            {"tool": "collaboration.spawn_agent", "mode": "exec", "available_to_caller": True},
            {"tool": "collaboration.spawn_agent", "mode": "direct_tool_call", "available_to_caller": True, "route": "shell"},
        )
        for value in variants:
            packet = self.packet()
            packet["host_binding"] = value

            with self.subTest(value=value), self.assertRaises(MODULE.PacketValidationError) as raised:
                MODULE.prepare_dispatch(packet)

            self.assertIn(MODULE.DIRECT_HOST_BINDING_GUIDANCE, " ".join(raised.exception.errors))

    def test_indirect_host_binding_aliases_are_blocked(self) -> None:
        aliases = (
            "functions.collaboration.spawn_agent",
            "functions.exec",
            "exec_command",
            "tools.multi_agent_v1__spawn_agent",
            "shell",
            "python",
            "node",
            "javascript",
        )
        for alias in aliases:
            packet = self.packet()
            packet["host_binding"]["tool"] = alias

            with self.subTest(alias=alias), self.assertRaises(MODULE.PacketValidationError) as raised:
                MODULE.prepare_dispatch(packet)

            errors = " ".join(raised.exception.errors)
            self.assertIn(alias, errors)
            self.assertIn(MODULE.DIRECT_HOST_BINDING_GUIDANCE, errors)

    def test_binding_attestation_is_not_worker_identity(self) -> None:
        normalized = MODULE.validate_packet(self.packet())
        canonical = MODULE._canonical_dispatch_payload(normalized)

        self.assertNotIn(b"host_binding", canonical)
        self.assertNotIn(b"available_to_caller", canonical)

    def test_caller_supplied_task_name_is_blocked(self) -> None:
        packet = self.packet()
        packet["task_name"] = "caller_name"

        with self.assertRaises(MODULE.PacketValidationError) as raised:
            MODULE.prepare_dispatch(packet)

        self.assertTrue(any("unexpected field: task_name" in item for item in raised.exception.errors))

    def test_invalid_task_identity_is_blocked_before_derivation(self) -> None:
        for value in ("", "1-invalid", "has whitespace", "x"):
            packet = self.packet()
            packet["task_id"] = value

            with self.subTest(value=value), self.assertRaises(MODULE.PacketValidationError):
                MODULE.prepare_dispatch(packet)

    def test_opaque_payload_is_blocked(self) -> None:
        packet = self.packet()
        packet["encrypted_brief"] = "ciphertext: AQIDBAUGBwgJ"

        with self.assertRaises(MODULE.PacketValidationError) as raised:
            MODULE.prepare_dispatch(packet)

        self.assertTrue(any("opaque" in item for item in raised.exception.errors))

    def test_missing_required_field_is_blocked(self) -> None:
        packet = self.packet()
        del packet["acceptance"]

        with self.assertRaises(MODULE.PacketValidationError) as raised:
            MODULE.prepare_dispatch(packet)

        self.assertTrue(any("acceptance: required" in item for item in raised.exception.errors))

    def test_unknown_role_is_blocked(self) -> None:
        packet = self.packet()
        packet["role"] = "reviewer"

        with self.assertRaises(MODULE.PacketValidationError) as raised:
            MODULE.prepare_dispatch(packet)

        self.assertTrue(any("unknown canonical role" in item for item in raised.exception.errors))

    def test_code_reviewer_is_spawn_ready_and_resolves_role_card(self) -> None:
        packet = self.packet()
        packet["role"] = "code-reviewer"
        packet["task_id"] = "CT-CODE-REVIEWER-B01"
        packet["objective"] = "Review the frozen candidate before conditional Test Engineer evidence."

        result = MODULE.prepare_dispatch(packet)

        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["role"], "code-reviewer")
        self.assertEqual(result["spawn"]["agent_type"], "advisor")
        role_card = Path(result["role_card"])
        self.assertTrue(role_card.is_absolute())
        self.assertEqual(role_card.name, "code-reviewer.md")
        self.assertTrue(role_card.is_file())
        self.assertIn(str(role_card), result["message"])

    def test_plaintext_message_word_cap_is_fail_closed(self) -> None:
        packet = self.packet()
        packet["objective"] = " ".join(["word"] * 300)

        with self.assertRaises(MODULE.PacketValidationError) as raised:
            MODULE.prepare_dispatch(packet)

        self.assertTrue(any("maximum is 250" in item for item in raised.exception.errors))

    def test_unknown_priced_unit_requires_measurement(self) -> None:
        packet = self.packet()
        packet["allocation"] = self.allocation()
        packet["allocation"]["priced_units"]["work"][0]["status"] = "UNKNOWN"

        result = MODULE.prepare_dispatch(packet)

        self.assertEqual(result["status"], "MEASURE")
        self.assertNotIn("spawn", result)

    def test_width_is_split(self) -> None:
        packet = self.packet()
        packet["allocation"] = self.allocation()
        packet["allocation"]["owner"] = ["one", "two"]

        result = MODULE.prepare_dispatch(packet)

        self.assertEqual(result["status"], "SPLIT")
        self.assertNotIn("spawn", result)

    def test_failed_prerequisite_is_blocked(self) -> None:
        packet = self.packet()
        packet["allocation"] = self.allocation()
        packet["allocation"]["prerequisites"] = [{"name": "check", "status": "failed"}]

        result = MODULE.prepare_dispatch(packet)

        self.assertEqual(result["status"], "BLOCK")
        self.assertNotIn("spawn", result)

    def test_admission_and_ready_wording_are_explicit(self) -> None:
        result = MODULE.prepare_dispatch(self.packet())

        self.assertEqual(result["admission"]["decision"], "ADMIT")
        self.assertIn("packet-valid plus direct-binding-attested", result["message"])
        self.assertIn("does not prove host acceptance", result["readiness"])
        self.assertIn("completion", result["readiness"])
        self.assertEqual(result["packet"]["admission_digest"], result["admission"]["digest"])

    def test_admission_digest_changes_with_allocation_material(self) -> None:
        first = MODULE.prepare_dispatch(self.packet())
        packet = self.packet()
        packet["allocation"] = self.allocation()
        packet["allocation"]["result"] = "a materially different result"
        second = MODULE.prepare_dispatch(packet)

        self.assertNotEqual(first["admission"]["digest"], second["admission"]["digest"])
        self.assertNotEqual(first["dispatch_id"], second["dispatch_id"])

    def test_critical_native_collaboration_fails_closed_without_handle(self) -> None:
        packet = self.packet()
        packet["allocation"] = self.allocation()
        packet["allocation"].update({"critical": True, "native_collaboration": True})

        result = MODULE.prepare_dispatch(packet)

        self.assertEqual(result["status"], "BLOCK")
        self.assertNotIn("spawn", result)

    def test_multiple_concerns_split(self) -> None:
        packet = self.packet()
        packet["allocation"]["concern"] = ["admission", "routing"]

        self.assertEqual(MODULE.prepare_dispatch(packet)["status"], "SPLIT")

    def test_unbounded_input_split(self) -> None:
        packet = self.packet()
        packet["allocation"]["input_refs"] = "unbounded"

        self.assertEqual(MODULE.prepare_dispatch(packet)["status"], "SPLIT")

    def test_validation_above_hard_stop_reserve_blocks(self) -> None:
        packet = self.packet()
        packet["allocation"] = self.allocation()
        packet["allocation"]["priced_units"]["validation"] = [
            {"status": "ESTIMATED", "seconds": 26, "source": "test-fixture"}
        ]

        self.assertEqual(MODULE.prepare_dispatch(packet)["status"], "BLOCK")

    def test_ordinary_plan_above_target_splits(self) -> None:
        packet = self.packet()
        packet["allocation"] = self.allocation()
        for category in packet["allocation"]["priced_units"]:
            packet["allocation"]["priced_units"][category][0]["seconds"] = 3

        self.assertEqual(MODULE.prepare_dispatch(packet)["status"], "SPLIT")

    def test_atomic_all_measured_plan_with_reserve_below_hard_stop_admits(self) -> None:
        packet = self.packet()
        allocation = self.allocation()
        allocation["atomic"] = True
        allocation["priced_units"] = {
            category: [{
                "status": "MEASURED", "seconds": 6, "source": "measured",
                "evidence_ref": "evidence:measured-duration",
            }]
            for category in ("setup", "work", "validation", "handoff")
        }
        packet["allocation"] = allocation

        self.assertEqual(MODULE.prepare_dispatch(packet)["status"], "READY")

    def test_timing_requires_positive_limits_and_reserve_headroom(self) -> None:
        for field in ("target_s", "checkpoint_s", "hard_stop_s", "max_hard_cap_s"):
            packet = self.packet()
            packet["allocation"]["timing_profile"][field] = 0
            with self.assertRaises(MODULE.PacketValidationError):
                MODULE.prepare_dispatch(packet)

        packet = self.packet()
        packet["allocation"]["timing_profile"]["reserve_s"] = 20
        with self.assertRaises(MODULE.PacketValidationError):
            MODULE.prepare_dispatch(packet)

    def test_candidate_wide_validation_is_split_from_scoped_task(self) -> None:
        packet = self.packet()
        packet["paths"] = ["AGENTS.md"]
        packet["validation"] = [
            "Verify HEAD, tree, diff, and 852 paths."
        ]
        packet["allocation"]["candidate_changed_paths"] = 852

        result = MODULE.prepare_dispatch(packet)

        self.assertEqual(result["status"], "SPLIT")
        self.assertTrue(result["admission"]["allocation"]["candidate_wide_validation"])
        self.assertNotIn("spawn", result)

        packet["allocation"]["prior_hard_stop"] = True
        retry = MODULE.prepare_dispatch(packet)
        self.assertEqual(retry["status"], "BLOCK")
        self.assertNotIn("spawn", retry)

    def test_prior_hard_stop_requires_measured_replan(self) -> None:
        packet = self.packet()
        packet["allocation"]["prior_hard_stop"] = True

        result = MODULE.prepare_dispatch(packet)

        self.assertEqual(result["status"], "BLOCK")
        self.assertNotIn("spawn", result)

    def test_estimated_time_never_admits_a_worker(self) -> None:
        packet = self.packet()
        packet["allocation"]["priced_units"]["work"][0] = {
            "status": "ESTIMATED", "seconds": 1, "source": "author estimate"
        }

        result = MODULE.prepare_dispatch(packet)

        self.assertEqual(result["status"], "MEASURE")
        self.assertNotIn("spawn", result)

    def test_measured_unit_requires_evidence_reference(self) -> None:
        packet = self.packet()
        packet["allocation"]["priced_units"]["setup"][0] = {
            "status": "MEASURED", "seconds": 1, "source": "claimed measurement"
        }

        with self.assertRaises(MODULE.PacketValidationError) as raised:
            MODULE.prepare_dispatch(packet)

        self.assertTrue(any("evidence_ref" in item for item in raised.exception.errors))


if __name__ == "__main__":
    unittest.main()
