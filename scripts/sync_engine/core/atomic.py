"""
Atomic operations for safe file handling
"""

import os
import shutil
import logging
import tempfile
from pathlib import Path
from typing import Optional, Callable, TypeVar, Any
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Generic type for operation results

@dataclass
class AtomicOperation:
    """Represents an atomic operation with rollback capability"""
    operation_type: str
    source_path: Path
    target_path: Path
    backup_path: Optional[Path] = None
    timestamp: float = 0.0
    
    def __post_init__(self):
        self.timestamp = datetime.now().timestamp()

class AtomicOperationManager:
    """Manages atomic file operations with rollback support"""
    
    def __init__(self, backup_dir: Optional[Path] = None):
        """
        Initialize atomic operation manager
        
        Args:
            backup_dir: Directory for backups, uses temp dir if None
        """
        self.backup_dir = backup_dir or Path(tempfile.gettempdir()) / "sync_engine_backup"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.operations: list[AtomicOperation] = []
    
    def _create_backup(self, path: Path) -> Optional[Path]:
        """Create backup of a file"""
        try:
            if not path.exists():
                return None
            
            # Create unique backup path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"{path.stem}_{timestamp}{path.suffix}"
            
            # Copy file with metadata
            shutil.copy2(path, backup_path)
            logger.debug(f"Created backup: {backup_path}")
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Error creating backup of {path}: {e}")
            return None
    
    def _restore_backup(self, backup_path: Path, target_path: Path) -> bool:
        """Restore file from backup"""
        try:
            if not backup_path.exists():
                return False
            
            # Restore file with metadata
            shutil.copy2(backup_path, target_path)
            logger.info(f"Restored from backup: {target_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error restoring backup to {target_path}: {e}")
            return False
    
    @contextmanager
    def atomic_write(self, target_path: Path, mode='w', encoding='utf-8'):
        """
        Context manager for atomic file writes
        
        Usage:
            with manager.atomic_write('file.txt') as f:
                f.write('content')
        """
        temp_path = Path(str(target_path) + '.tmp')
        backup_path = None
        
        try:
            # Create backup if file exists
            if target_path.exists():
                backup_path = self._create_backup(target_path)
            
            # Open temp file for writing
            with open(temp_path, mode, encoding=encoding) as f:
                yield f
            
            # Atomic replace
            temp_path.replace(target_path)
            
            # Track operation
            op = AtomicOperation(
                operation_type='write',
                source_path=temp_path,
                target_path=target_path,
                backup_path=backup_path
            )
            self.operations.append(op)
            
        except Exception as e:
            # Restore from backup on error
            if backup_path and backup_path.exists():
                self._restore_backup(backup_path, target_path)
            raise e
        finally:
            # Cleanup temp file
            if temp_path.exists():
                temp_path.unlink()
    
    @contextmanager
    def atomic_operation(self, operation_type: str, source_path: Path, target_path: Path):
        """
        Context manager for atomic operations
        
        Usage:
            with manager.atomic_operation('move', src, dst):
                # do operation
        """
        backup_path = None
        
        try:
            # Create backup if target exists
            if target_path.exists():
                backup_path = self._create_backup(target_path)
            
            # Perform operation
            yield
            
            # Track operation
            op = AtomicOperation(
                operation_type=operation_type,
                source_path=source_path,
                target_path=target_path,
                backup_path=backup_path
            )
            self.operations.append(op)
            
        except Exception as e:
            # Restore from backup on error
            if backup_path and backup_path.exists():
                self._restore_backup(backup_path, target_path)
            raise e
    
    def atomic_copy(self, source_path: Path, target_path: Path):
        """Atomic file copy operation"""
        with self.atomic_operation('copy', source_path, target_path):
            shutil.copy2(source_path, target_path)
            logger.debug(f"Atomic copy: {source_path} -> {target_path}")
    
    def atomic_move(self, source_path: Path, target_path: Path):
        """Atomic file move operation"""
        with self.atomic_operation('move', source_path, target_path):
            shutil.move(source_path, target_path)
            logger.debug(f"Atomic move: {source_path} -> {target_path}")
    
    def atomic_delete(self, target_path: Path):
        """Atomic file delete operation"""
        with self.atomic_operation('delete', target_path, target_path):
            target_path.unlink()
            logger.debug(f"Atomic delete: {target_path}")
    
    def atomic_operation_with_result(self, operation: Callable[[], T]) -> T:
        """
        Execute operation that returns a result atomically
        
        Usage:
            result = manager.atomic_operation_with_result(lambda: some_operation())
        """
        try:
            return operation()
        except Exception as e:
            logger.error(f"Error in atomic operation: {e}")
            raise
    
    def get_operations_since(self, timestamp: float) -> list[AtomicOperation]:
        """Get all operations since given timestamp"""
        return [op for op in self.operations if op.timestamp >= timestamp]
    
    def cleanup_old_backups(self, max_age_hours: int = 24):
        """Clean up old backup files"""
        try:
            current_time = datetime.now().timestamp()
            max_age_seconds = max_age_hours * 3600
            
            for backup_file in self.backup_dir.iterdir():
                if backup_file.is_file():
                    file_age = current_time - backup_file.stat().st_mtime
                    if file_age > max_age_seconds:
                        backup_file.unlink()
                        logger.debug(f"Cleaned up old backup: {backup_file}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup old backups"""
        self.cleanup_old_backups() 