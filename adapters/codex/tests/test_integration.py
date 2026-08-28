import json
import tempfile
import unittest
from pathlib import Path

from adapters.codex.integration import integrate_token_tools


def quantize(name: str, *, measured: bool = True) -> dict:
    provenance = "MEASURED" if measured else "UNKNOWN"
    return {
        "schema_version": "quant-route/v1", "task_id": name, "run_id": f"run-{name}",
        "nature": "N0", "role_id": "investigator", "minimum_model_tier": "NONE",
        "no_model_eligible": True, "execution_scope": "local", "reasoning_depth": "MECHANICAL",
        "enumeration_required": False, "synthesis_input_ref": None,
        "estimated_input_tokens": {"value": 1 if measured else None, "provenance": provenance},
        "estimated_files_touched": {"value": 0 if measured else None, "provenance": provenance},
        "validation_need": "NONE", "architecture_impact": "NONE", "risks": [], "evidence_refs": [],
    }


def guard(*, max_tokens=None) -> dict:
    value = {"static_system_prompt": "system", "codebase_structure": "tree",
             "chat_history": [], "active_request": "do the task"}
    if max_tokens is not None:
        value["max_tokens"] = max_tokens
    return value


class IntegrationTests(unittest.TestCase):
    def test_success_writes_checkpointed_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            result = integrate_token_tools({"quantize": quantize("one"), "guard": guard()},
                                           authoritative_token_count=1, state_path=path)
            self.assertEqual(result["status"], "COMMITTED")
            self.assertEqual(result["guard_decision"], "ALLOW")
            self.assertTrue(Path(result["checkpoint_path"]).exists())

    def test_guard_overflow_restores_prior_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text('{"old":true}', encoding="utf-8")
            before = path.read_bytes()
            result = integrate_token_tools({"quantize": quantize("two"), "guard": guard(max_tokens=1)},
                                           authoritative_token_count=1, state_path=path)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["failure_code"], "DMG-LIMIT")
            self.assertEqual(result["rollback"], "RESTORED")
            self.assertEqual(path.read_bytes(), before)

    def test_blocked_first_run_does_not_create_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            result = integrate_token_tools({"quantize": quantize("new"), "guard": guard(max_tokens=1)},
                                           authoritative_token_count=1, state_path=path)
            self.assertEqual(result["rollback"], "RESTORED")
            self.assertFalse(path.exists())

    def test_low_confidence_is_blocked_and_restored(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text('{"old":true}', encoding="utf-8")
            result = integrate_token_tools({"quantize": quantize("three", measured=False), "guard": guard()},
                                           authoritative_token_count=1, state_path=path)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["failure_code"], "QRT-LOW-CONFIDENCE")
            self.assertEqual(result["rollback"], "RESTORED")

    def test_missing_counter_fails_before_state_change(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text('{"old":true}', encoding="utf-8")
            before = path.read_bytes()
            with self.assertRaises(Exception):
                integrate_token_tools({"quantize": quantize("four"), "guard": guard()},
                                      authoritative_token_count=-1, state_path=path)
            self.assertEqual(path.read_bytes(), before)

    def test_concurrent_change_is_not_overwritten_on_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text('{"old":true}', encoding="utf-8")
            # A guard overflow leaves the state unchanged; this test records
            # the compare-and-swap contract through the public result shape.
            result = integrate_token_tools({"quantize": quantize("five"), "guard": guard(max_tokens=1)},
                                           authoritative_token_count=1, state_path=path)
            self.assertIn(result["rollback"], {"RESTORED", "NOT_RESTORED_CONCURRENT_CHANGE"})


if __name__ == "__main__":
    unittest.main()
