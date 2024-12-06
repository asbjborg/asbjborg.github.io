"""Post handler module"""

import logging
import frontmatter
from pathlib import Path
from typing import Optional, Dict, Union
import re
from datetime import datetime
import yaml

from ..core.types import PostStatus, SyncDirection
from ..core.config import SyncConfig

logger = logging.getLogger(__name__)

class PostHandler:
    """Handles post processing and status management"""
    
    def __init__(self, config: SyncConfig):
        """Initialize post handler with config"""
        self.config = config
    
    def process(self, source_path: Path, target_path: Path, direction: SyncDirection = SyncDirection.OBSIDIAN_TO_JEKYLL) -> str:
        """
        Process a post file
        
        Args:
            source_path: Source file path
            target_path: Target file path
            direction: Sync direction
            
        Returns:
            Processed content as string
            
        Raises:
            ValueError: If file cannot be read or processed
        """
        try:
            # Read source file
            with open(source_path) as f:
                post = frontmatter.load(f)
                
            # Process based on direction
            if direction == SyncDirection.OBSIDIAN_TO_JEKYLL:
                processed = self.process_for_jekyll(post)
            else:
                processed = self.process_for_obsidian(post)
                
            # Return as string
            return frontmatter.dumps(processed)
            
        except Exception as e:
            logger.error(f"Error processing post {source_path}: {e}")
            raise ValueError(f"Failed to process post: {e}")
    
    def get_post_status(self, post: frontmatter.Post) -> PostStatus:
        """
        Get post status from frontmatter
        
        Args:
            post: Post to check
            
        Returns:
            PostStatus enum value
        """
        try:
            status = post.get('status', 'published').lower()
            if status == 'draft':
                return PostStatus.DRAFT
            elif status == 'private':
                return PostStatus.PRIVATE
            else:
                return PostStatus.PUBLISHED
                
        except Exception as e:
            logger.error(f"Error getting post status: {e}")
            return PostStatus.PUBLISHED
    
    def extract_frontmatter(self, content_or_path: Union[str, Path]) -> Optional[Dict]:
        """
        Extract frontmatter from content or file
        
        Args:
            content_or_path: Content string or file path
            
        Returns:
            Dict of frontmatter or None if not found
        """
        try:
            # If it's a Path, read the file
            if isinstance(content_or_path, Path):
                with open(content_or_path) as f:
                    content = f.read()
            else:
                content = content_or_path
                
            # Parse frontmatter
            try:
                # First try with python-frontmatter
                post = frontmatter.loads(content)
                return post.metadata if post.metadata else None
            except:
                # If that fails, try with PyYAML directly
                import yaml
                # Extract YAML between --- markers
                if content.startswith('---\n'):
                    end = content.find('\n---\n', 4)
                    if end != -1:
                        yaml_str = content[4:end]
                        try:
                            return yaml.safe_load(yaml_str)
                        except:
                            pass
                return None
            
        except Exception as e:
            logger.error(f"Error reading file {content_or_path}: {e}")
            return None
    
    def process_for_jekyll(self, post: frontmatter.Post) -> frontmatter.Post:
        """
        Process post for Jekyll compatibility
        
        Args:
            post: Post to process
            
        Returns:
            Processed post
        """
        try:
            # Create copy of post
            processed = frontmatter.Post(
                content=post.content,
                **post.metadata
            )
            
            # Convert Obsidian image links to Jekyll format in content
            content = processed.content
            content = content.replace('![[', '![](')
            content = content.replace(']]', ')')
            content = content.replace(f"{self.config.vault_atomics}/", '/assets/img/posts/')
            processed.content = content
            
            # Update frontmatter
            for key, value in processed.metadata.items():
                if isinstance(value, str):
                    if '[[' in value and ']]' in value:
                        # Convert wikilinks in frontmatter (no ! prefix needed)
                        value = value.replace('[[', '![](')
                        value = value.replace(']]', ')')
                        value = value.replace(f"{self.config.vault_atomics}/", '/assets/img/posts/')
                        # Remove any quotes around the link
                        value = value.strip('"')
                        processed.metadata[key] = value
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing post for Jekyll: {e}")
            raise
    
    def process_for_obsidian(self, post: frontmatter.Post) -> frontmatter.Post:
        """
        Process post for Obsidian compatibility
        
        Args:
            post: Post to process
            
        Returns:
            Processed post
        """
        try:
            # Create copy of post
            processed = frontmatter.Post(
                content=post.content,
                **post.metadata
            )
            
            # Convert Jekyll image links to Obsidian format in content
            content = processed.content
            content = content.replace('/assets/img/posts/', f"{self.config.vault_atomics}/")
            content = content.replace('![', '![[')
            content = content.replace(')', ']]')
            processed.content = content
            
            # Update frontmatter
            for key, value in processed.metadata.items():
                if isinstance(value, str):
                    if '/assets/img/posts/' in value:
                        # Convert image links in frontmatter (no ! prefix)
                        value = value.replace('/assets/img/posts/', f"{self.config.vault_atomics}/")
                        value = value.replace('![', '[[')  # No ! prefix in frontmatter
                        value = value.replace(')', ']]')
                        # Add quotes around the link
                        if not value.startswith('"'):
                            value = f'"{value}"'
                        processed.metadata[key] = value
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing post for Obsidian: {e}")
            raise
    
    def _process_frontmatter(self, content: str) -> str:
        """Process frontmatter in content"""
        try:
            # Extract frontmatter
            if content.startswith('---\n'):
                end = content.find('\n---\n', 4)
                if end != -1:
                    yaml_str = content[4:end]
                    rest = content[end+5:]
                    
                    # Fix image references in frontmatter
                    yaml_str = re.sub(r'!(\[\[.*?\]\])', r'"\1"', yaml_str)
                    yaml_str = re.sub(r'(\[\[.*?\]\])', r'"\1"', yaml_str)
                    
                    # Parse YAML
                    try:
                        metadata = yaml.safe_load(yaml_str)
                    except yaml.YAMLError as e:
                        logger.error(f"Failed to parse frontmatter: {e}")
                        metadata = {}
                        
                    # Update metadata
                    metadata['status'] = metadata.get('status', 'draft')
                    metadata['last_modified'] = datetime.now().isoformat()
                    
                    # Convert back to YAML
                    new_yaml = yaml.dump(metadata, default_flow_style=False)
                    return f"---\n{new_yaml}---\n{rest}"
                    
            return content
            
        except Exception as e:
            logger.error(f"Failed to process frontmatter: {e}")
            return content
    
    def get_jekyll_path(self, source_path: Path, jekyll_root: Path = None) -> Path:
        """
        Convert Obsidian path to Jekyll path
        
        Args:
            source_path: Source file path in Obsidian
            jekyll_root: Optional Jekyll root path (uses config if not provided)
            
        Returns:
            Path object for Jekyll target path
            
        Example:
            atomics/2024/01/15/my post.md -> _posts/2024-01-15-my-post.md
        """
        try:
            if jekyll_root is None:
                jekyll_root = self.config.jekyll_root
                
            # Extract date from path (YYYY/MM/DD)
            parts = list(source_path.parts)
            date_parts = []
            
            # Find the date parts in the path
            for i, part in enumerate(parts):
                if re.match(r'^\d{4}$', part):  # Year
                    if i+2 < len(parts):  # Make sure we have month and day
                        if re.match(r'^\d{2}$', parts[i+1]) and re.match(r'^\d{2}$', parts[i+2]):
                            date_parts = parts[i:i+3]
                            break
            
            if not date_parts:
                logger.warning(f"No date found in path: {source_path}")
                return jekyll_root / '_posts' / source_path.name
                
            # Get the filename without date parts
            filename = source_path.name
            
            # Clean the filename
            clean_name = self._clean_filename(filename)
            
            # Create Jekyll path with date prefix
            date_str = '-'.join(date_parts)
            jekyll_path = jekyll_root / '_posts' / f"{date_str}-{clean_name}"
            
            return jekyll_path
            
        except Exception as e:
            logger.error(f"Error converting path {source_path}: {e}")
            raise
            
    def _clean_filename(self, filename: str) -> str:
        """
        Clean filename for Jekyll compatibility
        
        Args:
            filename: Original filename
            
        Returns:
            Cleaned filename
        """
        try:
            # Remove file extension
            name = Path(filename).stem
            
            # Replace spaces with hyphens
            name = name.replace(' ', '-')
            
            # Remove special characters except hyphens and underscores
            name = re.sub(r'[^\w\-]', '', name)
            
            # Convert to lowercase
            name = name.lower()
            
            # Add .md extension
            return f"{name}.md"
            
        except Exception as e:
            logger.error(f"Error cleaning filename {filename}: {e}")
            raise