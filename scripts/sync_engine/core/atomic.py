"""Atomic operations module"""

import logging
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional, List, Generator, Dict
from contextlib import contextmanager

from .types import SyncState, SyncOperation
from .config import SyncConfig

logger = logging.getLogger(__name__)

class AtomicOperation:
    """Handles low-level atomic file operations"""
    
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
            with AtomicOperation.atomic_write(path) as tmp_path:
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
            with AtomicOperation.atomic_update(path) as tmp_path:
                with open(tmp_path, 'w') as f:
                    f.write('updated content')
        """
        backup_path = None
        if target_path.exists():
            # Create backup
            backup_path = target_path.with_suffix(target_path.suffix + '.bak')
            shutil.copy2(target_path, backup_path)
        
        try:
            with AtomicOperation.atomic_write(target_path) as tmp_path:
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
            with AtomicOperation.atomic_write(target_path) as tmp_path:
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
            AtomicOperation.atomic_copy(source_path, target_path)
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
        self.history = []
        
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
                self._execute_operation(op)
                
            # Add to history
            self.history.extend(batch.operations)
            
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
        for path, backup in batch.backups.items():
            try:
                if backup.exists():
                    shutil.copy2(backup, path)
            except Exception as e:
                logger.error(f"Failed to restore {path} from {backup}: {e}")
                
    def _execute_operation(self, op: SyncState):
        """Execute a single sync operation"""
        if op.operation == SyncOperation.CREATE:
            AtomicOperation.atomic_copy(op.source_path, op.target_path)
        elif op.operation == SyncOperation.UPDATE:
            with AtomicOperation.atomic_update(op.target_path) as tmp_path:
                shutil.copy2(op.source_path, tmp_path)
        elif op.operation == SyncOperation.DELETE:
            AtomicOperation.atomic_delete(op.target_path)

class AtomicBatch:
    """Represents a batch of atomic operations"""
    
    def __init__(self, manager: 'AtomicManager'):
        """Initialize batch"""
        self.manager = manager
        self.operations = []
        self.backups = {}
        self.timestamp = time.time()
        
    def add(self, op: SyncState):
        """Add operation to batch"""
        self.operations.append(op)
        
    def __enter__(self):
        """Enter context manager"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager"""
        if exc_type is None:
            # Success - commit changes
            self.manager._commit_batch(self)
        else:
            # Error - rollback changes
            self.manager._rollback_batch(self)