"""File change detection module"""

import logging
import frontmatter
from pathlib import Path
from typing import Dict, List, Set, Tuple
import datetime

from .types import SyncState, SyncOperation, SyncDirection, PostStatus
from ..handlers.post import PostHandler

logger = logging.getLogger(__name__)

class ChangeDetector:
    """Handles file change detection"""
    
    def __init__(
        self,
        vault_path: Path,
        jekyll_path: Path,
        posts_path: Path,
        jekyll_posts: Path
    ):
        """Initialize change detector"""
        self.vault_path = vault_path
        self.jekyll_path = jekyll_path
        self.posts_path = posts_path
        self.jekyll_posts = jekyll_posts
        self.post_handler = PostHandler()
    
    def detect_changes(self) -> List[SyncState]:
        """
        Detect changes in both Obsidian and Jekyll directories
        
        Returns:
            List of SyncState objects representing detected changes
        """
        changes = []
        try:
            # Get current state of both sides
            obsidian_posts = {p.name: p for p in self.posts_path.glob('*.md')}
            jekyll_posts = {
                p.name: p for p in self.jekyll_posts.glob('*.md')
            }
            jekyll_drafts = {
                p.name: p for p in (self.jekyll_path / "_drafts").glob('*.md')
            }
            
            # Combine all Jekyll posts
            all_jekyll_posts = jekyll_posts | jekyll_drafts
            
            # Find all unique post names
            all_posts = set(obsidian_posts) | set(all_jekyll_posts)
            
            # Process each post
            for post_name in all_posts:
                obsidian_path = obsidian_posts.get(post_name)
                jekyll_path = all_jekyll_posts.get(post_name)
                
                if obsidian_path and jekyll_path:
                    # Post exists in both - check for modifications
                    changes.extend(self._check_modifications(
                        obsidian_path,
                        jekyll_path
                    ))
                    
                elif obsidian_path:
                    # Only in Obsidian - new or deleted from Jekyll
                    changes.extend(self._handle_obsidian_only(
                        obsidian_path,
                        post_name
                    ))
                    
                elif jekyll_path:
                    # Only in Jekyll - new or deleted from Obsidian
                    changes.extend(self._handle_jekyll_only(
                        jekyll_path,
                        post_name
                    ))
            
            return changes
            
        except Exception as e:
            logger.error(f"Error detecting changes: {e}")
            raise
    
    def _check_modifications(
        self,
        obsidian_path: Path,
        jekyll_path: Path
    ) -> List[SyncState]:
        """Check for modifications between Obsidian and Jekyll versions"""
        changes = []
        
        # Load both versions
        obsidian_post = frontmatter.load(str(obsidian_path))
        jekyll_post = frontmatter.load(str(jekyll_path))
        
        # Get post status
        status = self.post_handler.get_post_status(obsidian_post)
        if status == PostStatus.PRIVATE:
            return []
        
        # Check modification times
        obsidian_time = obsidian_post.get('modified')
        jekyll_time = jekyll_post.get('modified')
        
        # Convert modification times to timestamps if needed
        if isinstance(obsidian_time, (str, datetime.date, datetime.datetime)):
            obsidian_time = datetime.datetime.fromisoformat(str(obsidian_time)).timestamp()
        if isinstance(jekyll_time, (str, datetime.date, datetime.datetime)):
            jekyll_time = datetime.datetime.fromisoformat(str(jekyll_time)).timestamp()
        
        # Compare content first
        if not self._files_equal(obsidian_path, jekyll_path):
            # Files are different, prefer Obsidian changes
            if not jekyll_post.get('synced'):
                # Jekyll file hasn't been synced yet, treat as new
                return []
                
            # Always sync from Obsidian to Jekyll
            changes.append(self._create_sync_state(
                operation=SyncOperation.UPDATE,
                source_path=obsidian_path,
                target_path=jekyll_path,
                status=status,
                direction=SyncDirection.OBSIDIAN_TO_JEKYLL
            ))
        
        return changes
    
    def _files_equal(self, path1: Path, path2: Path) -> bool:
        """Check if two files have the same content"""
        try:
            with open(path1) as f1, open(path2) as f2:
                # Load both files as frontmatter posts
                post1 = frontmatter.load(f1)
                post2 = frontmatter.load(f2)
                
                # Compare metadata (excluding modified and synced)
                meta1 = {k: v for k, v in post1.metadata.items() if k not in ['modified', 'synced']}
                meta2 = {k: v for k, v in post2.metadata.items() if k not in ['modified', 'synced']}
                if meta1 != meta2:
                    return False
                
                # Compare content, ignoring whitespace
                content1 = post1.content.strip()
                content2 = post2.content.strip()
                return content1 == content2
                
        except Exception:
            return False
    
    def _handle_obsidian_only(
        self,
        obsidian_path: Path,
        post_name: str
    ) -> List[SyncState]:
        """Handle post that only exists in Obsidian"""
        changes = []
        
        # Load post
        post = frontmatter.load(str(obsidian_path))
        status = self.post_handler.get_post_status(post)
        
        if status == PostStatus.PRIVATE:
            return []
        
        # Determine target path
        if status == PostStatus.DRAFT:
            target_dir = self.jekyll_path / "_drafts"
        else:
            target_dir = self.jekyll_posts
        target_path = target_dir / post_name
        
        changes.append(self._create_sync_state(
            operation=SyncOperation.CREATE,
            source_path=obsidian_path,
            target_path=target_path,
            status=status,
            direction=SyncDirection.OBSIDIAN_TO_JEKYLL
        ))
        
        return changes
    
    def _handle_jekyll_only(
        self,
        jekyll_path: Path,
        post_name: str
    ) -> List[SyncState]:
        """Handle post that only exists in Jekyll"""
        changes = []
        
        # Load post
        post = frontmatter.load(str(jekyll_path))
        status = self.post_handler.get_post_status(post)
        
        if status == PostStatus.PRIVATE:
            return []
        
        # Determine target path
        target_path = self.posts_path / post_name
        
        # If we've synced before and the file is missing from Obsidian,
        # it must have been deleted
        if post.get('synced') == True and not target_path.exists():
            changes.append(self._create_sync_state(
                operation=SyncOperation.DELETE,
                source_path=target_path,
                target_path=jekyll_path,
                status=status,
                direction=SyncDirection.OBSIDIAN_TO_JEKYLL
            ))
        else:
            changes.append(self._create_sync_state(
                operation=SyncOperation.CREATE,
                source_path=jekyll_path,
                target_path=target_path,
                status=status,
                direction=SyncDirection.JEKYLL_TO_OBSIDIAN
            ))
        
        return changes
    
    def _create_sync_state(
        self,
        operation: SyncOperation,
        source_path: Path,
        target_path: Path,
        status: PostStatus,
        direction: SyncDirection
    ) -> SyncState:
        """Create a SyncState object with the given parameters"""
        return SyncState(
            operation=operation,
            source_path=source_path,
            target_path=target_path,
            status=status,
            sync_direction=direction
        )
    
    def _check_obsidian_changes(
        self,
        obsidian_posts: Dict[str, Path],
        jekyll_posts: Dict[str, Path],
        jekyll_drafts: Dict[str, Path],
        processed: Set[str]
    ) -> List[SyncState]:
        """Check for changes in Obsidian posts"""
        changes = []
        
        for post_name, post_path in obsidian_posts.items():
            processed.add(post_name)
            
            # Load post to check status
            post = frontmatter.load(str(post_path))
            status = self.post_handler.get_post_status(post)
            
            # Determine target path based on status
            if status == PostStatus.DRAFT:
                target_dir = self.jekyll_path / "_drafts"
            else:
                target_dir = self.jekyll_posts
            target_path = target_dir / post_name
            
            # Check if post exists in Jekyll
            jekyll_path = jekyll_posts.get(post_name) or jekyll_drafts.get(post_name)
            
            if not jekyll_path:
                # New post
                changes.append(SyncState(
                    operation=SyncOperation.CREATE,
                    source_path=post_path,
                    target_path=target_path,
                    status=status,
                    sync_direction=SyncDirection.OBSIDIAN_TO_JEKYLL
                ))
            else:
                # Check for modifications
                jekyll_post = frontmatter.load(str(jekyll_path))
                
                # Check modification times
                obsidian_time = post.get('modified')
                jekyll_time = jekyll_post.get('modified')
                
                if obsidian_time and jekyll_time:
                    # Use frontmatter times if available
                    if obsidian_time > jekyll_time:
                        changes.append(SyncState(
                            operation=SyncOperation.UPDATE,
                            source_path=post_path,
                            target_path=target_path,
                            status=status,
                            sync_direction=SyncDirection.OBSIDIAN_TO_JEKYLL
                        ))
                else:
                    # Fallback to file stats
                    obsidian_stat = post_path.stat().st_mtime
                    jekyll_stat = jekyll_path.stat().st_mtime
                    if obsidian_stat > jekyll_stat:
                        changes.append(SyncState(
                            operation=SyncOperation.UPDATE,
                            source_path=post_path,
                            target_path=target_path,
                            status=status,
                            sync_direction=SyncDirection.OBSIDIAN_TO_JEKYLL
                        ))
        
        # Check for deleted posts in Jekyll
        for post_name in set(obsidian_posts):
            if post_name not in jekyll_posts and post_name not in jekyll_drafts:
                # Post exists in Obsidian but not in Jekyll - it was deleted
                obsidian_path = obsidian_posts[post_name]
                
                # Load post to check status
                post = frontmatter.load(str(obsidian_path))
                status = self.post_handler.get_post_status(post)
                
                # Skip private posts
                if status == PostStatus.PRIVATE:
                    continue
                    
                # Determine target path based on status
                if status == PostStatus.DRAFT:
                    target_dir = self.jekyll_path / "_drafts"
                else:
                    target_dir = self.jekyll_posts
                target_path = target_dir / post_name
                
                changes.append(SyncState(
                    operation=SyncOperation.DELETE,
                    source_path=obsidian_path,
                    target_path=target_path,
                    sync_direction=SyncDirection.OBSIDIAN_TO_JEKYLL,
                    status=status
                ))
        
        return changes
    
    def _check_jekyll_changes(
        self,
        obsidian_posts: Dict[str, Path],
        jekyll_posts: Dict[str, Path],
        jekyll_drafts: Dict[str, Path],
        processed: Set[str]
    ) -> List[SyncState]:
        """Check for changes in Jekyll posts"""
        changes = []
        
        # Check both published and draft posts
        for posts_dict in [jekyll_posts, jekyll_drafts]:
            for post_name, post_path in posts_dict.items():
                if post_name in processed:
                    continue
                    
                processed.add(post_name)
                
                # Load post to check status
                post = frontmatter.load(str(post_path))
                status = self.post_handler.get_post_status(post)
                
                # Determine target path in Obsidian
                target_path = self.posts_path / post_name
                
                # Check if post exists in Obsidian
                obsidian_path = obsidian_posts.get(post_name)
                
                if not obsidian_path:
                    # New post
                    changes.append(SyncState(
                        operation=SyncOperation.CREATE,
                        source_path=post_path,
                        target_path=target_path,
                        status=status,
                        sync_direction=SyncDirection.JEKYLL_TO_OBSIDIAN
                    ))
                else:
                    # Check for modifications
                    obsidian_post = frontmatter.load(str(obsidian_path))
                    
                    # Check modification times
                    jekyll_time = post.get('modified')
                    obsidian_time = obsidian_post.get('modified')
                    
                    if jekyll_time and obsidian_time:
                        # Use frontmatter times if available
                        if jekyll_time > obsidian_time:
                            changes.append(SyncState(
                                operation=SyncOperation.UPDATE,
                                source_path=post_path,
                                target_path=target_path,
                                status=status,
                                sync_direction=SyncDirection.JEKYLL_TO_OBSIDIAN
                            ))
                    else:
                        # Fallback to file stats
                        jekyll_stat = post_path.stat().st_mtime
                        obsidian_stat = obsidian_path.stat().st_mtime
                        if jekyll_stat > obsidian_stat:
                            changes.append(SyncState(
                                operation=SyncOperation.UPDATE,
                                source_path=post_path,
                                target_path=target_path,
                                status=status,
                                sync_direction=SyncDirection.JEKYLL_TO_OBSIDIAN
                            ))
        
        return changes 