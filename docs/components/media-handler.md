# Media Handler

## Overview
The Media Handler manages all media file operations including path resolution, file copying, and image optimization. It ensures media files stay with their posts in daily folders.

## Core Features
- Media file detection and validation
- Path resolution and conversion
- Image optimization
- Unused media cleanup
- Bidirectional sync of media files

## Implementation

### MediaHandler Class
```python
class MediaHandler:
    """Handles media file operations and path conversions"""
    
    def __init__(self, config: Dict):
        """
        Initialize media handler
        
        Args:
            config: Configuration dictionary
            
        Required config:
            - vault_root: Obsidian vault root
            - jekyll_root: Jekyll site root
            - jekyll_assets: Jekyll assets path
            - optimize_images: Whether to optimize images
            - max_image_width: Maximum image width
        """
        
    def extract_media_refs(self, content: str) -> Set[Path]:
        """
        Extract media references from content
        
        Args:
            content: Markdown content with wikilinks
            
        Returns:
            Set of referenced media paths
            
        Example:
            >>> content = "![[atomics/2024/01/15/image.png]]"
            >>> refs = handler.extract_media_refs(content)
            >>> print(refs)
            {PosixPath('atomics/2024/01/15/image.png')}
        """
        
    def sync_media(self, refs: Set[Path], date_path: str) -> Dict[Path, Path]:
        """
        Sync media files to Jekyll
        
        Args:
            refs: Set of media paths to sync
            date_path: YYYY/MM/DD path for context
            
        Returns:
            Dict mapping source paths to target paths
        """
```

## Media Detection

### Reference Patterns
```python
WIKILINK_PATTERN = re.compile(r'!\[\[(.*?)\]\]')
MARKDOWN_PATTERN = re.compile(r'!\[.*?\]\((.*?)\)')
```

### Reference Extraction
```python
def extract_refs(content: str) -> Set[Path]:
    """Extract all media references from content"""
    refs = set()
    
    # Extract wikilinks
    for match in WIKILINK_PATTERN.finditer(content):
        refs.add(Path(match.group(1)))
        
    # Extract markdown links
    for match in MARKDOWN_PATTERN.finditer(content):
        refs.add(Path(match.group(1)))
        
    return refs
```

## Path Handling

### Obsidian Paths
- All media lives with its post in daily folders
- Use absolute vault paths: `![[atomics/YYYY/MM/DD/image.png]]`
- Original filenames preserved

### Jekyll Paths
- Media moved to assets folder
- Web-friendly paths: `/assets/img/posts/image.png`
- Filenames sanitized

### Path Resolution
```python
def resolve_media_path(ref: Path, date_path: str) -> Path:
    """Resolve media path relative to post date"""
    if ref.is_absolute():
        return ref
        
    # Relative path - use post's date folder
    return Path('atomics') / date_path / ref.name
```

## Image Processing

### Optimization
```python
def optimize_image(source: Path, target: Path):
    """Optimize image for web"""
    if not self.config['optimize_images']:
        shutil.copy2(source, target)
        return
        
    with Image.open(source) as img:
        # Resize if needed
        if img.width > self.config['max_image_width']:
            ratio = self.config['max_image_width'] / img.width
            new_size = (
                self.config['max_image_width'],
                int(img.height * ratio)
            )
            img = img.resize(new_size, Image.LANCZOS)
            
        # Save optimized
        img.save(target, optimize=True, quality=85)
```

### File Types
```python
SUPPORTED_TYPES = {
    '.jpg', '.jpeg', '.png', '.gif', '.webp'
}

def is_supported(path: Path) -> bool:
    """Check if file type is supported"""
    return path.suffix.lower() in SUPPORTED_TYPES
```

## Usage Examples

### Basic Media Sync
```python
handler = MediaHandler(config)

# Extract refs from post
content = post_path.read_text()
refs = handler.extract_media_refs(content)

# Sync media files
date_path = "2024/01/15"  # From post path
path_map = handler.sync_media(refs, date_path)

# Update content with new paths
for old_path, new_path in path_map.items():
    content = content.replace(str(old_path), str(new_path))
```

### Cleanup Unused Media
```python
def cleanup_unused(self, used_refs: Set[Path]):
    """Remove unused media files from Jekyll"""
    assets = Path(self.config['jekyll_root']) / self.config['jekyll_assets']
    
    for file in assets.glob('*'):
        if file.is_file() and file not in used_refs:
            file.unlink()
```

## See Also
- [File Structure](../reference/file-structure.md)
- [Post Handler](post-handler.md) 