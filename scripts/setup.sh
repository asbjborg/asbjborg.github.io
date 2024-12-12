#!/bin/zsh

# Check if .env exists
if [ -f ".env" ]; then
    echo "Warning: .env file already exists. Please remove it first if you want to start fresh."
    exit 1
fi

# Copy template files
cp .env.example .env
cp scripts/watch_sync.sh.template scripts/watch_sync.sh
cp scripts/sync_control.sh.template scripts/sync_control.sh
cp scripts/sync_wrapper.sh.template scripts/sync_wrapper.sh

# Make scripts executable
chmod +x scripts/watch_sync.sh scripts/sync_control.sh scripts/sync_wrapper.sh

# Copy script templates
cp scripts/sync_wrapper.sh.template scripts/sync_wrapper.sh

# Set permissions
chmod +x scripts/sync_wrapper.sh

# Install cron job
(crontab -l 2>/dev/null | grep -v 'sync_wrapper.sh'; echo "*/5 * * * * cd $PWD && ./scripts/sync_wrapper.sh") | crontab -

echo "Template files have been copied. Please edit .env with your settings."
echo "Required settings:"
echo "  - SYNC_VAULT_ROOT: Path to your Obsidian vault"
echo "  - SYNC_JEKYLL_ROOT: Path to your Jekyll site"
echo "  - SYNC_LOG_DIR: Path for sync logs"
echo ""
echo "Optional settings can be found in .env" 