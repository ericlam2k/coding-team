#!/usr/bin/env python3
"""Map abstract coding-team tiers to closest available GPT models.

Writes markdown model-pool.map.md with planned → actual.
Never fails hard on missing models — picks best available and notes gaps.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


# Preferred candidates per abstract tier (first match wins among available).
TIER_PREFS: dict[str, list[dict[str, str]]] = {
    "0": [
        {"slug": "gpt-5.6-luna", "effort": "medium", "label": "luna"},
        {"slug": "gpt-5.4-mini", "effort": "medium", "label": "5.4-mini"},
        {"slug": "gpt-5.4", "effort": "low", "label": "5.4 low"},
        {"slug": "gpt-5.5", "effort": "low", "label": "5.5 low"},
        {"slug": "gpt-5.6-terra", "effort": "low", "label": "terra low"},
        {"slug": "gpt-5.6-sol", "effort": "low", "label": "sol low"},
    ],
    "1 build": [
        {"slug": "gpt-5.6-terra", "effort": "medium", "label": "terra"},
        {"slug": "gpt-5.4", "effort": "medium", "label": "5.4"},
        {"slug": "gpt-5.5", "effort": "medium", "label": "5.5"},
        {"slug": "gpt-5.6-sol", "effort": "medium", "label": "sol medium"},
        {"slug": "gpt-5.6-luna", "effort": "high", "label": "luna high"},
        {"slug": "gpt-5.4-mini", "effort": "high", "label": "5.4-mini high"},
    ],
    "1 validate": [
        {"slug": "gpt-5.6-terra", "effort": "high", "label": "terra high"},
        {"slug": "gpt-5.4", "effort": "high", "label": "5.4 high"},
        {"slug": "gpt-5.5", "effort": "high", "label": "5.5 high"},
        {"slug": "gpt-5.6-sol", "effort": "medium", "label": "sol medium"},
        {"slug": "gpt-5.6-terra", "effort": "medium", "label": "terra medium"},
    ],
    "2": [
        {"slug": "gpt-5.6-sol", "effort": "high", "label": "sol high"},
        {"slug": "gpt-5.6-terra", "effort": "xhigh", "label": "terra xhigh"},
        {"slug": "gpt-5.5", "effort": "xhigh", "label": "5.5 xhigh"},
        {"slug": "gpt-5.6-sol", "effort": "medium", "label": "sol medium"},
        {"slug": "gpt-5.4", "effort": "xhigh", "label": "5.4 xhigh"},
    ],
    "3": [
        {"slug": "gpt-5.6-sol", "effort": "xhigh", "label": "sol xhigh"},
        {"slug": "gpt-5.6-sol", "effort": "max", "label": "sol max"},
        {"slug": "gpt-5.6-sol", "effort": "high", "label": "sol high"},
        {"slug": "gpt-5.6-terra", "effort": "max", "label": "terra max"},
        {"slug": "gpt-5.5", "effort": "xhigh", "label": "5.5 xhigh"},
    ],
}

PLANNED: dict[str, str] = {
    "0": "gpt-5.6-luna (or gpt-5.4-mini)",
    "1 build": "gpt-5.6-terra (or gpt-5.4)",
    "1 validate": "gpt-5.6-terra + effort high",
    "2": "gpt-5.6-sol + effort high",
    "3": "gpt-5.6-sol + effort xhigh/max",
}

TIER_ORDER = ["0", "1 build", "1 validate", "2", "3"]


def load_slugs(args: argparse.Namespace) -> list[str]:
    if args.stdin:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else []
    elif args.slugs_json:
        data = json.loads(Path(args.slugs_json).read_text(encoding="utf-8"))
    else:
        # Discover via sibling detect script when possible
        detect = Path(__file__).resolve().parent / "detect-model-pool.py"
        if detect.is_file():
            import subprocess

            proc = subprocess.run(
                [sys.executable, str(detect)],
                check=False,
                capture_output=True,
                text=True,
            )
            data = json.loads(proc.stdout) if proc.stdout.strip() else []
        else:
            data = []
    if not isinstance(data, list):
        raise SystemExit("expected a JSON list of slugs")
    return [s for s in data if isinstance(s, str)]


def pick(available: set[str], prefs: list[dict[str, str]]) -> tuple[str, str, str, list[str]]:
    notes: list[str] = []
    for pref in prefs:
        if pref["slug"] in available:
            return pref["slug"], pref["effort"], pref["label"], notes
    # No preferred slug — use any gpt-* present
    if available:
        fallback = sorted(available)[0]
        notes.append(f"no preferred slug; fell back to {fallback}")
        return fallback, "medium", "fallback", notes
    notes.append("no gpt-* models detected; placeholder only")
    return "gpt-5.6-sol", "medium", "placeholder", notes


def render(available: list[str], rows: list[dict[str, object]]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# model-pool.map.md (Codex)",
        "",
        f"Generated: `{now}`",
        "",
        "Abstract tiers from `core/model-routing.md` → closest available GPT slug.",
        "Tiers are non-binding; record planned → actual in briefs. Never block start on missing identity.",
        "",
        "## Available pool",
        "",
    ]
    if available:
        for s in available:
            lines.append(f"- `{s}`")
    else:
        lines.append("- _(none detected — placeholders below)_")
    lines += [
        "",
        "## Map",
        "",
        "| Tier | Planned | Actual slug | Effort | Notes |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        notes = "; ".join(r["notes"]) if r["notes"] else "—"
        lines.append(
            f"| **{r['tier']}** | {r['planned']} | `{r['actual']}` | `{r['effort']}` | {notes} |"
        )
    lines += [
        "",
        "## Usage",
        "",
        "Lead assigns a tier, then uses **Actual slug** + **Effort** when spawning Codex subagents.",
        "Inspect: `./bin/ct map propose --platform codex`; approve/write: `./bin/ct map approve --platform codex`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        action="append",
        dest="outs",
        help="Output path for model-pool.map.md (repeatable)",
    )
    parser.add_argument("--stdin", action="store_true", help="Read slug JSON list from stdin")
    parser.add_argument("--slugs-json", help="Path to JSON list of slugs")
    args = parser.parse_args()

    available_list = load_slugs(args)
    available = set(available_list)
    rows: list[dict[str, object]] = []
    for tier in TIER_ORDER:
        slug, effort, _label, notes = pick(available, TIER_PREFS[tier])
        preferred_slugs = {p["slug"] for p in TIER_PREFS[tier][:2]}
        if slug not in preferred_slugs and available:
            notes = notes + [f"preferred {', '.join(sorted(preferred_slugs))} unavailable"]
        rows.append(
            {
                "tier": tier,
                "planned": PLANNED[tier],
                "actual": slug,
                "effort": effort,
                "notes": notes,
            }
        )

    text = render(available_list, rows)
    outs = args.outs or [str(Path.cwd() / "model-pool.map.md")]
    for out in outs:
        path = Path(out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path}", file=sys.stderr)
    # Also print to stdout for piping/inspection
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
