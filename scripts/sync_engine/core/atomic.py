"""Atomic operations module"""

import logging
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional, List, Generator, Dict, TYPE_CHECKING
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
                    if target_path.exists():
                        target_path.unlink()
                    os.rename(tmp_path, target_path)
                except:
                    # On error, ensure temporary file is removed
                    if tmp_path.exists():
                        tmp_path.unlink()
                    raise
        except Exception as e:
            logger.error(f"Error during atomic write to {target_path}: {e}")
            raise

class AtomicManager:
    """Manages atomic file operations with backup and rollback"""
    
    def __init__(self, config: SyncConfig):
        """Initialize atomic manager with config"""
        self.config = config
        self.backup_dir = Path(config.backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.operations: List[AtomicOperation] = []
        
    def write(self, target_path: Path, content: str, make_backup: bool = True) -> None:
        """Write content atomically with optional backup"""
        try:
            # Create backup if requested
            if make_backup and target_path.exists():
                backup_path = self.create_backup(target_path)
            else:
                backup_path = None
                
            # Write content atomically
            with AtomicUtils.atomic_write(target_path) as tmp_path:
                tmp_path.write_text(content)
                
            # Track operation
            self.operations.append(AtomicOperation(
                operation_type=SyncOperation.WRITE,
                source_path=None,
                target_path=target_path,
                state=SyncState.COMPLETED,
                backup_path=backup_path
            ))
            
        except Exception as e:
            logger.error(f"Failed to write {target_path}: {e}")
            raise
            
    def copy(self, source_path: Path, target_path: Path, make_backup: bool = True) -> None:
        """Copy file atomically with optional backup"""
        try:
            # Create backup if requested
            if make_backup and target_path.exists():
                backup_path = self.create_backup(target_path)
            else:
                backup_path = None
                
            # Copy file atomically
            with AtomicUtils.atomic_write(target_path) as tmp_path:
                shutil.copy2(source_path, tmp_path)
                
            # Track operation
            self.operations.append(AtomicOperation(
                operation_type=SyncOperation.COPY,
                source_path=source_path,
                target_path=target_path,
                state=SyncState.COMPLETED,
                backup_path=backup_path
            ))
            
        except Exception as e:
            logger.error(f"Failed to copy {source_path} to {target_path}: {e}")
            raise
            
    def move(self, source_path: Path, target_path: Path, make_backup: bool = True) -> None:
        """Move file atomically with optional backup"""
        try:
            # Create backup if requested
            if make_backup and target_path.exists():
                backup_path = self.create_backup(target_path)
            else:
                backup_path = None
                
            # Move file atomically
            with AtomicUtils.atomic_write(target_path) as tmp_path:
                shutil.move(source_path, tmp_path)
                
            # Track operation
            self.operations.append(AtomicOperation(
                operation_type=SyncOperation.MOVE,
                source_path=source_path,
                target_path=target_path,
                state=SyncState.COMPLETED,
                backup_path=backup_path
            ))
            
        except Exception as e:
            logger.error(f"Failed to move {source_path} to {target_path}: {e}")
            raise
            
    def delete(self, target_path: Path, make_backup: bool = True) -> None:
        """Delete file with optional backup"""
        try:
            # Create backup if requested
            if make_backup and target_path.exists():
                backup_path = self.create_backup(target_path)
            else:
                backup_path = None
                
            # Delete file
            if target_path.exists():
                target_path.unlink()
                
            # Track operation
            self.operations.append(AtomicOperation(
                operation_type=SyncOperation.DELETE,
                source_path=None,
                target_path=target_path,
                state=SyncState.COMPLETED,
                backup_path=backup_path
            ))
            
        except Exception as e:
            logger.error(f"Failed to delete {target_path}: {e}")
            raise
            
    def create_backup(self, file_path: Path) -> Optional[Path]:
        """Create backup of file"""
        try:
            if not file_path.exists():
                return None
                
            # Generate backup path with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_dir / backup_name
            
            # Copy file to backup
            shutil.copy2(file_path, backup_path)
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup of {file_path}: {e}")
            return None
            
    def restore_backup(self, operation: AtomicOperation) -> bool:
        """Restore from backup for given operation"""
        try:
            if not operation.backup_path or not operation.backup_path.exists():
                return False
                
            # Restore from backup
            shutil.copy2(operation.backup_path, operation.target_path)
            
            # Update operation state
            operation.state = SyncState.ROLLED_BACK
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup for {operation.target_path}: {e}")
            return False
            
    def rollback(self) -> None:
        """Rollback all operations in reverse order"""
        for operation in reversed(self.operations):
            try:
                if operation.state != SyncState.COMPLETED:
                    continue
                    
                if operation.operation_type == SyncOperation.DELETE:
                    # Restore deleted file from backup
                    if operation.backup_path:
                        self.restore_backup(operation)
                        
                elif operation.operation_type in {SyncOperation.WRITE, SyncOperation.COPY, SyncOperation.MOVE}:
                    # Restore original file from backup
                    if operation.backup_path:
                        self.restore_backup(operation)
                    else:
                        # If no backup, just delete the file
                        operation.target_path.unlink(missing_ok=True)
                        operation.state = SyncState.ROLLED_BACK
                        
            except Exception as e:
                logger.error(f"Failed to rollback operation {operation}: {e}")
                continue
                
    def cleanup_backups(self, max_age_days: int = 7) -> None:
        """Clean up old backup files"""
        try:
            now = time.time()
            for backup_file in self.backup_dir.iterdir():
                if backup_file.is_file():
                    age_days = (now - backup_file.stat().st_mtime) / (24 * 3600)
                    if age_days > max_age_days:
                        backup_file.unlink()
                        
        except Exception as e:
            logger.error(f"Failed to cleanup backups: {e}")
            pass
            
    def execute_operation(self, operation: AtomicOperation) -> None:
        """Execute a single atomic operation"""
        try:
            if operation.operation_type == SyncOperation.WRITE:
                self.write(operation.target_path, operation.source_path.read_text())
            elif operation.operation_type == SyncOperation.COPY:
                self.copy(operation.source_path, operation.target_path)
            elif operation.operation_type == SyncOperation.MOVE:
                self.move(operation.source_path, operation.target_path)
            elif operation.operation_type == SyncOperation.DELETE:
                self.delete(operation.target_path)
                
            operation.state = SyncState.COMPLETED
            
        except Exception as e:
            operation.state = SyncState.FAILED
            logger.error(f"Operation failed: {e}")
            raise

@dataclass
class AtomicBatch:
    """Represents a batch of atomic operations"""
    manager: AtomicManager
    operations: List[AtomicOperation] = None
    backups: Dict[Path, Path] = None
    
    def __post_init__(self):
        """Initialize collections"""
        if self.operations is None:
            self.operations = []
        if self.backups is None:
            self.backups = {}
            
    def add_operation(self, operation: AtomicOperation) -> None:
        """Add operation to batch"""
        self.operations.append(operation)
        
    def execute(self) -> None:
        """Execute all operations in batch"""
        try:
            # Create backups first
            for op in self.operations:
                if op.target_path and op.target_path.exists():
                    backup = self.manager.create_backup(op.target_path)
                    if backup:
                        self.backups[op.target_path] = backup
                        
            # Execute operations
            for op in self.operations:
                self.manager.execute_operation(op)
                
        except Exception as e:
            logger.error(f"Batch operation failed: {e}")
            self.rollback()
            raise
            
    def rollback(self) -> None:
        """Rollback all operations in batch"""
        logger.info("Rolling back batch operations")
        
        # First restore any backups
        for path, backup in self.backups.items():
            try:
                if backup.exists():
                    shutil.copy2(backup, path)
            except Exception as e:
                logger.error(f"Failed to restore {path} from {backup}: {e}")
                
        # Then remove any newly created files that didn't have backups
        for op in self.operations:
            if op.target_path and op.target_path.exists():
                if op.target_path not in self.backups:
                    try:
                        op.target_path.unlink()
                    except Exception as e:
                        logger.error(f"Failed to remove {op.target_path}: {e}")
                        
        # Mark all operations as rolled back
        for op in self.operations:
            op.state = SyncState.ROLLED_BACK 