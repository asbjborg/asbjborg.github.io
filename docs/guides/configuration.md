# Configuration Guide

## Overview
The sync engine can be configured through environment variables or a configuration dictionary.

## Configuration Options

### Required Settings
- `vault_root`: Path to Obsidian vault root
- `jekyll_root`: Path to Jekyll site root

### Optional Settings

#### Path Settings
- `vault_atomics`: Subfolder for atomic notes (default: 'atomics')
- `jekyll_posts`: Jekyll posts folder (default: '_posts')
- `jekyll_assets`: Jekyll assets folder (default: 'assets/img/posts')

#### Behavior Settings
- `debug`: Enable debug logging (default: False)
- `continue_on_error`: Continue on non-critical errors (default: False)
- `auto_cleanup`: Enable automatic cleanup (default: True)
- `validate_paths`: Validate and create paths (default: True)
- `cleanup_delay`: Delay in seconds before cleanup (default: 0.0)
  - Set to 0 for immediate cleanup
  - Set > 0 to delay cleanup (e.g., 0.5 for half second)
  - Useful for testing and verification
  - Cleanup runs in background thread if delayed

#### Media Settings
- `optimize_images`: Enable image optimization (default: True)
- `max_image_width`: Maximum image width (default: 1200)

#### Backup Settings
- `backup_count`: Number of backups to keep (default: 5)
- `backup_dir`: Backup directory name (default: '.atomic_backups')

## Environment Variables
```bash
# Required
export SYNC_VAULT_ROOT="/path/to/vault"
export SYNC_JEKYLL_ROOT="/path/to/jekyll"

# Optional
export SYNC_DEBUG=true
export SYNC_AUTO_CLEANUP=true
export SYNC_CLEANUP_DELAY=0.5  # Half second delay
```

## Dictionary Configuration
```python
config = {
    'vault_root': '/path/to/vault',
    'jekyll_root': '/path/to/jekyll',
    'debug': True,
    'auto_cleanup': True,
    'cleanup_delay': 0.5  # Half second delay
}
manager = SyncManager(config)
```

## Best Practices

### Cleanup Configuration
- For production: Use default immediate cleanup
- For testing: Set cleanup_delay > 0
- For debugging: Disable auto_cleanup
- Monitor cleanup logs for issues

### Path Configuration
- Use absolute paths when possible
- Verify paths exist before sync
- Keep paths consistent across systems

### Debug Configuration
- Enable debug logging during setup
- Use continue_on_error for testing
- Validate paths during development

## See Also
- [Usage Guide](usage.md)
- [Error Handling](error-handling.md)
- [Testing Guide](../reference/testing.md) 