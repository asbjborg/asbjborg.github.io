"""Change detection module"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import frontmatter
import os
import re
import yaml

from .types import (
    SyncState,
    SyncOperation,
    SyncDirection,
    PostStatus,
    FileChange
)
from .config import SyncConfig
from ..handlers.post import PostHandler
from ..handlers.media import MediaHandler

logger = logging.getLogger(__name__)

class ChangeDetector:
    """Detects changes between Obsidian vault and Jekyll site"""
    
    def __init__(self, config: SyncConfig):
        """Initialize change detector"""
        self.config = config
        self.post_handler = PostHandler(config)
        self.media_handler = MediaHandler(config)
        
        # Initialize paths
        self.vault_root = Path(config.vault_root)
        self.jekyll_root = Path(config.jekyll_root)
        self.atomics_path = self.vault_root / config.vault_atomics
        self.jekyll_posts_path = self.jekyll_root / config.jekyll_posts
        self.jekyll_drafts = self.jekyll_root / '_drafts'
        
        # Create directories if they don't exist
        self.atomics_path.mkdir(parents=True, exist_ok=True)
        self.jekyll_posts_path.mkdir(parents=True, exist_ok=True)
        self.jekyll_drafts.mkdir(parents=True, exist_ok=True)
        
    def detect_changes(self) -> List[FileChange]:
        """Detect changes in both Obsidian and Jekyll directories"""
        logger.debug("Starting change detection")
        
        # Get current states
        obsidian_states = {str(s.source_path): s for s in self._get_obsidian_states()}
        logger.debug(f"Found {len(obsidian_states)} Obsidian files")
        
        jekyll_states = self._get_jekyll_states()
        logger.debug(f"Found {len(jekyll_states)} Jekyll files")
        
        # Compare states and get changes
        changes = self._compare_states(obsidian_states, jekyll_states)
        logger.debug(f"Detected {len(changes)} changes to sync")
        for change in changes:
            logger.debug(f"Change: {change.operation} {change.source_path} -> {change.target_path}")
            
        return changes
    
    def _get_obsidian_states(self) -> List[FileChange]:
        """Get sync states for Obsidian files"""
        states = {}
        try:
            # Walk through atomics directory
            logger.debug(f"Scanning Obsidian directory: {self.atomics_path}")
            for root, _, files in os.walk(self.atomics_path):
                root_path = Path(root)
                for file in files:
                    file_path = root_path / file
                    file_ext = file_path.suffix.lower()
                    logger.debug(f"Found file: {file_path} with extension {file_ext}")
                    
                    if file_ext == '.md':
                        # Process markdown files
                        try:
                            # Read frontmatter
                            with open(file_path) as f:
                                content = f.read()
                                post = frontmatter.loads(content)
                                if not post:
                                    logger.debug(f"No frontmatter found in {file_path}")
                                    continue

                                # Check if it's a post
                                status = post.get('status')
                                if not status or status not in {'published', 'draft', 'private'}:
                                    logger.debug(f"Invalid or missing status in {file_path}")
                                    continue

                                # Extract date and title for Jekyll path
                                try:
                                    date, title = self._extract_date_title(file_path)
                                    jekyll_filename = f"{date.strftime('%Y-%m-%d')}-{title}.md"
                                    target_path = self.jekyll_posts_path / jekyll_filename
                                    logger.debug(f"Mapped {file_path} to Jekyll path {target_path}")

                                except ValueError as e:
                                    logger.error(f"Could not extract date from path: {file_path} - {e}")
                                    continue

                                # Create sync state
                                state = FileChange(
                                    operation=SyncOperation.CREATE,
                                    source_path=file_path,
                                    target_path=target_path,
                                    sync_direction=SyncDirection.OBSIDIAN_TO_JEKYLL,
                                    status=PostStatus(status),
                                    last_modified=os.path.getmtime(file_path)
                                )
                                states[str(file_path)] = state
                                logger.debug(f"Created sync state for {file_path}")

                        except Exception as e:
                            logger.error(f"Error reading file {file_path}: {e}")
                            continue
                            
                    elif file_ext in {'.jpg', '.jpeg', '.png', '.gif'}:
                        # Process image files
                        try:
                            # Use MediaHandler to get target path
                            target_path = self.media_handler.get_jekyll_media_path(file_path)
                            logger.debug(f"Mapped image {file_path} to Jekyll path {target_path}")
                            
                            # Create sync state
                            state = FileChange(
                                operation=SyncOperation.CREATE,
                                source_path=file_path,
                                target_path=target_path,
                                sync_direction=SyncDirection.OBSIDIAN_TO_JEKYLL,
                                status=PostStatus.PUBLISHED,  # Images are always published
                                last_modified=os.path.getmtime(file_path)
                            )
                            states[str(file_path)] = state
                            logger.debug(f"Created sync state for image {file_path}")
                            
                        except Exception as e:
                            logger.error(f"Error processing image {file_path}: {e}")
                            continue

        except Exception as e:
            logger.error(f"Error scanning Obsidian files: {e}")

        return list(states.values())
    
    def _get_jekyll_states(self) -> Dict[str, FileChange]:
        """Get current state of Jekyll posts"""
        states = {}
        for posts_dir in [self.jekyll_posts_path, self.jekyll_drafts]:
            if not posts_dir.exists():
                continue
            for post_path in posts_dir.glob('*.md'):
                try:
                    # Extract date from Jekyll filename (YYYY-MM-DD-title.md)
                    try:
                        date_str = '-'.join(post_path.stem.split('-')[:3])
                        date = datetime.strptime(date_str, '%Y-%m-%d')
                        date_path = date.strftime('%Y/%m/%d')
                        title = post_path.stem.split('-', 3)[3].strip()
                    except (ValueError, IndexError):
                        logger.error(f"Invalid Jekyll filename format: {post_path}")
                        continue
                    
                    post = frontmatter.load(str(post_path))
                    status = self.post_handler.get_post_status(post)
                    if status != PostStatus.PRIVATE:
                        # Create proper atomics path with date structure
                        target_path = self.atomics_path / date_path / f"{title}.md"
                        states[str(post_path)] = FileChange(
                            operation=SyncOperation.CREATE,
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
    
    def _extract_date_title(self, path: Path) -> tuple[datetime, str]:
        """Extract date and title from path"""
        try:
            # First try to extract from path structure (YYYY/MM/DD/title.md)
            parts = list(path.parts)
            if len(parts) >= 4:
                try:
                    year = int(parts[-4])
                    month = int(parts[-3])
                    day = int(parts[-2])
                    title = os.path.splitext(parts[-1])[0]
                    return datetime(year, month, day), title
                except (ValueError, IndexError):
                    pass
                    
            # If that fails, try to extract from filename (YYYY-MM-DD-title.md)
            name = path.stem
            if len(name) >= 10 and name[4] == '-' and name[7] == '-':
                try:
                    year = int(name[0:4])
                    month = int(name[5:7])
                    day = int(name[8:10])
                    title = name[11:] if len(name) > 11 else ''
                    return datetime(year, month, day), title
                except (ValueError, IndexError):
                    pass
                    
            # If no date found, use file modification time
            mtime = path.stat().st_mtime
            dt = datetime.fromtimestamp(mtime)
            return dt, path.stem
            
        except Exception as e:
            logger.error(f"Error extracting date/title from path {path}: {e}")
            raise ValueError(f"Could not extract date and title from path: {path}") from e
    
    def _compare_states(self, obsidian_states: Dict[str, FileChange], jekyll_states: Dict[str, FileChange]) -> List[FileChange]:
        """Compare states and determine required operations"""
        changes = []
        
        # Build lookup tables for faster matching
        obsidian_lookup = {}  # (date, title) -> state
        for path, state in obsidian_states.items():
            try:
                date, title = self._extract_date_title(state.source_path)
                key = (date.date(), title)
                obsidian_lookup[key] = state
            except Exception as e:
                logger.error(f"Error processing Obsidian state {state}: {e}")
                continue
                
        jekyll_lookup = {}  # (date, title) -> state
        for path, state in jekyll_states.items():
            try:
                date, title = self._extract_date_title(state.source_path)
                key = (date.date(), title)
                jekyll_lookup[key] = state
            except Exception as e:
                logger.error(f"Error processing Jekyll state {state}: {e}")
                continue
                
        # Find changes
        for key, obsidian_state in obsidian_lookup.items():
            if key in jekyll_lookup:
                # Post exists in both - check if modified
                jekyll_state = jekyll_lookup[key]
                if obsidian_state.last_modified > jekyll_state.last_modified:
                    obsidian_state.operation = SyncOperation.UPDATE
                    changes.append(obsidian_state)
            else:
                # Post only in Obsidian - create in Jekyll
                changes.append(obsidian_state)
                
        # Find deleted posts (only in Jekyll)
        for key, jekyll_state in jekyll_lookup.items():
            if key not in obsidian_lookup:
                # Post only in Jekyll - delete it
                jekyll_state.operation = SyncOperation.DELETE
                changes.append(jekyll_state)
                
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
    
    def _read_frontmatter(self, file_path: Path) -> Optional[Dict]:
        """Read frontmatter from file"""
        try:
            with open(file_path) as f:
                content = f.read()
                
            # Try python-frontmatter first
            try:
                post = frontmatter.loads(content)
                return post.metadata if post.metadata else None
            except:
                # If that fails, try manual YAML parsing
                if content.startswith('---\n'):
                    end = content.find('\n---\n', 4)
                    if end != -1:
                        yaml_str = content[4:end]
                        # Replace ![[...]] with "[[...]]" to avoid YAML tag issues
                        yaml_str = re.sub(r'!(\[\[.*?\]\])', r'"\1"', yaml_str)
                        try:
                            return yaml.safe_load(yaml_str)
                        except:
                            pass
                return None
                
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None