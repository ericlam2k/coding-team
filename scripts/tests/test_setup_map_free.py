#!/usr/bin/env python3
"""Focused Sprint 1 checks for map-free setup and explicit map actions.

The tests copy only the installer/adapter boundary into a temporary checkout.
They therefore exercise real shell/Python entry points without touching the
working tree's model-map outputs or the user's Codex home.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


class SetupMapFreeTests(unittest.TestCase):
    def fixture(self) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        temp = tempfile.TemporaryDirectory(prefix="coding-team-s1-")
        root = Path(temp.name) / "coding-team"
        root.mkdir()
        paths = (
            "bin/ct",
            "install.sh",
            "scripts/install-coding-team.sh",
            "scripts/propose-model-map.py",
            "scripts/validate-qa-evidence.rb",
            "adapters/codex",
            "adapters/cursor",
            "adapters/cline",
            "skills/quality",
            "core/qa-operating-model.md",
            "addons/toggles.json",
            "examples/model-pool.map.codex.example.md",
        )
        for rel in paths:
            source = REPO / rel
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target, symlinks=True)
            else:
                shutil.copy2(source, target)
        # The real project keeps an approved map for current use.  These
        # fixtures exercise clean setup semantics, so remove pre-existing map
        # outputs before asserting that init/decline do not create them.
        for rel in (
            "adapters/codex/model-pool.map.md",
            "adapters/cursor/model-pool.map.md",
            "adapters/cline/model-pool.map.md",
            "examples/model-pool.map.md",
        ):
            (root / rel).unlink(missing_ok=True)
        home = Path(temp.name) / "home"
        home.mkdir()
        return temp, root, home

    @staticmethod
    def run_cmd(root: Path, home: Path, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update({"HOME": str(home), "CODEX_HOME": str(home / ".codex")})
        return subprocess.run(
            list(args),
            cwd=root,
            env=env,
            input=stdin,
            stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )

    @staticmethod
    def map_files(root: Path, home: Path) -> set[Path]:
        candidates = {
            root / "adapters/codex/model-pool.map.md",
            root / "adapters/cursor/model-pool.map.md",
            root / "adapters/cline/model-pool.map.md",
            root / "examples/model-pool.map.md",
            home / ".codex/skills/coding-team/model-pool.map.md",
        }
        return {path for path in candidates if path.exists() or path.is_symlink()}

    @staticmethod
    def regular_files(root: Path) -> set[Path]:
        return {
            path.relative_to(root)
            for path in root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }

    def test_init_is_map_free_even_with_compatibility_yes(self) -> None:
        temp, root, home = self.fixture()
        self.addCleanup(temp.cleanup)

        result = self.run_cmd(root, home, str(root / "bin/ct"), "init", "--platform", "codex", "--yes")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Model map: NOT_STARTED", result.stdout)
        self.assertIn("does not approve", result.stdout)
        self.assertEqual(self.map_files(root, home), set())
        self.assertTrue((home / ".codex/skills/coding-team").is_symlink())
        self.assertTrue((home / ".codex/skills/qa-evidence-enforcement").is_symlink())

    def test_single_install_and_legacy_aliases_are_identical_and_map_free(self) -> None:
        outputs: dict[str, str] = {}
        for label, args in (
            ("default", ()),
            ("hybrid", ("--profile", "hybrid")),
            ("full", ("--profile", "full")),
        ):
            with self.subTest(alias=label):
                temp, root, home = self.fixture()
                try:
                    result = self.run_cmd(
                        root, home, "bash", str(root / "scripts/install-coding-team.sh"),
                        *args, "--platform", "codex",
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(self.map_files(root, home), set())
                    self.assertTrue((home / ".codex/skills/coding-team").is_symlink())
                    self.assertTrue((home / ".codex/skills/qa-evidence-enforcement").is_symlink())
                    # Temporary fixture paths differ, so compare normalized
                    # output to prove aliases have identical behavior.
                    outputs[label] = result.stdout.replace(str(home), "<HOME>").replace(str(root), "<ROOT>")
                    if label != "default":
                        self.assertIn("deprecation", result.stderr.lower())
                finally:
                    temp.cleanup()
        for alias in ("hybrid", "full"):
            self.assertEqual(outputs[alias], outputs["default"])

    def test_single_install_is_idempotent(self) -> None:
        temp, root, home = self.fixture()
        self.addCleanup(temp.cleanup)
        command = ("bash", str(root / "scripts/install-coding-team.sh"), "--platform", "codex")
        first = self.run_cmd(root, home, *command)
        second = self.run_cmd(root, home, *command)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("already linked", second.stdout)
        self.assertEqual(self.map_files(root, home), set())

        temp, root, home = self.fixture()
        self.addCleanup(temp.cleanup)
        result = self.run_cmd(root, home, "bash", str(root / "install.sh"), "--platform", "codex", "--global")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.map_files(root, home), set())

    def test_proposal_and_decline_do_not_write_but_explicit_approval_writes_declared_outputs(self) -> None:
        temp, root, home = self.fixture()
        self.addCleanup(temp.cleanup)
        init = self.run_cmd(root, home, str(root / "bin/ct"), "init", "--platform", "codex")
        self.assertEqual(init.returncode, 0, init.stderr)
        before = self.regular_files(root)

        proposal = self.run_cmd(root, home, str(root / "bin/ct"), "map", "propose", "--platform", "codex")
        self.assertEqual(proposal.returncode, 0, proposal.stderr)
        self.assertIn("proposal (not written)", proposal.stdout)
        self.assertEqual(self.map_files(root, home), set())
        self.assertEqual(self.regular_files(root), before)

        decline = self.run_cmd(root, home, str(root / "bin/ct"), "map", "decline", "--platform", "codex")
        self.assertEqual(decline.returncode, 0, decline.stderr)
        self.assertEqual(self.map_files(root, home), set())

        approval = self.run_cmd(
            root,
            home,
            str(root / "bin/ct"),
            "map",
            "approve",
            "--platform",
            "codex",
            "--yes",
        )
        self.assertEqual(approval.returncode, 0, approval.stderr)
        self.assertEqual(
            self.map_files(root, home),
            {
                root / "adapters/codex/model-pool.map.md",
                root / "examples/model-pool.map.md",
                home / ".codex/skills/coding-team/model-pool.map.md",
            },
        )
        changed = self.regular_files(root) - before
        self.assertEqual(changed, {Path("adapters/codex/model-pool.map.md"), Path("examples/model-pool.map.md")})
        self.assertIn("Status: **approved**", (root / "adapters/codex/model-pool.map.md").read_text())

    def test_noninteractive_refresh_has_no_empty_array_failure(self) -> None:
        temp, root, home = self.fixture()
        self.addCleanup(temp.cleanup)
        init = self.run_cmd(root, home, str(root / "bin/ct"), "init", "--platform", "codex")
        self.assertEqual(init.returncode, 0, init.stderr)

        refresh = self.run_cmd(root, home, str(root / "bin/ct"), "refresh", "--platform", "codex")

        self.assertEqual(refresh.returncode, 2)
        combined = f"{refresh.stdout}\n{refresh.stderr}"
        self.assertNotIn("unbound variable", combined.lower())
        self.assertIn("pass --yes", combined)
        self.assertEqual(self.map_files(root, home), set())


if __name__ == "__main__":
    unittest.main()
