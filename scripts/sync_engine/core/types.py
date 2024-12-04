"""
Core types for the sync engine
"""

from enum import Enum, auto
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

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