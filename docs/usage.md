# Usage Guide

This guide covers the setup and usage of the sync system. For technical details and implementation information, see [Implementation Details](implementation.md).

## System Requirements

### Unix-based Systems (macOS/Linux)

- Python 3.8 or higher
- fswatch (`brew install fswatch` on macOS, available in most Linux package managers)
- zsh or bash shell

### Windows Users

This system is designed for Unix-based systems. Windows users have two options:

1. Recommended: Use WSL2 (Windows Subsystem for Linux)
   - Install WSL2 following [Microsoft's instructions](https://learn.microsoft.com/en-us/windows/wsl/install)
   - Install Ubuntu or another Linux distribution
   - Follow the Unix-based setup instructions within WSL2
   - Mount your Obsidian vault in WSL2 if needed

2. Alternative: Native Windows (Limited Support)
   - Native Windows support is not officially supported
   - Scripts would need manual conversion to PowerShell/batch
   - File watching would need alternative implementation
   - Use at your own risk

## Initial Setup

### 1. Python Environment

First, create and activate a virtual environment:

```bash
# Create virtual environment
python -m venv .venv

# Activate it (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration Setup

1. Run the setup script to create your local configuration:

   ```bash
   ./scripts/setup.sh
   ```

   This will:
   - Copy `.env.example` to `.env`
   - Create local script copies from templates
   - Make scripts executable

2. Edit `.env` with your settings:

   ```bash
   # Required Configuration
   SYNC_VAULT_ROOT="/path/to/your/obsidian/vault"
   SYNC_JEKYLL_ROOT="/path/to/your/jekyll/site"
   SYNC_LOG_DIR="/path/to/your/log/directory"
   
   # Important: Set Python path to your virtual environment
   SYNC_PYTHON_PATH="/full/path/to/your/.venv/bin/python"
   ```

3. Optional settings in `.env`:

   ```bash
   # Optional Paths
   SYNC_VAULT_ATOMICS="atomics"        # Obsidian folder to sync
   SYNC_JEKYLL_POSTS="_posts"          # Jekyll posts folder
   SYNC_JEKYLL_ASSETS="assets/img/posts" # Jekyll assets folder

   # Debug and Log Modes
   SYNC_DEBUG=false                    # Enable full debug output
   SYNC_LOG=true                       # Enable operation logging

   # Script Configuration
   SYNC_INTERVAL=300                   # Sync interval in seconds
   ```

### 3. Verify Setup

Test your configuration:

```bash
# Verify Python environment
$SYNC_PYTHON_PATH --version  # Should show Python version

# Test sync script
$SYNC_PYTHON_PATH scripts/sync.py
```

## Automated Sync

The site includes an automated sync system that watches for changes in your Obsidian vault and syncs them to Jekyll.

### Prerequisites

1. Install fswatch (required for file watching):

   ```bash
   brew install fswatch
   ```

### Control Commands

The sync process can be controlled using `sync_control.sh`:

```bash
# Start the sync watch process
./scripts/sync_control.sh start

# Stop the sync watch process
./scripts/sync_control.sh stop

# Restart the sync watch process
./scripts/sync_control.sh restart

# Check sync process status
./scripts/sync_control.sh status
```

### How It Works

1. File Watching
   - Monitors the Obsidian vault's `atomics` folder for changes
   - Detects when markdown files are created, updated, or deleted
   - Records all changes as they happen

2. Batch Processing
   - Changes are collected and batched together
   - Every 5 minutes, if there are changes, they're synced in one operation
   - You can work continuously without interruption

3. Logging
   - All operations are logged to `LOGS/watch.log`
   - Errors are logged to `LOGS/watch.error.log`
   - Each sync shows what files were included

### Log Files

The sync system maintains several log files:

1. `watch.log`: Main operation log showing:
   - Change detections
   - Sync operations
   - Files included in each sync
   - Timing information

2. `watch.error.log`: Error and debug information

3. `.pending_changes`: Temporary file tracking changes waiting to be synced

### Manual Sync

If needed, you can still run a manual sync:

```bash
source .env && python scripts/sync.py
```

For debug output:

```bash
source .env && SYNC_DEBUG=true python scripts/sync.py
```

## Troubleshooting

### Common Issues

1. "Already running" message
   - Use `sync_control.sh status` to check the process
   - Use `sync_control.sh restart` to restart if needed

2. No changes being detected
   - Check if fswatch is installed: `which fswatch`
   - Verify the vault path in `.env`
   - Check the watch log for errors

3. Changes not syncing
   - Changes are batched every 5 minutes
   - Check `watch.log` for pending changes
   - Verify file permissions in both directories

### Log Analysis

To monitor sync activity:

```bash
# Watch the main log
tail -f LOGS/watch.log

# Check for errors
tail -f LOGS/watch.error.log

# See pending changes
cat LOGS/.pending_changes
```

For any other issues, check the logs in `LOGS/` directory for detailed error messages.
