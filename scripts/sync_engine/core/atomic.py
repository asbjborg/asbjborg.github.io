"""Atomic file operations module"""

import os
import shutil
import logging
import tempfile
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Optional
import time

logger = logging.getLogger(__name__)

class AtomicOperation:
    """Handles atomic file operations"""
    
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

class AtomicBatch:
    """Represents a batch of atomic operations"""
    def __init__(self):
        self.operations = []
        self.backups = {}
        self.timestamp = time.time()
        
    def add(self, operation: SyncState):
        """Add operation to batch"""
        self.operations.append(operation)

class AtomicManager:
    """Handles atomic operations with history tracking"""
    
    def __init__(self):
        self.history = []
        self.backup_dir = Path(".atomic_backups")
        self.backup_dir.mkdir(exist_ok=True)
        
    @contextmanager
    def batch(self):
        """Batch multiple operations atomically"""
        batch = AtomicBatch()
        try:
            yield batch
            self._commit_batch(batch)
        except:
            self._rollback_batch(batch)
            raise
            
    def _commit_batch(self, batch: AtomicBatch):
        """Commit a batch of operations"""
        try:
            # Create batch backup directory
            batch_dir = self.backup_dir / f"batch_{batch.timestamp}"
            batch_dir.mkdir()
            
            # Backup files before changes
            for op in batch.operations:
                if op.source_path.exists():
                    backup_path = batch_dir / op.source_path.name
                    shutil.copy2(op.source_path, backup_path)
                    batch.backups[op.source_path] = backup_path
            
            # Execute operations
            for op in batch.operations:
                self._execute_operation(op)
            
            # Record successful batch
            self.history.append(batch)
            
            # Cleanup old backups (keep last 5)
            self._cleanup_old_backups()
            
        except Exception as e:
            logger.error(f"Error committing batch: {e}")
            self._rollback_batch(batch)
            raise
            
    def _rollback_batch(self, batch: AtomicBatch):
        """Rollback a batch of operations"""
        for path, backup in batch.backups.items():
            if backup.exists():
                shutil.copy2(backup, path)
                
    def _cleanup_old_backups(self, keep: int = 5):
        """Cleanup old backup directories"""
        dirs = sorted(self.backup_dir.glob("batch_*"), 
                     key=lambda x: float(x.name.split("_")[1]))
        for old_dir in dirs[:-keep]:
            shutil.rmtree(old_dir)
            
    def _execute_operation(self, op: SyncState):
        """Execute a single sync operation"""
        if op.operation == SyncOperation.CREATE:
            AtomicOperation.atomic_copy(op.source_path, op.target_path)
        elif op.operation == SyncOperation.UPDATE:
            AtomicOperation.atomic_update(op.target_path)
        elif op.operation == SyncOperation.DELETE:
            AtomicOperation.atomic_delete(op.target_path)