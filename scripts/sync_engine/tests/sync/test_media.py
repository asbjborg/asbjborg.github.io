"""Tests for sync media handling"""

import pytest
from pathlib import Path
from sync_engine.core.sync import SyncManager

class TestSyncMedia:
    """Tests for sync media handling"""
    
    def test_media_handling(self, test_config, setup_dirs):
        """Test media file processing"""
        vault_root, jekyll_path, atomic_path = setup_dirs
        
        # Create post with multiple images
        post_content = """---
status: published
image: ![[atomics/2024/01/15/featured.jpg]]
---
# Test Post

Image 1: ![[atomics/2024/01/15/test1.png]]
Image 2: ![[atomics/2024/01/15/test2.png]]
"""
        post_path = atomic_path / 'media-test.md'
        post_path.write_text(post_content)
        
        # Create test images in same folder
        (atomic_path / 'featured.jpg').write_bytes(b'jpg data')
        (atomic_path / 'test1.png').write_bytes(b'png1 data')
        (atomic_path / 'test2.png').write_bytes(b'png2 data')
        
        # Run sync
        manager = SyncManager(test_config)
        changes = manager.sync()
        
        # Verify all images were processed
        assert len(changes) == 4  # 1 post + 3 images
        assert len(list(jekyll_path.glob('assets/img/posts/*'))) == 3
        assert (jekyll_path / '_posts/2024-01-15-media-test.md').exists() 