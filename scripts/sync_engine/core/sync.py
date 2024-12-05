"""Core sync operations module"""

import logging
import frontmatter
from pathlib import Path
from typing import List, Optional
import re
import time

from .types import SyncState, SyncOperation, SyncDirection, PostStatus
from ..handlers.post import PostHandler
from ..handlers.media import MediaHandler

logger = logging.getLogger(__name__)

class SyncOperations:
    """Handles core sync operations"""
    
    def __init__(
        self,
        vault_path: Path,
        jekyll_path: Path,
        posts_path: Path,
        media_path: Path,
        jekyll_posts: Path,
        jekyll_assets: Path
    ):
        """Initialize sync operations"""
        self.vault_path = vault_path
        self.jekyll_path = jekyll_path
        self.posts_path = posts_path
        self.media_path = media_path
        self.jekyll_posts = jekyll_posts
        self.jekyll_assets = jekyll_assets
        
        # Initialize handlers
        self.post_handler = PostHandler()
        self.media_handler = MediaHandler(vault_path, jekyll_assets)
    
    def sync_to_jekyll(self, source_path: Path, status: PostStatus) -> List[SyncState]:
        """Sync a post from Obsidian to Jekyll"""
        changes = []
        try:
            # Load post
            post = frontmatter.load(str(source_path))
            
            # Determine target path based on status
            if status == PostStatus.DRAFT:
                target_dir = self.jekyll_path / "_drafts"
            else:
                target_dir = self.jekyll_posts
            target_path = target_dir / source_path.name
            
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
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, 'wb') as f:
                frontmatter.dump(processed_post, f)
                f.write(b'\n')
            
            # Record change
            changes.append(SyncState(
                operation=operation,
                source_path=source_path,
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
            logger.error(f"Error syncing {source_path} to Jekyll: {e}")
            raise
    
    def sync_to_obsidian(self, source_path: Path) -> List[SyncState]:
        """Sync a post from Jekyll to Obsidian"""
        changes = []
        try:
            # Load post
            post = frontmatter.load(str(source_path))
            
            # Determine target path
            target_path = self.posts_path / source_path.name
            
            # Convert Jekyll paths to Obsidian paths
            content = post.content
            # Convert standard markdown images
            content = content.replace('/assets/img/posts/', 'atomics/')
            content = content.replace('![', '![[').replace(')', ']]')
            post.content = content
            
            # Process media files from frontmatter and content
            media_refs = set()
            
            # Check frontmatter
            for key, value in post.metadata.items():
                if isinstance(value, str) and value.startswith('/assets/img/posts/'):
                    img_path = value
                    img_name = img_path.split('/')[-1]
                    media_refs.add((img_path, img_name))
                    # Update frontmatter
                    post.metadata[key] = f"![[atomics/{img_name}]]"
            
            # Check content for Jekyll-style images
            jekyll_pattern = r'!\[.*?\]\(/assets/img/posts/([^)]+?)\)'
            for match in re.finditer(jekyll_pattern, post.content):
                img_name = match.group(1)
                img_path = f"/assets/img/posts/{img_name}"
                media_refs.add((img_path, img_name))
            
            # Process each media file
            for img_path, img_name in media_refs:
                source_img = self.jekyll_path / img_path.lstrip('/')
                if source_img.exists():
                    target_img = self.media_path / img_name
                    target_img.parent.mkdir(parents=True, exist_ok=True)
                    target_img.write_bytes(source_img.read_bytes())
                    changes.append(SyncState(
                        operation=SyncOperation.CREATE,
                        source_path=source_img,
                        target_path=target_img,
                        sync_direction=SyncDirection.JEKYLL_TO_OBSIDIAN
                    ))
            
            # Create or update post
            if not target_path.exists():
                operation = SyncOperation.CREATE
            else:
                operation = SyncOperation.UPDATE
            
            # Write post
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, 'wb') as f:
                frontmatter.dump(post, f)
                f.write(b'\n')
            
            # Record change
            changes.append(SyncState(
                operation=operation,
                source_path=source_path,
                target_path=target_path,
                sync_direction=SyncDirection.JEKYLL_TO_OBSIDIAN
            ))
            
            return changes
            
        except Exception as e:
            logger.error(f"Error syncing {source_path} to Obsidian: {e}")
            raise
    
    def delete_post(self, target_path: Path) -> Optional[SyncState]:
        """Delete a post and return the change state"""
        try:
            if target_path.exists():
                target_path.unlink()
                return SyncState(
                    operation=SyncOperation.DELETE,
                    source_path=target_path,
                    target_path=None,
                    sync_direction=SyncDirection.NONE
                )
            return None
        except Exception as e:
            logger.error(f"Error deleting {target_path}: {e}")
            raise 
    
    def _sync_post(self, state: SyncState) -> None:
        """Sync a single post"""
        try:
            # Load source post
            post = frontmatter.load(str(state.source_path))
            
            # Skip private posts
            if self.post_handler.get_post_status(post) == PostStatus.PRIVATE:
                return
            
            # Process post based on operation
            if state.operation == SyncOperation.DELETE:
                if state.target_path.exists():
                    state.target_path.unlink()
                
            elif state.operation in [SyncOperation.CREATE, SyncOperation.UPDATE]:
                # Process post content
                if state.sync_direction == SyncDirection.OBSIDIAN_TO_JEKYLL:
                    processed = self.post_handler.process_for_jekyll(post)
                else:
                    processed = self.post_handler.process_for_obsidian(post)
                
                # Update modification time
                processed.metadata['modified'] = time.time()
                processed.metadata['synced'] = True
                
                # Ensure target directory exists
                state.target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write processed post
                frontmatter.dump(processed, str(state.target_path))
                
        except Exception as e:
            logger.error(f"Error syncing post {state.source_path}: {e}")
            raise 