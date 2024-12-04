"""
Core sync engine implementation
"""

import os
import logging
import frontmatter
from pathlib import Path
from typing import Dict

from .types import PostStatus, SyncOperation, SyncDirection, SyncState
from ..handlers.post import PostHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser('~/Library/Logs/obsidian-blog-sync.log'))
    ]
)
logger = logging.getLogger(__name__)

class SyncEngineV2:
    """V2 of the sync engine with improved architecture and features"""
    
    def __init__(self, config: Dict):
        """Initialize with configuration"""
        try:
            # Core paths
            self.vault_path = Path(config['vault_path']).expanduser().resolve()
            self.blog_path = Path(config['blog_path']).resolve()
            
            # Derived paths with defaults
            self.atomics_path = self.vault_path / config.get('vault_atomics_path', 'atomics')
            self.attachments_path = self.vault_path / config.get('vault_attachments_path', 'attachments')
            self.posts_path = self.blog_path / config.get('blog_posts_path', '_posts')
            self.assets_path = self.blog_path / config.get('blog_assets_path', 'assets/img/posts')
            
            # Initialize handlers
            self.post_handler = PostHandler()
            
            # Validate paths
            self._validate_paths()
            
            # Create necessary directories
            self._create_directories()
            
            # Initialize state tracking
            self.sync_states: Dict[Path, SyncState] = {}
            
            logger.info(f"Initialized SyncEngineV2")
            logger.info(f"Vault path: {self.vault_path}")
            logger.info(f"Blog path: {self.blog_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize SyncEngineV2: {str(e)}")
            raise
    
    def _validate_paths(self):
        """Validate all required paths exist"""
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {self.vault_path}")
        if not self.atomics_path.exists():
            raise ValueError(f"Atomics path does not exist: {self.atomics_path}")
        if not self.attachments_path.exists():
            raise ValueError(f"Attachments path does not exist: {self.attachments_path}")
    
    def _create_directories(self):
        """Create necessary output directories"""
        self.posts_path.mkdir(exist_ok=True)
        self.assets_path.mkdir(parents=True, exist_ok=True)
    
    def _compute_file_state(self, source_path: Path) -> SyncState:
        """Compute sync state for a file"""
        try:
            # Basic file checks
            if not source_path.exists():
                return SyncState(
                    operation=SyncOperation.SKIP,
                    source_path=source_path,
                    error="Source file does not exist"
                )
            
            # Get file metadata
            last_modified = source_path.stat().st_mtime
            
            # Load post and get status
            post = frontmatter.load(str(source_path))
            status = self.post_handler.get_post_status(post)
            
            # Generate target path
            target_path = self.post_handler.get_jekyll_path(source_path, self.posts_path)
            
            # Determine operation based on status and existence
            if not self.post_handler.should_keep_in_jekyll(status):
                # Remove from Jekyll if exists
                operation = SyncOperation.DELETE if target_path.exists() else SyncOperation.SKIP
                sync_direction = SyncDirection.NONE
            else:
                # Create or update based on existence and timestamps
                if not target_path.exists():
                    operation = SyncOperation.CREATE
                    sync_direction = SyncDirection.OBSIDIAN_TO_JEKYLL
                else:
                    # Compare modification times
                    target_modified = target_path.stat().st_mtime
                    if last_modified > target_modified:
                        operation = SyncOperation.UPDATE
                        sync_direction = SyncDirection.OBSIDIAN_TO_JEKYLL
                    elif target_modified > last_modified:
                        operation = SyncOperation.UPDATE
                        sync_direction = SyncDirection.JEKYLL_TO_OBSIDIAN
                    else:
                        operation = SyncOperation.SKIP
                        sync_direction = SyncDirection.NONE
            
            return SyncState(
                operation=operation,
                source_path=source_path,
                target_path=target_path,
                last_modified=last_modified,
                status=status,
                sync_direction=sync_direction
            )
            
        except Exception as e:
            return SyncState(
                operation=SyncOperation.SKIP,
                source_path=source_path,
                error=str(e)
            )
    
    def scan(self) -> Dict[Path, SyncState]:
        """
        Scan source directory and compute sync states
        
        Returns:
            Dictionary mapping source paths to their sync states
        """
        logger.info("Starting scan...")
        try:
            for path in self.atomics_path.rglob('*.md'):
                self.sync_states[path] = self._compute_file_state(path)
            
            # Log summary
            operations = {op: sum(1 for s in self.sync_states.values() if s.operation == op)
                        for op in SyncOperation}
            logger.info(f"Scan complete. Operations needed: {operations}")
            
            return self.sync_states
            
        except Exception as e:
            logger.error(f"Error during scan: {e}")
            raise
    
    def sync(self, dry_run: bool = False) -> Dict[Path, SyncState]:
        """
        Perform the sync operation
        
        Args:
            dry_run: If True, only simulate the sync
            
        Returns:
            Dictionary mapping source paths to their final sync states
        """
        if not self.sync_states:
            self.scan()
        
        logger.info(f"Starting {'dry run' if dry_run else 'sync'}...")
        
        try:
            for source_path, state in self.sync_states.items():
                if state.operation in (SyncOperation.CREATE, SyncOperation.UPDATE):
                    if not dry_run:
                        self._sync_file(source_path, state)
                elif state.operation == SyncOperation.DELETE:
                    if not dry_run and state.target_path:
                        state.target_path.unlink()
                        logger.info(f"Deleted: {state.target_path}")
            
            return self.sync_states
            
        except Exception as e:
            logger.error(f"Error during sync: {e}")
            raise
    
    def _sync_file(self, source_path: Path, state: SyncState):
        """Sync a single file"""
        try:
            # Load source post
            post = frontmatter.load(str(source_path))
            
            if state.operation == SyncOperation.DELETE:
                if state.target_path and state.target_path.exists():
                    state.target_path.unlink()
                    logger.info(f"Deleted: {state.target_path}")
                return
            
            if state.sync_direction == SyncDirection.JEKYLL_TO_OBSIDIAN:
                # Update only content in Obsidian, preserve frontmatter
                if state.target_path:
                    jekyll_post = frontmatter.load(str(state.target_path))
                    post.content = jekyll_post.content
                    with open(source_path, 'wb') as f:
                        frontmatter.dump(post, f)
                        f.write(b'\n')
                    logger.info(f"Updated Obsidian: {source_path}")
            else:
                # Process for Jekyll
                processed_post = self.post_handler.process_for_jekyll(post)
                if state.target_path:
                    with open(state.target_path, 'wb') as f:
                        frontmatter.dump(processed_post, f)
                        f.write(b'\n')
                    logger.info(f"{'Created' if state.operation == SyncOperation.CREATE else 'Updated'} Jekyll: {state.target_path}")
            
        except Exception as e:
            state.error = str(e)
            logger.error(f"Error processing {source_path}: {e}") 