# Change Detection

## Overview
The change detection system scans both Obsidian vault and Jekyll site to identify files that need synchronization. It follows the atomic-based approach where all content lives in daily folders.

## Key Features
- Recursively scans `/atomics/YYYY/MM/DD/` folders
- Detects posts by `status: "published"` frontmatter
- Extracts dates from folder paths
- Handles complex filenames and paths
- Validates date folder structure

## Implementation

### ChangeDetector Class
```python
class ChangeDetector:
    """Detects changes between Obsidian vault and Jekyll site"""
    
    def __init__(self, config: Dict):
        """
        Initialize with configuration
        
        Args:
            config: Configuration dictionary with required paths
            
        Required config:
            - vault_root: Path to Obsidian vault
            - jekyll_root: Path to Jekyll site
        """
        
    def detect(self) -> List[SyncState]:
        """
        Scans both Obsidian and Jekyll to detect changes
        
        Returns:
            List[SyncState]: List of changes to sync
        """
```

## Usage Example
```python
detector = ChangeDetector({
    'vault_root': '/path/to/vault',
    'jekyll_root': '/path/to/jekyll'
})

changes = detector.detect()
for change in changes:
    print(f"Change: {change.operation} - {change.source_path}")
```

## Error Handling
The detector handles various error conditions:
- Invalid frontmatter
- Missing files
- Permission issues
- Path validation errors
- Date format errors

## Testing
Test coverage includes:
- Basic post detection
- Complex filename handling
- Error conditions
- Performance with large datasets

See [test_changes.py](../../scripts/sync_engine/tests/test_changes.py) for test cases. 