#!/usr/bin/env bash
# Generic Coding Team single-install entry point.
#
# Installation always links the selected adapter and conditional QA skill.
# Legacy --profile hybrid|full flags are accepted as aliases only; they do not
# change the install payload or enable addons.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
CODEX_HOME="${CODEX_HOME/#\~/$HOME}"
PROFILE="hybrid"
PROFILE_EXPLICIT=0
PLATFORM=""
CHECK_ONLY=0

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/install-coding-team.sh [--platform codex|cursor|cline]
  ./scripts/install-coding-team.sh --check [--platform ...]

Profiles:
  hybrid  Lightweight default: adapter + QA skill; no model refresh or addons.
  full    Opt-in framework: adapter + QA skill plus full Codex addons.
          Model mapping remains a separate, explicit user action.

Start from a clean standalone clone:
  git clone https://github.com/ericlam2k/coding-team.git
  cd coding-team
  ./scripts/install-coding-team.sh --profile hybrid --platform codex

Environment:
  CODEX_HOME  Skill/config home (default: ~/.codex). Use a project-local path
              when the host sandbox cannot read the global Codex home.
USAGE
}

die() {
  echo "error: $*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      [[ $# -ge 2 ]] || die "--profile requires hybrid or full"
      PROFILE="$2"
      PROFILE_EXPLICIT=1
      shift 2
      ;;
    --platform)
      [[ $# -ge 2 ]] || die "--platform requires codex, cursor, or cline"
      PLATFORM="$2"
      shift 2
      ;;
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

if [[ -n "$PROFILE_ALIAS" ]]; then
  [[ "$PROFILE_ALIAS" == "hybrid" || "$PROFILE_ALIAS" == "full" ]] || die "profile must be hybrid or full"
  echo "deprecation: --profile $PROFILE_ALIAS is a compatibility alias; install is single-scope and profile-free." >&2
fi
[[ -n "$PLATFORM" ]] || PLATFORM="codex"
case "$PLATFORM" in
  codex|cursor|cline) ;;
  *) die "platform must be codex, cursor, or cline" ;;
esac

ADAPTER_SRC="$ROOT/adapters/$PLATFORM"
QA_SKILL_SRC="$ROOT/skills/quality/qa-evidence-enforcement"
[[ -d "$ADAPTER_SRC" ]] || die "missing adapter: $ADAPTER_SRC"
[[ -f "$ADAPTER_SRC/SKILL.md" ]] || die "missing adapter skill: $ADAPTER_SRC/SKILL.md"
[[ -f "$QA_SKILL_SRC/SKILL.md" ]] || die "missing QA skill: $QA_SKILL_SRC/SKILL.md"
[[ -f "$ROOT/core/qa-operating-model.md" ]] || die "missing QA policy: $ROOT/core/qa-operating-model.md"

if [[ "$PLATFORM" == "codex" ]]; then
  ADAPTER_DST="$CODEX_HOME/skills/coding-team"
  QA_SKILL_DST="$CODEX_HOME/skills/qa-evidence-enforcement"
else
  INSTALL_ROOT="$ROOT/.${PLATFORM}-install"
  ADAPTER_DST="$INSTALL_ROOT/coding-team"
  QA_SKILL_DST="$INSTALL_ROOT/qa-evidence-enforcement"
fi

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

remove_owned_addon_links() {
  [[ "$PLATFORM" == "codex" ]] || return 0
  for name in agentic-worker; do
    local dst="$CODEX_HOME/skills/$name"
    if [[ -L "$dst" && "$(readlink "$dst")" == "$ROOT/addons/"* ]]; then
      rm "$dst"
      echo "removed full-profile addon link: $dst"
    fi
  done
}

write_profile() {
  mkdir -p "$(dirname "$PROFILE_FILE")"
  printf '%s\n' "$PROFILE" > "$PROFILE_FILE"
  echo "active profile: $PROFILE ($PROFILE_FILE)"
}

check_links() {
  [[ -f "$ADAPTER_DST/SKILL.md" ]] || die "adapter is not active: $ADAPTER_DST"
  [[ -f "$QA_SKILL_DST/SKILL.md" ]] || die "QA skill is not active: $QA_SKILL_DST"
  [[ -f "$ROOT/core/qa-operating-model.md" ]] || die "QA policy is missing: $ROOT/core/qa-operating-model.md"
  [[ -f "$PROFILE_FILE" ]] || die "profile marker is missing: $PROFILE_FILE"
  [[ "$(<"$PROFILE_FILE")" == "$PROFILE" ]] || die "active profile is $(<"$PROFILE_FILE"), requested $PROFILE"
  echo "activation check: PASS ($PROFILE/$PLATFORM)"
  if [[ "$PROFILE_EXPLICIT" -eq 1 ]]; then
    echo "scope_selected: $PROFILE"
  else
    echo "scope_assumed: $PROFILE (compatibility default; pass --profile explicitly for internal/CI runs)"
  fi
}

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  check_links
  exit 0
fi

if [[ "$PROFILE" == "hybrid" ]]; then
  remove_owned_addon_links
  link_path "$ADAPTER_SRC" "$ADAPTER_DST"
  link_path "$QA_SKILL_SRC" "$QA_SKILL_DST"
  write_profile
  echo "Hybrid profile active: no model-map refresh and no addons enabled."
else
  [[ -x "$ROOT/bin/ct" ]] || die "missing executable: $ROOT/bin/ct"
  # Setup is deliberately map-free. Addons are explicit through --full;
  # mapping is approved separately with `bin/ct map approve`.
  "$ROOT/bin/ct" init --platform "$PLATFORM" --full
  write_profile
  echo "Full profile active: model map unchanged; Codex full addons enabled where supported."
fi

check_links
cat <<NEXT

Next session:
  export CODING_TEAM_ROOT="$ROOT"
  export CODEX_HOME="$CODEX_HOME"
  Load the coding-team skill for $PLATFORM.
  Installation is profile-free. Enable optional addons explicitly, for example:
    "$ROOT/bin/ct" enable agentic-worker
  Propose a model map whenever providers/API proxies/models change:
    "$ROOT/bin/ct" map propose --platform "$PLATFORM"
  Approve a proposal separately with: $ROOT/bin/ct map approve
  A proposal is never approval.
NEXT
