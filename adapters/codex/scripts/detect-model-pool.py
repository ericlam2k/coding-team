#!/usr/bin/env python3
"""Detect available model slugs from Codex home.

Reads ~/.codex/models_cache.json and config.toml (or $CODEX_HOME).
Prints a JSON array of valid model IDs to stdout.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


MAX_MODEL_ID_LENGTH = 200
CREDENTIAL_VALUE_RE = re.compile(
    r"^(?:sk[-_]|key[-_]|token[-_]|secret[-_]|bearer\s+|password[-_])",
    re.IGNORECASE,
)


def normalise_model_id(value: object) -> str | None:
    """Return a safe model ID without assuming a provider namespace."""

    if not isinstance(value, str):
        return None
    model_id = value.strip()
    if not model_id or len(model_id) > MAX_MODEL_ID_LENGTH:
        return None
    if any(ord(char) < 32 or ord(char) == 127 for char in model_id):
        return None
    if CREDENTIAL_VALUE_RE.search(model_id):
        return None
    return model_id


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
    if not isinstance(data, dict):
        return []
    models = data.get("models") or []
    out: list[str] = []
    for m in models:
        if not isinstance(m, dict):
            continue
        slug = normalise_model_id(m.get("slug"))
        if slug is not None:
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
    # model = "..."
    for m in re.finditer(r'(?m)^\s*model\s*=\s*"([^"]+)"', text):
        slug = normalise_model_id(m.group(1))
        if slug is not None:
            found.append(slug)
    # model_provider / profiles may list model ids similarly
    for m in re.finditer(r'(?m)^\s*model_id\s*=\s*"([^"]+)"', text):
        slug = normalise_model_id(m.group(1))
        if slug is not None:
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
