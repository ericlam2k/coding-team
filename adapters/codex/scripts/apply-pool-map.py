#!/usr/bin/env python3
"""Write a Codex model map using the shared host-neutral proposer.

This is a compatibility entry point. The installer uses
``scripts/propose-model-map.py`` for detect → propose → approve; this command
keeps the older direct-write interface without maintaining a second
map algorithm.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PROPOSER_PATH = ROOT / "scripts" / "propose-model-map.py"


def load_proposer():
    spec = importlib.util.spec_from_file_location("coding_team_model_proposer", PROPOSER_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {PROPOSER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_slugs(args: argparse.Namespace, proposer) -> list[str]:
    if args.stdin:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else []
    elif args.slugs_json:
        data = json.loads(Path(args.slugs_json).read_text(encoding="utf-8"))
    else:
        return proposer.detect_codex(Path(args.codex_home).expanduser())
    if not isinstance(data, list):
        raise SystemExit("expected a JSON list of model IDs")
    return [value.strip() for value in data if isinstance(value, str) and proposer.looks_like_slug(value)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        action="append",
        dest="outs",
        help="Output path for model-pool.map.md (repeatable)",
    )
    parser.add_argument("--stdin", action="store_true", help="Read a JSON list of model IDs from stdin")
    parser.add_argument("--slugs-json", help="Path to a JSON list of model IDs")
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    args = parser.parse_args()

    proposer = load_proposer()
    available = load_slugs(args, proposer)
    rows = proposer.build_rows(available)
    text = proposer.render("codex", available, rows, approved=True)
    outs = args.outs or [str(Path.cwd() / "model-pool.map.md")]
    for out in outs:
        path = Path(out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path}", file=sys.stderr)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
