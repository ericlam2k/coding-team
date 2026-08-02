#!/usr/bin/env bash
# Minimal Codex activation: link the framework adapter and bounded QA skill.
# No Python, YAML, or Ruby dependency is needed for activation.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
CODEX_HOME="${CODEX_HOME/#\~/$HOME}"
CHECK_ONLY=0

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/activate-codex-team.sh [--check]

Environment:
  CODEX_HOME  Codex config home (default: ~/.codex)

This links only the Coding Team adapter and bounded QA skill. It does not
refresh model maps or install addons.
USAGE
}

die() {
  echo "error: $*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)
      CHECK_ONLY=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1 (try --help)"
      ;;
  esac
done

ADAPTER_SRC="$ROOT/adapters/codex"
QA_SKILL_SRC="$ROOT/skills/quality/qa-evidence-enforcement"
CORE_POLICY="$ROOT/core/qa-operating-model.md"
ADAPTER_DST="$CODEX_HOME/skills/coding-team"
QA_SKILL_DST="$CODEX_HOME/skills/qa-evidence-enforcement"

[[ -d "$ADAPTER_SRC" ]] || die "missing adapter: $ADAPTER_SRC"
[[ -f "$ADAPTER_SRC/SKILL.md" ]] || die "missing adapter skill: $ADAPTER_SRC/SKILL.md"
[[ -f "$QA_SKILL_SRC/SKILL.md" ]] || die "missing QA skill: $QA_SKILL_SRC/SKILL.md"
[[ -f "$CORE_POLICY" ]] || die "missing QA policy: $CORE_POLICY"

link_path() {
  local src="$1" dst="$2"
  mkdir -p "$(dirname "$dst")"
  if [[ -L "$dst" ]]; then
    local current
    current="$(readlink "$dst")"
    if [[ "$current" == "$src" ]]; then
      echo "already linked: $dst -> $src"
      return 0
    fi
    echo "replacing symlink $dst (was -> $current)"
    rm "$dst"
  elif [[ -e "$dst" ]]; then
    die "refusing to overwrite non-symlink: $dst"
  fi
  ln -s "$src" "$dst"
  echo "linked: $dst -> $src"
}

if [[ "$CHECK_ONLY" -eq 0 ]]; then
  link_path "$ADAPTER_SRC" "$ADAPTER_DST"
  link_path "$QA_SKILL_SRC" "$QA_SKILL_DST"
fi

[[ -f "$ADAPTER_DST/SKILL.md" ]] || die "adapter link is not usable: $ADAPTER_DST"
[[ -f "$QA_SKILL_DST/SKILL.md" ]] || die "QA skill link is not usable: $QA_SKILL_DST"

cat <<NEXT

Coding Team activation verified.
CODING_TEAM_ROOT=$ROOT
QA policy=$CORE_POLICY
QA skill=$QA_SKILL_DST

Use this in the next session:
  export CODING_TEAM_ROOT="$ROOT"
  Read core/qa-operating-model.md before any bounded QA batch.
  Load qa-evidence-enforcement only when qa_required=true or qa_mode=bounded.
NEXT
