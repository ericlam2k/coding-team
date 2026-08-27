#!/usr/bin/env python3
"""Focused tests for the Codex adapter dispatch preflight."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare-dispatch.py"
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
            "fork_turns": "all",
            "allocation": self.allocation(),
        }

    def allocation(self) -> dict[str, object]:
        unit = {"status": "ESTIMATED", "seconds": 1, "source": "test-fixture"}
        return {
            "owner": "backend-engineer",
            "concern": "dispatch admission",
            "input_refs": ["adapters/codex/scripts/prepare-dispatch.py"],
            "result": "one bounded dispatch decision",
            "prerequisites": [{"name": "packet normalized", "status": "passed"}],
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
        self.assertEqual(result["spawn"]["fork_turns"], "all")
        self.assertEqual(result["spawn"]["agent_type"], "worker")
        self.assertEqual(result["spawn"]["task_name"], "ct_dispatch_rca_b01")
        self.assertRegex(result["dispatch_id"], r"^ctd_[0-9a-f]{24}$")
        self.assertNotIn("model", result["spawn"])
        self.assertNotIn("reasoning_effort", result["spawn"])
        self.assertNotIn("role", result["spawn"])
        self.assertNotIn("task_id", result["spawn"])
        role_card = Path(result["role_card"])
        self.assertTrue(role_card.is_absolute())
        self.assertTrue(role_card.is_file())
        self.assertIn(str(role_card), result["message"])
        self.assertLessEqual(result["word_count"], MODULE.MAX_MESSAGE_WORDS)
        self.assertNotIn("encrypted", result["message"].lower())

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

    def test_omitted_fork_turns_uses_named_model_safe_positive_depth(self) -> None:
        packet = self.packet()
        packet.pop("fork_turns")

        result = MODULE.prepare_dispatch(packet)

        self.assertEqual(result["spawn"]["fork_turns"], "3")
        self.assertEqual(result["spawn"]["model"], "gpt-5.6-luna")
        self.assertEqual(result["spawn"]["reasoning_effort"], "max")
        self.assertIn("fork_turns=3", result["spawn"]["message"])

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

    def test_none_fork_is_blocked(self) -> None:
        packet = self.packet()
        packet["fork_turns"] = "none"

        with self.assertRaises(MODULE.PacketValidationError) as raised:
            MODULE.prepare_dispatch(packet)

        self.assertTrue(any("fork_turns" in item and "none" in item for item in raised.exception.errors))

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
        self.assertIn("proves packet preflight only", result["message"])
        self.assertIn("does not prove supervision", result["readiness"])
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
            category: [{"status": "MEASURED", "seconds": 6, "source": "measured"}]
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


if __name__ == "__main__":
    unittest.main()
