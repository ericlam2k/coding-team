#!/usr/bin/env python3
"""Propose abstract-tier → host model map; write only after approval.

Platform-independent: tiers from core/model-routing.md; host slugs from a detector.
Default: print suggestion and ask Y/n (or --yes to skip prompt).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SELECTION_RULE = "Premium decide. Eco build. Cheap search/docs. Human gate for irreversible risk."

PLANNED = {
    "0": "cheap search/docs",
    "1 build": "eco build",
    "1 validate": "careful validate",
    "2": "premium decide",
    "3": "max-risk judgment",
}

TIER_ORDER = ["0", "1 build", "1 validate", "2", "3"]
TIER_EFFORT = {
    "0": "medium",
    "1 build": "medium",
    "1 validate": "high",
    "2": "high",
    "3": "max",
}


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


# Markers are hints only. They do not prove model quality or capability.
CHEAP_MARKERS = (
    "cheap", "fast", "flash", "mini", "luna", "lite", "air", "nano",
    "small", "haiku", "swift", "search", "docs", "utility",
)
ECO_BUILD_MARKERS = (
    "eco", "build", "builder", "code", "coder", "codex", "dev", "developer",
    "ecobuild", "ecobuilder",
)
REASONING_MARKERS = ("think", "reason", "reasoning", "deep", "pro", "plus", "sonnet")
PREMIUM_MARKERS = ("max", "ultra", "opus", "premium", "flagship", "frontier", "large")

_NUM_RE = re.compile(r"(\d+(?:\.\d+)?)")
_TOKEN_RE = re.compile(r"[^a-z0-9]+")
CREDENTIAL_VALUE_RE = re.compile(
    r"^(?:sk[-_]|key[-_]|token[-_]|secret[-_]|bearer\s+|password[-_])",
    re.IGNORECASE,
)


def looks_like_slug(value: object) -> bool:
    """Accept a printable model ID without assuming a provider prefix."""
    if not isinstance(value, str):
        return False
    slug = value.strip()
    if not (2 <= len(slug) <= 80):
        return False
    if slug.lower() in {"true", "false", "null", "none"}:
        return False
    if CREDENTIAL_VALUE_RE.search(slug):
        return False
    return all(32 <= ord(char) < 127 for char in slug)


def _tokens(slug: str) -> set[str]:
    return {token for token in _TOKEN_RE.split(slug.lower()) if token}


def model_family(slug: str) -> str:
    name = slug.split("/", 1)[-1].strip().lower()
    return name.split("-", 1)[0] if "-" in name else name


def _matches_any(slug: str, markers: tuple[str, ...]) -> bool:
    return any(marker in _tokens(slug) for marker in markers)


def _version_proxy(slug: str) -> float:
    numbers = [float(number) for number in _NUM_RE.findall(slug)]
    return max(numbers) if numbers else -1.0


def _pool_key(slug: str) -> tuple:
    return (_version_proxy(slug), len(slug), slug)


def _pick(pool: list[str], predicate, prefer_family: str | None = None) -> str | None:
    candidates = [slug for slug in pool if predicate(slug)]
    if not candidates:
        return None
    if prefer_family is not None:
        other_family = [slug for slug in candidates if model_family(slug) != prefer_family]
        if other_family:
            candidates = other_family
    return candidates[0]


def propose_slugs(pool: list[str]) -> dict[str, tuple[str | None, list[str]]]:
    """Map a detected pool to abstract tiers without fixed provider names."""
    pool = sorted(set(pool), key=_pool_key)
    result: dict[str, tuple[str | None, list[str]]] = {}
    if not pool:
        for tier in TIER_ORDER:
            result[tier] = (None, ["empty pool — no runtime slug detected; edit after approve"])
        return result

    t0 = _pick(pool, lambda slug: _matches_any(slug, CHEAP_MARKERS)) or pool[0]
    result["0"] = (t0, ["heuristic: cheap/utility markers or lowest-cost-looking slug"])

    t1b = _pick(pool, lambda slug: _matches_any(slug, ECO_BUILD_MARKERS) and slug != t0)
    t1b_notes = ["heuristic: eco/build/code markers"]
    if t1b is None:
        t1b = _pick(pool, lambda slug: _matches_any(slug, ECO_BUILD_MARKERS))
    if t1b is None:
        t1b = _pick(
            pool,
            lambda slug: not _matches_any(slug, PREMIUM_MARKERS) and slug != t0,
        )
        t1b_notes = ["heuristic: non-premium fallback (no eco/code marker)"]
    if t1b is None:
        t1b = _pick(pool, lambda slug: not _matches_any(slug, PREMIUM_MARKERS)) or t0
        t1b_notes = ["heuristic: fallback slug (no eco/code marker)"]
    result["1 build"] = (t1b, t1b_notes)

    build_family = model_family(t1b)
    t1v = _pick(
        pool,
        lambda slug: _matches_any(slug, REASONING_MARKERS) and slug != t1b,
        prefer_family=build_family,
    )
    if t1v is not None:
        notes = ["heuristic: strong reasoning slug"]
        notes.append(
            "different family than 1 build"
            if model_family(t1v) != build_family
            else "same family as 1 build (pool has no other capable family)"
        )
    else:
        t1v = next((slug for slug in pool if slug != t1b), t1b)
        notes = ["heuristic: fallback slug (no reasoning markers detected)"]
        if model_family(t1v) == build_family:
            notes.append("same family as 1 build (single-family pool)")
    result["1 validate"] = (t1v, notes)

    t2 = _pick(
        pool,
        lambda slug: _matches_any(slug, PREMIUM_MARKERS) and slug != t1b,
        prefer_family=build_family,
    )
    if t2 is not None:
        notes = ["heuristic: premium markers"]
    else:
        candidates = [slug for slug in pool if slug not in (t1b, t1v)] or [
            slug for slug in pool if slug != t1b
        ] or pool
        other_family = [slug for slug in candidates if model_family(slug) != build_family]
        t2 = (other_family or candidates)[-1]
        notes = ["heuristic: highest numeric version / longest slug as premium proxy"]
    notes.append(
        "different family than 1 build"
        if model_family(t2) != build_family
        else "same family as 1 build (pool has no other premium family)"
    )
    result["2"] = (t2, notes)

    premium = [slug for slug in pool if _matches_any(slug, PREMIUM_MARKERS)]
    candidates = [slug for slug in pool if slug != t2] or pool
    t3 = premium[-1] if premium else candidates[-1]
    notes = ["heuristic: most premium/flagship slug available"]
    if t3 == t2:
        notes.append("same slug as tier 2 (pool has only one premium candidate)")
    result["3"] = (t3, notes)
    return result


def build_rows(available: list[str]) -> list[dict[str, object]]:
    pool = sorted(set(available))
    proposed = propose_slugs(pool)
    rows = []
    for tier in TIER_ORDER:
        slug, notes = proposed.get(tier, (None, ["no heuristic match — edit after approve"]))
        if slug is None:
            slug = "none"
        rows.append(
            {
                "tier": tier,
                "planned": PLANNED[tier],
                "suggested": slug,
                "effort": TIER_EFFORT[tier],
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
        f"Selection rule: **{SELECTION_RULE}**",
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
        "Inspect: `./bin/ct map propose`; approve/write: `./bin/ct map approve`",
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
