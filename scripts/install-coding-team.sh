#!/usr/bin/env bash
# Canonical Coding Team installer.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
CODEX_HOME="${CODEX_HOME/#\~/$HOME}"
PROFILE_ALIAS=""
PLATFORM=""
CHECK_ONLY=0
ROLLBACK_ACTIONS=()
ROLLBACK_PATHS=()
ROLLBACK_OLDTARGETS=()
ROLLBACK_EXPECTED=()

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/install-coding-team.sh [--platform codex|cursor|cline]
  ./scripts/install-coding-team.sh --check [--platform codex|cursor|cline]

Compatibility:
  --profile hybrid|full  Accepted as a legacy alias. Both values install the
                         same adapter + conditional QA support.

Start from a clean standalone clone:
  git clone https://github.com/ericlam2k/coding-team.git
  cd coding-team
  ./scripts/install-coding-team.sh --platform codex

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
      PROFILE_ALIAS="$2"
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
  local prev
  if [[ -L "$dst" ]]; then
    prev="$(readlink "$dst")"
    if [[ "$prev" == "$src" ]]; then
      echo "already linked: $dst -> $src"
      return 0
    fi
    echo "replacing symlink $dst (was -> $prev)"
    rm "$dst"
    # Record rollback fields separately so paths and link targets may contain
    # colons without corrupting the rollback record.
    ROLLBACK_ACTIONS+=("restore")
    ROLLBACK_PATHS+=("$dst")
    ROLLBACK_OLDTARGETS+=("$prev")
    ROLLBACK_EXPECTED+=("$src")
  elif [[ -e "$dst" ]]; then
    die "refusing to overwrite non-symlink: $dst; choose another CODEX_HOME or remove the old install yourself"
  else
    # Record that we should remove the new symlink on failure.
    ROLLBACK_ACTIONS+=("remove")
    ROLLBACK_PATHS+=("$dst")
    ROLLBACK_OLDTARGETS+=("")
    ROLLBACK_EXPECTED+=("$src")
  fi
  ln -s "$src" "$dst"
  echo "linked: $dst -> $src"
}

rollback() {
  echo "installation failed — rolling back installer-owned changes..." >&2
  # undo in reverse order
  for ((i=${#ROLLBACK_ACTIONS[@]}-1; i>=0; i--)); do
    action="${ROLLBACK_ACTIONS[i]}"
    path="${ROLLBACK_PATHS[i]}"
    oldtarget="${ROLLBACK_OLDTARGETS[i]}"
    expected="${ROLLBACK_EXPECTED[i]}"

    if [[ "$action" == "remove" ]]; then
      # remove only if it's still a symlink that points to the expected installed source
      if [[ -L "$path" ]]; then
        cur="$(readlink "$path")"
        if [[ -n "$expected" && "$cur" == "$expected" ]]; then
          rm "$path" && echo "removed $path"
        else
          echo "warning: not removing $path because it points to '$cur' (expected '$expected')" >&2
        fi
      else
        echo "warning: not removing $path because it is not a symlink" >&2
      fi

    elif [[ "$action" == "restore" ]]; then
      # do not overwrite a non-symlink
      if [[ -e "$path" && ! -L "$path" ]]; then
        echo "warning: cannot restore $path because a non-symlink now exists" >&2
        continue
      fi
      # restore only if current symlink still points to the installed source we created
      if [[ -L "$path" ]]; then
        cur="$(readlink "$path")"
        if [[ -n "$expected" && "$cur" != "$expected" ]]; then
          echo "warning: not restoring $path because it points to '$cur' (expected installed source '$expected')" >&2
          continue
        fi
        rm "$path"
      fi
      ln -s "$oldtarget" "$path" && echo "restored $path -> $oldtarget"
    fi
  done
}

# Rollback on any non-zero exit; on success do nothing.
trap 'rc=$?; if [ "$rc" -ne 0 ]; then rollback; fi; exit "$rc"' EXIT

check_links() {
  [[ -f "$ADAPTER_DST/SKILL.md" ]] || die "adapter is not active: $ADAPTER_DST"
  [[ -f "$QA_SKILL_DST/SKILL.md" ]] || die "QA skill is not active: $QA_SKILL_DST"
  [[ -f "$ROOT/core/qa-operating-model.md" ]] || die "QA policy is missing: $ROOT/core/qa-operating-model.md"
  echo "activation check: PASS ($PLATFORM)"
}

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  check_links
  exit 0
fi

link_path "$ADAPTER_SRC" "$ADAPTER_DST"
link_path "$QA_SKILL_SRC" "$QA_SKILL_DST"
echo "Canonical install active: adapter + conditional QA support."
if [[ -n "$PROFILE_ALIAS" ]]; then
  echo "Compatibility alias accepted: --profile $PROFILE_ALIAS (no separate mode)."
fi

check_links
cat <<NEXT

Next session:
  export CODING_TEAM_ROOT="$ROOT"
  export CODEX_HOME="$CODEX_HOME"
  Load the coding-team skill for $PLATFORM.
  Model maps are optional; use ./bin/ct map propose or ./bin/ct map approve.
NEXT
