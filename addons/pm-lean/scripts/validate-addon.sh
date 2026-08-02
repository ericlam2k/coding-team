#!/usr/bin/env bash
set -euo pipefail

ADDON_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEAM_ROOT="$(cd "$ADDON_ROOT/../.." && pwd)"
SKILLS_ROOT="$ADDON_ROOT/skills"
names=(pm-lean-assumption-triage pm-lean-experiment-design)
forbidden_auto_claim='automatically (continue|route|approve|invoke)|auto-(chain|route|approve|invoke)|replace (the )?(Test Engineer|Gatekeeper)|change WIP'

for name in "${names[@]}"; do
  skill="$SKILLS_ROOT/$name"
  [[ -f "$skill/SKILL.md" ]] || { echo "missing SKILL.md: $name" >&2; exit 1; }
  [[ -f "$skill/agents/openai.yaml" ]] || { echo "missing openai metadata: $name" >&2; exit 1; }
  rg -q "^name: $name$" "$skill/SKILL.md" || { echo "wrong skill name: $name" >&2; exit 1; }
  rg -q 'allow_implicit_invocation: false' "$skill/agents/openai.yaml" || { echo "implicit invocation enabled: $name" >&2; exit 1; }
  ! rg -q '\[TODO:' "$skill/SKILL.md" || { echo "unfinished content: $name" >&2; exit 1; }
  ! rg -qi "$forbidden_auto_claim" "$skill/SKILL.md" || { echo "forbidden auto-orchestration claim: $name" >&2; exit 1; }
  ! rg -q "^name: $name$" "$TEAM_ROOT/skills" --glob SKILL.md || { echo "duplicate core skill name: $name" >&2; exit 1; }
done

[[ "$(find "$SKILLS_ROOT" -name SKILL.md -type f | wc -l | tr -d ' ')" == "2" ]] || { echo "expected exactly two pm-lean skills" >&2; exit 1; }
[[ "$(for name in "${names[@]}"; do printf '%s\n' "$name"; done | sort -u | wc -l | tr -d ' ')" == "2" ]] || { echo "duplicate pm-lean skill names" >&2; exit 1; }
[[ -f "$ADDON_ROOT/LICENSE" && -f "$ADDON_ROOT/UPSTREAM.md" ]] || { echo "missing attribution files" >&2; exit 1; }
rg -q '18468a95b427e70e258b51389796367c6f684e7d' "$ADDON_ROOT/UPSTREAM.md" || { echo "missing upstream pin" >&2; exit 1; }

echo "pm-lean addon validation passed"
