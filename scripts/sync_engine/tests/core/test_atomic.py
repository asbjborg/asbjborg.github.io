"""Tests for atomic operations.

This module tests:
- File operations (write, copy, move, delete)
- Batch operations (multiple operations)
- Rollback functionality (error handling)
- State management (operation tracking)
"""

import pytest
from pathlib import Path
import shutil
import time
from sync_engine.core.atomic import AtomicManager, AtomicBatch, AtomicOperation
from sync_engine.core.types import SyncState, SyncOperation
from sync_engine.core.config import SyncConfig, ConfigManager

class TestAtomicOperations:
    """Tests for atomic operations"""
    
    def test_atomic_write(self, atomic_manager, test_config):
        """Test atomic write operation.
        
        Features tested:
        - File operations: Atomic write
        - State management: Operation tracking
        - File handling: Content verification
        """
        source = test_config.vault_root / "test.md"
        source.write_text("test content")
        target = test_config.jekyll_root / "_posts/test.md"
        
        operation = AtomicOperation(
            operation_type=SyncOperation.WRITE,
            source_path=source,
            target_path=target,
            state=SyncState.PENDING
        )
        
        atomic_manager.execute_operation(operation)
        assert target.exists()
        assert target.read_text() == "test content"

    def test_atomic_copy(self, atomic_manager, test_config):
        """Test atomic copy operation.
        
        Features tested:
        - File operations: Binary file copying
        - State management: Operation tracking
        - File handling: Content preservation
        """
        source = test_config.vault_root / "test.png"
        source.write_bytes(b"test image")
        target = test_config.jekyll_root / "assets/img/posts/test.png"
        
        operation = AtomicOperation(
            operation_type=SyncOperation.COPY,
            source_path=source,
            target_path=target,
            state=SyncState.PENDING
        )
        
        atomic_manager.execute_operation(operation)
        assert target.exists()
        assert target.read_bytes() == b"test image"

    def test_atomic_move(self, atomic_manager, test_config):
        """Test atomic move operation.
        
        Features tested:
        - File operations: Atomic move
        - State management: Source deletion
        - File handling: Content preservation
        """
        source = test_config.vault_root / "old.md"
        source.write_text("test content")
        target = test_config.vault_root / "new.md"
        
        operation = AtomicOperation(
            operation_type=SyncOperation.MOVE,
            source_path=source,
            target_path=target,
            state=SyncState.PENDING
        )
        
        atomic_manager.execute_operation(operation)
        assert not source.exists()
        assert target.exists()
        assert target.read_text() == "test content"

    def test_atomic_delete(self, atomic_manager, test_config):
        """Test atomic delete operation.
        
        Features tested:
        - File operations: Safe deletion
        - State management: Deletion tracking
        - File handling: Existence verification
        """
        target = test_config.jekyll_root / "_posts/delete_me.md"
        target.write_text("to be deleted")
        
        operation = AtomicOperation(
            operation_type=SyncOperation.DELETE,
            source_path=None,
            target_path=target,
            state=SyncState.PENDING
        )
        
        atomic_manager.execute_operation(operation)
        assert not target.exists()

    def test_atomic_batch(self, atomic_manager, test_config):
        """Test atomic batch operations.
        
        Features tested:
        - Batch operations: Multiple file handling
        - State management: Batch tracking
        - File operations: Mixed operation types
        """
        # Create test files
        post = test_config.vault_root / "test_batch.md"
        post.write_text("test post")
        image = test_config.vault_root / "test_batch.png"
        image.write_bytes(b"test image")
        
        # Create batch operations
        operations = [
            AtomicOperation(
                operation_type=SyncOperation.WRITE,
                source_path=post,
                target_path=test_config.jekyll_root / "_posts/test_batch.md",
                state=SyncState.PENDING
            ),
            AtomicOperation(
                operation_type=SyncOperation.COPY,
                source_path=image,
                target_path=test_config.jekyll_root / "assets/img/posts/test_batch.png",
                state=SyncState.PENDING
            )
        ]
        
        batch = AtomicBatch(manager=atomic_manager, operations=operations)
        batch.execute()
        
        # Verify files were created
        assert (test_config.jekyll_root / "_posts/test_batch.md").exists()
        assert (test_config.jekyll_root / "assets/img/posts/test_batch.png").exists()
        
    def test_atomic_rollback(self, atomic_manager, test_config):
        """Test atomic operation rollback.
        
        Features tested:
        - Rollback: Failed operation handling
        - State management: Rollback tracking
        - Error handling: Exception propagation
        """
        # Create test file that will fail
        source = test_config.vault_root / "test_rollback.md"
        source.write_text("test content")
        target = test_config.jekyll_root / "_posts/test_rollback.md"
        
        # Create a batch with a failing operation
        operations = [
            AtomicOperation(
                operation_type=SyncOperation.WRITE,
                source_path=source,
                target_path=target,
                state=SyncState.PENDING
            ),
            AtomicOperation(
                operation_type=SyncOperation.WRITE,
                source_path=Path("nonexistent.md"),  # This will fail
                target_path=test_config.jekyll_root / "_posts/fail.md",
                state=SyncState.PENDING
            )
        ]
        
        batch = AtomicBatch(manager=atomic_manager, operations=operations)
        
        # Execute batch and expect failure
        with pytest.raises(Exception):
            batch.execute()
            
        # Verify first file was rolled back
        assert not target.exists() 