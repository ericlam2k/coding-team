"""Contract tests for the compact terminal adapter."""

import inspect
import math
import os
import sys
import tempfile
import time
import unittest

from adapters.codex import compact_terminal as compact_terminal_module
from adapters.codex.compact_terminal import (
    CTERM_ARGV,
    CTERM_DECODE,
    CTERM_INTERNAL,
    CTERM_LINE_LIMIT,
    CTERM_SPAWN,
    CTERM_TIMEOUT_VALUE,
    CompactTerminalError,
    execute_terminal_command,
)


class CompactTerminalContractTests(unittest.TestCase):
    def run_python(self, source, *arguments, timeout_s=2):
        return execute_terminal_command(
            [sys.executable, "-c", source, *arguments], timeout_s=timeout_s
        )

    def assert_private_error(self, expected_code, call, *args, **kwargs):
        with self.assertRaises(CompactTerminalError) as caught:
            call(*args, **kwargs)
        error = caught.exception
        self.assertEqual(error.code, expected_code)
        self.assertEqual(str(error), expected_code)
        self.assertEqual(error.args, (expected_code,))
        self.assertNotIn("private-marker", repr(error))
        return error

    def test_success_exact_schema_and_empty_output(self):
        result = self.run_python("pass")
        self.assertEqual(result, {"exit_code": 0, "last_lines": []})
        self.assertEqual(set(result), {"exit_code", "last_lines"})

    def test_nonzero_exit_preserves_tail(self):
        result = self.run_python("import sys; print('tail'); sys.exit(7)")
        self.assertEqual(result, {"exit_code": 7, "last_lines": ["tail"]})

    def test_combined_stream_preserves_flushed_write_order(self):
        source = (
            "import os; "
            "os.write(1, b'out-1\\n'); os.write(2, b'err-1\\n'); "
            "os.write(1, b'out-2\\n'); os.write(2, b'err-2\\n')"
        )
        result = self.run_python(source)
        self.assertEqual(
            result["last_lines"], ["out-1", "err-1", "out-2", "err-2"]
        )

    def test_retains_only_final_twenty_lines(self):
        result = self.run_python(
            "import sys; sys.stdout.write(''.join(f'{i}\\n' for i in range(25)))"
        )
        self.assertEqual(result["last_lines"], [str(i) for i in range(5, 25)])

    def test_normalizes_crlf_and_lone_cr_without_final_extra_line(self):
        result = self.run_python(
            "import os; os.write(1, b'a\\r\\nb\\rc\\r\\r')"
        )
        self.assertEqual(result["last_lines"], ["a", "b", "c", ""])

    def test_preserves_interior_empty_lines_but_not_final_terminator(self):
        result = self.run_python("import os; os.write(1, b'a\\n\\nb\\n')")
        self.assertEqual(result["last_lines"], ["a", "", "b"])

    def test_decodes_unicode_strictly(self):
        result = self.run_python("print('café')")
        self.assertEqual(result["last_lines"], ["café"])
        self.assert_private_error(
            CTERM_DECODE,
            self.run_python,
            "import os; os.write(1, b'private-marker\\xff')",
        )

    def test_line_limit_accepts_boundary_and_rejects_excess(self):
        accepted = self.run_python("import os; os.write(1, b'x' * 65536)")
        self.assertEqual(len(accepted["last_lines"][0]), 65536)
        self.assert_private_error(
            CTERM_LINE_LIMIT,
            self.run_python,
            "import os; os.write(1, b'private-marker' + b'x' * 65537)",
        )

    def test_shell_metacharacters_are_literal_argv(self):
        marker = "$(private-marker); echo expanded | *"
        result = self.run_python("import sys; print(sys.argv[1])", marker)
        self.assertEqual(result["last_lines"], [marker])

    def test_timeout_returns_null_exit_and_drained_tail(self):
        started = time.monotonic()
        result = self.run_python(
            "import signal, sys, time; "
            "signal.signal(signal.SIGTERM, lambda *_: "
            "(print('during-cleanup', flush=True), sys.exit(0))); "
            "print('before-timeout', flush=True); time.sleep(10)",
            timeout_s=0.1,
        )
        self.assertEqual(
            result,
            {
                "exit_code": None,
                "last_lines": ["before-timeout", "during-cleanup"],
            },
        )
        self.assertLess(time.monotonic() - started, 2)

    @unittest.skipUnless(os.name == "posix", "POSIX process-group lifecycle proof")
    def test_timeout_stops_descendant_that_ignores_termination(self):
        descendant = (
            "import pathlib, signal, sys, time; "
            "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
            "time.sleep(0.6); pathlib.Path(sys.argv[1]).write_text('unexpected')"
        )
        parent = (
            "import subprocess, sys, time; "
            "subprocess.Popen([sys.executable, '-c', sys.argv[1], sys.argv[2]]); "
            "print('descendant-started', flush=True); time.sleep(10)"
        )
        with tempfile.TemporaryDirectory() as directory:
            marker = os.path.join(directory, "descendant-marker")
            result = self.run_python(parent, descendant, marker, timeout_s=0.1)
            if compact_terminal_module._PROCESS_GROUP_CLEANUP_CAPABILITY is False:
                time.sleep(0.7)
                self.skipTest("process-group signals unavailable on this host")
            self.assertEqual(
                result,
                {"exit_code": None, "last_lines": ["descendant-started"]},
            )
            time.sleep(0.7)
            self.assertFalse(os.path.exists(marker))

    def test_timeout_is_keyword_only(self):
        with self.assertRaises(TypeError):
            execute_terminal_command([sys.executable, "-c", "pass"], 1)
        parameter = inspect.signature(execute_terminal_command).parameters["timeout_s"]
        self.assertIs(parameter.kind, inspect.Parameter.KEYWORD_ONLY)

    def test_invalid_argv_is_code_only(self):
        invalid_values = (
            "private-marker",
            b"private-marker",
            [],
            [""],
            ["ok", 1],
            ["ok", "private-marker\0"],
        )
        for value in invalid_values:
            with self.subTest(value=type(value).__name__):
                self.assert_private_error(
                    CTERM_ARGV, execute_terminal_command, value, timeout_s=1
                )

    def test_invalid_timeout_is_code_only(self):
        for value in (True, False, 0, -1, math.inf, -math.inf, math.nan, "private-marker"):
            with self.subTest(value=value):
                self.assert_private_error(
                    CTERM_TIMEOUT_VALUE,
                    execute_terminal_command,
                    [sys.executable],
                    timeout_s=value,
                )

    def test_spawn_failure_is_code_only(self):
        self.assert_private_error(
            CTERM_SPAWN,
            execute_terminal_command,
            ["private-marker-command-that-does-not-exist"],
            timeout_s=1,
        )

    def test_error_constructor_cannot_expose_arbitrary_code_or_detail(self):
        error = CompactTerminalError("private-marker")
        self.assertEqual(error.code, CTERM_INTERNAL)
        self.assertEqual(str(error), CTERM_INTERNAL)
        with self.assertRaises(TypeError):
            CompactTerminalError(CTERM_INTERNAL, "private-marker")


if __name__ == "__main__":
    unittest.main()
