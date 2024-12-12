# Implementation Details

This document covers the technical implementation details of the sync system.

## Platform Support

### Unix-based Systems
The system is primarily designed for and tested on Unix-based systems (macOS and Linux). All scripts and tools are developed with Unix compatibility in mind.

### Windows Compatibility
While the core Python code is platform-agnostic, the shell scripts and file watching mechanism are Unix-specific. Windows users should:

1. Use WSL2 (Recommended)
   - Provides full Unix compatibility
   - All features work as designed
   - No code modifications needed

2. Native Windows (Unsupported)
   - Would require:
     - PowerShell/batch script equivalents
     - Alternative to fswatch (e.g., watchdog)
     - Path handling modifications
   - Not officially supported or tested

## Project Structure

```
.
├── docs/                  # Documentation
├── scripts/
│   ├── core/             # Core functionality
│   ├── sync/             # Sync implementation
│   ├── utils/            # Utility functions
│   ├── setup.sh          # Initial setup script
│   ├── *.sh.template     # Script templates
│   └── sync.py          # Main sync script
├── tests/                # Test files
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
└── .venv/               # Virtual environment (generated)
```

## Python Environment

### Virtual Environment

The system uses a Python virtual environment to ensure dependency isolation and consistent execution:

1. Structure
   - `.venv/`: Virtual environment directory (git-ignored)
   - `requirements.txt`: Pinned dependencies
   - `SYNC_PYTHON_PATH`: Points to venv interpreter

2. Benefits
   - Isolated dependencies
   - Consistent execution environment
   - No conflicts with system Python
   - Reproducible setup across installations

3. Dependencies
   - Core dependencies in `requirements.txt`
   - Development dependencies separated
   - Version pins for stability

## Configuration Management

### Environment Variables

The system uses environment variables for configuration, stored in `.env`. The setup process:

1. Templates
   - `.env.example`: Template for environment variables
   - `scripts/*.sh.template`: Template shell scripts
   - All personal paths and settings stay in `.env`

2. Setup Process
   - `setup.sh` creates local copies from templates
   - Generated files are git-ignored
   - Each installation has its own local configuration

3. Required Variables
   ```bash
   SYNC_VAULT_ROOT      # Obsidian vault location
   SYNC_JEKYLL_ROOT     # Jekyll site location
   SYNC_LOG_DIR         # Log file location
   ```

4. Optional Variables
   ```bash
   SYNC_VAULT_ATOMICS   # Obsidian sync folder
   SYNC_JEKYLL_POSTS    # Jekyll posts folder
   SYNC_JEKYLL_ASSETS   # Jekyll assets folder
   SYNC_DEBUG           # Debug output toggle
   SYNC_LOG             # Operation logging toggle
   SYNC_INTERVAL        # Sync batch interval
   SYNC_PYTHON_PATH     # Custom Python interpreter
   ```

## Sync Process

### Watch Script (`watch_sync.sh`)

1. Environment Loading
   - Sources `.env` for configuration
   - Sets default values for optional variables
   - Creates required directories

2. Process Management
   - Maintains PID file for single instance
   - Handles cleanup on exit
   - Manages sync interval timing

3. Change Detection
   - Uses fswatch to monitor Obsidian
   - Records changes to pending file
   - Batches changes for efficiency

### Control Script (`sync_control.sh`)

1. Commands
   - start: Launches watch process
   - stop: Terminates watch process
   - restart: Full process restart
   - status: Shows current state

2. Process Handling
   - PID file management
   - Clean process termination
   - Status verification

### Wrapper Script (`sync_wrapper.sh`)

1. Purpose
   - Provides clean Python execution
   - Handles environment setup
   - Manages working directory

2. Configuration
   - Uses configured Python path
   - Sets up environment
   - Calls main sync script

## File Management

### Generated Files

The following files are generated locally and git-ignored:

1. Configuration
   - `.env`: Local settings
   - Generated shell scripts
   - `.venv/`: Virtual environment

2. Runtime Files
   - `.watch.pid`: Process ID
   - `.last_sync`: Timestamp
   - `.pending_changes`: Change queue

3. Logs
   - `watch.log`: Main log
   - `watch.error.log`: Error log

## Development Guidelines

### Adding New Features

1. Template Updates
   - Modify `.env.example` for new variables
   - Update script templates if needed
   - Document in implementation.md

2. Script Changes
   - Keep templates and scripts in sync
   - Test with setup.sh process
   - Verify git-ignore patterns

3. Python Changes
   - Test in clean virtual environment
   - Update requirements.txt if needed
   - Document new dependencies

### Testing

1. Setup Testing
   ```bash
   # Clean start
   rm -rf .env scripts/watch_sync.sh scripts/sync_control.sh scripts/sync_wrapper.sh .venv
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ./scripts/setup.sh
   ```

2. Configuration Test
   ```bash
   # Verify environment
   source .env && $SYNC_PYTHON_PATH scripts/sync.py
   ```

3. Watch Process Test
   ```bash
   ./scripts/sync_control.sh start
   ./scripts/sync_control.sh status
   ./scripts/sync_control.sh stop
   ```

## Troubleshooting

### Common Development Issues

1. Template Sync
   - Keep templates updated with changes
   - Test setup.sh regularly
   - Verify git-ignore patterns

2. Process Management
   - Check PID file handling
   - Verify cleanup procedures
   - Test process termination

3. Configuration
   - Test with minimal .env
   - Verify default values
   - Check path handling

4. Python Environment
   - Verify virtual environment activation
   - Check dependency installation
   - Confirm Python path in .env
   - Test with clean venv if issues persist