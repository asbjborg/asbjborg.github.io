"""Core sync orchestration module"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
import frontmatter
from dotenv import load_dotenv

from .atomic import AtomicManager
from .changes import ChangeDetector
from .types import SyncState, SyncOperation, PostStatus
from ..handlers.post import PostHandler
from ..handlers.media import MediaHandler

logger = logging.getLogger(__name__)

class SyncManager:
    """Manages the sync process between Obsidian and Jekyll"""
    
    DEFAULT_CONFIG = {
        'jekyll_posts': '_posts',
        'jekyll_assets': 'assets/img/posts',
        'atomics_root': 'atomics',
        'backup_count': 5,
        'auto_cleanup': True,
        'max_image_width': 1200,
        'optimize_images': True
    }
    
    def __init__(self, config: Dict):
        """
        Initialize sync manager with configuration
        
        Args:
            config: Configuration dictionary with required paths and optional settings
            
        Required config:
            - vault_root: Path to Obsidian vault
            - jekyll_root: Path to Jekyll site
            
        Optional config:
            - jekyll_posts: Jekyll posts directory (default: '_posts')
            - jekyll_assets: Jekyll assets directory (default: 'assets/img/posts')
            - atomics_root: Obsidian atomics directory (default: 'atomics')
            - backup_count: Number of backups to keep (default: 5)
            - auto_cleanup: Whether to auto-cleanup unused files (default: True)
        
        Raises:
            ValueError: If required config is missing or invalid
        """
        # Load .env if exists
        if Path('.env').exists():
            load_dotenv()
            
        # Check env vars if config not provided
        if not config.get('vault_root'):
            config['vault_root'] = os.getenv('VAULT_ROOT')
        if not config.get('jekyll_root'):
            config['jekyll_root'] = os.getenv('JEKYLL_ROOT')
            
        # Validate required config
        if not config.get('vault_root') or not config.get('jekyll_root'):
            raise ValueError("Missing required config: vault_root and jekyll_root are required")
            
        # Convert paths to Path objects and validate
        self.vault_path = Path(config['vault_root'])
        self.jekyll_path = Path(config['jekyll_root'])
        
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {self.vault_path}")
        if not self.jekyll_path.exists():
            raise ValueError(f"Jekyll path does not exist: {self.jekyll_path}")
            
        # Merge with defaults
        self.config = {**self.DEFAULT_CONFIG, **config}
        
        # Initialize paths
        self.atomics_root = self.vault_path / self.config['atomics_root']
        self.jekyll_posts = self.jekyll_path / self.config['jekyll_posts']
        
        # Initialize components with validated config
        self.atomic = AtomicManager()
        if self.config.get('backup_count'):
            self.atomic._cleanup_old_backups.keep = self.config['backup_count']
            
        self.changes = ChangeDetector(self.config)
        self.post_handler = PostHandler()
        self.media_handler = MediaHandler(
            self.vault_path,
            self.jekyll_path / self.config['jekyll_assets']
        )
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO if not config.get('debug') else logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _apply_dev_settings(self, dev_settings: Dict):
        """Apply development environment settings"""
        # Override defaults with dev settings
        self.DEFAULT_CONFIG.update(dev_settings)
    
    def validate_config(self) -> bool:
        """
        Validate current configuration
        
        Returns:
            bool: True if config is valid
            
        Raises:
            ValueError: If config is invalid
        """
        # Check required directories
        required_dirs = [
            (self.jekyll_posts, "Jekyll posts directory"),
            (self.jekyll_path / self.config['jekyll_assets'], "Jekyll assets directory"),
            (self.atomics_root, "Obsidian atomics directory")
        ]
        
        for path, name in required_dirs:
            if not path.exists():
                raise ValueError(f"{name} does not exist: {path}")
                
        # Validate numeric settings
        if not isinstance(self.config.get('backup_count', 5), int):
            raise ValueError("backup_count must be an integer")
            
        # Validate boolean settings
        if not isinstance(self.config.get('auto_cleanup', True), bool):
            raise ValueError("auto_cleanup must be a boolean")
            
        return True
    
    def sync(self) -> List[SyncState]:
        """
        Perform full sync between Obsidian and Jekyll
        
        Returns:
            List of sync states representing changes made
        """
        try:
            # Detect changes
            changes = self.changes.detect()
            if not changes:
                logger.info("No changes detected")
                return []
                
            # Process changes atomically
            with self.atomic.batch() as batch:
                for change in changes:
                    # Add the sync operation
                    batch.add(change)
                    
                    # Process any media references
                    if change.operation != SyncOperation.DELETE:
                        media_changes = self._process_media(change)
                        for media_change in media_changes:
                            batch.add(media_change)
            
            logger.info(f"Synced {len(changes)} changes")
            return changes
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            raise
    
    def _process_media(self, change: SyncState) -> List[SyncState]:
        """Process media files referenced in a post"""
        try:
            # Load post content
            post = frontmatter.load(str(change.source_path))
            
            # Extract media references
            media_refs = self.media_handler.get_media_references(str(post))
            media_changes = []
            
            # Process each reference
            for ref in media_refs:
                media_path = self.vault_path / ref
                if media_path.exists():
                    # Process media file
                    target_path = self.media_handler.process_media_file(media_path)
                    if target_path:
                        media_changes.append(SyncState(
                            operation=SyncOperation.CREATE,
                            source_path=media_path,
                            target_path=self.jekyll_path / target_path.lstrip('/'),
                            status=change.status,
                            sync_direction=change.sync_direction
                        ))
            
            return media_changes
            
        except Exception as e:
            logger.error(f"Error processing media for {change.source_path}: {e}")
            return []
    
    def cleanup(self):
        """Cleanup unused media files and old backups"""
        try:
            # Cleanup media
            self.media_handler.cleanup_unused()
            
            # Cleanup old backups
            self.atomic._cleanup_old_backups()
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise