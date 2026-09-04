#!/usr/bin/env python3
"""Check the installed Coding Team bundle without consulting a project checkout."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path


INSTALLED_ROOT = Path(__file__).resolve().parents[3]
TRUST_HELPER = INSTALLED_ROOT / "scripts" / "install-trust.py"


def _load_helper():
    spec = importlib.util.spec_from_file_location("coding_team_install_trust", TRUST_HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load installation trust helper: {TRUST_HELPER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    helper = _load_helper()
    result = helper.check(
        INSTALLED_ROOT,
        "codex",
        codex_home / "coding-team" / "install-receipt-codex.json",
        codex_home / "skills" / "coding-team",
        codex_home / "skills" / "qa-evidence-enforcement",
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("status") == "ACTIVE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
