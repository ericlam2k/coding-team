#!/usr/bin/env python3
"""Focused tests for the bounded Codex host-binding selector."""

from __future__ import annotations

import importlib.util
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare-dispatch.py"
RUNTIME = Path(__file__).resolve().parents[1] / "runtime.md"
SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"
SPEC = importlib.util.spec_from_file_location("prepare_dispatch", SCRIPT)
if SPEC is None or SPEC.loader is None:  # pragma: no cover
    raise RuntimeError(f"cannot load {SCRIPT}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PrepareDispatchTests(unittest.TestCase):
    @staticmethod
    def binding(tool: str) -> dict[str, object]:
        return {"tool": tool, "mode": "direct_tool_call", "available_to_caller": True}

    def v1_packet(self, **overrides: object) -> dict[str, object]:
        packet: dict[str, object] = {
            "role": "backend-engineer",
            "message": "Run one focused check.",
            "model": "gpt-5.6-luna",
            "effort": "medium",
            "fork_turns": "1",
            "host_binding": self.binding(MODULE.V1_HOST_BINDING),
        }
        packet.update(overrides)
        return packet

    def v2_packet(self, **overrides: object) -> dict[str, object]:
        packet: dict[str, object] = {
            "role": "code-reviewer",
            "message": "Review the immutable four-file candidate.",
            "host_binding": self.binding(MODULE.V2_HOST_BINDING),
        }
        packet.update(overrides)
        return packet

    def test_v1_ready_preserves_frozen_six_key_spawn(self) -> None:
        result = MODULE.prepare_dispatch(self.v1_packet())
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["binding"], MODULE.V1_HOST_BINDING)
        self.assertEqual(
            set(result["spawn"]),
            {"task_name", "agent_type", "fork_turns", "message", "model", "reasoning_effort"},
        )
        self.assertRegex(result["spawn"]["task_name"], r"^worker_[0-9a-f]{8}$")
        self.assertEqual(result["spawn"]["fork_turns"], "1")
        self.assertEqual(result["invocation"]["instruction"], MODULE.V1_HOST_INVOCATION)

    def test_v2_ready_matches_current_direct_host_shape(self) -> None:
        result = MODULE.prepare_dispatch(self.v2_packet())
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["binding"], MODULE.V2_HOST_BINDING)
        self.assertEqual(
            result["spawn"],
            {
                "agent_type": "advisor",
                "fork_context": False,
                "message": "Review the immutable four-file candidate.",
                "model": "gpt-5.6-luna",
                "reasoning_effort": "high",
            },
        )
        self.assertEqual(result["invocation"]["tool"], MODULE.V2_HOST_BINDING)
        self.assertEqual(result["invocation"]["instruction"], MODULE.V2_HOST_INVOCATION)
        self.assertRegex(result["dispatch_id"], r"^ctd_[0-9a-f]{24}$")

    def test_v2_optional_overrides_are_forwarded_only_when_supplied(self) -> None:
        default = MODULE.prepare_dispatch(self.v2_packet())["spawn"]
        matching = MODULE.prepare_dispatch(self.v2_packet(
            model="gpt-5.6-luna", reasoning_effort="high"
        ))["spawn"]
        self.assertEqual(default["model"], "gpt-5.6-luna")
        self.assertEqual(default["reasoning_effort"], "high")
        self.assertEqual(matching["model"], "gpt-5.6-luna")
        with self.assertRaises(MODULE.PacketValidationError):
            MODULE.prepare_dispatch(self.v2_packet(model="gpt-5.6-sol"))

    def test_v1_risk_routes_select_opus_or_fable(self) -> None:
        standard = self.v1_packet(
            role="system-architect", risk="standard",
            model="claude-opus-5", effort="high",
        )
        high = self.v1_packet(
            role="system-architect", risk="high",
            model="claude-fable-5-1", effort="high",
        )
        self.assertEqual(
            MODULE.prepare_dispatch(standard)["spawn"]["model"], "claude-opus-5"
        )
        self.assertEqual(
            MODULE.prepare_dispatch(high)["spawn"]["model"], "claude-fable-5-1"
        )

    def test_v2_risk_routes_select_opus_or_fable(self) -> None:
        standard = MODULE.prepare_dispatch(
            self.v2_packet(role="system-architect", risk="standard")
        )
        high = MODULE.prepare_dispatch(
            self.v2_packet(role="system-architect", risk="high")
        )
        self.assertEqual(standard["spawn"]["model"], "claude-opus-5")
        self.assertEqual(high["spawn"]["model"], "claude-fable-5-1")

    def test_backend_gatekeeper_requires_risk_and_exposes_nonautomatic_astra_fallback(self) -> None:
        standard = MODULE.prepare_dispatch(self.v2_packet(
            role="gatekeeper", model_route="backend", risk="standard"
        ))
        high = MODULE.prepare_dispatch(self.v2_packet(
            role="gatekeeper", model_route="backend", risk="high"
        ))
        self.assertEqual(standard["spawn"]["model"], "claude-opus-5")
        self.assertEqual(high["spawn"]["model"], "claude-fable-5-1")
        self.assertNotIn("gpt-6-astra", standard["spawn"].values())
        self.assertEqual(
            standard["routing"]["fallback"],
            {"model": "gpt-6-astra", "reasoning_effort": "high"},
        )
        self.assertFalse(standard["routing"]["automatic_fallback"])
        self.assertEqual(standard["routing"]["fallback_requires"], "a new authorized dispatch")

    def test_missing_or_invalid_risk_is_rejected_for_affected_roles(self) -> None:
        packets = (
            self.v2_packet(role="system-architect"),
            self.v2_packet(role="system-architect", risk="critical"),
            self.v2_packet(role="gatekeeper", model_route="backend"),
            self.v2_packet(role="gatekeeper", model_route="backend", risk="low"),
        )
        for packet in packets:
            with self.subTest(packet=packet), self.assertRaises(MODULE.PacketValidationError):
                MODULE.prepare_dispatch(packet)

    def test_risk_route_rejects_conflicting_models(self) -> None:
        for risk, model in (("standard", "claude-fable-5-1"), ("high", "claude-opus-5")):
            with self.subTest(risk=risk), self.assertRaises(MODULE.PacketValidationError):
                MODULE.prepare_dispatch(self.v2_packet(
                    role="system-architect", risk=risk, model=model
                ))

    def test_gatekeeper_and_te_routes_are_required_and_injected(self) -> None:
        architect = MODULE.prepare_dispatch(
            self.v2_packet(role="system-architect", risk="high")
        )["spawn"]
        self.assertEqual(
            (architect["model"], architect["reasoning_effort"]),
            ("claude-fable-5-1", "high"),
        )
        gatekeeper = self.v2_packet(role="gatekeeper", model_route="frontend")
        spawned = MODULE.prepare_dispatch(gatekeeper)["spawn"]
        self.assertEqual((spawned["model"], spawned["reasoning_effort"]), ("gpt-6-astra", "high"))
        backend_gatekeeper = MODULE.prepare_dispatch(
            self.v2_packet(role="gatekeeper", model_route="backend", risk="high")
        )["spawn"]
        self.assertEqual(
            (backend_gatekeeper["model"], backend_gatekeeper["reasoning_effort"]),
            ("claude-fable-5-1", "high"),
        )
        design = MODULE.prepare_dispatch(self.v2_packet(role="test-engineer", model_route="design"))["spawn"]
        self.assertEqual((design["model"], design["reasoning_effort"]), ("claude-sonnet-5", "high"))
        with self.assertRaises(MODULE.PacketValidationError):
            MODULE.prepare_dispatch(self.v2_packet(role="gatekeeper"))

    def test_v2_rejects_legacy_or_conflicting_effort_alias(self) -> None:
        for packet in (
            self.v2_packet(effort="high"),
            self.v2_packet(effort="high", reasoning_effort="high"),
        ):
            with self.subTest(packet=packet), self.assertRaises(MODULE.PacketValidationError) as raised:
                MODULE.prepare_dispatch(packet)
            self.assertIn("effort: unsupported", " ".join(raised.exception.errors))

    def test_v2_rejects_v1_and_caller_context_fields(self) -> None:
        for field, value in (
            ("task_name", "legacy_name"),
            ("fork_turns", "1"),
            ("fork_context", False),
        ):
            with self.subTest(field=field), self.assertRaises(MODULE.PacketValidationError):
                MODULE.prepare_dispatch(self.v2_packet(**{field: value}))

    def test_v1_requires_explicit_context_model_and_effort(self) -> None:
        for field in ("fork_turns", "model", "effort"):
            packet = self.v1_packet()
            packet.pop(field)
            with self.subTest(field=field), self.assertRaises(MODULE.PacketValidationError):
                MODULE.prepare_dispatch(packet)
        for value in ("none", "all", 0, -1, None):
            with self.subTest(value=value), self.assertRaises(MODULE.PacketValidationError):
                MODULE.prepare_dispatch(self.v1_packet(fork_turns=value))

    def test_attestation_must_be_exact(self) -> None:
        variants = (
            None,
            {"tool": MODULE.V2_HOST_BINDING, "mode": "direct_tool_call", "available_to_caller": False},
            {"tool": MODULE.V2_HOST_BINDING, "mode": "exec", "available_to_caller": True},
            {**self.binding(MODULE.V2_HOST_BINDING), "route": "shell"},
        )
        for value in variants:
            with self.subTest(value=value), self.assertRaises(MODULE.PacketValidationError) as raised:
                MODULE.prepare_dispatch(self.v2_packet(host_binding=value))
            self.assertIn(MODULE.DIRECT_HOST_BINDING_GUIDANCE, " ".join(raised.exception.errors))

    def test_unknown_and_indirect_bindings_fail_closed(self) -> None:
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
            with self.subTest(alias=alias), self.assertRaises(MODULE.PacketValidationError) as raised:
                MODULE.prepare_dispatch(self.v2_packet(host_binding=self.binding(alias)))
            errors = " ".join(raised.exception.errors)
            self.assertIn(alias, errors)
            self.assertIn(MODULE.DIRECT_HOST_BINDING_GUIDANCE, errors)

    def test_ready_metadata_is_outside_spawn_and_limits_claims(self) -> None:
        result = MODULE.prepare_dispatch(self.v2_packet())
        for field in ("binding", "dispatch_id", "readiness", "invocation", "host_binding"):
            self.assertNotIn(field, result["spawn"])
        self.assertEqual(result["readiness"], MODULE.READY_BOUNDARY)
        for claim in ("host acceptance", "child start", "supervision", "completion"):
            self.assertIn(claim, result["readiness"])

    def test_dispatch_id_is_deterministic_and_binding_scoped(self) -> None:
        first = MODULE.prepare_dispatch(self.v2_packet())
        second = MODULE.prepare_dispatch(self.v2_packet())
        changed = MODULE.prepare_dispatch(self.v2_packet(message="Review a changed candidate."))
        v1 = MODULE.prepare_dispatch(self.v1_packet(message="Review the immutable four-file candidate."))
        self.assertEqual(first["dispatch_id"], second["dispatch_id"])
        self.assertNotEqual(first["dispatch_id"], changed["dispatch_id"])
        self.assertNotEqual(first["dispatch_id"], v1["dispatch_id"])

    def test_cli_binding_failure_has_no_spawn(self) -> None:
        packet = self.v2_packet()
        packet["host_binding"] = self.binding("tools.multi_agent_v1__spawn_agent")
        output = io.StringIO()
        with patch("sys.stdin", io.StringIO(json.dumps(packet))), redirect_stdout(output):
            status = MODULE.main([])
        result = json.loads(output.getvalue())
        self.assertEqual(status, 2)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertNotIn("spawn", result)

    def test_cli_malformed_packets_fail_closed_without_traceback_or_spawn(self) -> None:
        malformed = (
            [],
            self.v2_packet(host_binding={
                "tool": [], "mode": "direct_tool_call", "available_to_caller": True,
            }),
        )
        for packet_value in malformed:
            output = io.StringIO()
            with self.subTest(packet=packet_value), patch(
                "sys.stdin", io.StringIO(json.dumps(packet_value))
            ), redirect_stdout(output):
                status = MODULE.main([])
            result = json.loads(output.getvalue())
            self.assertEqual(status, 2)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertNotIn("spawn", result)

    def test_removed_workflow_ceremony_stays_rejected(self) -> None:
        for field in ("task_id", "allocation", "admission", "receipt", "prior_hard_stop"):
            with self.subTest(field=field), self.assertRaises(MODULE.PacketValidationError):
                MODULE.prepare_dispatch(self.v2_packet(**{field: "legacy"}))

    def test_docs_bind_both_exact_host_variants(self) -> None:
        runtime = " ".join(RUNTIME.read_text(encoding="utf-8").split())
        skill = " ".join(SKILL.read_text(encoding="utf-8").split())
        for prose in (runtime, skill):
            self.assertIn(MODULE.V1_HOST_BINDING, prose)
            self.assertIn(MODULE.V2_HOST_BINDING, prose)
            self.assertIn(MODULE.V1_HOST_INVOCATION, prose)
            self.assertIn(MODULE.V2_HOST_INVOCATION, prose)
            self.assertIn(MODULE.READY_BOUNDARY, prose)
            self.assertIn("fork_context=false", prose)
            self.assertIn("agent_id", prose)


if __name__ == "__main__":
    unittest.main()
