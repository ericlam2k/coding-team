#!/usr/bin/env python3
"""Detect model IDs from explicitly configured Codex model sources."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tomllib
from pathlib import Path
from typing import Any, Iterator

MAX_MODEL_ID_LENGTH = 200
CREDENTIAL_VALUE_RE = re.compile(r"^(?:sk[-_]|key[-_]|token[-_]|secret[-_]|bearer\s+|password[-_])", re.I)
SENSITIVE_PATH_RE = re.compile(r"(?:^|[._-])(secret|secrets|auth|credential|credentials|token|password|passwd|api[-_]?key)(?:$|[._-])", re.I)


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
    return Path(raw).expanduser() if raw else Path.home() / ".codex"


def _read_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def _read_toml(path: Path) -> Any | None:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError):
        return None


def slugs_from_models_cache(path: Path) -> list[str]:
    data = _read_json(path) if path.is_file() else None
    if not isinstance(data, dict) or not isinstance(data.get("models"), list):
        return []
    return [
        slug
        for model in data["models"]
        if isinstance(model, dict)
        for slug in [normalise_model_id(model.get("slug"))]
        if slug is not None
    ]


def _model_values(value: object) -> Iterator[str]:
    if isinstance(value, str):
        slug = normalise_model_id(value)
        if slug is not None:
            yield slug
    elif isinstance(value, dict):
        for key in ("id", "slug"):
            slug = normalise_model_id(value.get(key))
            if slug is not None:
                yield slug


def _walk_config(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"model", "model_id"}:
                yield from _model_values(child)
            elif key == "available_models" and isinstance(child, list):
                for item in child:
                    yield from _model_values(item)
            else:
                yield from _walk_config(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_config(child)


def slugs_from_config_toml(path: Path) -> list[str]:
    data = _read_toml(path) if path.is_file() else None
    return list(_walk_config(data)) if isinstance(data, dict) else []


def _relative_source(home: Path, path: Path, label: str) -> str:
    try:
        rendered = str(path.resolve().relative_to(home.resolve()))
    except ValueError:
        rendered = path.name
    if not rendered or any(SENSITIVE_PATH_RE.search(part) for part in Path(rendered).parts):
        rendered = "referenced-file"
    return f"{label}:{rendered}"


def _warning(home: Path, path: Path, label: str) -> str:
    return f"{_relative_source(home, path, label)} could not be read or parsed"


def _safe_reference(home: Path, raw: object, suffixes: tuple[str, ...]) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = home / candidate
    if candidate.suffix.lower() not in suffixes or any(_sensitive_path_component(part) for part in candidate.parts):
        return None
    try:
        resolved = candidate.resolve(strict=True)
    except OSError:
        return None
    if resolved.suffix.lower() not in suffixes or any(_sensitive_path_component(part) for part in resolved.parts):
        return None
    return resolved if resolved.is_file() else None


def _sensitive_path_component(component: str) -> bool:
    lowered = component.lower()
    return lowered == ".env" or lowered.startswith(".env.") or bool(SENSITIVE_PATH_RE.search(component))


def _reference_values(config: dict[str, Any], key: str) -> Iterator[object]:
    for current_key, value in config.items():
        if current_key == key:
            yield from (value if isinstance(value, list) else [value])
        if isinstance(value, dict):
            yield from _reference_values(value, key)


def _add_models(result: dict[str, list[Any]], slugs: Iterator[str], source: str) -> None:
    by_slug = {model["slug"]: model for model in result["models"]}
    for slug in slugs:
        model = by_slug.get(slug)
        if model is None:
            model = {"slug": slug, "sources": []}
            result["models"].append(model)
            by_slug[slug] = model
        if source not in model["sources"]:
            model["sources"].append(source)


def discover_pool(home: Path) -> dict[str, list[Any]]:
    """Discover literal model IDs from bounded, explicitly referenced files."""
    result: dict[str, list[Any]] = {"models": [], "warnings": []}

    cache = home / "models_cache.json"
    if cache.is_file():
        data = _read_json(cache)
        if not isinstance(data, dict) or not isinstance(data.get("models"), list):
            result["warnings"].append(_warning(home, cache, "cache"))
        else:
            _add_models(result, iter(slugs_from_models_cache(cache)), _relative_source(home, cache, "cache"))
    else:
        result["warnings"].append(_warning(home, cache, "cache"))

    config = home / "config.toml"
    config_data = _read_toml(config) if config.is_file() else None
    if not config.is_file():
        result["warnings"].append(_warning(home, config, "config"))
        return result
    if not isinstance(config_data, dict):
        result["warnings"].append(_warning(home, config, "config"))
        return result

    _add_models(result, _walk_config(config_data), _relative_source(home, config, "config"))
    for raw in _reference_values(config_data, "model_catalog_json"):
        catalog = _safe_reference(home, raw, (".json",))
        if catalog is None:
            if isinstance(raw, str) and raw.strip():
                result["warnings"].append("config referenced an unsafe or unavailable catalog")
            continue
        catalog_data = _read_json(catalog)
        if not isinstance(catalog_data, dict) or not isinstance(catalog_data.get("models"), list):
            result["warnings"].append(_warning(home, catalog, "catalog"))
            continue
        slugs = (
            slug
            for model in catalog_data["models"]
            if isinstance(model, dict)
            for slug in [normalise_model_id(model.get("slug"))]
            if slug is not None
        )
        _add_models(result, slugs, _relative_source(home, catalog, "catalog"))

    for key in ("agent_config", "agent_configs", "agent_config_files"):
        for raw in _reference_values(config_data, key):
            agent = _safe_reference(home, raw, (".json", ".toml"))
            if agent is None:
                if isinstance(raw, str) and raw.strip():
                    result["warnings"].append("config referenced an unsafe or unavailable agent config")
                continue
            agent_data = _read_json(agent) if agent.suffix.lower() == ".json" else _read_toml(agent)
            if not isinstance(agent_data, dict):
                result["warnings"].append(_warning(home, agent, "agent-config"))
                continue
            _add_models(result, _walk_config(agent_data), _relative_source(home, agent, "agent-config"))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--details", action="store_true")
    args = parser.parse_args()
    details = discover_pool(codex_home())
    output: object = details if args.details else [model["slug"] for model in details["models"]]
    json.dump(output, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
