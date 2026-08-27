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

    def test_semantic_markers_map_to_the_intended_tiers(self):
        proposed = PROPOSER.propose_slugs(
            ["search-lite", "ecobuild", "frontier-think"]
        )

        self.assertEqual(proposed["0"][0], "search-lite")
        self.assertEqual(proposed["1 build"][0], "ecobuild")
        self.assertEqual(proposed["1 validate"][0], "frontier-think")
        self.assertEqual(proposed["2"][0], "frontier-think")
        self.assertEqual(proposed["3"][0], "frontier-think")

    def test_premium_model_is_not_consumed_as_build_fallback(self):
        proposed = PROPOSER.propose_slugs(["luna", "frontier-think"])

        self.assertEqual(proposed["0"][0], "luna")
        self.assertEqual(proposed["1 build"][0], "luna")
        self.assertEqual(proposed["2"][0], "frontier-think")

    def test_single_model_pool_stays_in_pool(self):
        proposed = PROPOSER.propose_slugs(["provider/ecobuild"])

        self.assertEqual(
            {slug for slug, _notes in proposed.values()},
            {"provider/ecobuild"},
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

    def test_legacy_writer_uses_the_shared_non_gpt_proposal(self):
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

            self.assertEqual(result.returncode, 0, result.stderr)
            text = output.read_text(encoding="utf-8")

        self.assertIn("cheap-search", text)
        self.assertIn("ecobuild", text)
        self.assertIn("frontier-think", text)
        self.assertIn(PROPOSER.SELECTION_RULE, text)


if __name__ == "__main__":
    unittest.main()
