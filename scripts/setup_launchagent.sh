#!/bin/zsh

# Get the absolute path of the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SITE_ROOT="$(dirname "$SCRIPT_DIR")"

# Create LOGS directory if it doesn't exist
mkdir -p "$SITE_ROOT/LOGS"

# Set permissions for scripts
chmod +x "$SITE_ROOT/scripts/sync_control.sh"
chmod +x "$SITE_ROOT/scripts/watch_sync.sh"
chmod +x "$SITE_ROOT/scripts/sync_wrapper.sh"

# Copy plist to LaunchAgents directory
PLIST_SOURCE="$SITE_ROOT/com.asbjborg.site.sync.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.asbjborg.site.sync.plist"

# Unload existing LaunchAgent if it exists
if [ -f "$PLIST_DEST" ]; then
    launchctl unload "$PLIST_DEST"
fi

# Copy plist file
cp "$PLIST_SOURCE" "$PLIST_DEST"

# Set correct permissions
chmod 644 "$PLIST_DEST"

# Load the LaunchAgent
launchctl load "$PLIST_DEST"

echo "LaunchAgent installed and loaded successfully" 