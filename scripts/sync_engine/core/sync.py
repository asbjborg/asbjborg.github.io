"""Core sync orchestration module"""

import logging
from pathlib import Path
from typing import List, Optional
import frontmatter
from datetime import datetime

from .atomic import AtomicManager
from .changes import ChangeDetector
from .types import SyncState, SyncOperation, PostStatus
from .config import SyncConfig
from .exceptions import SyncError
from ..handlers.post import PostHandler
from ..handlers.media import MediaHandler
from .engine import SyncEngineV2

logger = logging.getLogger(__name__)

class SyncManager:
    """Manages the sync process between Obsidian and Jekyll"""
    
    def __init__(self, config: SyncConfig):
        """
        Initialize sync manager
        
        Args:
            config: Configuration object for the sync manager
        """
        self.config = config
        
        # Initialize engine with config
        self.engine = SyncEngineV2(self.config)
        
        # Initialize components
        self.atomic = AtomicManager(self.config)
        self.changes = ChangeDetector(self.config)
        self.post_handler = PostHandler()
        self.media_handler = MediaHandler(self.config)
        
        logger.info("SyncManager initialized successfully")
        logger.debug(f"Using configuration: {self.config}")
    
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
            changes = self.changes.detect_changes()
            logger.info(f"Detected {len(changes)} changes")
            
            # Process each change
            processed_changes = []
            for state in changes:
                try:
                    logger.debug(f"Processing change: {state}")
                    
                    # Process media references first
                    if state.operation != SyncOperation.DELETE:
                        self.media_handler.process_references(state.source_path)
                    
                    # Sync file
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
        """Clean up unused files"""
        try:
            # Clean up media files
            self.media_handler.cleanup_unused()
            
            # Clean up backup directories
            backup_dir = self.config.vault_root / '.atomic_backups'
            if backup_dir.exists():
                try:
                    import shutil
                    shutil.rmtree(backup_dir)
                except (PermissionError, OSError) as e:
                    logger.warning(f"Could not remove backup directory {backup_dir}: {e}")
                    # Try to remove individual files
                    for file in backup_dir.glob('*'):
                        try:
                            if file.is_file():
                                file.unlink()
                        except (PermissionError, OSError) as e:
                            logger.warning(f"Could not remove backup file {file}: {e}")
                            
                backup_dir.mkdir(parents=True, exist_ok=True)
                
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            # Don't raise error for cleanup failures
            pass
    
    def _sync_post(self, state: SyncState) -> None:
        """Sync a single post"""
        try:
            if state.operation == SyncOperation.DELETE:
                if state.target_path.exists():
                    state.target_path.unlink()
            else:
                # Only process markdown files as posts
                if state.source_path.suffix.lower() == '.md':
                    logger.debug(f"Processing markdown file: {state.source_path}")
                    # Get correct Jekyll path
                    target_path = self.post_handler.get_jekyll_path(
                        state.source_path,
                        self.config.jekyll_root
                    )
                    logger.debug(f"Target Jekyll path: {target_path}")
                    
                    # Create _posts directory if it doesn't exist
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Process post
                    content = self.post_handler.process(
                        state.source_path,
                        target_path
                    )
                    
                    # Write with atomic operation
                    self.atomic.write(
                        target_path,
                        content,
                        make_backup=True
                    )
                    
                    # Update state target path
                    state.target_path = target_path
                else:
                    logger.debug(f"Processing media file: {state.source_path}")
                    # Use MediaHandler to sync media file
                    target_path = self.media_handler.sync_media(state.source_path)
                    logger.debug(f"Successfully synced media file to: {target_path}")
                    
                    # Update state target path
                    state.target_path = target_path
    
        except Exception as e:
            logger.error(f"Failed to sync {state.source_path}: {e}")
            raise SyncError(f"Sync failed: {e}") from e
    
    def _is_text_file(self, path: Path) -> bool:
        """Check if file is a text file"""
        text_extensions = {'.md', '.txt', '.html', '.yml', '.yaml', '.json'}
        return path.suffix.lower() in text_extensions
        
    def _mark_synced(self, state: SyncState) -> None:
        """Mark a file as synced"""
        try:
            if not self._is_text_file(state.source_path):
                return  # Skip non-text files
                
            # Read current content
            with open(state.source_path) as f:
                content = f.read()
                
            # Update sync status
            if not content.startswith('---\n'):
                content = '---\n---\n' + content
                
            # Parse frontmatter
            post = frontmatter.loads(content)
            post.metadata['sync_status'] = 'synced'
            post.metadata['last_synced'] = datetime.now().isoformat()
            
            # Write back
            with open(state.source_path, 'w') as f:
                f.write(frontmatter.dumps(post))
                
        except Exception as e:
            logger.error(f"Failed to mark sync status: {e}")
            raise SyncError(f"Failed to mark sync status: {e}") from e