#!/usr/bin/env python3
"""Detect available GPT model slugs from Codex home.

Reads ~/.codex/models_cache.json and config.toml (or $CODEX_HOME).
Prints a JSON array of gpt-* slugs to stdout.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def codex_home() -> Path:
    raw = os.environ.get("CODEX_HOME", "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".codex"


def slugs_from_models_cache(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    models = data.get("models") or []
    out: list[str] = []
    for m in models:
        if not isinstance(m, dict):
            continue
        slug = m.get("slug")
        if isinstance(slug, str) and slug.startswith("gpt-"):
            out.append(slug)
    return out


def slugs_from_config_toml(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    found: list[str] = []
    # model = "gpt-..."
    for m in re.finditer(r'(?m)^\s*model\s*=\s*"([^"]+)"', text):
        slug = m.group(1)
        if slug.startswith("gpt-"):
            found.append(slug)
    # model_provider / profiles may list model ids similarly
    for m in re.finditer(r'(?m)^\s*model_id\s*=\s*"([^"]+)"', text):
        slug = m.group(1)
        if slug.startswith("gpt-"):
            found.append(slug)
    return found


def main() -> int:
    home = codex_home()
    slugs: list[str] = []
    seen: set[str] = set()
    for src in (
        slugs_from_models_cache(home / "models_cache.json"),
        slugs_from_config_toml(home / "config.toml"),
    ):
        for s in src:
            if s not in seen:
                seen.add(s)
                slugs.append(s)
    json.dump(slugs, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
