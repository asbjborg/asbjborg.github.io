"""
Core sync engine implementation
"""

import os
import logging
import frontmatter
from pathlib import Path
from typing import Dict, Optional, Union
import re
import shutil

from .types import PostStatus, SyncOperation, SyncDirection, SyncState
from ..handlers.post import PostHandler
from ..handlers.media import MediaHandler

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
    
    def __init__(
        self,
        config: Optional[Dict] = None,
        *,
        vault_root: Optional[Union[str, Path]] = None,
        jekyll_root: Optional[Union[str, Path]] = None,
        vault_posts: Optional[str] = None,
        vault_media: Optional[str] = None,
        jekyll_posts: Optional[str] = None,
        jekyll_assets: Optional[str] = None
    ):
        """
        Initialize with either a config dictionary or individual parameters
        
        Args:
            config: Configuration dictionary (optional)
            vault_root: Path to Obsidian vault
            jekyll_root: Path to Jekyll site
            vault_posts: Path to posts in vault (relative to vault_root)
            vault_media: Path to media in vault (relative to vault_root)
            jekyll_posts: Path to posts in Jekyll (relative to jekyll_root)
            jekyll_assets: Path to assets in Jekyll (relative to jekyll_root)
        """
        try:
            if config is not None:
                # Initialize from config dict
                self.vault_path = Path(config['vault_path']).expanduser().resolve()
                self.jekyll_path = Path(config['blog_path']).resolve()
                self.posts_path = self.vault_path / config.get('vault_posts_path', '_posts')
                self.media_path = self.vault_path / config.get('vault_media_path', 'atomics')
                self.jekyll_posts = self.jekyll_path / config.get('jekyll_posts_path', '_posts')
                self.jekyll_assets = self.jekyll_path / config.get('jekyll_assets_path', 'assets/img/posts')
            else:
                # Initialize from individual parameters
                if not all([vault_root, jekyll_root, vault_posts, vault_media, jekyll_posts, jekyll_assets]):
                    raise ValueError("When not using config dict, all parameters must be provided")
                
                self.vault_path = Path(vault_root).expanduser().resolve()
                self.jekyll_path = Path(jekyll_root).resolve()
                self.posts_path = self.vault_path / vault_posts
                self.media_path = self.vault_path / vault_media
                self.jekyll_posts = self.jekyll_path / jekyll_posts
                self.jekyll_assets = self.jekyll_path / jekyll_assets
            
            # Initialize handlers
            self.post_handler = PostHandler()
            self.media_handler = MediaHandler(self.vault_path, self.jekyll_assets)
            
            # Create necessary directories
            self._create_directories()
            
            # Initialize state tracking
            self.sync_states: Dict[Path, SyncState] = {}
            
            logger.info(f"Initialized SyncEngineV2")
            logger.info(f"Vault path: {self.vault_path}")
            logger.info(f"Jekyll path: {self.jekyll_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize SyncEngineV2: {str(e)}")
            raise
    
    def _create_directories(self):
        """Create necessary output directories"""
        self.posts_path.mkdir(parents=True, exist_ok=True)
        self.media_path.mkdir(parents=True, exist_ok=True)
        self.jekyll_posts.mkdir(parents=True, exist_ok=True)
        self.jekyll_assets.mkdir(parents=True, exist_ok=True)
        (self.jekyll_path / "_drafts").mkdir(parents=True, exist_ok=True)
    
    def sync(self, direction: Optional[SyncDirection] = None) -> list[SyncState]:
        """
        Perform sync operation in specified direction
        
        Args:
            direction: Direction to sync (optional, defaults to bidirectional)
            
        Returns:
            List of sync states representing the changes made
        """
        changes = []
        try:
            if direction == SyncDirection.OBSIDIAN_TO_JEKYLL:
                changes.extend(self._sync_obsidian_to_jekyll())
            elif direction == SyncDirection.JEKYLL_TO_OBSIDIAN:
                changes.extend(self._sync_jekyll_to_obsidian())
            else:
                # Bidirectional sync
                changes.extend(self._sync_bidirectional())
            
            return changes
            
        except Exception as e:
            logger.error(f"Error during sync: {e}")
            raise
    
    def _sync_obsidian_to_jekyll(self) -> list[SyncState]:
        """Sync changes from Obsidian to Jekyll"""
        changes = []
        try:
            # Process all markdown files in posts directory
            for post_path in self.posts_path.glob('*.md'):
                # Load post and get status
                post = frontmatter.load(str(post_path))
                status = self.post_handler.get_post_status(post)
                
                # Skip private posts
                if status == PostStatus.PRIVATE:
                    continue
                
                # Determine target path based on status
                if status == PostStatus.DRAFT:
                    target_dir = self.jekyll_path / "_drafts"
                else:
                    target_dir = self.jekyll_posts
                
                # Generate target path
                target_path = target_dir / post_path.name
                
                # Process post content
                processed_post = self.post_handler.process_for_jekyll(post)
                
                # Track media references
                media_refs = self.media_handler.get_media_references(str(post))
                
                # Create or update post
                if not target_path.exists():
                    operation = SyncOperation.CREATE
                else:
                    operation = SyncOperation.UPDATE
                
                # Write post
                with open(target_path, 'wb') as f:
                    frontmatter.dump(processed_post, f)
                    f.write(b'\n')
                
                # Record change
                changes.append(SyncState(
                    operation=operation,
                    source_path=post_path,
                    target_path=target_path,
                    status=status,
                    sync_direction=SyncDirection.OBSIDIAN_TO_JEKYLL
                ))
                
                # Process media files
                for media_ref in media_refs:
                    media_path = self.vault_path / media_ref
                    if media_path.exists():
                        target_media = self.media_handler.process_media_file(media_path)
                        if target_media:
                            changes.append(SyncState(
                                operation=SyncOperation.CREATE,
                                source_path=media_path,
                                target_path=self.jekyll_path / target_media.lstrip('/'),
                                sync_direction=SyncDirection.OBSIDIAN_TO_JEKYLL
                            ))
            
            return changes
            
        except Exception as e:
            logger.error(f"Error during Obsidian to Jekyll sync: {e}")
            raise
    
    def _sync_jekyll_to_obsidian(self) -> list[SyncState]:
        """Sync changes from Jekyll to Obsidian"""
        changes = []
        processed_images = set()  # Track processed images to avoid duplicates
        try:
            # Process all markdown files in posts and drafts
            for post_dir in [self.jekyll_posts, self.jekyll_path / "_drafts"]:
                if not post_dir.exists():
                    continue
                    
                for post_path in post_dir.glob('*.md'):
                    # Load post
                    post = frontmatter.load(str(post_path))
                    
                    # Determine target path
                    target_path = self.posts_path / post_path.name
                    
                    # Convert Jekyll paths to Obsidian paths
                    content = post.content
                    # Convert standard markdown images
                    content = re.sub(
                        r'!\[(.*?)\]\(/assets/img/posts/(.*?)\)',
                        r'![[atomics/\2]]',
                        content
                    )
                    post.content = content
                    
                    # Process media files from frontmatter
                    for key, value in post.metadata.items():
                        if isinstance(value, str) and value.startswith('/assets/img/posts/'):
                            img_path = value
                            img_name = img_path.split('/')[-1]
                            source_path = self.jekyll_path / img_path.lstrip('/')
                            if source_path.exists() and img_name not in processed_images:
                                img_target = self.media_path / img_name
                                img_target.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(source_path, img_target)
                                changes.append(SyncState(
                                    operation=SyncOperation.CREATE,
                                    source_path=source_path,
                                    target_path=img_target,
                                    sync_direction=SyncDirection.JEKYLL_TO_OBSIDIAN
                                ))
                                processed_images.add(img_name)
                                # Update frontmatter
                                post.metadata[key] = f"![[atomics/{img_name}]]"
                    
                    # Create or update post
                    if not target_path.exists():
                        operation = SyncOperation.CREATE
                    else:
                        operation = SyncOperation.UPDATE
                    
                    # Write post with updated content and frontmatter
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(target_path, 'wb') as f:
                        frontmatter.dump(post, f)
                        f.write(b'\n')
                    
                    # Record post change
                    changes.append(SyncState(
                        operation=operation,
                        source_path=post_path,
                        target_path=target_path,
                        sync_direction=SyncDirection.JEKYLL_TO_OBSIDIAN
                    ))
                    
                    # Process media files from content
                    for img_match in re.finditer(r'/assets/img/posts/(.*?)(?=[\s\)])', content):
                        img_path = img_match.group(0)  # Full path
                        img_name = img_match.group(1)  # Just filename
                        source_path = self.jekyll_path / img_path.lstrip('/')
                        if source_path.exists() and img_name not in processed_images:
                            img_target = self.media_path / img_name
                            img_target.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(source_path, img_target)
                            changes.append(SyncState(
                                operation=SyncOperation.CREATE,
                                source_path=source_path,
                                target_path=img_target,
                                sync_direction=SyncDirection.JEKYLL_TO_OBSIDIAN
                            ))
                            processed_images.add(img_name)
            
            return changes
            
        except Exception as e:
            logger.error(f"Error during Jekyll to Obsidian sync: {e}")
            raise
    
    def _sync_bidirectional(self) -> list[SyncState]:
        """Perform bidirectional sync with conflict resolution"""
        changes = []
        try:
            # Get all posts from both sides
            obsidian_posts = {p.name: p for p in self.posts_path.glob('*.md')}
            jekyll_posts = {
                p.name: p for p in self.jekyll_posts.glob('*.md')
            }
            jekyll_drafts = {
                p.name: p for p in (self.jekyll_path / "_drafts").glob('*.md')
            }
            
            # Process each post
            all_posts = set(obsidian_posts) | set(jekyll_posts) | set(jekyll_drafts)
            for post_name in all_posts:
                obsidian_path = obsidian_posts.get(post_name)
                jekyll_path = jekyll_posts.get(post_name) or jekyll_drafts.get(post_name)
                
                if obsidian_path and jekyll_path:
                    # Both exist - check modification times
                    obsidian_post = frontmatter.load(str(obsidian_path))
                    jekyll_post = frontmatter.load(str(jekyll_path))
                    
                    # Get modification times from frontmatter or fallback to file stats
                    obsidian_time = obsidian_post.get('modified')
                    jekyll_time = jekyll_post.get('modified')
                    
                    if obsidian_time and jekyll_time:
                        # Use frontmatter times if available
                        if obsidian_time > jekyll_time:
                            changes.extend(self._sync_obsidian_to_jekyll())
                        else:
                            changes.extend(self._sync_jekyll_to_obsidian())
                    else:
                        # Fallback to file stats
                        obsidian_stat = obsidian_path.stat().st_mtime
                        jekyll_stat = jekyll_path.stat().st_mtime
                        if obsidian_stat > jekyll_stat:
                            changes.extend(self._sync_obsidian_to_jekyll())
                        else:
                            changes.extend(self._sync_jekyll_to_obsidian())
                elif obsidian_path:
                    # Only in Obsidian
                    changes.extend(self._sync_obsidian_to_jekyll())
                else:
                    # Only in Jekyll
                    changes.extend(self._sync_jekyll_to_obsidian())
            
            return changes
            
        except Exception as e:
            logger.error(f"Error during bidirectional sync: {e}")
            raise
    
    def detect_changes(self) -> list[SyncState]:
        """
        Detect changes in both Obsidian and Jekyll directories
        
        Returns:
            List of SyncState objects representing detected changes
        """
        changes = []
        try:
            # Get current state of both sides
            obsidian_posts = {p.name: p for p in self.posts_path.glob('*.md')}
            jekyll_posts = {
                p.name: p for p in self.jekyll_posts.glob('*.md')
            }
            jekyll_drafts = {
                p.name: p for p in (self.jekyll_path / "_drafts").glob('*.md')
            }
            
            # Track processed files to avoid duplicates
            processed = set()
            
            # Check Obsidian posts
            for post_name, post_path in obsidian_posts.items():
                processed.add(post_name)
                
                # Load post to check status
                post = frontmatter.load(str(post_path))
                status = self.post_handler.get_post_status(post)
                
                # Determine target path based on status
                if status == PostStatus.DRAFT:
                    target_dir = self.jekyll_path / "_drafts"
                else:
                    target_dir = self.jekyll_posts
                target_path = target_dir / post_name
                
                # Check if post exists in Jekyll
                jekyll_path = jekyll_posts.get(post_name) or jekyll_drafts.get(post_name)
                
                if not jekyll_path:
                    # New post
                    changes.append(SyncState(
                        operation=SyncOperation.CREATE,
                        source_path=post_path,
                        target_path=target_path,
                        status=status,
                        sync_direction=SyncDirection.OBSIDIAN_TO_JEKYLL
                    ))
                else:
                    # Check for modifications
                    jekyll_post = frontmatter.load(str(jekyll_path))
                    
                    # Check modification times
                    obsidian_time = post.get('modified')
                    jekyll_time = jekyll_post.get('modified')
                    
                    if obsidian_time and jekyll_time:
                        # Use frontmatter times if available
                        if obsidian_time > jekyll_time:
                            changes.append(SyncState(
                                operation=SyncOperation.UPDATE,
                                source_path=post_path,
                                target_path=target_path,
                                status=status,
                                sync_direction=SyncDirection.OBSIDIAN_TO_JEKYLL
                            ))
                    else:
                        # Fallback to file stats
                        obsidian_stat = post_path.stat().st_mtime
                        jekyll_stat = jekyll_path.stat().st_mtime
                        if obsidian_stat > jekyll_stat:
                            changes.append(SyncState(
                                operation=SyncOperation.UPDATE,
                                source_path=post_path,
                                target_path=target_path,
                                status=status,
                                sync_direction=SyncDirection.OBSIDIAN_TO_JEKYLL
                            ))
            
            # Check for deleted posts
            for post_name in set(jekyll_posts) | set(jekyll_drafts):
                if post_name not in processed:
                    # Post exists in Jekyll but not in Obsidian
                    jekyll_path = jekyll_posts.get(post_name) or jekyll_drafts.get(post_name)
                    changes.append(SyncState(
                        operation=SyncOperation.DELETE,
                        source_path=self.posts_path / post_name,  # Original location
                        target_path=jekyll_path,
                        sync_direction=SyncDirection.OBSIDIAN_TO_JEKYLL
                    ))
            
            return changes
            
        except Exception as e:
            logger.error(f"Error detecting changes: {e}")
            raise