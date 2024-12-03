#!/bin/bash

# Navigate to the blog directory
cd "$(dirname "$0")/.." || exit

# Activate virtual environment
source .venv/bin/activate

# Run the sync script
python scripts/sync_obsidian.py

# Check if there are any changes
if [[ -n $(git status -s) ]]; then
    # Add all changes in _posts directory
    git add _posts/

    # Count number of changed files in _posts directory
    changed_files=$(git status --porcelain _posts/ | wc -l | tr -d ' ')

    # Only proceed if we have changes in _posts
    if [ "$changed_files" -gt 0 ]; then
        # Commit with timestamp
        git commit -m "feat: sync blog posts $(date '+%Y-%m-%d %H:%M:%S')"

        # Push to main
        git push origin main

        # Show notification using AppleScript
        osascript -e "display notification \"$changed_files files synced to blog\" with title \"Blog Sync\" sound name \"Glass\""
        
        # Open posts directory
        open _posts/
    fi
fi 