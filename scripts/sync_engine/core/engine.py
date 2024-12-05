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
        vault_atomics: str = "atomics",
        jekyll_posts: str = "_posts",
        jekyll_assets: str = "assets/img/posts"
    ):
        """Initialize sync engine"""
        self.config = ConfigManager.load_from_dict({
            "vault_path": vault_root,
            "jekyll_path": jekyll_root,
            "vault_atomics": vault_atomics,
            "jekyll_posts": jekyll_posts,
            "jekyll_assets": jekyll_assets
        })
        
        # Initialize handlers
        self.post_handler = PostHandler()
        self.media_handler = MediaHandler(
            vault_path=self.config.vault_path,
            jekyll_assets=self.config.jekyll_assets_path
        )
        
        # Initialize change detector
        self.change_detector = ChangeDetector(
            vault_path=self.config.vault_path,
            jekyll_path=self.config.jekyll_path,
            atomics_path=self.config.atomics_path,
            jekyll_posts=self.config.jekyll_posts_path
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