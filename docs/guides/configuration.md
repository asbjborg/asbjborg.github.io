# Configuration Guide

## Overview
The sync engine uses a flexible configuration system to control its behavior. This guide covers all available options and their usage.

## Configuration Options

### Required Settings
```python
config = {
    'vault_root': '/path/to/vault',     # Obsidian vault root
    'jekyll_root': '/path/to/jekyll',   # Jekyll site root
}
```

### Optional Settings
```python
config = {
    'vault_root': '/path/to/vault',
    'jekyll_root': '/path/to/jekyll',
    'vault_atomics': 'atomics',         # Obsidian atomic notes folder
    'jekyll_posts': '_posts',           # Jekyll posts folder
    'jekyll_assets': 'assets/img/posts',# Jekyll media folder
    'debug': False,                     # Enable debug logging
    'backup_count': 5,                  # Number of backups to keep
    'auto_cleanup': True,               # Auto cleanup old backups
    'max_image_width': 1200,            # Max image width in pixels
    'optimize_images': True             # Enable image optimization
}
```

### Environment Variables
```shell
# Required paths
SYNC_VAULT_ROOT=/path/to/vault
SYNC_JEKYLL_ROOT=/path/to/jekyll

# Optional settings
SYNC_DEBUG=false
SYNC_BACKUP_COUNT=5
SYNC_AUTO_CLEANUP=true
SYNC_MAX_IMAGE_WIDTH=1200
SYNC_OPTIMIZE_IMAGES=true
```

### Validation
The configuration is validated when loaded:
```python
def validate_config(config: Dict) -> None:
    # Check required fields
    required = ['vault_root', 'jekyll_root']
    for field in required:
        if field not in config:
            raise ConfigError(f"Missing required config: {field}")
            
    # Validate paths
    path = Path(config['vault_root'])
    if not path.exists():
        raise ConfigError(f"Vault not found: {path}")
```

### Loading Configuration
```python
# Load from environment
config = ConfigManager.load_from_env()

# Load from dictionary
config = ConfigManager.load_from_dict({
    'vault_root': environ.get('SYNC_VAULT_ROOT'),
    'jekyll_root': environ.get('SYNC_JEKYLL_ROOT'),
    'debug': True
})

# Override settings
vault_root = Path(config['vault_root'])
if not vault_root.exists():
    raise ValueError(f"Vault not found: {vault_root}")

config = ConfigManager.load_from_dict({
    'vault_root': vault_root,   # Override as needed
    'jekyll_root': jekyll_root,
    'debug': True
})
```

## Usage Examples

### Minimal Configuration
```python
from sync_engine.core.sync import SyncManager

config = {
    'vault_root': '/path/to/vault',
    'jekyll_root': '/path/to/jekyll'
}

manager = SyncManager(config)  # Uses defaults for other settings
```

### Custom Settings
```python
config = {
    'vault_root': '/path/to/vault',
    'jekyll_root': '/path/to/jekyll',
    'backup_count': 10,                 # Keep more backups
    'optimize_images': False,           # Disable optimization
    'max_image_width': 1600            # Allow larger images
}
```

## Best Practices

1. Always validate paths:
```python
vault_root = Path(config['vault_root'])
if not vault_root.exists():
    raise ValueError(f"Vault not found: {vault_root}")
```

2. Use environment variables for sensitive paths:
```python
from os import environ

config = {
    'vault_root': environ.get('VAULT_ROOT'),
    'jekyll_root': environ.get('JEKYLL_ROOT')
}
```

3. Set reasonable defaults:
```python
config = {
    **DEFAULT_CONFIG,           # Start with defaults
    'vault_root': vault_root,   # Override as needed
    'optimize_images': False    # Override specific settings
}
```

## Common Issues

### Path Issues
- Relative vs absolute paths
- Permission problems
- Missing directories

### Value Issues
- Invalid backup counts
- Invalid image dimensions
- Boolean parsing from env vars

## See Also
- [File Structure](../reference/file-structure.md)
- [Usage Guide](usage.md) 