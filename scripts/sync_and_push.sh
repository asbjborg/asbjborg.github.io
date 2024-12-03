#!/bin/bash

# Navigate to the blog directory
cd "$(dirname "$0")/.." || exit

# Activate virtual environment
source .venv/bin/activate

# Run the sync script
python scripts/sync_obsidian.py

# Check if there are any changes
if [[ -n $(git status -s) ]]; then
    # Add all changes in _posts directory and assets directory
    git add _posts/ assets/

    # Count number of changed files
    changed_files=$(git status --porcelain _posts/ assets/ | wc -l | tr -d ' ')

    # Only proceed if we have changes
    if [ "$changed_files" -gt 0 ]; then
        # Get current branch
        current_branch=$(git rev-parse --abbrev-ref HEAD)

        # Commit with timestamp
        git commit -m "feat: sync blog posts $(date '+%Y-%m-%d %H:%M:%S')"

        # Push to current branch
        git push origin "$current_branch"

        # Show notification using AppleScript
        osascript -e "display notification \"$changed_files files synced to blog\" with title \"Blog Sync\" sound name \"Glass\""
        
        # Open log file
        open ~/Library/Logs/obsidian-blog-sync.log
    fi
fi 