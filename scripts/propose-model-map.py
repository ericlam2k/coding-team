#!/usr/bin/env python3
"""Propose abstract-tier → host model map; write only after approval.

Platform-independent: tiers from core/model-routing.md; host slugs from a detector.
Default: print suggestion and ask Y/n (or --yes to skip prompt).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Generic capability prefs — host detectors may return any slug set.
# Codex GPT prefs first; Cursor/Cline pools match by substring heuristics later.
TIER_PREFS: dict[str, list[dict[str, str]]] = {
    "0": [
        {"slug": "gpt-5.6-luna", "effort": "medium"},
        {"slug": "gpt-5.4-mini", "effort": "medium"},
        {"slug": "composer-2.5-fast", "effort": "low"},
        {"slug": "gpt-5.4", "effort": "low"},
        {"slug": "gpt-5.6-terra", "effort": "low"},
    ],
    "1 build": [
        {"slug": "gpt-5.6-terra", "effort": "medium"},
        {"slug": "claude-sonnet-5-thinking-high", "effort": "high"},
        {"slug": "gpt-5.4", "effort": "medium"},
        {"slug": "gpt-5.5", "effort": "medium"},
        {"slug": "cursor-grok-4.5-high-fast", "effort": "medium"},
    ],
    "1 validate": [
        {"slug": "gpt-5.6-terra", "effort": "high"},
        {"slug": "gpt-5.6-terra-medium", "effort": "medium"},
        {"slug": "gpt-5.4", "effort": "high"},
        {"slug": "gpt-5.5", "effort": "high"},
    ],
    "2": [
        {"slug": "gpt-5.6-sol", "effort": "high"},
        {"slug": "gpt-5.6-sol-medium", "effort": "medium"},
        {"slug": "claude-opus-4-8-thinking-high", "effort": "high"},
        {"slug": "gpt-5.5", "effort": "xhigh"},
    ],
    "3": [
        {"slug": "gpt-5.6-sol", "effort": "xhigh"},
        {"slug": "claude-fable-5-thinking-high", "effort": "high"},
        {"slug": "gpt-5.6-sol", "effort": "max"},
        {"slug": "gpt-5.6-sol", "effort": "high"},
    ],
}

PLANNED = {
    "0": "cheap utility (Luna / mini / composer-fast)",
    "1 build": "eco implement (Terra / Sonnet)",
    "1 validate": "careful validate (Terra high)",
    "2": "premium plan/debate (Sol / Opus)",
    "3": "max-risk judgment (Sol xhigh / Fable)",
}

TIER_ORDER = ["0", "1 build", "1 validate", "2", "3"]


def detect_codex(codex_home: Path) -> list[str]:
    script = ROOT / "adapters" / "codex" / "scripts" / "detect-model-pool.py"
    env = {"CODEX_HOME": str(codex_home)}
    import os

    full_env = {**os.environ, **env}
    proc = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        capture_output=True,
        text=True,
        env=full_env,
    )
    if not proc.stdout.strip():
        return []
    data = json.loads(proc.stdout)
    return [s for s in data if isinstance(s, str)]


def detect_cursor() -> list[str]:
    # Best-effort: known Cursor pool labels (non-binding suggestions).
    return [
        "composer-2.5-fast",
        "claude-sonnet-5-thinking-high",
        "cursor-grok-4.5-high-fast",
        "gpt-5.6-terra-medium",
        "gpt-5.6-sol-medium",
        "claude-opus-4-8-thinking-high",
        "claude-fable-5-thinking-high",
    ]


def detect_cline() -> list[str]:
    # Placeholder pool — user approves/edits at install.
    return [
        "gpt-5.6-luna",
        "gpt-5.6-terra",
        "gpt-5.6-sol",
        "claude-sonnet-4",
        "claude-opus-4",
    ]


def pick(available: set[str], prefs: list[dict[str, str]]) -> tuple[str, str, list[str]]:
    notes: list[str] = []
    for pref in prefs:
        if pref["slug"] in available:
            return pref["slug"], pref["effort"], notes
    # substring soft match
    for pref in prefs:
        for a in available:
            if pref["slug"].split("-")[0] in a or pref["slug"] in a:
                notes.append(f"soft-matched {pref['slug']} → {a}")
                return a, pref["effort"], notes
    if available:
        fb = sorted(available)[0]
        notes.append(f"no preferred slug; fell back to {fb}")
        return fb, "medium", notes
    notes.append("empty pool — placeholder; edit after approve")
    return prefs[0]["slug"], prefs[0]["effort"], notes


def build_rows(available: list[str]) -> list[dict[str, object]]:
    aset = set(available)
    rows = []
    for tier in TIER_ORDER:
        slug, effort, notes = pick(aset, TIER_PREFS[tier])
        rows.append(
            {
                "tier": tier,
                "planned": PLANNED[tier],
                "suggested": slug,
                "effort": effort,
                "notes": notes,
            }
        )
    return rows


def render(platform: str, available: list[str], rows: list[dict[str, object]], approved: bool) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    status = "approved" if approved else "proposal (not written)"
    lines = [
        f"# model-pool.map.md ({platform})",
        "",
        f"Generated: `{now}`",
        f"Status: **{status}**",
        "",
        "Abstract tiers from `core/model-routing.md` → host pool slugs.",
        "Tiers are non-binding. Record planned → actual in briefs. Never block start on missing identity.",
        "",
        "## Available pool",
        "",
    ]
    if available:
        for s in available:
            lines.append(f"- `{s}`")
    else:
        lines.append("- _(none detected — placeholders / edit before use)_")
    lines += [
        "",
        "## Map",
        "",
        "| Tier | Planned intent | Mapped slug | Effort | Notes |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        notes = "; ".join(r["notes"]) if r["notes"] else "—"
        lines.append(
            f"| **{r['tier']}** | {r['planned']} | `{r['suggested']}` | `{r['effort']}` | {notes} |"
        )
    lines += [
        "",
        "## Usage",
        "",
        "Lead assigns a tier, then uses **Mapped slug** + **Effort** when spawning specialists.",
        "Refresh with approval: `./bin/ct refresh`",
        "",
    ]
    return "\n".join(lines)


def print_suggestion(platform: str, available: list[str], rows: list[dict[str, object]]) -> None:
    print()
    print("=" * 60)
    print(f"MODEL MAP SUGGESTION ({platform})")
    print("=" * 60)
    print()
    print("Detected pool:")
    if available:
        for s in available:
            print(f"  - {s}")
    else:
        print("  (empty — using placeholders)")
    print()
    print(f"{'Tier':<12} {'Suggested slug':<36} {'Effort':<8} Notes")
    print("-" * 72)
    for r in rows:
        notes = "; ".join(r["notes"]) if r["notes"] else ""
        print(f"{r['tier']:<12} {r['suggested']:<36} {r['effort']:<8} {notes}")
    print()
    print("These are suggestions only. Core stays platform-independent.")
    print("=" * 60)


def approve_prompt() -> bool:
    if not sys.stdin.isatty():
        print("Non-interactive stdin — pass --yes to approve, or run in a terminal.", file=sys.stderr)
        return False
    try:
        ans = input("Approve and write this model map? [Y/n]: ").strip().lower()
    except EOFError:
        return False
    return ans in ("", "y", "yes")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=["codex", "cursor", "cline"], required=True)
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    parser.add_argument(
        "--out",
        action="append",
        dest="outs",
        help="Output path(s) to write after approval",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Approve without prompt (CI / non-interactive)",
    )
    parser.add_argument(
        "--propose-only",
        action="store_true",
        help="Print suggestion only; never write",
    )
    args = parser.parse_args()

    if args.platform == "codex":
        available = detect_codex(Path(args.codex_home).expanduser())
    elif args.platform == "cursor":
        available = detect_cursor()
    else:
        available = detect_cline()

    rows = build_rows(available)
    print_suggestion(args.platform, available, rows)

    if args.propose_only:
        sys.stdout.write(render(args.platform, available, rows, approved=False))
        return 0

    approved = bool(args.yes) or approve_prompt()
    if not approved:
        print("Not approved — model map NOT written.", file=sys.stderr)
        return 2

    text = render(args.platform, available, rows, approved=True)
    outs = args.outs or []
    if not outs:
        print("Approved but no --out paths given; printing map only.", file=sys.stderr)
        sys.stdout.write(text)
        return 0

    for out in outs:
        path = Path(out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
