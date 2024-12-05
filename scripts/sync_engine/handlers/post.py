"""Post handler module"""

import logging
import frontmatter
from pathlib import Path
from typing import Optional

from ..core.types import PostStatus

logger = logging.getLogger(__name__)

class PostHandler:
    """Handles post processing and status management"""
    
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
            
            # Convert Obsidian image links to Jekyll format
            content = processed.content
            content = content.replace('![[', '![](')
            content = content.replace(']]', ')')
            content = content.replace('atomics/', '/assets/img/posts/')
            processed.content = content
            
            # Update frontmatter
            for key, value in processed.metadata.items():
                if isinstance(value, str):
                    if '![[' in value and ']]' in value:
                        # Convert image links in frontmatter
                        value = value.replace('![[', '![](')
                        value = value.replace(']]', ')')
                        value = value.replace('atomics/', '/assets/img/posts/')
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
            
            # Convert Jekyll image links to Obsidian format
            content = processed.content
            content = content.replace('/assets/img/posts/', 'atomics/')
            content = content.replace('![', '![[')
            content = content.replace(')', ']]')
            processed.content = content
            
            # Update frontmatter
            for key, value in processed.metadata.items():
                if isinstance(value, str):
                    if '/assets/img/posts/' in value:
                        # Convert image links in frontmatter
                        value = value.replace('/assets/img/posts/', 'atomics/')
                        value = value.replace('![', '![[')
                        value = value.replace(')', ']]')
                        processed.metadata[key] = value
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing post for Obsidian: {e}")
            raise