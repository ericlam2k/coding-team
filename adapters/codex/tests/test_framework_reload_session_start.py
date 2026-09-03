from __future__ import annotations

import importlib.util
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "framework-reload-session-start.py"
SPEC = importlib.util.spec_from_file_location("framework_reload_session_start", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FrameworkReloadSessionStartTests(unittest.TestCase):
    def run_hook(self, event: object) -> tuple[int, dict[str, object]]:
        output = io.StringIO()
        with patch("sys.stdin", io.StringIO(json.dumps(event))), redirect_stdout(output):
            code = MODULE.main()
        return code, json.loads(output.getvalue())

    def test_compact_session_reanchors_by_contract(self) -> None:
        code, result = self.run_hook({"hook_event_name": "SessionStart", "source": "compact"})
        self.assertEqual(code, 0)
        self.assertTrue(result["continue"])
        self.assertEqual(result["hookSpecificOutput"]["hookEventName"], "SessionStart")  # type: ignore[index]
        self.assertIn("Framework re-anchor", result["hookSpecificOutput"]["additionalContext"])  # type: ignore[index]

    def test_non_compact_session_is_noop(self) -> None:
        code, result = self.run_hook({"hook_event_name": "SessionStart", "source": "startup"})
        self.assertEqual(code, 0)
        self.assertNotIn("hookSpecificOutput", result)

    def test_invalid_input_fails_closed(self) -> None:
        output = io.StringIO()
        with patch("sys.stdin", io.StringIO("not-json")), redirect_stdout(output):
            code = MODULE.main()
        result = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertFalse(result["continue"])
        self.assertEqual(result["stopReason"], "CODING_TEAM_RELOAD:EVENT_INVALID")


if __name__ == "__main__":
    unittest.main()
