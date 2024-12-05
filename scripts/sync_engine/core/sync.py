"""Core sync orchestration module"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
import frontmatter

from .atomic import AtomicManager
from .changes import ChangeDetector
from .types import SyncState, SyncOperation, PostStatus
from .config import ConfigManager, SyncConfig
from .exceptions import SyncError
from ..handlers.post import PostHandler
from ..handlers.media import MediaHandler

logger = logging.getLogger(__name__)

class SyncManager:
    """Manages the sync process between Obsidian and Jekyll"""
    
    def __init__(self, config: Dict = None):
        """
        Initialize sync manager
        
        Args:
            config: Optional configuration dictionary. If not provided, loads from environment.
        """
        try:
            # Load configuration
            self.config = (
                ConfigManager.load_from_dict(config)
                if config is not None
                else ConfigManager.load_from_env()
            )
            
            # Initialize components
            self.atomic = AtomicManager()
            self.changes = ChangeDetector(self.config)
            self.post_handler = PostHandler()
            self.media_handler = MediaHandler(
                self.config.vault_path,
                self.config.jekyll_assets_path
            )
            
            logger.info("SyncManager initialized successfully")
            logger.debug(f"Using configuration: {self.config}")
            
        except Exception as e:
            logger.error(f"Failed to initialize SyncManager: {e}")
            raise SyncError(f"Initialization failed: {e}") from e
    
    def sync(self) -> List[SyncState]:
        """
        Sync files between Obsidian and Jekyll
        
        Returns:
            List[SyncState]: List of changes that were synced
        
        Raises:
            SyncError: If sync fails
        """
        try:
            logger.info("Starting sync operation")
            
            # Get changes
            changes = self.changes.detect()
            logger.info(f"Detected {len(changes)} changes")
            
            # Process each change
            processed_changes = []
            for state in changes:
                try:
                    logger.debug(f"Processing change: {state}")
                    
                    # Process media references first
                    if state.operation != SyncOperation.DELETE:
                        self.media_handler.process_references(state.source_path)
                    
                    # Sync post
                    self._sync_post(state)
                    processed_changes.append(state)
                    
                    # Mark as synced
                    if state.operation != SyncOperation.DELETE:
                        self._mark_synced(state)
                        
                    logger.debug(f"Successfully processed change: {state}")
                    
                except Exception as e:
                    logger.error(f"Failed to process change {state}: {e}")
                    if not self.config.continue_on_error:
                        raise
            
            # Run cleanup if enabled
            if self.config.auto_cleanup:
                self.cleanup()
            
            logger.info(f"Sync completed successfully. Processed {len(processed_changes)} changes")
            return processed_changes
            
        except Exception as e:
            logger.error(f"Sync operation failed: {e}")
            raise SyncError(f"Sync failed: {e}") from e
    
    def cleanup(self) -> None:
        """Clean up unused files and old backups"""
        try:
            logger.info("Starting cleanup")
            
            # Clean up old backups
            self.atomic.cleanup_backups(keep=self.config.backup_count)
            
            # Clean up unused media
            self.media_handler.cleanup_unused()
            
            logger.info("Cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise SyncError(f"Cleanup failed: {e}") from e
    
    def _sync_post(self, state: SyncState) -> None:
        """Sync a single post"""
        try:
            if state.operation == SyncOperation.DELETE:
                if state.target_path.exists():
                    state.target_path.unlink()
            else:
                # Process post
                content = self.post_handler.process(
                    state.source_path,
                    state.target_path
                )
                
                # Write with atomic operation
                self.atomic.write(
                    state.target_path,
                    content,
                    make_backup=True
                )
                
        except Exception as e:
            logger.error(f"Failed to sync post {state.source_path}: {e}")
            raise SyncError(f"Post sync failed: {e}") from e
    
    def _mark_synced(self, state: SyncState) -> None:
        """Mark files as synced in frontmatter"""
        try:
            for path in [state.source_path, state.target_path]:
                if path.exists():
                    post = frontmatter.load(str(path))
                    post.metadata['synced'] = True
                    frontmatter.dump(post, str(path))
                    
        except Exception as e:
            logger.error(f"Failed to mark sync status: {e}")
            raise SyncError(f"Failed to mark sync status: {e}") from e