"""Guard canonical Code Reviewer wiring across the host-neutral and Codex trees."""

from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ORCHESTRATION = ROOT / "core" / "orchestration.md"
CORE_README = ROOT / "core" / "README.md"
ROLE_DIR = ROOT / "core" / "roles"
CODE_REVIEW_ROLE = ROLE_DIR / "code-reviewer.md"
CODE_REVIEW_TEMPLATE = ROOT / "core" / "templates" / "code-review.md"
QA_POLICY = ROOT / "core" / "qa-operating-model.md"
PREPARE_DISPATCH = ROOT / "adapters" / "codex" / "scripts" / "prepare-dispatch.py"
INSTALLER = ROOT / "scripts" / "install-coding-team.sh"


def _section(markdown: str, heading: str) -> str:
    """Return one level-2 Markdown section, excluding the next section."""

    match = re.search(
        rf"^{re.escape(heading)}\s*$([\s\S]*?)(?=^## |\Z)",
        markdown,
        flags=re.MULTILINE,
    )
    if match is None:
        raise AssertionError(f"missing Markdown section: {heading}")
    return match.group(1)


def _load_prepare_dispatch():
    spec = importlib.util.spec_from_file_location("prepare_dispatch", PREPARE_DISPATCH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {PREPARE_DISPATCH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_table_roles() -> set[str]:
    section = _section(ORCHESTRATION.read_text(encoding="utf-8"), "## Canonical role IDs")
    return set(re.findall(r"^\| `([^`]+)` \|", section, flags=re.MULTILINE))


def _readme_role_index() -> set[str]:
    section = _section(CORE_README.read_text(encoding="utf-8"), "## Roles")
    return {
        role_id
        for _path, role_id in re.findall(
            r"^\| \[roles/([^/]+)\.md\]\([^)]*\) \| `([^`]+)`",
            section,
            flags=re.MULTILINE,
        )
    }


class CodeReviewerConsistencyTests(unittest.TestCase):
    def test_canonical_roles_match_cards_index_and_codex_allow_list(self) -> None:
        canonical = _canonical_table_roles()
        card_roles = {path.stem for path in ROLE_DIR.glob("*.md")}
        dispatch_roles = set(_load_prepare_dispatch().CANONICAL_ROLES)

        self.assertTrue(canonical, "canonical role table must not be empty")
        self.assertEqual(canonical, card_roles)
        self.assertEqual(canonical, _readme_role_index())
        self.assertEqual(canonical, dispatch_roles)

    def test_code_reviewer_role_template_and_indexes_exist(self) -> None:
        self.assertTrue(CODE_REVIEW_ROLE.is_file())
        self.assertTrue(CODE_REVIEW_TEMPLATE.is_file())

        readme = CORE_README.read_text(encoding="utf-8")
        self.assertIn(
            "[roles/code-reviewer.md](roles/code-reviewer.md)",
            readme,
        )
        self.assertIn(
            "[templates/code-review.md](templates/code-review.md)",
            readme,
        )

    def test_reviewer_to_te_route_requires_an_explicit_trigger(self) -> None:
        policy = QA_POLICY.read_text(encoding="utf-8")
        reviewer = CODE_REVIEW_ROLE.read_text(encoding="utf-8")
        routing = (ROOT / "core" / "model-routing.md").read_text(encoding="utf-8")
        policy_compact = " ".join(policy.split())
        reviewer_compact = " ".join(reviewer.split())
        routing_compact = " ".join(routing.split())

        self.assertIn("must not infer `qa_required`, `qa_mode`", policy_compact)
        self.assertIn("`ESCALATE_TO_TEST_ENGINEER`", policy_compact)
        self.assertIn("Never invent `qa_required`, `qa_mode`", reviewer_compact)
        self.assertIn("Code Reviewer; Test Engineer", routing_compact)
        self.assertIn("1 validate", routing_compact)

    def test_installer_fails_closed_when_reviewer_assets_are_missing(self) -> None:
        for missing in ("core/roles/code-reviewer.md", "core/templates/code-review.md"):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as temp_dir:
                checkout = Path(temp_dir) / "coding-team"
                (checkout / "scripts").mkdir(parents=True)
                shutil.copy2(INSTALLER, checkout / "scripts" / INSTALLER.name)

                for required in (
                    "adapters/codex/SKILL.md",
                    "skills/quality/qa-evidence-enforcement/SKILL.md",
                    "core/qa-operating-model.md",
                ):
                    required_path = checkout / required
                    required_path.parent.mkdir(parents=True, exist_ok=True)
                    required_path.write_text("fixture\n", encoding="utf-8")

                for reviewer_asset in (
                    "core/roles/code-reviewer.md",
                    "core/templates/code-review.md",
                ):
                    if reviewer_asset != missing:
                        asset_path = checkout / reviewer_asset
                        asset_path.parent.mkdir(parents=True, exist_ok=True)
                        asset_path.write_text("fixture\n", encoding="utf-8")

                codex_home = Path(temp_dir) / "codex-home"
                result = subprocess.run(
                    ["bash", str(checkout / "scripts" / INSTALLER.name), "--platform", "codex"],
                    cwd=checkout,
                    env={**os.environ, "CODEX_HOME": str(codex_home)},
                    capture_output=True,
                    text=True,
                    check=False,
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("missing Code Reviewer", result.stderr)
                self.assertFalse((codex_home / "skills" / "coding-team").exists())


if __name__ == "__main__":
    unittest.main()
