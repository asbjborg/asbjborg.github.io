"""Tests for sync error handling"""

import pytest
from pathlib import Path
from sync_engine.core.sync import SyncManager

class TestSyncErrors:
    """Tests for sync error handling"""
    
    def test_sync_with_errors(self, test_config, setup_dirs):
        """Test sync with some errors"""
        vault_root, jekyll_path, atomic_path = setup_dirs
        
        # Create valid post
        post1 = atomic_path / 'valid-note.md'
        post1.write_text("""---
status: published
---
Valid post""")
        
        # Create invalid post
        post2 = atomic_path / 'invalid-note.md'
        post2.write_text("Invalid frontmatter")
        
        # Run sync
        manager = SyncManager(test_config)
        changes = manager.sync()
        
        # Verify only valid post was synced
        assert len(changes) == 1
        assert changes[0].source_path.name == 'valid-note.md'
        assert (jekyll_path / '_posts/2024-01-15-valid-note.md').exists()

    def test_atomic_rollback(self, test_config, setup_dirs):
        """Test atomic rollback on error"""
        vault_root, jekyll_path, atomic_path = setup_dirs
        
        # Create post and image
        post_path = atomic_path / 'test-rollback.md'
        post_path.write_text("""---
status: published
---
Test with ![[atomics/2024/01/15/test.png]]""")
        
        img_path = atomic_path / 'test.png'
        img_path.write_bytes(b'png data')
        
        # Create MediaHandler that raises an error
        class ErrorMediaHandler:
            def get_media_references(self, _):
                raise Exception("Simulated error")
        
        # Create manager with error-prone handler
        manager = SyncManager(test_config)
        manager.media_handler = ErrorMediaHandler()
        
        # Run sync and verify rollback
        with pytest.raises(Exception):
            manager.sync()
        
        # Verify no files were created
        assert not list(jekyll_path.glob('_posts/*'))
        assert not list(jekyll_path.glob('assets/img/posts/*')) 