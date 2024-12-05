"""Change detection module"""

import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import frontmatter

from .types import SyncState, SyncOperation, SyncDirection, PostStatus
from ..handlers.post import PostHandler

logger = logging.getLogger(__name__)

class ChangeDetector:
    """Handles all change detection logic"""
    
    def __init__(self, config: Dict):
        """Initialize change detector"""
        self.config = config
        self.vault_path = Path(config['vault_path'])
        self.jekyll_path = Path(config['jekyll_path'])
        self.atomics_path = self.vault_path / config['vault_atomics']
        self.jekyll_posts = self.jekyll_path / config.get('jekyll_posts', '_posts')
        self.post_handler = PostHandler()
    
    def detect(self) -> List[SyncState]:
        """Detect changes between Obsidian and Jekyll"""
        obsidian_states = self._get_obsidian_states()
        jekyll_states = self._get_jekyll_states()
        return self._compare_states(obsidian_states, jekyll_states)
    
    def _get_obsidian_states(self) -> Dict[str, SyncState]:
        """Get current state of Obsidian atomic notes"""
        states = {}
        
        # Recursively scan all markdown files in atomics
        for post_path in self.atomics_path.rglob('*.md'):
            try:
                # Check if it's in a date folder (YYYY/MM/DD)
                try:
                    date_parts = list(post_path.relative_to(self.atomics_path).parts)[:3]
                    if len(date_parts) < 3:
                        continue  # Not in a date folder
                    # Validate date format
                    datetime.strptime('/'.join(date_parts), '%Y/%m/%d')
                except (ValueError, IndexError):
                    continue  # Not a valid date path
                
                # Check if it's a post (has status in frontmatter)
                post = frontmatter.load(str(post_path))
                status = self.post_handler.get_post_status(post)
                if status is None:  # Not a post
                    continue
                
                # Create Jekyll filename with date prefix
                jekyll_name = f"{'-'.join(date_parts)}-{post_path.stem}.md"
                target_path = self.jekyll_posts / jekyll_name
                
                states[jekyll_name] = SyncState(
                    operation=SyncOperation.NONE,
                    source_path=post_path,
                    target_path=target_path,
                    status=status,
                    sync_direction=SyncDirection.OBSIDIAN_TO_JEKYLL,
                    last_modified=self._get_modified_time(post, post_path)
                )
                
            except Exception as e:
                logger.error(f"Error reading file {post_path}: {e}")
                continue
        
        return states
    
    def _get_jekyll_states(self) -> Dict[str, SyncState]:
        """Get current state of Jekyll posts"""
        states = {}
        for posts_dir in [self.jekyll_posts, self.jekyll_path / '_drafts']:
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