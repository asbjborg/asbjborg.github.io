"""Core sync engine module"""

import logging
from pathlib import Path
from typing import List, Optional
import time

import frontmatter

from .types import SyncState, SyncOperation, SyncDirection, PostStatus
from .config import SyncConfig
from .changes import ChangeDetector
from .atomic import AtomicManager
from ..handlers.media import MediaHandler
from ..handlers.post import PostHandler

logger = logging.getLogger(__name__)

class SyncEngineV2:
    """Sync engine for bidirectional sync between Obsidian and Jekyll"""
    
    def __init__(self, config: SyncConfig):
        """
        Initialize sync engine
        
        Args:
            config: Configuration object for the sync engine
        """
        self.config = config
        
        # Initialize components
        self.detector = ChangeDetector(self.config)
        self.atomic = AtomicManager(self.config)
        self.post_handler = PostHandler(self.config)
        self.media_handler = MediaHandler(self.config)
    
    def detect_changes(self) -> List[SyncState]:
        """
        Detect changes in both Obsidian and Jekyll directories
        
        Returns:
            List of sync states representing detected changes
        """
        return self.detector.detect_changes()
    
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
                # Process post content
                processed = self.post_handler.process(
                    state.source_path,
                    state.target_path,
                    state.sync_direction
                )
                    
                # Ensure target directory exists
                state.target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write processed post
                state.target_path.write_text(processed)
                
        except Exception as e:
            logger.error(f"Error syncing post {state.source_path}: {e}")
            raise