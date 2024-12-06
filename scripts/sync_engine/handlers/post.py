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
        """Convert Obsidian path to Jekyll path"""
        try:
            if jekyll_root is None:
                jekyll_root = self.config.jekyll_root
                
            # Extract date from path (YYYY/MM/DD)
            parts = list(source_path.parts)
            date_prefix = None
            
            # Try to find date in path
            for i in range(len(parts) - 3):
                try:
                    year = int(parts[i])
                    month = int(parts[i + 1])
                    day = int(parts[i + 2])
                    if 2000 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                        date_prefix = f"{year:04d}-{month:02d}-{day:02d}"
                        break
                except (ValueError, IndexError):
                    continue
            
            if not date_prefix:
                # Use current date if no date in path
                now = datetime.now()
                date_prefix = now.strftime('%Y-%m-%d')
                
            # Get filename without extension
            filename = source_path.stem
            
            # Convert spaces to hyphens and remove special characters
            filename = re.sub(r'[^\w\s-]', '', filename)
            filename = re.sub(r'[-\s]+', '-', filename).strip('-').lower()
            
            # Create Jekyll path
            jekyll_filename = f"{date_prefix}-{filename}.md"
            return jekyll_root / '_posts' / jekyll_filename
            
        except Exception as e:
            logger.error(f"Error converting path {source_path}: {e}")
            raise ValueError(f"Failed to convert path: {e}") from e