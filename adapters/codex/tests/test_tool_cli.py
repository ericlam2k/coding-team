"""Integration tests for explicit compact-terminal CLI activation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
CT = ROOT / "bin" / "ct"


class ToolCliIntegrationTests(unittest.TestCase):
    def invoke(
        self, *args: str, timeout: float = 5, input_text: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(CT), *args], capture_output=True, text=True, timeout=timeout,
            check=False, input=input_text,
        )

    def terminal(self, *command: str, timeout_s: str = "2") -> subprocess.CompletedProcess[str]:
        return self.invoke("tools", "terminal", "--timeout-s", timeout_s, "--", *command)

    def skeleton(
        self, root: Path, path: Path, *, max_bytes: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        args = ["tools", "skeleton", "--allowed-root", str(root)]
        if max_bytes is not None:
            args.extend(("--max-bytes", max_bytes))
        args.extend(("--", str(path)))
        return self.invoke(*args)

    def quantization_request(self, **overrides: object) -> dict[str, object]:
        request: dict[str, object] = {
            "schema_version": "quant-route/v1",
            "task_id": "CLI-1",
            "run_id": "cli/01",
            "nature": "N1",
            "role_id": "backend-engineer",
            "minimum_model_tier": "0",
            "no_model_eligible": False,
            "execution_scope": "SCOPED_WRITE",
            "reasoning_depth": "MECHANICAL",
            "enumeration_required": False,
            "synthesis_input_ref": None,
            "estimated_input_tokens": {"value": 1000, "provenance": "MEASURED"},
            "estimated_files_touched": {"value": 1, "provenance": "MEASURED"},
            "validation_need": "NONE",
            "architecture_impact": "NONE",
            "risks": [],
            "evidence_refs": [],
        }
        request.update(overrides)
        return request

    def guard_request(self, **overrides: object) -> dict[str, object]:
        request: dict[str, object] = {
            "static_system_prompt": "Static policy",
            "codebase_structure": "Codebase structure",
            "chat_history": [
                {"role": "user", "content": "Earlier request"},
                {"role": "assistant", "content": "Earlier response"},
            ],
            "active_request": "Active request",
        }
        request.update(overrides)
        return request

    def test_literal_arguments_and_exact_result_schema(self) -> None:
        literal = "$(printf unsafe);*"
        result = self.terminal(
            sys.executable, "-c", "import sys; print(sys.argv[1])", literal
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        payload = json.loads(result.stdout)
        self.assertEqual(set(payload), {"exit_code", "last_lines"})
        self.assertEqual(payload, {"exit_code": 0, "last_lines": [literal]})
        self.assertEqual(result.stdout, json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")

    def test_tail_is_bounded_to_twenty_lines(self) -> None:
        result = self.terminal(sys.executable, "-c", "print(*range(25), sep='\\n')")
        self.assertEqual(json.loads(result.stdout)["last_lines"], [str(i) for i in range(5, 25)])

    def test_timeout_is_a_compact_result(self) -> None:
        result = self.terminal(
            sys.executable, "-c", "import time; print('ready', flush=True); time.sleep(2)",
            timeout_s="0.05",
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {"exit_code": None, "last_lines": ["ready"]})

    def test_cli_and_spawn_errors_are_private_json_on_stderr(self) -> None:
        invalid = self.invoke("tools", "terminal", "--timeout-s", "secret")
        self.assertNotEqual(invalid.returncode, 0)
        self.assertEqual(invalid.stdout, "")
        self.assertEqual(json.loads(invalid.stderr), {"error": "CTERM-CLI-ARGV"})
        spawn = self.terminal("/definitely/not/a/real/executable/private-name")
        self.assertNotEqual(spawn.returncode, 0)
        self.assertEqual(spawn.stdout, "")
        self.assertEqual(json.loads(spawn.stderr), {"error": "CTERM-SPAWN"})
        self.assertNotIn("private-name", spawn.stderr)

    def test_status_and_help_do_not_activate_terminal(self) -> None:
        for command in ("status", "help"):
            with self.subTest(command=command):
                result = self.invoke(command)
                self.assertEqual(result.returncode, 0)
                self.assertNotIn('"exit_code":', result.stdout)
                self.assertNotIn('"definitions":', result.stdout)
                self.assertEqual(result.stderr, "")

    def test_skeleton_cli_is_fail_closed_before_file_access(self) -> None:
        private = "/private/path/that-must-not-be-opened.py"
        result = self.invoke(
            "tools", "skeleton", "--allowed-root", "/private/root", "--", private
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            json.loads(result.stderr), {"error": "AST-MEMORY-UNSUPPORTED"}
        )
        self.assertNotIn(private, result.stderr)

    def test_skeleton_never_calls_core_even_with_valid_or_malformed_args(self) -> None:
        from adapters.codex import tool_cli

        with mock.patch.object(
            tool_cli, "get_file_skeleton", side_effect=AssertionError("must not call")
        ) as core_call:
            for args in (
                [],
                ["--allowed-root", "root", "--", "file.py"],
                ["private-malformed-payload"],
            ):
                with self.subTest(args=args):
                    with mock.patch.object(tool_cli.sys, "stderr") as stderr:
                        self.assertEqual(tool_cli._skeleton(args), 2)
                        stderr.write.assert_called_once_with(
                            '{"error":"AST-MEMORY-UNSUPPORTED"}\n'
                        )
        core_call.assert_not_called()

    def test_quantize_routes_request_from_stdin(self) -> None:
        result = self.invoke(
            "tools", "quantize", "--request-file", "-",
            input_text=json.dumps(self.quantization_request()),
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ROUTED")
        self.assertEqual(payload["quantized_class"], "Q1")

    def test_quantize_returns_blocked_result_from_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request_file = Path(directory) / "request with spaces.json"
            request_file.write_text(
                json.dumps(self.quantization_request(risks=["SECURITY"])),
                encoding="utf-8",
            )
            result = self.invoke(
                "tools", "quantize", "--request-file", str(request_file)
            )
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "BLOCKED")
        self.assertEqual(payload["failure_code"], "QRT-HUMAN-GATE")

    def test_quantize_malformed_payload_and_missing_file_are_private(self) -> None:
        private = "private-payload-value"
        malformed = self.invoke(
            "tools", "quantize", "--request-file", "-",
            input_text='{"secret":"' + private + '",}',
        )
        missing = self.invoke(
            "tools", "quantize", "--request-file", "/private/missing/request.json"
        )
        self.assertEqual(json.loads(malformed.stderr), {"error": "QRT-CLI-JSON"})
        self.assertEqual(json.loads(missing.stderr), {"error": "QRT-CLI-IO"})
        for result in (malformed, missing):
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertNotIn(private, result.stderr)
            self.assertNotIn("/private/", result.stderr)

    def test_quantize_schema_and_cli_argument_errors_are_stable(self) -> None:
        schema = self.quantization_request(task_id=[])
        invalid_schema = self.invoke(
            "tools", "quantize", "--request-file", "-",
            input_text=json.dumps(schema),
        )
        invalid_cli = self.invoke("tools", "quantize", "request.json")
        self.assertEqual(json.loads(invalid_schema.stderr), {"error": "QRT-SCHEMA"})
        self.assertEqual(json.loads(invalid_cli.stderr), {"error": "QRT-CLI-ARGV"})

    def test_guard_stdin_preserves_exact_order_and_last_request(self) -> None:
        request = self.guard_request()
        result = self.invoke(
            "tools", "guard", "--request-file", "-",
            "--authoritative-token-count", "259999",
            input_text=json.dumps(request),
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "ALLOW")
        self.assertEqual(payload["token_count"], 259_999)
        self.assertEqual(
            payload["messages"],
            [
                {"role": "system", "content": request["static_system_prompt"]},
                {"role": "system", "content": request["codebase_structure"]},
                *request["chat_history"],
                {"role": "user", "content": request["active_request"]},
            ],
        )
        self.assertEqual(payload["messages"][-1]["content"], "Active request")

    def test_guard_boundary_allows_259999_and_rejects_260000(self) -> None:
        serialized = json.dumps(self.guard_request())
        allowed = self.invoke(
            "tools", "guard", "--request-file", "-",
            "--authoritative-token-count", "259999", input_text=serialized,
        )
        rejected = self.invoke(
            "tools", "guard", "--request-file", "-",
            "--authoritative-token-count", "260000", input_text=serialized,
        )
        self.assertEqual(allowed.returncode, 0)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertEqual(rejected.stdout, "")
        self.assertEqual(json.loads(rejected.stderr), {"error": "DMG-LIMIT"})

    def test_guard_cli_accepts_runtime_limits_and_rejects_invalid_config(self) -> None:
        configured = self.guard_request(
            platform_context_window=1000, reserve_tokens=200, max_tokens=500
        )
        allowed = self.invoke(
            "tools", "guard", "--request-file", "-",
            "--authoritative-token-count", "499", input_text=json.dumps(configured),
        )
        self.assertEqual(json.loads(allowed.stdout)["token_ceiling"], 500)
        invalid = self.invoke(
            "tools", "guard", "--request-file", "-",
            "--authoritative-token-count", "1",
            input_text=json.dumps(self.guard_request(reserve_tokens=272000)),
        )
        self.assertEqual(json.loads(invalid.stderr), {"error": "DMG-TOKEN-CEILING"})

    def test_guard_file_and_prefix_stability(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request_file = Path(directory) / "guard request.json"
            request_file.write_text(json.dumps(self.guard_request()), encoding="utf-8")
            baseline = self.invoke(
                "tools", "guard", "--request-file", str(request_file),
                "--authoritative-token-count", "10",
            )
            request_file.write_text(
                json.dumps(self.guard_request(
                    chat_history=[{"role": "user", "content": "Changed"}],
                    active_request="Changed active request",
                )),
                encoding="utf-8",
            )
            changed_history = self.invoke(
                "tools", "guard", "--request-file", str(request_file),
                "--authoritative-token-count", "11",
            )
        self.assertEqual(
            json.loads(baseline.stdout)["prefix_digest"],
            json.loads(changed_history.stdout)["prefix_digest"],
        )

    def test_guard_missing_and_invalid_counter_fail_closed(self) -> None:
        missing = self.invoke("tools", "guard", "--request-file", "-")
        invalid = self.invoke(
            "tools", "guard", "--request-file", "-",
            "--authoritative-token-count", "-1",
        )
        self.assertEqual(json.loads(missing.stderr), {"error": "DMG-COUNTER-MISSING"})
        self.assertEqual(json.loads(invalid.stderr), {"error": "DMG-COUNTER-INVALID"})
        self.assertNotEqual(missing.returncode, 0)
        self.assertNotEqual(invalid.returncode, 0)

    def test_guard_malformed_private_payload_and_no_auto_dispatch(self) -> None:
        private = "private-message-value"
        malformed = self.invoke(
            "tools", "guard", "--request-file", "-",
            "--authoritative-token-count", "1",
            input_text='{"active_request":"' + private + '",}',
        )
        self.assertEqual(json.loads(malformed.stderr), {"error": "DMG-SCHEMA"})
        self.assertNotIn(private, malformed.stderr)
        for command in ("status", "help"):
            result = self.invoke(command)
            self.assertEqual(result.returncode, 0)
            self.assertNotIn('"decision":"ALLOW"', result.stdout)


if __name__ == "__main__":
    unittest.main()
