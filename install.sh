#!/usr/bin/env bash
# Friendly one-command entrypoint. The lower-level installer remains
# scripts/install-coding-team.sh for automation and explicit host selection.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM=""
PROJECT_PATH=""
CHECK_ONLY=0
PROPOSE_MAP=0
ENABLE_LIST=""
DISABLE_LIST=""
QUESTIONNAIRE=1
INTERACTIVE=0

usage() {
  cat <<'USAGE'
Usage:
  ./install.sh                                  # detect host and install
  ./install.sh --platform codex|cursor|cline   # choose host explicitly
  ./install.sh --project /path/to/repo         # install + add project pointer
  ./install.sh --no-questionnaire               # skip prompts (CI/automation)
  ./install.sh --check                          # verify an existing install

Helpful options:
  --refresh-map       Show a read-only model-map suggestion
  --enable pm-lean    Enable the optional PM Lean addon
  --disable pm-lean   Disable the optional PM Lean addon
  --global            Accepted for compatibility; the default is global where supported

The normal path is one command: ./install.sh
USAGE
}

die() {
  echo "error: $*" >&2
  exit 1
}

is_supported_platform() {
  case "$1" in
    codex|cursor|cline) return 0 ;;
    *) return 1 ;;
  esac
}

detect_platform() {
  if [[ -n "${CODING_TEAM_PLATFORM:-}" ]]; then
    printf '%s\n' "$CODING_TEAM_PLATFORM"
    return 0
  fi

  local candidates=""
  if [[ -n "${CODEX_HOME:-}" || -d "$HOME/.codex" ]]; then
    candidates="codex"
  fi
  if [[ -n "${CURSOR_HOME:-}" || -d "$HOME/.cursor" ]]; then
    candidates="${candidates:+$candidates,}cursor"
  fi
  if [[ -n "${CLINE_HOME:-}" || -d "$HOME/.cline" ]]; then
    candidates="${candidates:+$candidates,}cline"
  fi
  printf '%s\n' "$candidates"
}

choose_platform() {
  local detected="" selected="" first=""
  detected="$(detect_platform)"

  if [[ "$detected" != *,* && -n "$detected" ]]; then
    echo "Detected host: $detected" >&2
    printf '%s\n' "$detected"
    return 0
  fi

  if [[ "$detected" == *,* ]]; then
    first="${detected%%,*}"
    if [[ "$INTERACTIVE" -eq 1 ]]; then
      echo "I found more than one AI coding host: ${detected//,/, }." >&2
      if ! read -r -p "Which host should coding-team use? [$first]: " selected; then
        selected=""
      fi
      selected="${selected:-$first}"
    else
      die "multiple hosts detected ($detected); pass --platform or run interactively"
    fi
  elif [[ "$INTERACTIVE" -eq 1 ]]; then
    echo "I could not detect your AI coding host." >&2
    echo "Choose one: codex, cursor, or cline." >&2
    if ! read -r -p "Host [codex]: " selected; then
      selected=""
    fi
    selected="${selected:-codex}"
  else
    # Codex is the safest non-interactive default because it has a stable
    # user-home install target and can be overridden with --platform.
    selected="codex"
    echo "No host detected; using Codex. Use --platform to choose another host." >&2
  fi

  if ! is_supported_platform "$selected"; then
    if [[ "$INTERACTIVE" -ne 1 ]]; then
      die "unsupported host '$selected'; choose codex, cursor, or cline"
    fi
    local attempt=1
    while (( attempt <= 3 )); do
      echo "Please enter codex, cursor, or cline." >&2
      if ! read -r -p "Host [$first]: " selected; then
        selected=""
      fi
      selected="${selected:-$first}"
      is_supported_platform "$selected" && break
      attempt=$((attempt + 1))
    done
  fi

  is_supported_platform "$selected" || die "unsupported host '$selected'; choose codex, cursor, or cline"
  printf '%s\n' "$selected"
}

run_questionnaire() {
  [[ "$QUESTIONNAIRE" -eq 1 ]] || return 0
  if [[ "$INTERACTIVE" -ne 1 ]]; then
    echo "Questionnaire skipped because this is a non-interactive session." >&2
    return 0
  fi

  local project=""
  echo
  if [[ -z "$PROJECT_PATH" ]]; then
    echo "Optional first-project setup (press Enter to skip):"
    if ! read -r -p "Project folder (optional; press Enter to skip): " project; then
      project=""
    fi
    PROJECT_PATH="$project"
  else
    echo "First project: $PROJECT_PATH"
  fi
}

prepare_project() {
  [[ -n "$PROJECT_PATH" ]] || return 0

  # Shells expand ~ before a command, but text entered at a prompt does not.
  PROJECT_PATH="${PROJECT_PATH/#\~/$HOME}"
  if [[ ! -d "$PROJECT_PATH" ]]; then
    echo "Project setup skipped: not a directory: $PROJECT_PATH" >&2
    echo "You can run this later: ./bin/ct project /path/to/your/project" >&2
    return 0
  fi

  if ! "$ROOT/bin/ct" project "$PROJECT_PATH"; then
    echo "Project setup skipped because the folder could not be updated: $PROJECT_PATH" >&2
    echo "The framework installation itself is still complete." >&2
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform)
      [[ $# -ge 2 ]] || die "--platform requires codex, cursor, or cline"
      PLATFORM="$2"
      shift 2
      ;;
    --project)
      [[ $# -ge 2 ]] || die "--project requires a repository path"
      PROJECT_PATH="$2"
      shift 2
      ;;
    --no-questionnaire)
      QUESTIONNAIRE=0
      shift
      ;;
    --check)
      CHECK_ONLY=1
      shift
      ;;
    --refresh-map)
      PROPOSE_MAP=1
      shift
      ;;
    --enable)
      [[ $# -ge 2 ]] || die "--enable requires an addon name"
      ENABLE_LIST="$2"
      shift 2
      ;;
    --disable)
      [[ $# -ge 2 ]] || die "--disable requires an addon name"
      DISABLE_LIST="$2"
      shift 2
      ;;
    --global)
      echo "note: --global is retained for compatibility; the normal install is already global where supported." >&2
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1 (try ./install.sh --help)"
      ;;
  esac
done

if [[ -t 0 && -t 1 ]]; then
  INTERACTIVE=1
fi

# --no-questionnaire is also a no-prompt mode so automation never hangs on a
# host-selection question. Pass --platform when a non-Codex host is intended.
if [[ "$QUESTIONNAIRE" -eq 0 ]]; then
  INTERACTIVE=0
fi

if [[ -z "$PLATFORM" ]]; then
  PLATFORM="$(choose_platform)"
else
  echo "Selected host: $PLATFORM" >&2
fi

case "$PLATFORM" in
  codex|cursor|cline) ;;
  *) die "unsupported host '$PLATFORM'; choose codex, cursor, or cline" ;;
esac

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  [[ -z "$PROJECT_PATH$ENABLE_LIST$DISABLE_LIST" ]] || die "--check cannot be combined with project or addon changes"
  exec "$ROOT/scripts/install-coding-team.sh" --check --platform "$PLATFORM"
fi

run_questionnaire

"$ROOT/scripts/install-coding-team.sh" --platform "$PLATFORM"

prepare_project

if [[ -n "$ENABLE_LIST" ]]; then
  "$ROOT/bin/ct" enable "$ENABLE_LIST"
fi

if [[ -n "$DISABLE_LIST" ]]; then
  "$ROOT/bin/ct" disable "$DISABLE_LIST"
fi

if [[ "$PROPOSE_MAP" -eq 1 ]]; then
  echo
  echo "Read-only model-map suggestion (no file will be written):"
  "$ROOT/bin/ct" map propose --platform "$PLATFORM"
fi

cat <<NEXT

Setup complete.
Next:
  1. Open or restart your AI coding host.
  2. Describe one small change in plain English.
  3. Keep the human review step before commit or release.

If your host cannot find the framework, rerun this installer for that host.
Do not pin a consumer project to this source checkout.
NEXT
