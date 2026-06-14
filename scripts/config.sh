#!/usr/bin/env bash
# Config loader. Source this from any script: `source "$(dirname ...)/config.sh"`.
# Loads config.env if present, else config.example.env, else built-in defaults.
# Exposes: ARCHIVE_ROOT FETCH_ENGINE BROWSE_BIN THROTTLE_SECONDS OBSIDIAN_* RESOLVED_BROWSE

_cfg_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Built-in defaults (so the bundle works with zero config).
ARCHIVE_ROOT="${ARCHIVE_ROOT:-$HOME/wx-archive}"
FETCH_ENGINE="${FETCH_ENGINE:-auto}"
BROWSE_BIN="${BROWSE_BIN:-$HOME/.claude/skills/gstack/browse/dist/browse}"
THROTTLE_SECONDS="${THROTTLE_SECONDS:-1}"
OBSIDIAN_ENABLED="${OBSIDIAN_ENABLED:-false}"
OBSIDIAN_VAULT="${OBSIDIAN_VAULT:-}"
OBSIDIAN_TEARDOWN_DIR="${OBSIDIAN_TEARDOWN_DIR:-内容系统/博主拆解}"
OBSIDIAN_FRAMEWORK_LIBRARY="${OBSIDIAN_FRAMEWORK_LIBRARY:-内容系统/爆款框架库.md}"

if [ -f "$_cfg_dir/config.env" ]; then
  set -a; . "$_cfg_dir/config.env"; set +a
elif [ -f "$_cfg_dir/config.example.env" ]; then
  set -a; . "$_cfg_dir/config.example.env"; set +a
fi

# Expand ~ in path-like vars.
ARCHIVE_ROOT="${ARCHIVE_ROOT/#\~/$HOME}"
BROWSE_BIN="${BROWSE_BIN/#\~/$HOME}"
OBSIDIAN_VAULT="${OBSIDIAN_VAULT/#\~/$HOME}"

# Resolve an actually-usable browse binary (config path, then common fallbacks).
resolve_browse() {
  for b in "$BROWSE_BIN" \
           "$HOME/.claude/skills/gstack/browse/dist/browse" \
           "$(command -v browse 2>/dev/null)"; do
    [ -n "$b" ] && [ -x "$b" ] && { echo "$b"; return 0; }
  done
  return 1
}
RESOLVED_BROWSE="$(resolve_browse || true)"

# Effective engine after auto-detection.
effective_engine() {
  case "$FETCH_ENGINE" in
    browse|requests|manual) echo "$FETCH_ENGINE" ;;
    auto)
      if [ -n "$RESOLVED_BROWSE" ]; then echo "browse"; else echo "requests"; fi ;;
    *) echo "requests" ;;
  esac
}
