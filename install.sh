#!/usr/bin/env bash
# Install coding-team for a host runtime.
# Usage: ./install.sh --platform codex [--global|--project <path>] [--refresh-map]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM=""
DO_GLOBAL=0
PROJECT_PATH=""
REFRESH_MAP=0

usage() {
  cat <<'USAGE'
Usage:
  ./install.sh --platform codex [--global] [--project <path>] [--refresh-map]

Options:
  --platform codex|cursor|cline   Target runtime (only codex in v1)
  --global                        Symlink adapters/codex → $CODEX_HOME/skills/coding-team
  --project <path>                Append AGENTS.md coding-team pointer into a consumer project
  --refresh-map                   Re-run model pool detect/apply (skill target + examples/)
  -h, --help                      Show this help

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

# Default to global install when neither flag given (unless refresh-only with existing link).
if [[ "$DO_GLOBAL" -eq 0 && -z "$PROJECT_PATH" && "$REFRESH_MAP" -eq 0 ]]; then
  DO_GLOBAL=1
fi
if [[ "$DO_GLOBAL" -eq 0 && -z "$PROJECT_PATH" && "$REFRESH_MAP" -eq 1 ]]; then
  DO_GLOBAL=1
fi

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
CODEX_HOME="${CODEX_HOME/#\~/$HOME}"

SKILL_SRC="$ROOT/adapters/codex"
SKILL_DST="$CODEX_HOME/skills/coding-team"
DETECT="$SKILL_SRC/scripts/detect-model-pool.py"
APPLY="$SKILL_SRC/scripts/apply-pool-map.py"
EXAMPLE_MAP="$ROOT/examples/model-pool.map.codex.example.md"
EXAMPLE_REFRESH="$ROOT/examples/model-pool.map.md"

[[ -d "$SKILL_SRC" ]] || die "missing adapter: $SKILL_SRC"
[[ -f "$DETECT" && -f "$APPLY" ]] || die "missing pool scripts under adapters/codex/scripts/"

link_skill() {
  mkdir -p "$CODEX_HOME/skills"
  if [[ -e "$SKILL_DST" || -L "$SKILL_DST" ]]; then
    if [[ -L "$SKILL_DST" ]]; then
      local current
      current="$(readlink "$SKILL_DST")"
      if [[ "$current" == "$SKILL_SRC" ]]; then
        echo "skill already linked: $SKILL_DST → $SKILL_SRC"
        return 0
      fi
      echo "replacing existing symlink $SKILL_DST (was → $current)"
      rm "$SKILL_DST"
    else
      die "refusing to overwrite non-symlink: $SKILL_DST (remove it and re-run)"
    fi
  fi
  ln -s "$SKILL_SRC" "$SKILL_DST"
  echo "linked skill: $SKILL_DST → $SKILL_SRC"
}

refresh_map() {
  local targets=()
  # Prefer writing into the installed skill (symlink target = adapters/codex)
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

# Always refresh map on install/refresh (install embeds map into skill + examples/)
if [[ "$DO_GLOBAL" -eq 1 || "$REFRESH_MAP" -eq 1 || -n "$PROJECT_PATH" ]]; then
  refresh_map
fi

if [[ -n "$PROJECT_PATH" ]]; then
  append_agents "$PROJECT_PATH"
fi

# Keep the committed example in sync shape if missing
if [[ ! -f "$EXAMPLE_MAP" ]]; then
  echo "note: missing $EXAMPLE_MAP (expected in repo)" >&2
fi

cat <<NEXT

Next steps
----------
1. Confirm the skill is visible to Codex:
     ls -la "$SKILL_DST"
2. In Codex, invoke the **Coding Team** skill chip, or ask Codex to use \$coding-team.
3. Optional — point a consumer project at this checkout:
     export CODING_TEAM_ROOT="$ROOT"
     ./install.sh --platform codex --project /path/to/your/app
4. Design skills stay in the repo (not duplicated into CODEX_HOME).
   Lead reads them via CODING_TEAM_ROOT:
     $ROOT/skills/design/hallmark
     $ROOT/skills/design/awesome-design-md
5. Refresh the pool map after Codex model changes:
     ./install.sh --platform codex --refresh-map

Model map: $SKILL_DST/model-pool.map.md
NEXT
