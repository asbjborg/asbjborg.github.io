# Usage Guide

## Quick Start

### 1. Installation
```bash
# Clone the repository
git clone https://github.com/asbjborg/obsidian-blog-sync.git
cd obsidian-blog-sync

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file in your project root:
```bash
# Required paths
SYNC_VAULT_ROOT=/path/to/your/vault
SYNC_JEKYLL_ROOT=/path/to/your/jekyll

# Optional settings (showing defaults)
SYNC_VAULT_ATOMICS=atomics
SYNC_JEKYLL_POSTS=_posts
SYNC_JEKYLL_ASSETS=assets/img/posts
SYNC_DEBUG=false
SYNC_AUTO_CLEANUP=true
```

### 3. Basic Usage
```python
from sync_engine.core.sync import SyncManager

# Initialize with environment variables
manager = SyncManager()

# Run sync
manager.sync()
```

## Common Tasks

### Publishing a Post
1. Create a note in your daily folder (e.g., `/atomics/2024/01/15/my-post.md`)
2. Add required frontmatter:
   ```yaml
   ---
   status: "published"  # Makes this a blog post
   title: "My First Post"
   tags:
       - tag1
       - tag2
   ---
   ```
3. Run sync - it will appear in Jekyll's `_posts` folder

### Adding Images
1. Add images to the same daily folder as your post
2. Reference them using absolute vault paths:
   ```markdown
   ![Image description](![[atomics/2024/01/15/image.png]])
   ```
3. Run sync - images are automatically:
   - Copied to Jekyll's assets folder
   - Paths converted for web
   - Optimized if enabled

### Working with Drafts
1. Use `status: "draft"` in frontmatter
2. Draft posts are:
   - Ignored during sync by default
   - Can be included with `sync_drafts=True`
   - Never deleted from Jekyll if exists

### Manual Sync
```python
# Sync specific files
manager.sync_file('/path/to/post.md')

# Sync with options
manager.sync(
    sync_drafts=True,  # Include draft posts
    force=True,        # Force update all files
    dry_run=True       # Preview changes without writing
)
```

## Advanced Usage

### Custom Configuration
```python
config = {
    'vault_root': '/path/to/vault',
    'jekyll_root': '/path/to/jekyll',
    'backup_count': 10,                 # Keep more backups
    'optimize_images': False,           # Disable optimization
    'max_image_width': 1600            # Allow larger images
}

manager = SyncManager(config)
```

### Error Recovery
```python
try:
    manager.sync()
except Exception as e:
    # Last operation rolled back automatically
    print(f"Sync failed: {e}")
    
    # List available backups
    backups = manager.atomic.list_backups()
    
    # Restore specific backup if needed
    manager.atomic.restore_backup(backups[-1])
```

### Cleanup Operations
```python
# Clean up unused media and old backups
manager.cleanup()

# Just clean old backups
manager.atomic.cleanup_backups(keep=5)
```

## Best Practices

### File Organization
- Keep posts in daily folders: `/atomics/YYYY/MM/DD/`
- Keep images with their posts
- Use descriptive filenames
- Use absolute vault paths in links

### Frontmatter
- Always include `status` field
- Use consistent date format
- Keep metadata minimal
- Use quotes for strings with special chars

### Sync Strategy
- Run sync frequently (e.g., every 5 minutes)
- Keep backups (default: last 5)
- Clean up regularly
- Monitor logs for issues

## Troubleshooting

### Common Issues
1. **Missing Files**
   - Check file permissions
   - Verify paths in .env
   - Check for typos in paths

2. **Sync Conflicts**
   - Latest version wins by default
   - Check file timestamps
   - Use force=True to override

3. **Image Issues**
   - Verify absolute vault paths
   - Check image exists in same folder
   - Verify image permissions

### Getting Help
- Check error messages in logs
- Enable debug mode for more info:
  ```python
  manager = SyncManager({'debug': True})
  ```
- Review backup history if needed

## See Also
- [Configuration Guide](configuration.md) - Detailed config options
- [Error Handling](error-handling.md) - Error handling details
- [File Structure](../reference/file-structure.md) - File organization 