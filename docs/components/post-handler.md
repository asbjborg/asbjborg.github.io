# Post Handler

## Overview
The Post Handler manages all markdown post operations including frontmatter processing, status management, and path conversions.

## Core Features
- Frontmatter validation and processing
- Post status management (published/draft)
- Path conversion between Obsidian and Jekyll
- Date extraction from paths

## Implementation

### PostHandler Class
```python
class PostHandler:
    """Handles post processing and conversion"""
    
    def get_post_status(self, post: frontmatter.Post) -> Optional[PostStatus]:
        """
        Get post status from frontmatter
        
        Args:
            post: Frontmatter post object
            
        Returns:
            PostStatus if valid, None if not a post
            
        Example:
            >>> post = frontmatter.load('post.md')
            >>> status = handler.get_post_status(post)
            >>> if status == PostStatus.PUBLISHED:
            ...     process_post(post)
        """
        
    def convert_paths(self, content: str, direction: SyncDirection) -> str:
        """
        Convert paths between Obsidian and Jekyll formats
        
        Args:
            content: Post content with paths
            direction: Conversion direction
            
        Returns:
            Content with converted paths
            
        Example:
            >>> content = "![[atomics/2024/01/15/image.png]]"
            >>> jekyll = handler.convert_paths(content, SyncDirection.OBSIDIAN_TO_JEKYLL)
            >>> print(jekyll)
            "/assets/img/posts/image.png"
        """
```

## Post Status

### Status Types
```python
class PostStatus(Enum):
    PUBLISHED = "published"
    DRAFT = "draft"
    PRIVATE = "private"
```

### Status Detection
```python
def get_post_status(post: frontmatter.Post) -> Optional[PostStatus]:
    status = post.get('status')
    if not status:
        return None
        
    try:
        return PostStatus(status.lower())
    except ValueError:
        return None
```

## Path Handling

### Obsidian to Jekyll
```python
# Input: ![[atomics/2024/01/15/image.png]]
# Output: /assets/img/posts/image.png

def convert_to_jekyll(path: str) -> str:
    """Convert Obsidian wikilink to Jekyll path"""
    if not (match := WIKILINK_PATTERN.match(path)):
        return path
        
    image_path = match.group(1)
    return f"/assets/img/posts/{Path(image_path).name}"
```

### Jekyll to Obsidian
```python
# Input: /assets/img/posts/image.png
# Output: ![[atomics/2024/01/15/image.png]]

def convert_to_obsidian(path: str, date_path: str) -> str:
    """Convert Jekyll path to Obsidian wikilink"""
    if not path.startswith('/assets/img/posts/'):
        return path
        
    image_name = Path(path).name
    return f"![[atomics/{date_path}/{image_name}]]"
```

## Frontmatter Processing

### Required Fields
```yaml
---
status: published  # Required: published/draft/private
title: My Post    # Optional but recommended
image: ![[atomics/2024/01/15/cover.png]]  # Optional
modified: 2024-01-15T12:34:56  # Optional, for sync
---
```

### Validation
```python
def validate_frontmatter(post: frontmatter.Post) -> bool:
    """Validate required frontmatter fields"""
    if 'status' not in post:
        return False
        
    try:
        PostStatus(post['status'].lower())
        return True
    except ValueError:
        return False
```

## Usage Examples

### Basic Post Processing
```python
handler = PostHandler()

# Load and validate post
post = frontmatter.load('post.md')
if not handler.validate_frontmatter(post):
    logger.warning("Invalid frontmatter")
    return

# Check status
status = handler.get_post_status(post)
if status != PostStatus.PUBLISHED:
    return  # Skip non-published posts

# Convert paths for Jekyll
content = handler.convert_paths(
    post.content,
    SyncDirection.OBSIDIAN_TO_JEKYLL
)
```

## See Also
- [File Structure](../reference/file-structure.md)
- [Media Handler](media-handler.md) 