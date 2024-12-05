import pytest
from pathlib import Path
import shutil
import time
from sync_engine.core.atomic import AtomicManager, AtomicBatch
from sync_engine.core.types import SyncState, SyncOperation

@pytest.fixture
def atomic_manager(tmp_path):
    manager = AtomicManager()
    manager.backup_dir = tmp_path / ".atomic_backups"
    return manager

def test_batch_operations(atomic_manager, tmp_path):
    # Create test files
    source = tmp_path / "source.txt"
    target = tmp_path / "target.txt"
    source.write_text("test content")
    
    # Create sync operation
    op = SyncState(
        operation=SyncOperation.CREATE,
        source_path=source,
        target_path=target
    )
    
    # Execute batch
    with atomic_manager.batch() as batch:
        batch.add(op)
        
    # Verify operation
    assert target.exists()
    assert target.read_text() == "test content"
    
    # Verify backup was created
    backup_dirs = list(atomic_manager.backup_dir.glob("batch_*"))
    assert len(backup_dirs) == 1
    assert len(list(backup_dirs[0].glob("*"))) == 1

def test_batch_rollback(atomic_manager, tmp_path):
    # Create test files
    source = tmp_path / "source.txt"
    target = tmp_path / "target.txt"
    source.write_text("original content")
    
    # Create sync operation that will fail
    op = SyncState(
        operation=SyncOperation.CREATE,
        source_path=source,
        target_path=target
    )
    
    # Execute batch that raises error
    with pytest.raises(Exception):
        with atomic_manager.batch() as batch:
            batch.add(op)
            raise Exception("Test error")
    
    # Verify original file is unchanged
    assert source.read_text() == "original content"
    assert not target.exists() 

def test_batch_update(atomic_manager, tmp_path):
    """Test updating existing files"""
    # Setup initial files
    source = tmp_path / "source.txt"
    target = tmp_path / "target.txt"
    source.write_text("original")
    target.write_text("old content")
    
    op = SyncState(
        operation=SyncOperation.UPDATE,
        source_path=source,
        target_path=target
    )
    
    # Execute update
    with atomic_manager.batch() as batch:
        batch.add(op)
        
    # Verify update
    assert target.read_text() == "original"
    # Verify backup exists
    assert len(list(atomic_manager.backup_dir.glob("batch_*"))) == 1

def test_batch_delete(atomic_manager, tmp_path):
    """Test deleting files"""
    target = tmp_path / "to_delete.txt"
    target.write_text("delete me")
    
    op = SyncState(
        operation=SyncOperation.DELETE,
        source_path=target,
        target_path=target
    )
    
    with atomic_manager.batch() as batch:
        batch.add(op)
        
    # Verify deletion
    assert not target.exists()
    # Verify backup exists
    backup_dirs = list(atomic_manager.backup_dir.glob("batch_*"))
    assert len(backup_dirs) == 1
    assert len(list(backup_dirs[0].glob("*.txt"))) == 1

def test_backup_cleanup(atomic_manager, tmp_path):
    """Test cleanup of old backups"""
    # Create multiple batches
    for i in range(7):  # More than our keep limit of 5
        source = tmp_path / f"source_{i}.txt"
        source.write_text(f"content {i}")
        
        op = SyncState(
            operation=SyncOperation.CREATE,
            source_path=source,
            target_path=tmp_path / f"target_{i}.txt"
        )
        
        with atomic_manager.batch() as batch:
            batch.add(op)
            time.sleep(0.01)  # Ensure unique timestamps
    
    # Verify only 5 most recent backups remain
    backup_dirs = list(atomic_manager.backup_dir.glob("batch_*"))
    assert len(backup_dirs) == 5
    
    # Verify we kept the most recent ones
    timestamps = [float(d.name.split("_")[1]) for d in backup_dirs]
    assert sorted(timestamps) == timestamps  # Should be in order
    
def test_multiple_operations_in_batch(atomic_manager, tmp_path):
    """Test multiple operations in single batch"""
    # Setup files
    files = []
    for i in range(3):
        source = tmp_path / f"source_{i}.txt"
        target = tmp_path / f"target_{i}.txt"
        source.write_text(f"content {i}")
        files.append((source, target))
    
    # Create batch with multiple operations
    with atomic_manager.batch() as batch:
        for source, target in files:
            op = SyncState(
                operation=SyncOperation.CREATE,
                source_path=source,
                target_path=target
            )
            batch.add(op)
    
    # Verify all operations succeeded
    for _, target in files:
        assert target.exists()
    
    # Verify single backup directory with multiple files
    backup_dirs = list(atomic_manager.backup_dir.glob("batch_*"))
    assert len(backup_dirs) == 1
    assert len(list(backup_dirs[0].glob("*.txt"))) == 3

def test_mixed_operations_rollback(atomic_manager, tmp_path):
    """Test rollback of mixed operations"""
    # Setup initial state
    source1 = tmp_path / "source1.txt"
    target1 = tmp_path / "target1.txt"
    source1.write_text("content 1")
    
    source2 = tmp_path / "source2.txt"
    target2 = tmp_path / "target2.txt"
    target2.write_text("original 2")
    
    # Create batch with create and update operations
    with pytest.raises(Exception):
        with atomic_manager.batch() as batch:
            # Add CREATE operation
            batch.add(SyncState(
                operation=SyncOperation.CREATE,
                source_path=source1,
                target_path=target1
            ))
            # Add UPDATE operation
            batch.add(SyncState(
                operation=SyncOperation.UPDATE,
                source_path=source2,
                target_path=target2
            ))
            raise Exception("Simulated error")
    
    # Verify everything rolled back
    assert not target1.exists()
    assert target2.read_text() == "original 2" 