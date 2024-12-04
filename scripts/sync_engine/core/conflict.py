"""
Conflict resolution for sync operations
"""

import logging
import hashlib
import difflib
from pathlib import Path
from typing import Optional, Tuple, Dict
from dataclasses import dataclass
from datetime import datetime
import frontmatter

from .types import SyncDirection

logger = logging.getLogger(__name__)

@dataclass
class ConflictInfo:
    """Information about a sync conflict"""
    obsidian_path: Path
    jekyll_path: Path
    obsidian_modified: float
    jekyll_modified: float
    obsidian_content_hash: str
    jekyll_content_hash: str
    content_differs: bool
    frontmatter_differs: bool
    resolution: Optional[SyncDirection] = None

class ConflictResolver:
    """Handles sync conflicts between Obsidian and Jekyll"""
    
    @staticmethod
    def get_content_hash(content: str) -> str:
        """Generate hash of content for comparison"""
        return hashlib.md5(content.encode()).hexdigest()
    
    @staticmethod
    def get_frontmatter_hash(post: frontmatter.Post) -> str:
        """Generate hash of frontmatter for comparison"""
        # Convert frontmatter to string, sort keys for consistency
        fm_str = str(sorted(post.metadata.items()))
        return hashlib.md5(fm_str.encode()).hexdigest()
    
    @staticmethod
    def split_content_frontmatter(post: frontmatter.Post) -> Tuple[str, Dict]:
        """Split post into content and frontmatter"""
        return post.content, dict(post.metadata)
    
    def detect_conflict(self, obsidian_path: Path, jekyll_path: Path) -> Optional[ConflictInfo]:
        """
        Detect if there's a conflict between Obsidian and Jekyll versions
        
        Args:
            obsidian_path: Path to Obsidian file
            jekyll_path: Path to Jekyll file
            
        Returns:
            ConflictInfo if conflict detected, None otherwise
        """
        try:
            # Load both versions
            obsidian_post = frontmatter.load(str(obsidian_path))
            jekyll_post = frontmatter.load(str(jekyll_path))
            
            # Get modification times
            obsidian_modified = obsidian_path.stat().st_mtime
            jekyll_modified = jekyll_path.stat().st_mtime
            
            # Split content and frontmatter
            obsidian_content, obsidian_fm = self.split_content_frontmatter(obsidian_post)
            jekyll_content, jekyll_fm = self.split_content_frontmatter(jekyll_post)
            
            # Generate hashes
            obsidian_content_hash = self.get_content_hash(obsidian_content)
            jekyll_content_hash = self.get_content_hash(jekyll_content)
            
            # Check if content or frontmatter differs
            content_differs = obsidian_content_hash != jekyll_content_hash
            frontmatter_differs = self.get_frontmatter_hash(obsidian_post) != self.get_frontmatter_hash(jekyll_post)
            
            # If either differs, we have a conflict
            if content_differs or frontmatter_differs:
                return ConflictInfo(
                    obsidian_path=obsidian_path,
                    jekyll_path=jekyll_path,
                    obsidian_modified=obsidian_modified,
                    jekyll_modified=jekyll_modified,
                    obsidian_content_hash=obsidian_content_hash,
                    jekyll_content_hash=jekyll_content_hash,
                    content_differs=content_differs,
                    frontmatter_differs=frontmatter_differs
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting conflict: {e}")
            return None
    
    def resolve_conflict(self, conflict: ConflictInfo) -> SyncDirection:
        """
        Resolve a sync conflict
        
        Strategy:
        1. If only frontmatter differs: preserve Obsidian frontmatter
        2. If content differs:
           - Use most recently modified version
           - If Jekyll is newer: only update content in Obsidian
           - If Obsidian is newer: update both content and frontmatter in Jekyll
        
        Args:
            conflict: Information about the conflict
            
        Returns:
            Direction to sync (which version to use)
        """
        try:
            # If only frontmatter differs, always preserve Obsidian
            if not conflict.content_differs and conflict.frontmatter_differs:
                logger.info("Only frontmatter differs - preserving Obsidian version")
                return SyncDirection.OBSIDIAN_TO_JEKYLL
            
            # If content differs, use most recent version
            if conflict.jekyll_modified > conflict.obsidian_modified:
                logger.info("Jekyll version is newer - updating Obsidian content")
                return SyncDirection.JEKYLL_TO_OBSIDIAN
            else:
                logger.info("Obsidian version is newer - updating Jekyll")
                return SyncDirection.OBSIDIAN_TO_JEKYLL
            
        except Exception as e:
            logger.error(f"Error resolving conflict: {e}")
            # Default to Obsidian version if resolution fails
            return SyncDirection.OBSIDIAN_TO_JEKYLL
    
    def get_content_diff(self, obsidian_path: Path, jekyll_path: Path) -> str:
        """
        Get a human-readable diff of content changes
        
        Args:
            obsidian_path: Path to Obsidian file
            jekyll_path: Path to Jekyll file
            
        Returns:
            String containing the diff
        """
        try:
            # Load both versions
            obsidian_post = frontmatter.load(str(obsidian_path))
            jekyll_post = frontmatter.load(str(jekyll_path))
            
            # Get content
            obsidian_lines = obsidian_post.content.splitlines()
            jekyll_lines = jekyll_post.content.splitlines()
            
            # Generate diff
            diff = difflib.unified_diff(
                jekyll_lines,
                obsidian_lines,
                fromfile='jekyll',
                tofile='obsidian',
                lineterm=''
            )
            
            return '\n'.join(diff)
            
        except Exception as e:
            logger.error(f"Error generating diff: {e}")
            return "" 