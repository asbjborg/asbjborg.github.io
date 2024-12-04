"""
Post handler for processing Obsidian posts
"""

import logging
import frontmatter
from pathlib import Path
from typing import Optional
from datetime import datetime

from ..core.types import PostStatus

logger = logging.getLogger(__name__)

class PostHandler:
    """Handles post processing and conversion"""
    
    @staticmethod
    def get_post_status(post: frontmatter.Post) -> PostStatus:
        """Get post status according to sync strategy"""
        status = post.get('status', None)
        if status == "published":
            return PostStatus.PUBLISHED
        elif status == "draft":
            return PostStatus.DRAFT
        elif status == "private":
            return PostStatus.PRIVATE
        return PostStatus.NONE
    
    @staticmethod
    def should_keep_in_jekyll(status: PostStatus) -> bool:
        """Determine if post should be kept in Jekyll"""
        return status in (PostStatus.PUBLISHED, PostStatus.DRAFT)
    
    @staticmethod
    def process_for_jekyll(post: frontmatter.Post) -> frontmatter.Post:
        """Process a post for Jekyll"""
        clean_post = frontmatter.Post(content=post.content)
        
        # Required Jekyll fields
        clean_post['title'] = post.get('title', post.get('name', 'Untitled'))
        
        # Handle time field
        if post.get('time'):
            try:
                time_str = post['time']
                h, m, s = map(int, time_str.split(':'))
                clean_post['time'] = h * 3600 + m * 60 + s
            except:
                logger.warning(f"Could not parse time: {post.get('time')}")
        
        # Process tags
        if post.get('tags'):
            tags = post['tags']
            if isinstance(tags, list):
                filtered_tags = [tag for tag in tags if tag not in ['atomic', 'internal']]
                if filtered_tags:
                    clean_post['tags'] = filtered_tags
        
        # Ensure content ends with newline
        if not clean_post.content.endswith('\n'):
            clean_post.content += '\n'
        
        return clean_post
    
    @staticmethod
    def get_jekyll_path(source_path: Path, posts_dir: Path) -> Path:
        """Generate Jekyll post path from Obsidian note path"""
        try:
            # Extract date from path (YYYY/MM/DD)
            try:
                date_parts = [
                    source_path.parts[-4],  # Year
                    source_path.parts[-3].zfill(2),  # Month
                    source_path.parts[-2].zfill(2)  # Day
                ]
                date = '-'.join(date_parts)
            except:
                logger.warning(f"Could not extract date from path {source_path}, using current date")
                date = datetime.now().strftime('%Y-%m-%d')
            
            # Generate safe title
            safe_title = source_path.stem.lower().replace(' ', '-')
            safe_title = ''.join(c for c in safe_title if c.isalnum() or c in '-_')
            
            return posts_dir / f"{date}-{safe_title}.md"
            
        except Exception as e:
            logger.error(f"Error generating Jekyll path for {source_path}: {e}")
            raise 