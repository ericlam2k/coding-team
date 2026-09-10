#!/usr/bin/env python3
"""Focused installation-trust contract tests."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "install-trust.py"
SPEC = importlib.util.spec_from_file_location("install_trust", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class InstallTrustTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "bundle"
        for relative in MODULE.COMMON_AUTHORITY:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"authority:{relative}\n", encoding="utf-8")
        for relative in (
            "adapters/codex/SKILL.md",
            "adapters/codex/runtime.md",
            "adapters/codex/framework-reload.md",
            "adapters/codex/scripts/prepare-dispatch.py",
            "adapters/codex/scripts/check-install.py",
            "core/roles/lead.md",
            "core/roles/backend-engineer.md",
        ):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"authority:{relative}\n", encoding="utf-8")
        self.receipt = Path(self.temporary.name) / "state" / "receipt.json"
        self.adapter_dst = Path(self.temporary.name) / "active" / "coding-team"
        self.qa_dst = Path(self.temporary.name) / "active" / "qa"
        self.adapter_dst.parent.mkdir(parents=True)
        self.adapter_dst.symlink_to(self.root / "adapters/codex")
        self.qa_dst.symlink_to(self.root / "skills/quality/qa-evidence-enforcement")

    def issue(self) -> dict[str, object]:
        return MODULE.issue(self.root, "codex", self.receipt, self.adapter_dst, self.qa_dst)

    def check(self) -> dict[str, object]:
        return MODULE.check(self.root, "codex", self.receipt, self.adapter_dst, self.qa_dst)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_matching_receipt_reuses_install_validation(self) -> None:
        issued = self.issue()
        result = self.check()
        self.assertEqual(issued["status"], "ACTIVE")
        self.assertEqual(result["status"], "ACTIVE")
        self.assertEqual(result["framework_validation"], "REUSED_INSTALL_RECEIPT")
        self.assertEqual(result["product_validation"], "REQUIRED")
        self.assertFalse(result["framework_wide_scan"])
        self.assertLessEqual(result["authority_files_checked"], 64)

    def test_authority_drift_requires_install_revalidation(self) -> None:
        self.issue()
        (self.root / "core/orchestration.md").write_text("drift\n", encoding="utf-8")
        result = self.check()
        self.assertEqual(result["status"], "INACTIVE")
        self.assertIn("authority_drift", result["reasons"])
        self.assertEqual(result["product_validation"], "REQUIRED")

    def test_missing_root_platform_and_compatibility_fail_closed(self) -> None:
        self.issue()
        wrong_root = Path(self.temporary.name) / "other"
        wrong_root.mkdir()
        self.assertEqual(MODULE.check(wrong_root, "codex", self.receipt, self.adapter_dst, self.qa_dst)["status"], "INACTIVE")
        self.assertEqual(MODULE.check(self.root, "cursor", self.receipt, self.adapter_dst, self.qa_dst)["status"], "INACTIVE")
        value = json.loads(self.receipt.read_text(encoding="utf-8"))
        value["contract_version"] = 999
        self.receipt.write_text(json.dumps(value), encoding="utf-8")
        result = self.check()
        self.assertIn("compatibility_changed", result["reasons"])

    def test_consumer_project_is_not_an_input_or_scan_target(self) -> None:
        self.issue()
        consumer = Path(self.temporary.name) / "wysy-consumer"
        consumer.mkdir()
        for index in range(852):
            (consumer / f"product-{index}.txt").write_text("product\n", encoding="utf-8")
        before = {path.name for path in consumer.iterdir()}
        result = self.check()
        after = {path.name for path in consumer.iterdir()}
        self.assertEqual(result["status"], "ACTIVE")
        self.assertEqual(before, after)
        self.assertNotIn(str(consumer), json.dumps(result))

    def test_installer_issues_once_and_check_does_not_issue(self) -> None:
        installer = (ROOT / "scripts/install-coding-team.sh").read_text(encoding="utf-8")
        self.assertIn('"$TRUST_HELPER" issue', installer)
        self.assertIn('"$TRUST_HELPER" check', installer)
        check_block = installer.split('if [[ "$CHECK_ONLY" -eq 1 ]]', 1)[1].split("fi", 1)[0]
        self.assertIn('"$TRUST_HELPER" check', check_block)
        self.assertNotIn('"$TRUST_HELPER" issue', check_block)
        self.assertNotIn("find ", installer)
        self.assertNotIn('export CODING_TEAM_ROOT=', installer)

    def test_all_install_entries_avoid_source_root_pinning(self) -> None:
        friendly = (ROOT / "install.sh").read_text(encoding="utf-8")
        cli = (ROOT / "bin/ct").read_text(encoding="utf-8")
        self.assertNotIn('export CODING_TEAM_ROOT=', friendly)
        self.assertNotIn('Set CODING_TEAM_ROOT=', cli)
        self.assertNotIn('`CODING_TEAM_ROOT=${ROOT}`', cli)
        self.assertIn('"$ROOT/scripts/install-coding-team.sh" --platform "$platform"', cli)
        self.assertIn("use the installed root returned by its receipt check", cli)

    def test_issue_cli_prints_summary_not_manifest(self) -> None:
        completed = subprocess.run(
            [
                "python3", str(SCRIPT), "issue", "--root", str(self.root),
                "--platform", "codex", "--receipt", str(self.receipt),
                "--adapter-dst", str(self.adapter_dst), "--qa-dst", str(self.qa_dst),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "ACTIVE")
        self.assertLessEqual(result["authority_files_recorded"], 64)
        self.assertNotIn("authority_manifest", result)

    def test_malformed_receipts_and_wrong_link_fail_closed(self) -> None:
        self.issue()
        for raw in ("[]", "null", "42", '"text"'):
            self.receipt.write_text(raw, encoding="utf-8")
            self.assertEqual(self.check()["status"], "INACTIVE")
        self.receipt.write_bytes(b"\xff\xfe")
        self.assertEqual(self.check()["status"], "INACTIVE")
        self.issue()
        self.adapter_dst.unlink()
        self.adapter_dst.symlink_to(self.root / "core")
        result = self.check()
        self.assertEqual(result["status"], "INACTIVE")
        self.assertIn("activation_invalid", result["reasons"])

    def test_issue_refuses_wrong_activation_target(self) -> None:
        self.adapter_dst.unlink()
        self.adapter_dst.symlink_to(self.root / "core")
        with self.assertRaises(MODULE.TrustError):
            self.issue()

    def test_installed_wrapper_ignores_stale_project_root(self) -> None:
        codex_home = Path(self.temporary.name) / "codex-home"
        adapter = codex_home / "skills" / "coding-team"
        qa = codex_home / "skills" / "qa-evidence-enforcement"
        adapter.parent.mkdir(parents=True)
        adapter.symlink_to(ROOT / "adapters/codex")
        qa.symlink_to(ROOT / "skills/quality/qa-evidence-enforcement")
        receipt = codex_home / "coding-team" / "install-receipt-codex.json"
        MODULE.issue(ROOT, "codex", receipt, adapter, qa)
        dirty_lab = Path(self.temporary.name) / "wysy" / "coding-team"
        dirty_lab.mkdir(parents=True)
        for index in range(852):
            (dirty_lab / f"wip-{index}.txt").write_text("dirty source wip\n", encoding="utf-8")
        env = {
            **os.environ,
            "CODEX_HOME": str(codex_home),
            "CODING_TEAM_ROOT": str(dirty_lab),
        }
        completed = subprocess.run(
            ["python3", str(ROOT / "adapters/codex/scripts/check-install.py")],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "ACTIVE")
        self.assertEqual(result["installed_root"], str(ROOT.resolve()))
        self.assertNotIn(str(dirty_lab), completed.stdout)


if __name__ == "__main__":
    unittest.main()
