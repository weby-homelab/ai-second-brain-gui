#!/bin/sh
# POWER-GUI entrypoint: warm FTS index before starting the web server.
# This ensures the first search query is fast even on a fresh volume mount.
set -eu

VAULT="${POWER_GUI_VAULT_PATH:-/brain}"

# Only attempt FTS sync when the vault directory is non-empty (i.e., the
# volume is actually mounted and contains Markdown files).
if [ -d "$VAULT" ] && find "$VAULT" -maxdepth 2 -name "*.md" -quit 2>/dev/null; then
    echo "[entrypoint] Pre-warming FTS search index for vault: $VAULT"
    # Use power sync --no-embeddings for a fast, dense-free FTS-only sync.
    # Failures are non-fatal: the GUI degrades to scan-based fallback.
    power sync "$VAULT" --fts-only --allow-partial 2>/dev/null || \
        echo "[entrypoint] FTS pre-warm skipped (vault empty or sync unavailable)"
else
    echo "[entrypoint] Vault not mounted or empty — skipping FTS pre-warm"
fi

exec python -m power_gui.app --host "${POWER_GUI_HOST:-0.0.0.0}" --port "${POWER_GUI_PORT:-8080}" --vault "$VAULT"
