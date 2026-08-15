#!/usr/bin/env bash
# Install coding-team for a host runtime.
# Usage:
#   ./install.sh --platform codex [--global|--project <path>] [--refresh-map]
#   ./install.sh --platform codex --global --enable agentic-worker
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM=""
DO_GLOBAL=0
PROJECT_PATH=""
REFRESH_MAP=0
ENABLE_LIST=""
DISABLE_LIST=""

usage() {
  cat <<'USAGE'
Usage:
  ./install.sh --platform codex [--global] [--project <path>] [--refresh-map]
               [--enable <addon[,addon...]>] [--disable <addon[,addon...]>]

Recommended profile install:
  ./scripts/install-coding-team.sh --profile hybrid --platform codex
  ./scripts/install-coding-team.sh --profile full --platform codex

Options:
  --platform codex|cursor|cline   Target runtime (only codex in v1)
  --global                        Symlink adapters/codex → $CODEX_HOME/skills/coding-team
  --project <path>                Append AGENTS.md coding-team pointer into a consumer project
  --refresh-map                   Explicitly approve a model-map refresh (skill target + examples/)
  --enable NAME[,NAME...]         Enable standalone addons (pm-lean, agentic-worker). Default OFF.
  --disable NAME[,NAME...]        Disable standalone addons (removes Codex skill symlinks)
  -h, --help                      Show this help

Addons are NOT part of core. See addons/README.md and addons/toggles.json.

Environment:
  CODEX_HOME   Codex config home (default: ~/.codex)
  CODING_TEAM_ROOT  Optional; AGENTS.md / skill resolve to this checkout when set
USAGE
}

die() {
  echo "error: $*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform)
      [[ $# -ge 2 ]] || die "--platform requires a value"
      PLATFORM="$2"
      shift 2
      ;;
    --global)
      DO_GLOBAL=1
      shift
      ;;
    --project)
      [[ $# -ge 2 ]] || die "--project requires a path"
      PROJECT_PATH="$2"
      shift 2
      ;;
    --refresh-map)
      REFRESH_MAP=1
      shift
      ;;
    --enable)
      [[ $# -ge 2 ]] || die "--enable requires a value"
      ENABLE_LIST="$2"
      shift 2
      ;;
    --disable)
      [[ $# -ge 2 ]] || die "--disable requires a value"
      DISABLE_LIST="$2"
      shift 2
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

[[ -n "$PLATFORM" ]] || die "missing --platform (try --help)"

case "$PLATFORM" in
  cursor|cline)
    echo "not implemented in v1" >&2
    exit 1
    ;;
  codex)
    ;;
  *)
    die "unknown platform: $PLATFORM (expected codex|cursor|cline)"
    ;;
esac

# Default to global install when neither flag given (unless only enable/disable/refresh).
if [[ "$DO_GLOBAL" -eq 0 && -z "$PROJECT_PATH" && "$REFRESH_MAP" -eq 0 && -z "$ENABLE_LIST" && -z "$DISABLE_LIST" ]]; then
  DO_GLOBAL=1
fi
if [[ "$DO_GLOBAL" -eq 0 && -z "$PROJECT_PATH" && ( "$REFRESH_MAP" -eq 1 || -n "$ENABLE_LIST" || -n "$DISABLE_LIST" ) ]]; then
  DO_GLOBAL=1
fi

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
CODEX_HOME="${CODEX_HOME/#\~/$HOME}"

SKILL_SRC="$ROOT/adapters/codex"
SKILL_DST="$CODEX_HOME/skills/coding-team"
QA_SKILL_SRC="$ROOT/skills/quality/qa-evidence-enforcement"
QA_SKILL_DST="$CODEX_HOME/skills/qa-evidence-enforcement"
QA_VALIDATOR="$ROOT/scripts/validate-qa-evidence.rb"
DETECT="$SKILL_SRC/scripts/detect-model-pool.py"
APPLY="$SKILL_SRC/scripts/apply-pool-map.py"
EXAMPLE_MAP="$ROOT/examples/model-pool.map.codex.example.md"
EXAMPLE_REFRESH="$ROOT/examples/model-pool.map.md"
TOGGLES="$ROOT/addons/toggles.json"

[[ -d "$SKILL_SRC" ]] || die "missing adapter: $SKILL_SRC"
[[ -f "$DETECT" && -f "$APPLY" ]] || die "missing pool scripts under adapters/codex/scripts/"
[[ -f "$QA_SKILL_SRC/SKILL.md" ]] || die "missing QA enforcement skill: $QA_SKILL_SRC/SKILL.md"
[[ -f "$QA_VALIDATOR" ]] || die "missing QA evidence validator: $QA_VALIDATOR"

link_path() {
  local src="$1" dst="$2"
  mkdir -p "$(dirname "$dst")"
  if [[ -e "$dst" || -L "$dst" ]]; then
    if [[ -L "$dst" ]]; then
      local current
      current="$(readlink "$dst")"
      if [[ "$current" == "$src" ]]; then
        echo "already linked: $dst → $src"
        return 0
      fi
      echo "replacing symlink $dst (was → $current)"
      rm "$dst"
    else
      die "refusing to overwrite non-symlink: $dst"
    fi
  fi
  ln -s "$src" "$dst"
  echo "linked: $dst → $src"
}

unlink_path() {
  local dst="$1"
  if [[ -L "$dst" ]]; then
    rm "$dst"
    echo "removed symlink: $dst"
  elif [[ -e "$dst" ]]; then
    die "refusing to remove non-symlink: $dst"
  else
    echo "not present: $dst"
  fi
}

link_skill() {
  link_path "$SKILL_SRC" "$SKILL_DST"
  link_path "$QA_SKILL_SRC" "$QA_SKILL_DST"
  echo "QA evidence enforcement: conditional skill + validator installed"
}

set_toggle() {
  local name="$1" enabled="$2"
  python3 - "$TOGGLES" "$name" "$enabled" <<'PY'
import json, sys
path, name, enabled = sys.argv[1], sys.argv[2], sys.argv[3].lower() == "true"
data = json.loads(open(path, encoding="utf-8").read())
addons = data.setdefault("addons", {})
if name not in addons:
    sys.exit(f"unknown addon: {name} (known: {', '.join(sorted(addons))})")
addons[name]["enabled"] = enabled
open(path, "w", encoding="utf-8").write(json.dumps(data, indent=2) + "\n")
print(f"toggles.json: {name}.enabled = {enabled}")
PY
}

enable_addon() {
  local name="$1"
  case "$name" in
    pm-lean)
      set_toggle pm-lean true
      link_path "$ROOT/addons/pm-lean/skills/pm-lean-assumption-triage" "$CODEX_HOME/skills/pm-lean-assumption-triage"
      link_path "$ROOT/addons/pm-lean/skills/pm-lean-experiment-design" "$CODEX_HOME/skills/pm-lean-experiment-design"
      ;;
    agentic-worker)
      set_toggle agentic-worker true
      link_path "$ROOT/addons/agentic-worker/skills/agentic-worker" "$CODEX_HOME/skills/agentic-worker"
      ;;
    *)
      die "unknown addon: $name (expected pm-lean or agentic-worker)"
      ;;
  esac
}

disable_addon() {
  local name="$1"
  case "$name" in
    pm-lean)
      set_toggle pm-lean false
      unlink_path "$CODEX_HOME/skills/pm-lean-assumption-triage"
      unlink_path "$CODEX_HOME/skills/pm-lean-experiment-design"
      ;;
    agentic-worker)
      set_toggle agentic-worker false
      unlink_path "$CODEX_HOME/skills/agentic-worker"
      ;;
    *)
      die "unknown addon: $name (expected pm-lean or agentic-worker)"
      ;;
  esac
}

split_csv() {
  local csv="$1"
  local IFS=','
  # shellcheck disable=SC2086
  set -- $csv
  for item in "$@"; do
    item="$(echo "$item" | tr -d '[:space:]')"
    [[ -n "$item" ]] && echo "$item"
  done
}

refresh_map() {
  local targets=()
  if [[ -d "$SKILL_DST" || -L "$SKILL_DST" ]]; then
    targets+=("$SKILL_DST/model-pool.map.md")
  else
    targets+=("$SKILL_SRC/model-pool.map.md")
  fi
  targets+=("$EXAMPLE_REFRESH")

  echo "detecting Codex model pool (CODEX_HOME=$CODEX_HOME)…"
  local slugs
  slugs="$(CODEX_HOME="$CODEX_HOME" python3 "$DETECT")"
  echo "$slugs" | python3 "$APPLY" --stdin \
    --out "${targets[0]}" \
    --out "${targets[1]}" >/dev/null
  echo "refreshed:"
  printf '  %s\n' "${targets[@]}"
}

append_agents() {
  local project="$1"
  [[ -d "$project" ]] || die "project path is not a directory: $project"
  local agents="$project/AGENTS.md"
  local marker="<!-- coding-team:begin -->"
  local block
  block="$(cat <<BLOCK
${marker}
## Coding Team (Codex)

Set \`CODING_TEAM_ROOT\` to the coding-team checkout (this install used: \`${ROOT}\`), or rely on the \`coding-team\` skill symlink under \`\$CODEX_HOME/skills/coding-team\`.

When orchestrating multi-role work:

1. Load the **coding-team** skill (\`\$coding-team\` / skill chip).
2. Resolve \`CODING_TEAM_ROOT\` and read \`core/\` + skill \`model-pool.map.md\`.
3. WIP ≤ 2; Test Engineer → Gatekeeper sequential; incomplete → ask human.
4. Design: hallmark + awesome-design-md under \`\$CODING_TEAM_ROOT/skills/design/\`.
5. Optional addons (default OFF) — enable via \`./install.sh --enable …\` — see \`addons/README.md\`.

Drop-in reference from the coding-team repo: see also \`${ROOT}/AGENTS.md\`.
<!-- coding-team:end -->
BLOCK
)"

  if [[ -f "$agents" ]] && grep -q 'coding-team:begin' "$agents"; then
    echo "AGENTS.md already has coding-team pointer: $agents"
    return 0
  fi
  if [[ -f "$agents" ]]; then
    printf '\n%s\n' "$block" >> "$agents"
    echo "appended coding-team pointer to $agents"
  else
    printf '%s\n' "$block" > "$agents"
    echo "wrote $agents"
  fi
}

echo "coding-team install (platform=codex)"
echo "  repo:        $ROOT"
echo "  CODEX_HOME:  $CODEX_HOME"

if [[ "$DO_GLOBAL" -eq 1 ]]; then
  link_skill
fi

if [[ -n "$DISABLE_LIST" ]]; then
  while IFS= read -r name; do
    [[ -n "$name" ]] && disable_addon "$name"
  done < <(split_csv "$DISABLE_LIST")
fi

if [[ -n "$ENABLE_LIST" ]]; then
  while IFS= read -r name; do
    [[ -n "$name" ]] && enable_addon "$name"
  done < <(split_csv "$ENABLE_LIST")
fi

# Linking the adapter, adding a project pointer, or toggling addons never
# starts model mapping. A map refresh is an explicit, user-invoked operation.
if [[ "$REFRESH_MAP" -eq 1 ]]; then
  refresh_map
fi

if [[ -n "$PROJECT_PATH" ]]; then
  append_agents "$PROJECT_PATH"
fi

if [[ ! -f "$EXAMPLE_MAP" ]]; then
  echo "note: missing $EXAMPLE_MAP (expected in repo)" >&2
fi

cat <<NEXT

Next steps
----------
1. Confirm the coding-team skill:
     ls -la "$SKILL_DST"
2. Optional addons (default OFF — not injected into core):
     ./install.sh --platform codex --global --enable pm-lean
     ./install.sh --platform codex --global --disable pm-lean
   State file: $TOGGLES
3. In Codex, invoke **Coding Team**; enable addons only when you want them.
4. Explicitly refresh/approve the pool map after Codex model changes:
     ./install.sh --platform codex --refresh-map

Model map path (unchanged unless --refresh-map): $SKILL_DST/model-pool.map.md
NEXT
