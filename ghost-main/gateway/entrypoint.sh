#!/bin/bash
# Entrypoint script for Ghost Gateway
# Ensures game storage directory is writable by appuser

GAME_DIR="${GAME_STORAGE_DIR:-/app/generated_games}"

# Fix permissions on game storage directory (Docker volume may be root-owned)
if [ -d "$GAME_DIR" ]; then
    chown -R appuser:appuser "$GAME_DIR" 2>/dev/null || true
    chmod -R 755 "$GAME_DIR" 2>/dev/null || true
fi

# Ensure directory exists
mkdir -p "$GAME_DIR" 2>/dev/null || true

# Execute the main command
exec "$@"
