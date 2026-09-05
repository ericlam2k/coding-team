from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROPOSER = load_module(ROOT / "scripts" / "propose-model-map.py", "model_proposer")
DETECTOR = load_module(
    ROOT / "adapters" / "codex" / "scripts" / "detect-model-pool.py",
    "model_detector",
)


class ModelMapProposalTests(unittest.TestCase):
    def test_detector_keeps_non_gpt_ids_and_filters_credential_like_values(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            (home / "models_cache.json").write_text(
                json.dumps(
                    {
                        "models": [
                            {"slug": "ecobuild"},
                            {"slug": "frontier-think"},
                            {"slug": "provider/model"},
                            {"slug": "sk-secret"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (home / "config.toml").write_text(
                'model = "vendor/eco"\nmodel_id = "frontier-think"\n',
                encoding="utf-8",
            )

            detected = DETECTOR.slugs_from_models_cache(home / "models_cache.json")
            configured = DETECTOR.slugs_from_config_toml(home / "config.toml")

        self.assertEqual(detected, ["ecobuild", "frontier-think", "provider/model"])
        self.assertEqual(configured, ["vendor/eco", "frontier-think"])

    def test_semantic_markers_are_not_capability_evidence(self):
        proposed = PROPOSER.propose_slugs(
            ["search-lite", "ecobuild", "frontier-think"]
        )

        self.assertTrue(all(slug is None for slug, _notes in proposed.values()))

    def test_premium_model_is_not_consumed_as_build_fallback(self):
        proposed = PROPOSER.propose_slugs(["luna", "frontier-think"])

        self.assertTrue(all(slug is None for slug, _notes in proposed.values()))

    def test_single_model_pool_stays_in_pool(self):
        proposed = PROPOSER.propose_slugs(["provider/ecobuild"])

        self.assertEqual(
            {slug for slug, _notes in proposed.values()},
            {None},
        )

    def test_propose_only_prints_without_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            codex_home = temp_path / "codex"
            codex_home.mkdir()
            (codex_home / "models_cache.json").write_text(
                json.dumps(
                    {"models": [{"slug": "ecobuild"}, {"slug": "frontier-think"}]}
                ),
                encoding="utf-8",
            )
            output = temp_path / "candidate.md"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "propose-model-map.py"),
                    "--platform",
                    "codex",
                    "--codex-home",
                    str(codex_home),
                    "--propose-only",
                    "--out",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(output.exists())
        self.assertIn("ecobuild", result.stdout)
        self.assertIn("frontier-think", result.stdout)
        self.assertIn(PROPOSER.SELECTION_RULE, result.stdout)

    def test_legacy_writer_cannot_bypass_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "model-pool.map.md"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "adapters" / "codex" / "scripts" / "apply-pool-map.py"),
                    "--stdin",
                    "--out",
                    str(output),
                ],
                input=json.dumps(["cheap-search", "ecobuild", "frontier-think"]),
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())


class ExplicitSelectionTests(unittest.TestCase):
    def setUp(self):
        self.pool = ["alpha-premium", "alpha-balanced", "beta-premium", "beta-balanced", "cheap-builder"]
        self.inventory = {"models": [{"slug": slug, "sources": ["fixture"]} for slug in self.pool], "warnings": []}
        self.selection = {
            "tiers": {tier: {"primary": "alpha-premium", "fallback": "beta-premium"} for tier in PROPOSER.TIER_ORDER},
            "roles": {
                "product-manager": {"primary": "beta-premium", "fallback": "beta-balanced"},
                "system-architect": {"primary": "alpha-premium", "fallback": "alpha-balanced"},
                "advisor": {"primary": "beta-premium", "fallback": "beta-balanced"},
                "contradictor": {"primary": "alpha-premium", "fallback": "alpha-balanced"},
                "test-engineer:implement": {"primary": "cheap-builder", "fallback": "beta-balanced"},
            },
            "families": {"alpha-premium": "alpha", "alpha-balanced": "alpha", "beta-premium": "beta", "beta-balanced": "beta", "cheap-builder": "gamma"},
        }

    def build(self):
        return PROPOSER.build_proposal("codex", self.inventory, self.selection)

    def test_complete_roles_and_te_phases(self):
        proposal = self.build()
        self.assertEqual(proposal["problems"], [])
        role_rows = {row["key"]: row for row in proposal["roles"]}
        self.assertEqual({key.split(":")[0] for key in role_rows}, set(PROPOSER.ROLE_TIERS))
        self.assertEqual(role_rows["test-engineer:design"]["tier"], "2")
        self.assertEqual(role_rows["test-engineer:implement"]["suggested"], "cheap-builder")
        self.assertIn("no model", proposal["te_execution"])
        self.assertEqual(proposal["benchmark_status"], "UNVERIFIED")

    def test_pair_fallback_overlap_is_rejected(self):
        self.selection["roles"]["product-manager"]["fallback"] = "alpha-balanced"
        self.assertTrue(any("families overlap" in problem for problem in self.build()["problems"]))

    def test_family_not_guessed_from_alias(self):
        self.selection["families"].pop("beta-balanced")
        self.assertTrue(any("metadata missing" in problem for problem in self.build()["problems"]))

    def test_unknown_or_identical_fallback_rejected(self):
        for fallback in ("not-in-pool", "alpha-premium"):
            self.selection["tiers"]["0"]["fallback"] = fallback
            with self.assertRaises(ValueError):
                self.build()

    def test_unmapped_is_not_an_approved_guess(self):
        proposal = PROPOSER.build_proposal("codex", self.inventory)
        self.assertTrue(proposal["problems"])
        self.assertTrue(all(row["suggested"] == "UNMAPPED" for row in proposal["tiers"]))

    def test_digest_binds_roles_fallback_and_pool(self):
        before = PROPOSER.proposal_digest(self.build())
        self.selection["roles"]["test-engineer:implement"]["fallback"] = "alpha-balanced"
        self.assertNotEqual(before, PROPOSER.proposal_digest(self.build()))
        second = PROPOSER.proposal_digest(self.build())
        self.inventory["models"].append({"slug": "new-model", "sources": ["fixture"]})
        self.assertNotEqual(second, PROPOSER.proposal_digest(self.build()))

    def test_bad_selection_shapes_rejected(self):
        for selection in ([], {"tiers": []}, {"roles": {"imaginary-role": {}}}, {"notes": ["bad\nline"]}):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                PROPOSER.build_proposal("codex", self.inventory, selection)

    def test_cli_exact_approval_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            (home / "models_cache.json").write_text(json.dumps({"models": [{"slug": slug} for slug in self.pool]}))
            (home / "config.toml").write_text("")
            selection = home / "selection.json"
            selection.write_text(json.dumps(self.selection))
            output = home / "approved.md"
            command = [sys.executable, "-B", str(ROOT / "scripts/propose-model-map.py"), "--platform", "codex", "--codex-home", str(home), "--selection", str(selection), "--out", str(output)]
            preview = subprocess.run(command + ["--propose-only", "--json"], capture_output=True, text=True)
            self.assertEqual(preview.returncode, 0, preview.stderr)
            digest = json.loads(preview.stdout)["digest"]
            self.assertFalse(output.exists())
            for options in (["--yes"], ["--yes", "--accept-unverified", "--approve-digest", "wrong"]):
                result = subprocess.run(command + options, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(output.exists())
            approved = command + ["--yes", "--accept-unverified", "--approve-digest", digest]
            result = subprocess.run(approved, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("APPROVED WITH EXPLICIT", output.read_text())
            original = output.read_bytes()
            result = subprocess.run(approved, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(original, output.read_bytes())


if __name__ == "__main__":
    unittest.main()
