"""Core sync engine module"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
import time

import frontmatter

from .types import SyncState, SyncOperation, SyncDirection, PostStatus
from .config import ConfigManager, SyncConfig
from .changes import ChangeDetector
from .atomic import AtomicOperation
from ..handlers.media import MediaHandler
from ..handlers.post import PostHandler

logger = logging.getLogger(__name__)

class SyncEngineV2:
    """V2 of the sync engine with improved architecture and features"""
    
    def __init__(
        self,
        vault_root: Path,
        jekyll_root: Path,
        vault_posts: str = "_posts",
        vault_media: str = "atomics",
        jekyll_posts: str = "_posts",
        jekyll_assets: str = "assets/img/posts"
    ):
        """Initialize sync engine"""
        self.vault_root = Path(vault_root).resolve()
        self.jekyll_root = Path(jekyll_root).resolve()
        self.vault_posts = vault_posts
        self.vault_media = vault_media
        self.jekyll_posts = jekyll_posts
        self.jekyll_assets = jekyll_assets
        
        # Initialize handlers
        self.post_handler = PostHandler()
        self.media_handler = MediaHandler(
            vault_path=self.vault_root,
            jekyll_assets=self.jekyll_root / self.jekyll_assets
        )
        
        # Initialize change detector
        self.change_detector = ChangeDetector(
            vault_path=self.vault_root,
            jekyll_path=self.jekyll_root,
            posts_path=self.vault_root / self.vault_posts,
            jekyll_posts=self.jekyll_root / self.jekyll_posts
        )
    
    def detect_changes(self) -> List[SyncState]:
        """Detect changes in both Obsidian and Jekyll directories"""
        return self.change_detector.detect_changes()
    
    def sync(self, direction: Optional[SyncDirection] = None) -> None:
        """
        Sync files between Obsidian and Jekyll
        
        Args:
            direction: Optional sync direction, if None will sync both ways
        """
        try:
            # Get changes
            changes = self.detect_changes()
            
            # Filter changes by direction if specified
            if direction:
                changes = [c for c in changes if c.sync_direction == direction]
            
            # Process each change
            for state in changes:
                # Skip changes in wrong direction
                if direction and state.sync_direction != direction:
                    continue
                    
                # Process media references first
                if state.operation != SyncOperation.DELETE:
                    self.media_handler.process_references(state.source_path)
                
                # Sync post
                self._sync_post(state)
                
                # Mark as synced in both directions
                if state.operation != SyncOperation.DELETE:
                    # Mark source as synced
                    source = frontmatter.load(str(state.source_path))
                    source.metadata['synced'] = True
                    frontmatter.dump(source, str(state.source_path))
                    
                    # Mark target as synced after processing
                    if state.target_path.exists():
                        target = frontmatter.load(str(state.target_path))
                        target.metadata['synced'] = True
                        frontmatter.dump(target, str(state.target_path))
            
        except Exception as e:
            logger.error(f"Error during sync: {e}")
            raise
    
    def _sync_obsidian_to_jekyll(self) -> List[SyncState]:
        """Sync changes from Obsidian to Jekyll"""
        changes = []
        try:
            # Get changes
            detected = self.detect_changes()
            
            # Process each change
            for change in detected:
                if change.sync_direction == SyncDirection.OBSIDIAN_TO_JEKYLL:
                    # Skip private posts
                    if change.status == PostStatus.PRIVATE:
                        continue
                        
                    if change.operation == SyncOperation.DELETE:
                        # Delete from Jekyll
                        if change.target_path:
                            with AtomicOperation.atomic_delete(change.target_path) as backup_path:
                                changes.append(change)
                    else:
                        # Create or update in Jekyll
                        changes.extend(self.sync_ops.sync_to_jekyll(
                            change.source_path,
                            change.status or PostStatus.PUBLISHED
                        ))
            
            return changes
            
        except Exception as e:
            logger.error(f"Error during Obsidian to Jekyll sync: {e}")
            raise
    
    def _sync_jekyll_to_obsidian(self) -> List[SyncState]:
        """Sync changes from Jekyll to Obsidian"""
        changes = []
        try:
            # Get changes
            detected = self.detect_changes()
            
            # Process each change
            for change in detected:
                if change.sync_direction == SyncDirection.JEKYLL_TO_OBSIDIAN:
                    if change.operation == SyncOperation.DELETE:
                        # Delete from Obsidian
                        if change.target_path:
                            with AtomicOperation.atomic_delete(change.target_path) as backup_path:
                                changes.append(change)
                    else:
                        # Create or update in Obsidian
                        changes.extend(self.sync_ops.sync_to_obsidian(change.source_path))
            
            return changes
            
        except Exception as e:
            logger.error(f"Error during Jekyll to Obsidian sync: {e}")
            raise
    
    def _sync_bidirectional(self) -> List[SyncState]:
        """Perform bidirectional sync with conflict resolution"""
        changes = []
        try:
            # Get all changes
            detected = self.detect_changes()
            
            # Group changes by file name
            changes_by_file = {}
            for change in detected:
                file_name = change.source_path.name
                if file_name not in changes_by_file:
                    changes_by_file[file_name] = []
                changes_by_file[file_name].append(change)
            
            # Process each file's changes
            for file_name, file_changes in changes_by_file.items():
                if len(file_changes) == 1:
                    # Single change, just apply it
                    change = file_changes[0]
                    if change.sync_direction == SyncDirection.OBSIDIAN_TO_JEKYLL:
                        changes.extend(self._sync_obsidian_to_jekyll())
                    else:
                        changes.extend(self._sync_jekyll_to_obsidian())
                else:
                    # Multiple changes, resolve conflict
                    obsidian_change = next(
                        (c for c in file_changes if c.sync_direction == SyncDirection.OBSIDIAN_TO_JEKYLL),
                        None
                    )
                    jekyll_change = next(
                        (c for c in file_changes if c.sync_direction == SyncDirection.JEKYLL_TO_OBSIDIAN),
                        None
                    )
                    
                    if obsidian_change and jekyll_change:
                        # Both sides changed, use newer version
                        if obsidian_change.last_modified > jekyll_change.last_modified:
                            changes.extend(self._sync_obsidian_to_jekyll())
                        else:
                            changes.extend(self._sync_jekyll_to_obsidian())
            
            return changes
            
        except Exception as e:
            logger.error(f"Error during bidirectional sync: {e}")
            raise
    
    def _sync_post(self, state: SyncState) -> None:
        """
        Sync a single post
        
        Args:
            state: Sync state for the post
        """
        try:
            # Process post based on operation
            if state.operation == SyncOperation.DELETE:
                if state.target_path.exists():
                    state.target_path.unlink()
                    
            elif state.operation in [SyncOperation.CREATE, SyncOperation.UPDATE]:
                # Load source post
                post = frontmatter.load(str(state.source_path))
                
                # Skip private posts
                if self.post_handler.get_post_status(post) == PostStatus.PRIVATE:
                    return
                    
                # Process post content
                if state.sync_direction == SyncDirection.OBSIDIAN_TO_JEKYLL:
                    processed = self.post_handler.process_for_jekyll(post)
                else:
                    processed = self.post_handler.process_for_obsidian(post)
                    
                # Update modification time and sync status
                processed.metadata['modified'] = time.time()
                processed.metadata['synced'] = True
                
                # Ensure target directory exists
                state.target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write processed post
                frontmatter.dump(processed, str(state.target_path))
                
        except Exception as e:
            logger.error(f"Error syncing post {state.source_path}: {e}")
            raise