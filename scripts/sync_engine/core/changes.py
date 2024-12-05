"""Change detection module"""

import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import frontmatter
import os

from .types import SyncState, SyncOperation, SyncDirection, PostStatus
from .config import SyncConfig
from ..handlers.post import PostHandler
from ..handlers.media import MediaHandler

logger = logging.getLogger(__name__)

class ChangeDetector:
    """Detects changes between Obsidian vault and Jekyll site"""
    
    def __init__(self, config: SyncConfig):
        """Initialize change detector"""
        self.config = config
        self.post_handler = PostHandler()
        self.media_handler = MediaHandler(config)
        
        # Initialize paths
        self.vault_root = Path(config.vault_root)
        self.jekyll_root = Path(config.jekyll_root)
        self.atomics_path = self.vault_root / config.vault_atomics
        self.jekyll_posts = self.jekyll_root / config.jekyll_posts
        self.jekyll_drafts = self.jekyll_root / '_drafts'
        
        # Create directories if they don't exist
        self.atomics_path.mkdir(parents=True, exist_ok=True)
        self.jekyll_posts.mkdir(parents=True, exist_ok=True)
        self.jekyll_drafts.mkdir(parents=True, exist_ok=True)
        
    def detect_changes(self) -> List[SyncState]:
        """
        Detect changes in both Obsidian and Jekyll directories
        
        Returns:
            List[SyncState]: List of changes to sync
        """
        changes = []
        
        # Get Obsidian states
        obsidian_states = self._get_obsidian_states()
        changes.extend(obsidian_states)
        
        # Get Jekyll states
        jekyll_states = self._get_jekyll_states()
        changes.extend(jekyll_states)
        
        return changes
    
    def _get_obsidian_states(self) -> List[SyncState]:
        """Get sync states for Obsidian files"""
        states = {}
        try:
            # Walk through atomics directory
            for root, _, files in os.walk(self.atomics_path):
                root_path = Path(root)
                for file in files:
                    if not file.endswith('.md'):
                        continue

                    file_path = root_path / file
                    try:
                        # Read frontmatter
                        with open(file_path) as f:
                            content = f.read()
                            frontmatter = self.post_handler.extract_frontmatter(content)
                            if not frontmatter:
                                continue

                            # Check if it's a post
                            status = frontmatter.get('status')
                            if not status or status not in {'published', 'draft', 'private'}:
                                continue

                            # Get relative path from atomics root
                            rel_path = file_path.relative_to(self.atomics_path)
                            target_path = self.jekyll_posts_path / rel_path

                            # Create sync state
                            state = SyncState(
                                operation=SyncOperation.CREATE,
                                source_path=file_path,
                                target_path=target_path,
                                sync_direction=SyncDirection.OBSIDIAN_TO_JEKYLL,
                                status=PostStatus(status),
                                last_modified=os.path.getmtime(file_path)
                            )
                            states[file_path] = state

                    except Exception as e:
                        logger.error(f"Error reading file {file_path}: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error scanning Obsidian files: {e}")

        return list(states.values())
    
    def _get_jekyll_states(self) -> Dict[str, SyncState]:
        """Get current state of Jekyll posts"""
        states = {}
        for posts_dir in [self.jekyll_posts, self.jekyll_root / '_drafts']:
            if not posts_dir.exists():
                continue
            for post_path in posts_dir.glob('*.md'):
                try:
                    # Extract date from Jekyll filename (YYYY-MM-DD-title.md)
                    try:
                        date_str = '-'.join(post_path.stem.split('-')[:3])
                        date = datetime.strptime(date_str, '%Y-%m-%d')
                        date_path = date.strftime('%Y/%m/%d')
                    except (ValueError, IndexError):
                        logger.error(f"Invalid Jekyll filename format: {post_path}")
                        continue
                    
                    post = frontmatter.load(str(post_path))
                    status = self.post_handler.get_post_status(post)
                    if status != PostStatus.PRIVATE:
                        # Create proper atomics path with date structure
                        target_path = self.atomics_path / date_path / post_path.stem.split('-', 3)[3].strip() + '.md'
                        states[post_path.name] = SyncState(
                            operation=SyncOperation.NONE,
                            source_path=post_path,
                            target_path=target_path,
                            status=status,
                            sync_direction=SyncDirection.JEKYLL_TO_OBSIDIAN,
                            last_modified=self._get_modified_time(post, post_path)
                        )
                except Exception as e:
                    logger.error(f"Error reading Jekyll post {post_path}: {e}")
                    continue
        
        return states
    
    def _compare_states(self, obsidian_states: Dict[str, SyncState], jekyll_states: Dict[str, SyncState]) -> List[SyncState]:
        """Compare states and determine required operations"""
        changes = []
        
        # Check Obsidian -> Jekyll changes
        for name, obsidian_state in obsidian_states.items():
            if name not in jekyll_states:
                # New post in Obsidian
                obsidian_state.operation = SyncOperation.CREATE
                changes.append(obsidian_state)
            else:
                # Post exists in both, check for updates
                jekyll_state = jekyll_states[name]
                if obsidian_state.last_modified > jekyll_state.last_modified:
                    obsidian_state.operation = SyncOperation.UPDATE
                    changes.append(obsidian_state)
        
        # Check Jekyll -> Obsidian changes
        for name, jekyll_state in jekyll_states.items():
            if name not in obsidian_states:
                # Post deleted from Obsidian
                jekyll_state.operation = SyncOperation.DELETE
                changes.append(jekyll_state)
            # Updates from Jekyll to Obsidian are handled above
        
        return changes
    
    def _get_modified_time(self, post: frontmatter.Post, path: Path) -> float:
        """Get modification time from frontmatter or file stats"""
        # Try frontmatter first
        modified = post.get('modified')
        if modified:
            if isinstance(modified, (str, datetime)):
                return datetime.fromisoformat(str(modified)).timestamp()
            return float(modified)
        
        # Fallback to file stats
        return path.stat().st_mtime