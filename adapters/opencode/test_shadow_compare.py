"""Disposable stdlib tests for the read-only OpenCode shadow comparator."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

try:
    from .shadow_compare import (
        DuplicateRecordError,
        ShadowCompareError,
        canonical_json,
        compare,
        main,
    )
except ImportError:  # pragma: no cover - supports direct script execution.
    from shadow_compare import (  # type: ignore
        DuplicateRecordError,
        ShadowCompareError,
        canonical_json,
        compare,
        main,
    )


class ShadowCompareTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.parent = Path(self.temp_dir.name)
        self.receipts = self.parent / "receipts"
        self.flow = self.parent / "flow"
        self.receipts.mkdir()
        self.flow.mkdir()
        self.receipt_payload = {
            "schema_version": 1,
            "task_id": "task-1",
            "run_id": "run-1",
            "attempt_id": "attempt-1",
            "role_id": "backend-engineer",
            "planned_model": "opencode-go/deepseek-v4-pro",
            "actual_model": "opencode-go/gpt-5.6-luna",
            "actual_model_status": "TRUSTED",
            "map_ref": "adapters/opencode/model-pool.map.md",
            "map_revision": "rev-1",
            "map_digest": "a" * 64,
            "source_sha": "b" * 40,
            "record_revision": 2,
            "finalized_at": "2026-08-19T12:00:00Z",
        }
        self.flow_payload = {
            "schema_version": 1,
            "task_id": "task-1",
            "run_id": "run-1",
            "attempt_id": "attempt-1",
            "role_id": "backend-engineer",
            "map_ref": "adapters/opencode/model-pool.map.md",
            "map_revision": "rev-1",
            "map_digest": "a" * 64,
            "source_sha": "b" * 40,
            "revision": 2,
            "updated_at": "2026-08-19T12:00:00Z",
        }

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_json(self, path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")

    def write_receipt(self, name: str = "receipt.json", **changes: object) -> Path:
        value = dict(self.receipt_payload)
        value.update(changes)
        path = self.receipts / name
        self.write_json(path, value)
        return path

    def write_flow(self, name: str = "flow.json", **changes: object) -> Path:
        value = dict(self.flow_payload)
        value.update(changes)
        path = self.flow / name
        self.write_json(path, value)
        return path

    def entries(self, report: dict[str, object], classification: str) -> list[dict[str, object]]:
        return [
            entry
            for entry in report["entries"]  # type: ignore[index]
            if entry["classification"] == classification  # type: ignore[index]
        ]

    def test_match_includes_receipt_identity_and_models(self) -> None:
        self.write_receipt()
        self.write_flow()

        report = compare(self.receipts, self.flow)

        self.assertEqual(report["summary"]["MATCH"], 1)  # type: ignore[index]
        entry = self.entries(report, "MATCH")[0]
        self.assertEqual(entry["role_id"], "backend-engineer")
        self.assertEqual(entry["planned_model"], self.receipt_payload["planned_model"])
        self.assertEqual(entry["actual_model"], self.receipt_payload["actual_model"])
        self.assertEqual(entry["actual_model_status"], "TRUSTED")
        self.assertEqual(entry["task_id"], "task-1")
        self.assertEqual(entry["run_id"], "run-1")
        self.assertEqual(entry["attempt_id"], "attempt-1")
        self.assertEqual(entry["receipt_ref"], "receipt.json")
        self.assertEqual(entry["flow_ref"], "flow.json")

    def test_missing_expected_side_is_reported(self) -> None:
        self.write_receipt()

        report = compare(self.receipts, self.flow)

        self.assertEqual(report["summary"]["MISSING"], 1)  # type: ignore[index]
        self.assertIn("expected flow", self.entries(report, "MISSING")[0]["reason"])

    def test_mismatch_reports_only_trusted_field_names(self) -> None:
        self.write_receipt()
        self.write_flow(map_digest="c" * 64)

        report = compare(self.receipts, self.flow)

        entry = self.entries(report, "MISMATCH")[0]
        self.assertIn("map_digest", entry["reason"])
        self.assertNotIn("c" * 64, canonical_json(report))

    def test_stale_uses_an_explicit_selected_reference(self) -> None:
        self.write_receipt()
        self.write_flow(revision=1, updated_at="2026-08-19T11:00:00Z")

        report = compare(self.receipts, self.flow, reference="receipt")

        self.assertEqual(report["summary"]["STALE"], 1)  # type: ignore[index]
        self.assertIn("flow", self.entries(report, "STALE")[0]["reason"])

    def test_current_wysy_style_flow_without_ids_is_unjoinable(self) -> None:
        self.write_receipt()
        self.write_json(
            self.flow / "current.json",
            {
                "schema_version": 1,
                "flow_id": "task-1",
                "request": "raw prompt should never be printed",
                "monitor": {
                    "raw_request": "api_key=do-not-print",
                    "model": {"planned": "secret-output"},
                },
                "docs": {"run_id": "run-1:task-1"},
            },
        )

        report = compare(self.receipts, self.flow)
        rendered = canonical_json(report)

        self.assertEqual(report["summary"]["UNJOINABLE"], 1)  # type: ignore[index]
        self.assertNotIn('"classification":"MATCH"', rendered)
        self.assertNotIn("raw prompt", rendered)
        self.assertNotIn("api_key", rendered)
        self.assertNotIn("secret-output", rendered)
        self.assertNotIn("cost", rendered)
        self.assertNotIn(os.fspath(self.parent), rendered)

    def test_pending_input_is_orphaned_and_not_retried(self) -> None:
        pending = self.receipts / "task-1" / "run-1" / "attempt-1.json.pending"
        pending.parent.mkdir(parents=True)
        pending.write_text("pending raw output", encoding="utf-8")
        before = pending.read_bytes()

        report = compare(self.receipts, self.flow)

        self.assertEqual(report["entries"], [])
        self.assertEqual(report["orphans"][0]["classification"], "ORPHANED")  # type: ignore[index]
        self.assertEqual(pending.read_bytes(), before)

    def test_duplicate_receipt_is_a_contract_error(self) -> None:
        self.write_receipt("a.json")
        self.write_receipt("b.json")

        with self.assertRaises(DuplicateRecordError):
            compare(self.receipts, self.flow)

    def test_deterministic_output_and_ordering(self) -> None:
        self.write_receipt("z.json", task_id="task-z")
        self.write_receipt("a.json", task_id="task-a")
        self.write_flow("z-flow.json", task_id="task-z")
        self.write_flow("a-flow.json", task_id="task-a")

        first = canonical_json(compare(self.receipts, self.flow))
        second = canonical_json(compare(self.receipts, self.flow))

        self.assertEqual(first, second)
        self.assertLess(first.index("task-a"), first.index("task-z"))

    def test_compare_does_not_mutate_receipt_or_parent_flow(self) -> None:
        parent_snapshot = sorted(
            (path.relative_to(self.parent).as_posix(), path.read_bytes() if path.is_file() else None)
            for path in self.parent.rglob("*")
        )
        self.write_receipt()
        self.write_flow()
        before = sorted(
            (path.relative_to(self.parent).as_posix(), path.read_bytes() if path.is_file() else None)
            for path in self.parent.rglob("*")
        )

        compare(self.receipts, self.flow)

        after = sorted(
            (path.relative_to(self.parent).as_posix(), path.read_bytes() if path.is_file() else None)
            for path in self.parent.rglob("*")
        )
        self.assertEqual(after, before)
        self.assertEqual(sorted(path.name for path in self.parent.iterdir()), ["flow", "receipts"])
        self.assertEqual(parent_snapshot, [("flow", None), ("receipts", None)])

    def test_no_network_is_used(self) -> None:
        self.write_receipt()
        self.write_flow()
        with patch.object(socket, "socket", side_effect=AssertionError("network")):
            report = compare(self.receipts, self.flow)
        self.assertEqual(report["summary"]["MATCH"], 1)  # type: ignore[index]

    def test_symlink_root_and_child_are_rejected(self) -> None:
        self.write_receipt()
        root_link = self.parent / "receipt-link"
        root_link.symlink_to(self.receipts, target_is_directory=True)
        with redirect_stderr(io.StringIO()):
            result = main(["--receipt-root", os.fspath(root_link)])
        self.assertEqual(result, 1)

        child_link = self.receipts / "escape.json"
        child_link.symlink_to(self.parent / "outside.json")
        with self.assertRaises(ShadowCompareError):
            compare(self.receipts)

    def test_cli_valid_unjoinable_is_zero_and_error_is_nonzero(self) -> None:
        self.write_json(self.flow / "current.json", {"flow_id": "flow-only"})
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            valid_code = main(
                ["--receipt-root", os.fspath(self.receipts), "--flow-root", os.fspath(self.flow)]
            )
        self.assertEqual(valid_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(json.loads(stdout.getvalue())["summary"]["UNJOINABLE"], 1)

        bad = self.receipts / "bad.json"
        bad.write_text("not json", encoding="utf-8")
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            invalid_code = main(["--receipt-root", os.fspath(self.receipts)])
        self.assertEqual(invalid_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("shadow compare error", stderr.getvalue())

    def test_cli_does_not_discover_parent_paths(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = main([])
        self.assertNotEqual(result, 0)
        self.assertEqual(stdout.getvalue(), "")

    def test_nested_complete_fixture_projection_is_explicitly_joinable(self) -> None:
        self.write_receipt()
        flow = dict(self.flow_payload)
        for field in ("task_id", "run_id", "attempt_id", "map_ref", "map_revision", "map_digest", "source_sha"):
            flow.pop(field, None)
        flow["shadow_projection"] = {
            "task_id": "task-1",
            "run_id": "run-1",
            "attempt_id": "attempt-1",
            "map_ref": "adapters/opencode/model-pool.map.md",
            "map_revision": "rev-1",
            "map_digest": "a" * 64,
            "source_sha": "b" * 40,
        }
        self.write_json(self.flow / "projection.json", flow)

        report = compare(self.receipts, self.flow)

        self.assertEqual(report["summary"]["MATCH"], 1)  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()
