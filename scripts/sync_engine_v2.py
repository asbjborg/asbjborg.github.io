#!/usr/bin/env python3

import os
import sys
import time
import logging
import frontmatter
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum, auto
from datetime import datetime

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

class SyncOperation(Enum):
    """Enum for different sync operations"""
    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()
    SKIP = auto()

@dataclass
class SyncState:
    """Represents the state of a file in the sync process"""
    operation: SyncOperation
    source_path: Path
    target_path: Optional[Path] = None
    error: Optional[str] = None
    last_modified: Optional[float] = None
    checksum: Optional[str] = None

class SyncEngineV2:
    """V2 of the sync engine with improved architecture and features"""
    
    def __init__(self, config: Dict):
        """
        Initialize the sync engine with configuration
        
        Args:
            config: Dictionary containing configuration parameters
                Required keys:
                - vault_path: Path to Obsidian vault
                - blog_path: Path to Jekyll blog
                Optional keys:
                - vault_atomics_path: Path to atomics folder (default: 'atomics')
                - vault_attachments_path: Path to attachments (default: 'attachments')
                - blog_posts_path: Path to posts folder (default: '_posts')
                - blog_assets_path: Path to assets folder (default: 'assets/img/posts')
        """
        try:
            # Core paths
            self.vault_path = Path(config['vault_path']).expanduser().resolve()
            self.blog_path = Path(config['blog_path']).resolve()
            
            # Derived paths with defaults
            self.atomics_path = self.vault_path / config.get('vault_atomics_path', 'atomics')
            self.attachments_path = self.vault_path / config.get('vault_attachments_path', 'attachments')
            self.posts_path = self.blog_path / config.get('blog_posts_path', '_posts')
            self.assets_path = self.blog_path / config.get('blog_assets_path', 'assets/img/posts')
            
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
        """
        Compute the sync state for a file
        
        Args:
            source_path: Path to the source file
            
        Returns:
            SyncState object representing the current state
        """
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
            
            # Generate target path
            target_path = self._get_target_path(source_path)
            
            # Determine operation
            if not target_path.exists():
                operation = SyncOperation.CREATE
            else:
                # Compare modification times and content if needed
                target_modified = target_path.stat().st_mtime
                if last_modified > target_modified:
                    operation = SyncOperation.UPDATE
                else:
                    operation = SyncOperation.SKIP
            
            return SyncState(
                operation=operation,
                source_path=source_path,
                target_path=target_path,
                last_modified=last_modified
            )
            
        except Exception as e:
            return SyncState(
                operation=SyncOperation.SKIP,
                source_path=source_path,
                error=str(e)
            )
    
    def _get_target_path(self, source_path: Path) -> Path:
        """
        Generate the target Jekyll post path from an Obsidian note path
        
        Args:
            source_path: Path to the source Obsidian note
            
        Returns:
            Path object for the target Jekyll post
        """
        try:
            # Extract date from path (YYYY/MM/DD)
            try:
                date_parts = [
                    source_path.parts[-4],  # Year
                    source_path.parts[-3].zfill(2),  # Month
                    source_path.parts[-2].zfill(2)  # Day
                ]
                date = '-'.join(date_parts)
            except:
                # Fallback to current date
                logger.warning(f"Could not extract date from path {source_path}, using current date")
                date = datetime.now().strftime('%Y-%m-%d')
            
            # Generate safe title from filename
            safe_title = source_path.stem.lower().replace(' ', '-')
            safe_title = ''.join(c for c in safe_title if c.isalnum() or c in '-_')
            
            return self.posts_path / f"{date}-{safe_title}.md"
            
        except Exception as e:
            logger.error(f"Error generating target path for {source_path}: {e}")
            raise
    
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
        """
        Sync a single file
        
        Args:
            source_path: Path to the source file
            state: Current sync state for the file
        """
        try:
            # Load and process the post
            post = frontmatter.load(str(source_path))
            
            # Skip if not marked for publishing
            if not post.get('published', False):
                state.operation = SyncOperation.SKIP
                return
            
            # Process the post (will be expanded in future commits)
            processed_post = self._process_post(post)
            
            # Write the processed post
            if state.target_path:
                with open(state.target_path, 'wb') as f:
                    frontmatter.dump(processed_post, f)
                    f.write(b'\n')  # Ensure file ends with newline
                
                logger.info(f"{'Created' if state.operation == SyncOperation.CREATE else 'Updated'}: {state.target_path}")
            
        except Exception as e:
            state.error = str(e)
            logger.error(f"Error processing {source_path}: {e}")
    
    def _process_post(self, post: frontmatter.Post) -> frontmatter.Post:
        """
        Process a post's frontmatter and content
        
        Args:
            post: The post to process
            
        Returns:
            Processed post
        """
        # Create new post with clean frontmatter
        clean_post = frontmatter.Post(content=post.content)
        
        # Process title
        clean_post['title'] = post.get('title', post.get('name', 'Untitled'))
        
        # Keep original time for update tracking
        if post.get('time'):
            clean_post['time'] = post.get('time')
        
        # Process tags - filter out internal tags
        if post.get('tags'):
            tags = post['tags']
            if isinstance(tags, list):
                filtered_tags = [tag for tag in tags if tag not in ['atomic', 'internal']]
                if filtered_tags:
                    clean_post['tags'] = filtered_tags
        
        # Ensure content ends with newline
        if not clean_post.content.endswith('\n'):
            clean_post.content += '\n'
        
        return clean_post 