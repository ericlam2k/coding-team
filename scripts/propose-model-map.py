#!/usr/bin/env python3
"""Inspect all model options and propose explicit role/phase routes before approval."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELECTION_RULE = "Premium decide. Eco build. Cheap search/docs. Human gate for irreversible risk."
PLANNED = {"0": "cheap search/docs", "1 build": "eco build", "1 validate": "careful validate", "2": "premium decide", "3": "max-risk judgment"}
TIER_ORDER = list(PLANNED)
TIER_EFFORT = {"0": "medium", "1 build": "medium", "1 validate": "high", "2": "high", "3": "xhigh"}
ROLE_TIERS = {
    "lead": "2", "product-manager": "2", "system-architect": "2",
    "advisor": "2", "contradictor": "2", "domain-advisor": "2",
    "frontend-ux-lead": "2", "investigator": "0", "backend-engineer": "1 build",
    "frontend-builder": "1 build", "code-reviewer": "1 validate",
    "test-engineer": "1 validate", "gatekeeper": "3", "docs-steward": "0",
}
RISK_VARIANTS = {
    "system-architect": ("standard", "high"),
    "gatekeeper:backend": ("standard", "high"),
}
CROSS_FAMILY_PAIRS = (("product-manager", "system-architect"), ("advisor", "contradictor"))
EFFORTS = {"low", "medium", "high", "xhigh", "max", "ultra"}
CREDENTIAL_VALUE_RE = re.compile(r"^(?:sk[-_]|key[-_]|token[-_]|secret[-_]|bearer\s+|password[-_])", re.I)


def looks_like_slug(value: object) -> bool:
    return (
        isinstance(value, str) and 2 <= len(value.strip()) <= 200
        and not CREDENTIAL_VALUE_RE.search(value.strip())
        and value.strip().lower() not in {"true", "false", "null", "none"}
        and all(32 <= ord(char) < 127 and char not in "|`<>" for char in value)
    )


def detect_codex_details(codex_home: Path) -> dict:
    script = ROOT / "adapters/codex/scripts/detect-model-pool.py"
    result = subprocess.run(
        [sys.executable, "-B", str(script), "--details"], capture_output=True,
        text=True, check=False, env={**os.environ, "CODEX_HOME": str(codex_home)},
    )
    if result.returncode:
        raise ValueError("Codex discovery failed; no map can be approved")
    try:
        details = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise ValueError("Codex discovery returned invalid JSON") from None
    if not isinstance(details, dict) or not isinstance(details.get("models"), list):
        raise ValueError("Codex discovery returned an invalid inventory")
    details["models"] = [entry for entry in details["models"] if isinstance(entry, dict) and looks_like_slug(entry.get("slug"))]
    return details


def detect_codex(codex_home: Path) -> list[str]:
    return [entry["slug"] for entry in detect_codex_details(codex_home)["models"]]


def detect_cursor() -> list[str]:
    return []


def detect_cline() -> list[str]:
    return []


def propose_slugs(pool: list[str]) -> dict:
    return {tier: (None, ["UNVERIFIED: names do not establish capability or cost; select explicitly"])
            for tier in TIER_ORDER}


def route_row(key: str, tier: str, entry: dict, available: list[str]) -> dict:
    if not isinstance(entry, dict) or set(entry) - {"primary", "fallback", "effort", "fallback_effort"}:
        raise ValueError(f"Invalid route fields for {key}")
    primary, fallback = entry.get("primary"), entry.get("fallback")
    for value in (primary, fallback):
        if value is not None and (not looks_like_slug(value) or value not in available):
            raise ValueError(f"{key}: selected model absent from detected pool")
    if primary is not None and primary == fallback:
        raise ValueError(f"{key}: fallback must differ from primary")
    effort = entry.get("effort", TIER_EFFORT[tier])
    fallback_effort = entry.get("fallback_effort", effort)
    if not isinstance(effort, str) or not isinstance(fallback_effort, str) or effort not in EFFORTS or fallback_effort not in EFFORTS:
        raise ValueError(f"{key}: invalid effort setting")
    return {
        "key": key, "tier": tier, "planned": PLANNED[tier],
        "suggested": primary or "UNMAPPED", "fallback": fallback or "UNMAPPED",
        "effort": effort, "fallback_effort": fallback_effort,
        "status": "UNVERIFIED" if primary and fallback else "UNMAPPED",
        "notes": ["Explicit provisional choice; benchmark, effective cost, route and effort support unverified"],
    }


def _route_entry(
    roles: dict, keys: tuple[str, ...], fallback: dict, risk: str | None = None
) -> dict:
    """Resolve a flat or risk-nested route without inventing a model choice."""
    for key in keys:
        candidate = roles.get(key)
        if not isinstance(candidate, dict):
            continue
        if risk is not None and isinstance(candidate.get(risk), dict):
            return candidate[risk]
        if "primary" in candidate or "fallback" in candidate:
            return candidate
    return fallback


def build_rows(available: list[str], selection: dict | None = None) -> list[dict]:
    selection = selection or {}
    return [route_row(tier, tier, selection.get(tier, {}), available) for tier in TIER_ORDER]


def build_proposal(platform: str, inventory: dict, selection: dict | None = None) -> dict:
    if selection is None:
        selection = {}
    if not isinstance(selection, dict) or set(selection) - {"tiers", "roles", "families", "notes"}:
        raise ValueError("Selection must contain only tiers, roles, families and notes")
    tiers, roles, families = (selection.get(name, {}) for name in ("tiers", "roles", "families"))
    if not all(isinstance(value, dict) for value in (tiers, roles, families)):
        raise ValueError("tiers, roles and families must be objects")
    phase_keys = {"test-engineer:design", "test-engineer:implement"}
    allowed_role_keys = (
        (set(ROLE_TIERS) - {"test-engineer"})
        | phase_keys
        | {"system-architect:standard", "system-architect:high"}
        | {"gatekeeper:frontend", "gatekeeper:backend"}
        | {"gatekeeper:backend:standard", "gatekeeper:backend:high"}
    )
    if set(tiers) - set(TIER_ORDER) or set(roles) - allowed_role_keys:
        raise ValueError("Unknown tier, role or phase in selection")
    available = sorted({entry["slug"] for entry in inventory["models"]})
    if any(not looks_like_slug(slug) or not isinstance(family, str) or not re.fullmatch(r"[a-z][a-z0-9_-]*", family)
           for slug, family in families.items()):
        raise ValueError("Families require explicit slugs and lowercase canonical family labels")
    notes = selection.get("notes", [])
    if not isinstance(notes, list) or any(not isinstance(note, str) or len(note) > 2000 or any(ord(char) < 32 for char in note) for note in notes):
        raise ValueError("Notes must be bounded single-line strings")
    rows = build_rows(available, tiers)
    role_rows = []
    for role, tier in ROLE_TIERS.items():
        if role == "test-engineer":
            phases = (("test-engineer:design", "2"), ("test-engineer:implement", "1 build"))
            for key, phase_tier in phases:
                role_rows.append(route_row(key, phase_tier, roles.get(key, tiers.get(phase_tier, {})), available))
        elif role == "system-architect":
            for risk in RISK_VARIANTS[role]:
                key = f"{role}:{risk}"
                entry = _route_entry(
                    roles, (key, role), tiers.get(tier, {}), risk=risk
                )
                role_rows.append(route_row(key, tier, entry, available))
        elif role == "gatekeeper":
            frontend = _route_entry(
                roles, ("gatekeeper:frontend", "gatekeeper"), tiers.get(tier, {})
            )
            role_rows.append(route_row("gatekeeper:frontend", tier, frontend, available))
            for risk in RISK_VARIANTS["gatekeeper:backend"]:
                key = f"gatekeeper:backend:{risk}"
                entry = _route_entry(
                    roles,
                    (key, "gatekeeper:backend", "gatekeeper"),
                    tiers.get(tier, {}),
                    risk=risk,
                )
                role_rows.append(route_row(key, tier, entry, available))
        else:
            role_rows.append(route_row(role, tier, roles.get(role, tiers.get(tier, {})), available))
    problems = []
    by_role = {row["key"]: row for row in role_rows}
    for left, right in CROSS_FAMILY_PAIRS:
        family_sets = []
        for role in (left, right):
            role_matches = [
                row for key, row in by_role.items()
                if key == role or key.startswith(f"{role}:")
            ]
            chosen = [
                row[field] for row in role_matches for field in ("suggested", "fallback")
            ]
            if any(slug not in families for slug in chosen):
                problems.append(f"{role}: primary/fallback family metadata missing")
            family_sets.append({families[slug] for slug in chosen if slug in families})
        if family_sets[0] & family_sets[1]:
            problems.append(f"{left}/{right}: primary or fallback families overlap")
    if any(row["status"] == "UNMAPPED" for row in rows + role_rows):
        problems.append("Every model-assigned tier/role/phase needs a distinct primary and fallback")
    return {
        "platform": platform, "inventory": inventory, "tiers": rows, "roles": role_rows,
        "families": families, "notes": notes, "problems": problems,
        "benchmark_status": "UNVERIFIED", "runtime_status": "NOT_PROBED",
        "te_execution": "Run the frozen tests with the local test runner; no model is required for deterministic execution. Ambiguous failures return to Lead.",
        "fallback_policy": "Alternatives only: no automatic retry or model change after a hard stop. Revalidate actual family separation on any changed route.",
    }


def proposal_digest(proposal: dict) -> str:
    return hashlib.sha256(json.dumps(proposal, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ").replace("`", "'")


def render_proposal(proposal: dict, approved: bool = False) -> str:
    lines = [
        f"# Model-map proposal ({proposal['platform']})", "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"Status: {'APPROVED WITH EXPLICIT UNVERIFIED-EVIDENCE EXCEPTION' if approved else 'PROPOSAL ONLY - NOT INSTALLED'}",
        f"Digest: `{proposal_digest(proposal)}`", "", SELECTION_RULE,
        "", "Benchmark/cost evidence: UNVERIFIED. Discovery is not runtime availability.",
        "", "## All detected options", "", "| Exact slug | Sources |", "|---|---|",
    ]
    for entry in proposal["inventory"]["models"]:
        lines.append(f"| `{markdown_cell(entry['slug'])}` | {markdown_cell('; '.join(entry.get('sources', [])))} |")
    for title, key in (("Tier choices", "tiers"), ("Role and phase choices", "roles")):
        lines += ["", f"## {title}", "", "| Tier / role / phase | Primary | Fallback | Effort primary / fallback | Evidence |", "|---|---|---|---|---|"]
        for row in proposal[key]:
            lines.append(f"| {row['key']} | `{markdown_cell(row['suggested'])}` | `{markdown_cell(row['fallback'])}` | {row['effort']} / {row['fallback_effort']} | {row['status']} |")
    lines += ["", "## Test execution and fallback", "", proposal["te_execution"], "", proposal["fallback_policy"]]
    lines += ["", "Family rule: PM/SA and Advisor/Contradictor must have disjoint family sets, including fallback choices."]
    lines += ["", "## Selection notes", ""] + [f"- {markdown_cell(note)}" for note in proposal["notes"]]
    lines += ["", "## Approval options", "", "1. Revise the explicit selection and rerun.",
              "2. Hold for public benchmark, cost, privacy and route verification.",
              "3. Explicitly accept the unverified-evidence exception and approve this exact digest."]
    issues = proposal["problems"] + proposal["inventory"].get("warnings", [])
    if issues:
        lines += ["", "## Unresolved checks", ""] + [f"- {markdown_cell(issue)}" for issue in issues]
    return "\n".join(lines) + "\n"


def render(platform: str, available: list[str], rows: list[dict], approved: bool) -> str:
    if approved:
        raise ValueError("Approval requires explicit selection and matching proposal digest")
    proposal = build_proposal(platform, {"models": [{"slug": slug, "sources": ["supplied list"]} for slug in available], "warnings": []})
    return render_proposal(proposal)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=["codex", "cursor", "cline"], required=True)
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    parser.add_argument("--selection", help="Explicit provisional tier/role/family choices in JSON")
    parser.add_argument("--out", action="append", dest="outs", help="Approved map destination; never written in propose-only mode")
    parser.add_argument("--yes", "-y", action="store_true", help="Explicit write approval; also requires matching digest and evidence exception")
    parser.add_argument("--approve-digest", help="Exact digest printed by reviewed proposal")
    parser.add_argument("--accept-unverified", action="store_true", help="Explicitly accept missing benchmark/cost/route evidence")
    parser.add_argument("--propose-only", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print structured proposal instead of Markdown")
    args = parser.parse_args()
    try:
        if args.platform == "codex":
            inventory = detect_codex_details(Path(args.codex_home).expanduser())
        else:
            inventory = {"models": [], "warnings": ["No live discovery adapter configured for this platform; no fabricated pool is used"]}
        try:
            selection = json.loads(Path(args.selection).read_text(encoding="utf-8")) if args.selection else None
        except (OSError, json.JSONDecodeError):
            raise ValueError("Cannot read valid selection JSON") from None
        proposal = build_proposal(args.platform, inventory, selection)
        digest = proposal_digest(proposal)
        if args.propose_only or not args.yes:
            print(json.dumps({"digest": digest, "proposal": proposal}, indent=2) if args.json else render_proposal(proposal), end="\n" if args.json else "")
            return 0
        if proposal["problems"] or inventory.get("warnings"):
            raise ValueError("Approval blocked by incomplete routes, family conflicts or discovery warnings")
        if not args.accept_unverified or args.approve_digest != digest:
            raise ValueError("Approval requires --accept-unverified and exact current --approve-digest; no map written")
        text = render_proposal(proposal, approved=True)
        destinations = [Path(out).expanduser() for out in args.outs or []]
        if len({path.resolve() for path in destinations}) != len(destinations):
            raise ValueError("Duplicate resolved output destinations")
        if any(path.exists() or path.is_symlink() for path in destinations):
            raise ValueError("Refusing to overwrite an existing map; preserve and resolve it explicitly first")
        for path in destinations:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as output:
                output.write(text)
            print(f"wrote {path}", file=sys.stderr)
        sys.stdout.write(text)
        return 0
    except (ValueError, OSError) as error:
        print(f"Model proposal stopped: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
