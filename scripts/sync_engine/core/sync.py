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
        self.post_handler = PostHandler(self.config)
        self.media_handler = MediaHandler(self.config)
        
        logger.info("SyncManager initialized successfully")
        logger.debug(f"Using configuration: {self.config}")
    
    def sync(self) -> List[SyncState]:
        """
        Sync files between Obsidian and Jekyll
        
        Returns:
            List of sync states for processed files
        """
        try:
            # Detect changes
            logger.info("Starting sync operation")
            changes = self.changes.detect_changes()
            
            # Log changes
            logger.debug(f"Found {len(changes)} changes to sync")
            for change in changes:
                logger.debug(f"Change: {change.operation} {change.source_path} -> {change.target_path}")
            
            logger.info(f"Detected {len(changes)} changes")
            
            # Process each change
            for change in changes:
                logger.debug(f"Processing change: {change}")
                try:
                    if change.operation == SyncOperation.DELETE:
                        if change.target_path and change.target_path.exists():
                            change.target_path.unlink()
                    else:
                        # Only process markdown files as posts
                        if change.source_path.suffix.lower() == '.md':
                            logger.debug(f"Processing markdown file: {change.source_path}")
                            # Get correct Jekyll path
                            target_path = self.post_handler.get_jekyll_path(
                                change.source_path,
                                self.config.jekyll_root
                            )
                            logger.debug(f"Target Jekyll path: {target_path}")
                            
                            # Create parent directories
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            # Process post
                            content = self.post_handler.process(
                                change.source_path,
                                target_path
                            )
                            
                            # Write with atomic operation
                            self.atomic.write(
                                target_path,
                                content,
                                make_backup=True
                            )
                            
                            # Update state target path
                            change.target_path = target_path
                        else:
                            logger.debug(f"Processing media file: {change.source_path}")
                            # Use MediaHandler to sync media file
                            target_path = self.media_handler.sync_media(change.source_path)
                            logger.debug(f"Successfully synced media file to: {target_path}")
                            
                            # Update state target path
                            change.target_path = target_path
                            
                    logger.debug(f"Successfully processed change: {change}")
                    
                except Exception as e:
                    logger.error(f"Failed to process change {change}: {e}")
                    raise
            
            # Run cleanup if enabled
            if self.config.auto_cleanup:
                if self.config.cleanup_delay > 0:
                    import threading
                    # Schedule delayed cleanup
                    threading.Timer(self.config.cleanup_delay, self.cleanup).start()
                else:
                    # Run cleanup immediately
                    self.cleanup()
            
            logger.info(f"Sync completed successfully. Processed {len(changes)} changes")
            return changes
            
        except Exception as e:
            logger.error(f"Sync operation failed: {e}")
            raise SyncError(f"Sync failed: {e}") from e
    
    def cleanup(self) -> None:
        """Clean up unused files"""
        try:
            # Clean up media files
            self.media_handler.cleanup_unused()
            
            # Clean up posts
            posts_dir = self.config.jekyll_root / self.config.jekyll_posts
            if posts_dir.exists():
                for post in posts_dir.glob('*.md'):
                    post.unlink()
                    logger.debug(f"Cleaned up post: {post}")
            
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