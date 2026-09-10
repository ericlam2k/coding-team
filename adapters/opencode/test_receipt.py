"""Unit tests for the hermetic OpenCode receipt writer."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from .receipt import (
        TRUSTED_RUNTIME_RECEIPT,
        PendingReceipt,
        ReceiptConflict,
        ReceiptError,
        ReceiptValidationError,
        RootValidationError,
        record_receipt,
    )
except ImportError:  # pragma: no cover - supports direct script execution.
    from receipt import (  # type: ignore
        TRUSTED_RUNTIME_RECEIPT,
        PendingReceipt,
        ReceiptConflict,
        ReceiptError,
        ReceiptValidationError,
        RootValidationError,
        record_receipt,
    )


class ReceiptWriterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.parent = Path(self.temp_dir.name)
        self.root = self.parent / "coding-team"
        (self.root / "core").mkdir(parents=True)
        (self.root / "adapters" / "opencode").mkdir(parents=True)
        subprocess.run(
            ["git", "init", "--quiet", os.fspath(self.root)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.payload = {
            "task_id": "task-1",
            "run_id": "run-1",
            "attempt_id": "attempt-1",
            "role_id": "backend-engineer",
            "planned_model": "opencode-go/deepseek-v4-pro",
            "planned_tier": "1-build-backend",
            "map_ref": "adapters/opencode/model-pool.map.md",
            "map_revision": "rev-1",
            "map_digest": "a" * 64,
            "exit_state": "COMPLETE",
            "source_sha": "b" * 40,
            "usage": {
                "status": "UNAVAILABLE",
                "source": "runtime receipt not supplied",
                "basis": "provider usage was not exposed",
            },
            "cost": {
                "status": "UNAVAILABLE",
                "source": "runtime receipt not supplied",
                "basis": "provider cost was not exposed",
            },
            "performance": {
                "status": "UNAVAILABLE",
                "source": "runtime receipt not supplied",
                "basis": "performance was not measured",
            },
            "artifact_refs": ["artifacts/test-result.json"],
        }

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def record(self, **changes: object) -> Path:
        payload = dict(self.payload)
        payload.update(changes)
        return record_receipt(self.root, payload)

    def expected_path(self) -> Path:
        return (
            self.root
            / ".coding-team"
            / "receipts"
            / "opencode"
            / "task-1"
            / "run-1"
            / "attempt-1"
            / "attempt-1.json"
        ).resolve()

    def read_receipt(self, path: Path) -> dict[str, object]:
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)

    def test_valid_record(self) -> None:
        path = self.record()
        self.assertEqual(path, self.expected_path())
        self.assertTrue(path.is_file())
        self.assertFalse(path.with_name(path.name + ".pending").exists())
        data = self.read_receipt(path)
        self.assertEqual(data["role_id"], "backend-engineer")
        self.assertEqual(data["planned_model"], self.payload["planned_model"])
        self.assertEqual(data["actual_model"], "UNAVAILABLE")
        self.assertEqual(data["record_ref"], ".coding-team/receipts/opencode/task-1/run-1/attempt-1/attempt-1.json")
        self.assertEqual(data["auto_action"], "none")
        self.assertTrue(str(data["created_at"]).endswith("Z"))
        self.assertTrue(str(data["finalized_at"]).endswith("Z"))

    def test_actual_model_is_unavailable_without_trusted_source(self) -> None:
        path = self.record(actual_model="provider/model", actual_model_source="catalog")
        data = self.read_receipt(path)
        self.assertEqual(data["actual_model"], "UNAVAILABLE")
        self.assertEqual(data["actual_model_source"], "UNAVAILABLE")
        self.assertEqual(data["actual_model_status"], "UNAVAILABLE")

    def test_trusted_runtime_model_is_retained(self) -> None:
        path = self.record(
            actual_model="opencode-go/gpt-5.6-luna",
            actual_model_source=TRUSTED_RUNTIME_RECEIPT,
        )
        data = self.read_receipt(path)
        self.assertEqual(data["actual_model"], "opencode-go/gpt-5.6-luna")
        self.assertEqual(data["actual_model_source"], TRUSTED_RUNTIME_RECEIPT)
        self.assertEqual(data["actual_model_status"], "TRUSTED")

    def test_cost_unavailable_does_not_infer_a_value(self) -> None:
        payload = dict(self.payload)
        payload["usage"] = {
            "status": "MEASURED",
            "source": "runtime receipt",
            "basis": "provider token counters",
            "input_tokens": 10,
            "output_tokens": 5,
        }
        payload["performance"] = {
            "status": "MEASURED",
            "source": "local timer",
            "basis": "elapsed wall clock",
            "latency_ms": 12,
        }
        path = record_receipt(self.root, payload)
        data = self.read_receipt(path)
        self.assertEqual(data["cost"]["status"], "UNAVAILABLE")
        self.assertNotIn("amount", data["cost"])

    def test_relative_artifact_reference_is_recorded(self) -> None:
        path = self.record(artifact_refs=["artifacts/unit/result.json", "logs/run.txt"])
        self.assertEqual(
            self.read_receipt(path)["artifact_refs"],
            ["artifacts/unit/result.json", "logs/run.txt"],
        )

    def test_absolute_and_traversal_artifact_references_are_rejected(self) -> None:
        for reference in ("/tmp/result.json", "../result.json", "artifacts/../../result.json", "C:\\result.json"):
            with self.subTest(reference=reference):
                with self.assertRaises(ReceiptValidationError):
                    self.record(artifact_refs=[reference])
        self.assertFalse((self.root / ".coding-team").exists())

    def test_wrong_root_and_parent_root_are_rejected(self) -> None:
        with self.assertRaises(RootValidationError):
            self.record_receipt_at(self.root / "core")

        subprocess.run(
            ["git", "init", "--quiet", os.fspath(self.parent)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        with self.assertRaises(RootValidationError):
            self.record_receipt_at(self.parent)
        self.assertFalse((self.parent / ".coding-team").exists())

    def record_receipt_at(self, root: Path) -> Path:
        return record_receipt(root, self.payload)

    def test_symlink_root_and_non_repository_root_are_rejected(self) -> None:
        link = self.parent / "root-link"
        link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(RootValidationError):
            self.record_receipt_at(link)

        non_repo = self.parent / "not-a-repository"
        non_repo.mkdir()
        with self.assertRaises(RootValidationError):
            self.record_receipt_at(non_repo)

    def test_unknown_top_level_fields_are_rejected(self) -> None:
        payload = dict(self.payload)
        payload["raw_output"] = "provider response"
        with self.assertRaises(ReceiptValidationError):
            record_receipt(self.root, payload)
        self.assertFalse((self.root / ".coding-team").exists())

    def test_invalid_sha_and_map_digest_are_rejected(self) -> None:
        for field in ("source_sha", "map_digest"):
            with self.subTest(field=field):
                payload = dict(self.payload)
                payload[field] = "not-a-digest"
                with self.assertRaises(ReceiptValidationError):
                    record_receipt(self.root, payload)

    def test_atomic_write_cleans_pending_on_handled_failure(self) -> None:
        with patch("adapters.opencode.receipt.os.link", side_effect=OSError("blocked")):
            with self.assertRaises(ReceiptError):
                self.record()
        attempt_dir = self.expected_path().parent
        self.assertFalse(self.expected_path().exists())
        self.assertFalse((attempt_dir / "attempt-1.json.pending").exists())

    def test_racing_conflicting_final_is_not_overwritten(self) -> None:
        final_path = self.expected_path()
        competing_content = b'{"writer":"other"}\n'

        def publish_competing(_pending_path: Path, destination: Path) -> None:
            destination.write_bytes(competing_content)
            raise FileExistsError("final appeared during publication")

        with patch("adapters.opencode.receipt.os.link", side_effect=publish_competing):
            with self.assertRaises(ReceiptConflict):
                self.record()
        self.assertEqual(final_path.read_bytes(), competing_content)
        self.assertFalse(final_path.with_name(final_path.name + ".pending").exists())

    def test_racing_identical_final_is_a_noop(self) -> None:
        final_path = self.expected_path()

        def publish_competing(pending_path: Path, destination: Path) -> None:
            destination.write_bytes(pending_path.read_bytes())
            raise FileExistsError("identical final appeared during publication")

        with patch("adapters.opencode.receipt.os.link", side_effect=publish_competing):
            path = self.record()
        self.assertEqual(path, final_path)
        self.assertTrue(final_path.is_file())
        self.assertFalse(final_path.with_name(final_path.name + ".pending").exists())

    def test_duplicate_identical_record_is_a_noop(self) -> None:
        path = self.record()
        original = path.read_bytes()
        with patch("adapters.opencode.receipt.os.replace", side_effect=AssertionError("rewrite")):
            duplicate = self.record()
        self.assertEqual(duplicate, path)
        self.assertEqual(path.read_bytes(), original)

    def test_conflicting_duplicate_fails_closed(self) -> None:
        path = self.record()
        original = path.read_bytes()
        with self.assertRaises(ReceiptConflict):
            self.record(source_sha="c" * 40)
        self.assertEqual(path.read_bytes(), original)

    def test_stale_pending_is_observable_and_not_retried(self) -> None:
        attempt_dir = self.expected_path().parent
        attempt_dir.mkdir(parents=True)
        pending = attempt_dir / "attempt-1.json.pending"
        pending.write_text("orphan", encoding="utf-8")
        with self.assertRaises(PendingReceipt):
            self.record()
        self.assertTrue(pending.is_file())
        self.assertFalse(self.expected_path().exists())

    def test_stale_alternate_pending_name_is_also_observable(self) -> None:
        attempt_dir = self.expected_path().parent
        attempt_dir.mkdir(parents=True)
        pending = attempt_dir / "attempt-1.pending"
        pending.write_text("orphan", encoding="utf-8")
        with self.assertRaises(PendingReceipt):
            self.record()
        self.assertTrue(pending.is_file())

    def test_non_string_metric_statuses_return_validation_errors(self) -> None:
        for status in ([], {}, 1, None, True):
            with self.subTest(status=status):
                payload = dict(self.payload)
                usage = dict(self.payload["usage"])
                usage["status"] = status
                payload["usage"] = usage
                with self.assertRaises(ReceiptValidationError):
                    record_receipt(self.root, payload)

    def test_cli_record_operation(self) -> None:
        arguments = [
            sys.executable,
            os.fspath(Path(__file__).with_name("receipt.py")),
            "record",
            "--root",
            os.fspath(self.root),
            "--task-id",
            self.payload["task_id"],
            "--run-id",
            self.payload["run_id"],
            "--attempt-id",
            self.payload["attempt_id"],
            "--role-id",
            self.payload["role_id"],
            "--planned-model",
            self.payload["planned_model"],
            "--planned-tier",
            self.payload["planned_tier"],
            "--map-ref",
            self.payload["map_ref"],
            "--map-revision",
            self.payload["map_revision"],
            "--map-digest",
            self.payload["map_digest"],
            "--exit-state",
            self.payload["exit_state"],
            "--source-sha",
            self.payload["source_sha"],
            "--artifact-ref",
            self.payload["artifact_refs"][0],
            "--usage-status",
            self.payload["usage"]["status"],
            "--usage-source",
            self.payload["usage"]["source"],
            "--usage-basis",
            self.payload["usage"]["basis"],
            "--cost-status",
            self.payload["cost"]["status"],
            "--cost-source",
            self.payload["cost"]["source"],
            "--cost-basis",
            self.payload["cost"]["basis"],
            "--performance-status",
            self.payload["performance"]["status"],
            "--performance-source",
            self.payload["performance"]["source"],
            "--performance-basis",
            self.payload["performance"]["basis"],
        ]
        result = subprocess.run(arguments, check=False, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.expected_path().is_file())

    def test_raw_output_and_secret_like_values_are_rejected(self) -> None:
        for field in ("raw_prompt", "raw_output", "api_key"):
            with self.subTest(field=field):
                payload = dict(self.payload)
                payload[field] = "do not persist this"  # type: ignore[index]
                with self.assertRaises(ReceiptValidationError):
                    record_receipt(self.root, payload)
        with self.assertRaises(ReceiptValidationError):
            self.record(artifact_refs=["artifacts/secrets.json"])
        self.assertFalse((self.root / ".coding-team").exists())

    def test_spaced_raw_provenance_is_rejected(self) -> None:
        for value in ("raw output", "raw  prompt", "raw-output", "r a w . o u t p u t"):
            with self.subTest(value=value):
                payload = dict(self.payload)
                usage = dict(self.payload["usage"])
                usage["source"] = value
                payload["usage"] = usage
                with self.assertRaises(ReceiptValidationError):
                    record_receipt(self.root, payload)

        payload = dict(self.payload)
        payload["actual_model_source"] = "raw output"
        with self.assertRaises(ReceiptValidationError):
            record_receipt(self.root, payload)

    def test_spaced_secret_key_forms_are_rejected(self) -> None:
        values = (
            "api key : value",
            "access token = value",
            "pass word: value",
            "author-ization / value",
            "t o k e n : value",
        )
        for value in values:
            with self.subTest(value=value):
                payload = dict(self.payload)
                usage = dict(self.payload["usage"])
                usage["source"] = value
                payload["usage"] = usage
                with self.assertRaises(ReceiptValidationError):
                    record_receipt(self.root, payload)

    def test_no_parent_wysy_mutation(self) -> None:
        before = sorted(path.name for path in self.parent.iterdir())
        self.record()
        after = sorted(path.name for path in self.parent.iterdir())
        self.assertEqual(after, before)
        self.assertFalse((self.parent / ".coding-team").exists())
        self.assertTrue((self.root / ".coding-team" / "receipts").is_dir())


if __name__ == "__main__":
    unittest.main()
