# Configuration Guide

## Overview
The sync engine uses a flexible configuration system to control its behavior. This guide covers all available options and their usage.

## Basic Configuration

### Required Settings
```python
config = {
    'vault_root': '/path/to/vault',     # Obsidian vault root
    'jekyll_root': '/path/to/jekyll'    # Jekyll site root
}
```

### Default Values
```python
DEFAULT_CONFIG = {
    # Directory Settings
    'atomics_root': 'atomics',          # Root for atomic notes
    'jekyll_posts': '_posts',           # Jekyll posts directory
    'jekyll_assets': 'assets/img/posts', # Jekyll media directory
    
    # Sync Settings
    'backup_count': 5,                  # Number of backups to keep
    'auto_cleanup': True,               # Remove unused media
    
    # Media Settings
    'max_image_width': 1200,            # Max image width
    'optimize_images': True             # Enable image optimization
}
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

## Environment Variables
The engine also checks for environment variables:

```bash
# Required paths
VAULT_ROOT=/path/to/vault
JEKYLL_ROOT=/path/to/jekyll

# Optional settings
BACKUP_COUNT=5
AUTO_CLEANUP=true
OPTIMIZE_IMAGES=true
MAX_IMAGE_WIDTH=1200
```

## Configuration Validation

### Required Fields
- `vault_root`: Must exist and be readable
- `jekyll_root`: Must exist and be writable

### Optional Fields
- `backup_count`: Integer > 0
- `max_image_width`: Integer > 0
- `auto_cleanup`: Boolean
- `optimize_images`: Boolean

### Example Validation
```python
def validate_config(config: Dict) -> bool:
    """Validate configuration settings"""
    required = ['vault_root', 'jekyll_root']
    for key in required:
        if key not in config:
            raise ValueError(f"Missing required config: {key}")
        
    path = Path(config['vault_root'])
    if not path.exists():
        raise ValueError(f"Vault path does not exist: {path}")
    
    return True
```

## Best Practices

1. Always validate paths:
```python
vault_path = Path(config['vault_root'])
if not vault_path.exists():
    raise ValueError(f"Vault not found: {vault_path}")
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
    'vault_root': vault_path,   # Override as needed
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