#!/usr/bin/env python3
"""Focused quality-role and package-index checks."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "adapters/codex/scripts/prepare-dispatch.py"


def _load():
    spec = importlib.util.spec_from_file_location("prepare_dispatch", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class QualityConsistencyTests(unittest.TestCase):
    def test_role_cards_match_formatter_roles(self) -> None:
        roles = {path.stem for path in (ROOT / "core/roles").glob("*.md")}
        self.assertEqual(roles, set(_load().CANONICAL_ROLES))
        self.assertNotIn("monitor-agent", roles)

    def test_quality_roles_are_independent_triggers(self) -> None:
        policy = (ROOT / "core/qa-operating-model.md").read_text(encoding="utf-8")
        self.assertIn("independent inspection", policy)
        self.assertIn("not mandatory", policy)
        self.assertIn("affected by the changed bytes", policy)

    def test_reviewer_assets_remain_installable(self) -> None:
        self.assertTrue((ROOT / "core/roles/code-reviewer.md").is_file())
        self.assertTrue((ROOT / "core/templates/code-review.md").is_file())
        installer = (ROOT / "scripts/install-coding-team.sh").read_text(encoding="utf-8")
        self.assertIn('"$TRUST_HELPER" issue', installer)


if __name__ == "__main__":
    unittest.main()
