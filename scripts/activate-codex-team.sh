#!/usr/bin/env bash
# Backward-compatible name. Use scripts/install-coding-team.sh instead.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$ROOT/scripts/install-coding-team.sh" --platform codex "$@"
