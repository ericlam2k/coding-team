from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "adapters" / "codex" / "scripts" / "detect-model-pool.py"
SPEC = importlib.util.spec_from_file_location("model_pool_detector", SCRIPT)
assert SPEC and SPEC.loader
DETECTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DETECTOR)


class ModelPoolDiscoveryTests(unittest.TestCase):
    def test_discover_reads_bounded_sources_and_deduplicates_literal_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            (home / "models_cache.json").write_text(
                json.dumps({"models": [{"slug": "provider/alias"}, {"slug": "cache-only"}]}), encoding="utf-8"
            )
            (home / "catalog.json").write_text(
                json.dumps({"models": [{"slug": "provider/alias"}, {"slug": "catalog-only"}]}), encoding="utf-8"
            )
            (home / "agent.toml").write_text(
                '[agent]\nmodel = "agent-only"\navailable_models = ["provider/alias", { slug = "agent-object" }]\n', encoding="utf-8"
            )
            (home / "config.toml").write_text(
                '# model = "comment-is-not-a-model"\nmodel = "config-model"\nmodel_id = "provider/alias"\navailable_models = [\n  "list-model",\n  { id = "object-model" },\n]\nmodel_catalog_json = "catalog.json"\nagent_configs = ["agent.toml"]\n', encoding="utf-8"
            )

            result = DETECTOR.discover_pool(home)

        self.assertEqual([item["slug"] for item in result["models"]], [
            "provider/alias", "cache-only", "config-model", "list-model",
            "object-model", "catalog-only", "agent-only", "agent-object",
        ])
        aliases = next(item for item in result["models"] if item["slug"] == "provider/alias")
        self.assertEqual(aliases["sources"], ["cache:models_cache.json", "config:config.toml", "catalog:catalog.json", "agent-config:agent.toml"])
        self.assertEqual(result["warnings"], [])

    def test_malformed_and_credential_like_inputs_are_sanitized(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            (home / "models_cache.json").write_text("{not json sk-cache-secret}", encoding="utf-8")
            (home / "config.toml").write_text(
                'model = "sk-config-secret"\nmodel_catalog_json = "api_key.json"\nagent_config = "broken.toml"\n', encoding="utf-8"
            )
            (home / "broken.toml").write_text('model = "unterminated\n', encoding="utf-8")
            result = DETECTOR.discover_pool(home)

        rendered = json.dumps(result)
        self.assertNotIn("sk-cache-secret", rendered)
        self.assertNotIn("sk-config-secret", rendered)
        self.assertNotIn("api_key.json", rendered)
        self.assertNotIn("unterminated", rendered)
        self.assertTrue(result["warnings"])

    def test_symlink_target_is_validated_and_malformed_catalog_warns(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            (home / "models_cache.json").write_text(json.dumps({"models": []}), encoding="utf-8")
            (home / "auth.json").write_text(json.dumps({"models": [{"slug": "leaked-model"}]}), encoding="utf-8")
            (home / "catalog.json").symlink_to(home / "auth.json")
            (home / "malformed.json").write_text(json.dumps({"not_models": []}), encoding="utf-8")
            (home / "config.toml").write_text(
                'model_catalog_json = ["catalog.json", "malformed.json"]\n', encoding="utf-8"
            )

            result = DETECTOR.discover_pool(home)

        rendered = json.dumps(result)
        self.assertNotIn("leaked-model", rendered)
        self.assertNotIn("auth.json", rendered)
        self.assertTrue(any("unsafe or unavailable catalog" in warning for warning in result["warnings"]))
        self.assertTrue(any("catalog:malformed.json" in warning for warning in result["warnings"]))

    def test_default_and_details_cli_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            (home / "models_cache.json").write_text(json.dumps({"models": [{"slug": "cli-model"}]}), encoding="utf-8")
            env = {**os.environ, "CODEX_HOME": str(home)}
            default = subprocess.run([sys.executable, str(SCRIPT)], env=env, capture_output=True, text=True, check=False)
            details = subprocess.run([sys.executable, str(SCRIPT), "--details"], env=env, capture_output=True, text=True, check=False)

        self.assertEqual(default.returncode, 0)
        self.assertEqual(json.loads(default.stdout), ["cli-model"])
        self.assertEqual(json.loads(details.stdout)["models"][0]["slug"], "cli-model")


if __name__ == "__main__":
    unittest.main()
