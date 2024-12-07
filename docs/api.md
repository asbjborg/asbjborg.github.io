# API Documentation

## Table of Contents

1. [Sync Engine](#sync-engine)
2. [File Handler](#file-handler)
3. [Path Converter](#path-converter)
4. [Frontmatter Handler](#frontmatter-handler)
5. [Backup Handler](#backup-handler)

## Sync Engine

### SyncEngine

Main class for handling bidirectional sync between Obsidian and Jekyll.

```python
class SyncEngine:
    def __init__(self, vault_root: str, jekyll_root: str, debug: bool = False, dry_run: bool = False):
        """Initialize sync engine.
        
        Args:
            vault_root: Root directory of Obsidian vault
            jekyll_root: Root directory of Jekyll site
            debug: Enable debug logging
            dry_run: Preview changes without modifying files
        """
        pass
    
    def sync(self) -> None:
        """Run the sync process.
        
        1. Determine files to sync
        2. Handle conflicts based on modification time
        3. Convert and copy files
        4. Update frontmatter
        """
        pass
```

## File Handler

### FileHandler

Handles file operations and directory scanning.

```python
class FileHandler:
    def __init__(self, vault_root: str, jekyll_root: str, debug: bool = False):
        """Initialize file handler.
        
        Args:
            vault_root: Root directory of Obsidian vault
            jekyll_root: Root directory of Jekyll site
            debug: Enable debug logging
        """
        pass
    
    def get_obsidian_files(self) -> Tuple[List[Path], List[Path]]:
        """Get lists of published and draft files from Obsidian vault.
        
        Returns:
            Tuple of (published_files, draft_files)
        """
        pass
    
    def get_jekyll_files(self) -> Tuple[List[Path], List[Path]]:
        """Get lists of posts and assets from Jekyll site.
        
        Returns:
            Tuple of (posts, assets)
        """
        pass
```

## Path Converter

### PathConverter

Converts paths between Obsidian and Jekyll formats.

```python
class PathConverter:
    def __init__(self, vault_root: str, jekyll_root: str, debug: bool = False):
        """Initialize path converter.
        
        Args:
            vault_root: Root directory of Obsidian vault
            jekyll_root: Root directory of Jekyll site
            debug: Enable debug logging
        """
        pass
    
    def obsidian_to_jekyll_post(self, obsidian_path: Path) -> Path:
        """Convert Obsidian post path to Jekyll format.
        
        Args:
            obsidian_path: Path to Obsidian post
            
        Returns:
            Jekyll post path
        """
        pass
    
    def jekyll_to_obsidian_post(self, jekyll_path: Path) -> Path:
        """Convert Jekyll post path to Obsidian format.
        
        Args:
            jekyll_path: Path to Jekyll post
            
        Returns:
            Obsidian post path
        """
        pass
    
    def obsidian_to_jekyll_image(self, wikilink: str, in_frontmatter: bool = False) -> str:
        """Convert Obsidian image wikilink to Jekyll path.
        
        Args:
            wikilink: Obsidian wikilink (e.g., ![[image.png]])
            in_frontmatter: Whether path is in frontmatter
            
        Returns:
            Jekyll image path
        """
        pass
    
    def jekyll_to_obsidian_image(self, jekyll_path: str, post_filename: str, in_frontmatter: bool = False) -> str:
        """Convert Jekyll image path to Obsidian wikilink.
        
        Args:
            jekyll_path: Jekyll image path
            post_filename: Name of post file
            in_frontmatter: Whether path is in frontmatter
            
        Returns:
            Obsidian wikilink
        """
        pass
```

## Frontmatter Handler

### FrontmatterHandler

Handles frontmatter conversion and validation.

```python
class FrontmatterHandler:
    def __init__(self, path_converter, debug: bool = False, dry_run: bool = False):
        """Initialize frontmatter handler.
        
        Args:
            path_converter: PathConverter instance
            debug: Enable debug logging
            dry_run: Preview changes without modifying files
        """
        pass
    
    def obsidian_to_jekyll(self, frontmatter: Dict[str, Any], obsidian_path: Path) -> Dict[str, Any]:
        """Convert Obsidian frontmatter to Jekyll format.
        
        Args:
            frontmatter: Obsidian frontmatter
            obsidian_path: Path to Obsidian file
            
        Returns:
            Jekyll frontmatter
        """
        pass
    
    def jekyll_to_obsidian(self, frontmatter: Dict[str, Any], jekyll_path: Path) -> Dict[str, Any]:
        """Convert Jekyll frontmatter to Obsidian format.
        
        Args:
            frontmatter: Jekyll frontmatter
            jekyll_path: Path to Jekyll file
            
        Returns:
            Obsidian frontmatter
        """
        pass
```

## Backup Handler

### BackupHandler

Handles backup creation and rotation.

```python
class BackupHandler:
    def __init__(self, vault_root: str, jekyll_root: str, debug: bool = False, dry_run: bool = False):
        """Initialize backup handler.
        
        Args:
            vault_root: Root directory of Obsidian vault
            jekyll_root: Root directory of Jekyll site
            debug: Enable debug logging
            dry_run: Preview changes without modifying files
        """
        pass
    
    def backup_pkm(self) -> None:
        """Create backup of PKM files."""
        pass
    
    def backup_jekyll(self) -> None:
        """Create backup of Jekyll files."""
        pass
    
    def backup_all(self) -> None:
        """Create backups of both PKM and Jekyll files."""
        pass
    
    def rotate_backups(self, backup_dir: Path) -> None:
        """Remove old backups keeping only max_backups most recent.
        
        Args:
            backup_dir: Directory containing backups
        """
        pass
```

## Error Classes

### Custom Exceptions

```python
class SyncError(Exception):
    """Base class for sync-related errors."""
    pass

class FilePermissionError(SyncError):
    """Raised when there are permission issues with files."""
    pass

class FileOperationError(SyncError):
    """Raised when file operations fail."""
    pass
```

## Constants

### Environment Variables

```python
PKM_ROOT: str       # Root directory of Obsidian vault
JEKYLL_ROOT: str    # Root directory of Jekyll site
SYNC_DEBUG: bool    # Enable debug logging
SYNC_MAX_BACKUPS: int  # Number of backups to keep
```

### File Paths

```python
OBSIDIAN_POSTS: str = "atomics/**/*.md"      # Obsidian posts glob pattern
JEKYLL_POSTS: str = "_posts/*.md"            # Jekyll posts glob pattern
JEKYLL_ASSETS: str = "assets/img/posts/*"    # Jekyll assets glob pattern
``` 