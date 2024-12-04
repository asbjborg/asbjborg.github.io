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

class PostStatus(Enum):
    """Post status states according to sync strategy"""
    PUBLISHED = "published"
    DRAFT = "draft"
    PRIVATE = "private"
    NONE = None

class SyncOperation(Enum):
    """Sync operations"""
    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()
    SKIP = auto()

class SyncDirection(Enum):
    """Direction of sync for conflict resolution"""
    OBSIDIAN_TO_JEKYLL = auto()
    JEKYLL_TO_OBSIDIAN = auto()
    NONE = auto()

@dataclass
class SyncState:
    """Represents the state of a file in the sync process"""
    operation: SyncOperation
    source_path: Path
    target_path: Optional[Path] = None
    error: Optional[str] = None
    last_modified: Optional[float] = None
    status: PostStatus = PostStatus.NONE
    sync_direction: SyncDirection = SyncDirection.NONE
    checksum: Optional[str] = None

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

    def _get_post_status(self, post: frontmatter.Post) -> PostStatus:
        """
        Get post status according to sync strategy
        
        Status rules:
        - "published": Sync to Jekyll
        - "draft": Keep in Jekyll for revision
        - "private" or None: Remove from Jekyll
        """
        status = post.get('status', None)
        if status == "published":
            return PostStatus.PUBLISHED
        elif status == "draft":
            return PostStatus.DRAFT
        elif status == "private":
            return PostStatus.PRIVATE
        return PostStatus.NONE

    def _should_keep_in_jekyll(self, status: PostStatus) -> bool:
        """
        Determine if post should be kept in Jekyll
        
        Keep if:
        - Published (active post)
        - Draft (working on revision)
        Remove if:
        - Private (explicitly private)
        - None (not a blog post)
        """
        return status in (PostStatus.PUBLISHED, PostStatus.DRAFT)

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
            status = self._get_post_status(post)
            
            # Generate target path
            target_path = self._get_target_path(source_path)
            
            # Determine operation based on status and existence
            if not self._should_keep_in_jekyll(status):
                # Remove from Jekyll if exists
                operation = SyncOperation.DELETE if target_path.exists() else SyncOperation.SKIP
            else:
                # Create or update based on existence and timestamps
                if not target_path.exists():
                    operation = SyncOperation.CREATE
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
                processed_post = self._process_post(post)
                if state.target_path:
                    with open(state.target_path, 'wb') as f:
                        frontmatter.dump(processed_post, f)
                        f.write(b'\n')
                    logger.info(f"{'Created' if state.operation == SyncOperation.CREATE else 'Updated'} Jekyll: {state.target_path}")
            
        except Exception as e:
            state.error = str(e)
            logger.error(f"Error processing {source_path}: {e}")

    def _process_post(self, post: frontmatter.Post) -> frontmatter.Post:
        """Process a post for Jekyll"""
        # Create new post with clean frontmatter
        clean_post = frontmatter.Post(content=post.content)
        
        # Required Jekyll fields
        clean_post['title'] = post.get('title', post.get('name', 'Untitled'))
        
        # Handle time field
        if post.get('time'):
            # Convert HH:MM:SS to seconds since midnight
            try:
                time_str = post['time']
                h, m, s = map(int, time_str.split(':'))
                clean_post['time'] = h * 3600 + m * 60 + s
            except:
                logger.warning(f"Could not parse time: {post.get('time')}")
        
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