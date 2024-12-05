# Sync Engine Documentation

## Overview
The sync engine manages bidirectional synchronization between an Obsidian vault and a Jekyll blog. It follows a strict atomic-based approach where all content lives in daily folders under the atomics directory.

## Core Components

### 1. Change Detection (`changes.py`)
Handles detection of changes between Obsidian and Jekyll.

```python
class ChangeDetector:
    """Detects changes between Obsidian vault and Jekyll site"""
    
    def detect(self) -> List[SyncState]:
        """
        Scans both Obsidian and Jekyll to detect changes
        
        Returns:
            List[SyncState]: List of changes to sync
        
        Example:
            detector = ChangeDetector(config)
            changes = detector.detect()
        """
```

Key Features:
- Recursively scans `/atomics/YYYY/MM/DD/` folders
- Detects posts by `status: "published"` frontmatter
- Extracts dates from folder paths
- Handles complex filenames and paths
- Validates date folder structure

### 2. Atomic Operations (`atomic.py`)
Manages safe file operations with backup and rollback capabilities.

```python
class AtomicManager:
    """Handles atomic file operations with backup/rollback"""
    
    def execute(self, operation: SyncOperation) -> bool:
        """
        Executes an operation with automatic backup/rollback
        
        Args:
            operation: Operation to execute
            
        Returns:
            bool: Success status
        """
```

### 3. Post Handler (`post.py`)
Processes markdown posts and their frontmatter.

### 4. Media Handler (`media.py`)
Manages media files and their references.

## File Structure

```
/PKM
    /atomics                    # All atomic notes
        /2024
            /12
                /03            # All files for December 3rd
                    /my first post.md              # Blog post
                    /Pasted image 20241203214844.png  # Image
```

## Configuration

```python
DEFAULT_CONFIG = {
    'jekyll_posts': '_posts',
    'jekyll_assets': 'assets/img/posts',
    'atomics_root': 'atomics',
    'backup_count': 5,
    'auto_cleanup': True,
    'max_image_width': 1200,
    'optimize_images': True
}
```

## Usage Examples

### Basic Sync
```python
from sync_engine.core.sync import SyncManager

config = {
    'vault_root': '/path/to/vault',
    'jekyll_root': '/path/to/jekyll'
}

manager = SyncManager(config)
manager.sync()
```

### Custom Configuration
```python
config = {
    'vault_root': '/path/to/vault',
    'jekyll_root': '/path/to/jekyll',
    'backup_count': 10,
    'optimize_images': False
}

manager = SyncManager(config)
```

## Error Handling

The engine handles various error conditions:
- Invalid frontmatter
- Missing files
- Permission issues
- Path validation errors
- Date format errors

## Performance Considerations

- Scans are recursive but date-folder validated
- Image optimization is configurable
- Backup retention is configurable
- Large vaults (>1000 files) tested

## Testing

Test coverage includes:
- Basic operations
- Complex scenarios
- Error handling
- Performance testing

Run tests with:
```bash
pytest scripts/sync_engine/tests/
``` 