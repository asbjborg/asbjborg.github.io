"""Tests for sync cleanup functionality"""

import pytest
from pathlib import Path
from sync_engine.core.sync import SyncManager

class TestSyncCleanup:
    """Tests for sync cleanup functionality"""
    
    def test_cleanup(self, test_config, setup_dirs):
        """Test cleanup functionality"""
        vault_root, jekyll_path, atomic_path = setup_dirs
        
        # Create some test files
        (jekyll_path / 'assets/img/posts/old.png').write_bytes(b'old')
        (vault_root / '.atomic_backups/batch_123').mkdir(parents=True)
        
        # Create a post that doesn't reference the image
        post_path = atomic_path / 'test.md'
        post_path.write_text("""---
status: published
---
# Test Post
No images here
""")
        
        # Run cleanup
        manager = SyncManager(test_config)
        manager.sync()  # First sync to establish post
        manager.cleanup()
        
        # Verify cleanup - unused image should be removed
        assert not (jekyll_path / 'assets/img/posts/old.png').exists()
        assert not (vault_root / '.atomic_backups/batch_123').exists() 