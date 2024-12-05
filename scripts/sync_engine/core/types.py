"""Type definitions for sync engine"""

from enum import Enum, auto
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

class PostStatus(Enum):
    """Post status enum"""
    DRAFT = "draft"
    PUBLISHED = "published"
    PRIVATE = "private"

class SyncOperation(Enum):
    """Sync operation enum"""
    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()

class SyncDirection(Enum):
    """Sync direction enum"""
    OBSIDIAN_TO_JEKYLL = auto()
    JEKYLL_TO_OBSIDIAN = auto()
    NONE = auto()

@dataclass
class SyncState:
    """Represents the state of a sync operation"""
    operation: SyncOperation
    source_path: Path
    target_path: Optional[Path]
    sync_direction: SyncDirection = SyncDirection.OBSIDIAN_TO_JEKYLL
    status: Optional[PostStatus] = None
    last_modified: Optional[float] = None 