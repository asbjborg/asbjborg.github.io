"""Atomic operations module"""

import logging
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional, List, Generator, Dict
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime

from .types import SyncState, SyncOperation
from .config import SyncConfig

logger = logging.getLogger(__name__)

@dataclass
class AtomicOperation:
    """Represents an atomic file operation"""
    operation_type: SyncOperation
    source_path: Optional[Path]
    target_path: Path
    state: SyncState = SyncState.PENDING
    backup_path: Optional[Path] = None

class AtomicUtils:
    """Static utility methods for atomic operations"""
    
    @staticmethod
    @contextmanager
    def atomic_write(target_path: Path) -> Generator[Path, None, None]:
        """
        Context manager for atomic file writes
        
        Args:
            target_path: Path to write to
            
        Yields:
            Temporary path to write to
            
        Example:
            with AtomicUtils.atomic_write(path) as tmp_path:
                with open(tmp_path, 'w') as f:
                    f.write('content')
        """
        # Create parent directories if needed
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create temporary file in same directory
        tmp_dir = target_path.parent
        tmp_prefix = f".{target_path.name}."
        tmp_suffix = ".tmp"
        
        try:
            with tempfile.NamedTemporaryFile(
                mode='w+b',
                dir=tmp_dir,
                prefix=tmp_prefix,
                suffix=tmp_suffix,
                delete=False
            ) as tmp:
                tmp_path = Path(tmp.name)
                try:
                    yield tmp_path
                    # On success, rename temporary file to target
                    if os.name == 'nt':  # Windows
                        if target_path.exists():
                            target_path.unlink()
                    tmp_path.replace(target_path)
                except:
                    # On error, ensure temporary file is removed
                    tmp_path.unlink()
                    raise
        except Exception as e:
            logger.error(f"Error during atomic write to {target_path}: {e}")
            raise
    
    @staticmethod
    @contextmanager
    def atomic_update(target_path: Path) -> Generator[Path, None, None]:
        """
        Context manager for atomic file updates with backup
        
        Args:
            target_path: Path to update
            
        Yields:
            Temporary path to write to
            
        Example:
            with AtomicUtils.atomic_update(path) as tmp_path:
                with open(tmp_path, 'w') as f:
                    f.write('updated content')
        """
        backup_path = None
        if target_path.exists():
            # Create backup
            backup_path = target_path.with_suffix(target_path.suffix + '.bak')
            shutil.copy2(target_path, backup_path)
        
        try:
            with AtomicUtils.atomic_write(target_path) as tmp_path:
                yield tmp_path
                if backup_path:
                    backup_path.unlink()
        except:
            # Restore from backup on error
            if backup_path and backup_path.exists():
                backup_path.replace(target_path)
            raise
    
    @staticmethod
    def atomic_copy(source_path: Path, target_path: Path) -> None:
        """
        Atomically copy a file
        
        Args:
            source_path: Path to copy from
            target_path: Path to copy to
        """
        try:
            with AtomicUtils.atomic_write(target_path) as tmp_path:
                shutil.copy2(source_path, tmp_path)
        except Exception as e:
            logger.error(f"Error copying {source_path} to {target_path}: {e}")
            raise
    
    @staticmethod
    def atomic_move(source_path: Path, target_path: Path) -> None:
        """
        Atomically move a file
        
        Args:
            source_path: Path to move from
            target_path: Path to move to
        """
        try:
            # First copy atomically
            AtomicUtils.atomic_copy(source_path, target_path)
            # Then remove source
            source_path.unlink()
        except Exception as e:
            logger.error(f"Error moving {source_path} to {target_path}: {e}")
            raise
    
    @staticmethod
    def atomic_delete(target_path: Path, backup: bool = True) -> Optional[Path]:
        """
        Atomically delete a file with optional backup
        
        Args:
            target_path: Path to delete
            backup: Whether to keep a backup
            
        Returns:
            Path to backup file if backup=True, None otherwise
        """
        try:
            if not target_path.exists():
                return None
            
            if backup:
                # Create backup
                backup_path = target_path.with_suffix(target_path.suffix + '.bak')
                shutil.copy2(target_path, backup_path)
                target_path.unlink()
                return backup_path
            else:
                target_path.unlink()
                return None
                
        except Exception as e:
            logger.error(f"Error deleting {target_path}: {e}")
            raise

class AtomicManager:
    """Handles high-level atomic operations with history tracking"""
    
    def __init__(self, config: Optional[SyncConfig] = None):
        """
        Initialize atomic manager
        
        Args:
            config: Optional configuration
        """
        self.config = config
        self.backup_dir = Path(config.backup_dir if config else '.atomic_backups')
        self.backup_count = int(config.backup_count if config else 5)
        self.backup_dir.mkdir(exist_ok=True)
        self.history: List[AtomicOperation] = []
        
    def execute_operation(self, operation: AtomicOperation) -> None:
        """Execute a single atomic operation"""
        try:
            if operation.operation_type == SyncOperation.WRITE:
                with AtomicUtils.atomic_write(operation.target_path) as tmp_path:
                    shutil.copy2(operation.source_path, tmp_path)
            elif operation.operation_type == SyncOperation.COPY:
                AtomicUtils.atomic_copy(operation.source_path, operation.target_path)
            elif operation.operation_type == SyncOperation.MOVE:
                AtomicUtils.atomic_move(operation.source_path, operation.target_path)
            elif operation.operation_type == SyncOperation.DELETE:
                backup_path = AtomicUtils.atomic_delete(operation.target_path)
                operation.backup_path = backup_path
            
            operation.state = SyncState.COMPLETED
            self.history.append(operation)
            
        except Exception as e:
            operation.state = SyncState.FAILED
            logger.error(f"Operation failed: {e}")
            raise
        
    def execute_batch(self, batch: 'AtomicBatch') -> None:
        """Execute a batch of operations atomically"""
        self._commit_batch(batch)
        
    def batch(self) -> 'AtomicBatch':
        """Create new atomic batch"""
        return AtomicBatch(self)
        
    def _backup_file(self, path: Path) -> Optional[Path]:
        """Create backup of file"""
        if not path.exists():
            return None
            
        # Create timestamped backup directory
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        backup_dir = self.backup_dir / f"batch_{timestamp}"
        backup_dir.mkdir(exist_ok=True)
        
        # Copy file to backup
        backup_path = backup_dir / path.name
        shutil.copy2(path, backup_path)
        
        return backup_path
        
    def cleanup_backups(self, keep: Optional[int] = None):
        """
        Remove old backup directories
        
        Args:
            keep: Number of backups to keep, defaults to config.backup_count
        """
        keep = keep or self.backup_count
        backup_dirs = sorted(self.backup_dir.glob('batch_*'))
        while len(backup_dirs) > keep:
            shutil.rmtree(backup_dirs[0])
            backup_dirs.pop(0)
            
    def _commit_batch(self, batch: 'AtomicBatch'):
        """Commit a batch of operations"""
        try:
            # Create backups first
            for op in batch.operations:
                if op.target_path and op.target_path.exists():
                    backup = self._backup_file(op.target_path)
                    if backup:
                        batch.backups[op.target_path] = backup
            
            # Execute operations
            for op in batch.operations:
                self.execute_operation(op)
                
            # Clean up old backups if needed
            if self.config and self.config.auto_cleanup:
                self.cleanup_backups()
                
        except Exception as e:
            logger.error(f"Batch operation failed: {e}")
            self._rollback_batch(batch)
            raise
            
    def _rollback_batch(self, batch: 'AtomicBatch'):
        """Rollback a batch of operations"""
        logger.info("Rolling back batch operations")
        
        # First restore any backups
        for path, backup in batch.backups.items():
            try:
                if backup.exists():
                    shutil.copy2(backup, path)
            except Exception as e:
                logger.error(f"Failed to restore {path} from {backup}: {e}")
        
        # Then remove any newly created files that didn't have backups
        for op in batch.operations:
            if op.target_path and op.target_path.exists():
                if op.target_path not in batch.backups:
                    try:
                        op.target_path.unlink()
                    except Exception as e:
                        logger.error(f"Failed to remove {op.target_path}: {e}")
    
    def _backup(self, target_path: Path) -> None:
        """Create backup of target file"""
        if not target_path.exists():
            return
            
        # Create backup directory
        backup_dir = target_path.parent / '.atomic_backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create backup with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f"{target_path.name}.{timestamp}.bak"
        
        # Copy file to backup
        import shutil
        shutil.copy2(target_path, backup_path)
        
    def write(self, target_path: Path, content: str, make_backup: bool = True) -> None:
        """Write content to file atomically"""
        if make_backup:
            self._backup(target_path)
            
        # Create parent directories
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temp file first
        temp_path = target_path.with_suffix(target_path.suffix + '.tmp')
        temp_path.write_text(content)
        
        # Move temp file to target
        temp_path.replace(target_path)
        
    def copy(self, source_path: Path, target_path: Path, make_backup: bool = True) -> None:
        """Copy file atomically"""
        try:
            # Create parent directories
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup if needed
            if make_backup and target_path.exists():
                self._backup(target_path)
            
            # Copy to temp file first
            temp_path = target_path.with_suffix(target_path.suffix + '.tmp')
            shutil.copy2(source_path, temp_path)
            
            # Move temp file to target
            temp_path.replace(target_path)
            
            # Record operation
            operation = AtomicOperation(
                operation_type=SyncOperation.COPY,
                source_path=source_path,
                target_path=target_path,
                state=SyncState.COMPLETED
            )
            self.history.append(operation)
            
        except Exception as e:
            logger.error(f"Failed to copy {source_path} to {target_path}: {e}")
            raise

@dataclass
class AtomicBatch:
    """Represents a batch of atomic operations"""
    operations: List[AtomicOperation]
    backups: Dict[Path, Path] = None
    
    def __post_init__(self):
        """Initialize backups dict"""
        if self.backups is None:
            self.backups = {}