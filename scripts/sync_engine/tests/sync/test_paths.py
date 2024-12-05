"""Tests for sync path handling"""

import pytest
from pathlib import Path
from sync_engine.core.sync import SyncManager

class TestSyncPaths:
    """Tests for sync path handling"""
    
    def test_complex_paths(self, test_config, setup_dirs):
        """Test handling of complex file paths"""
        vault_root, jekyll_path, atomic_path = setup_dirs
        
        # Create post with complex paths
        post_content = """---
status: published
image: ![[atomics/2024/01/15/image with spaces.png]]
---
# Complex Paths

1. ![[atomics/2024/01/15/über.jpg]]
2. ![[atomics/2024/01/15/test#1.png]]
3. ![[atomics/2024/01/15/very-very-very-very-very-very-long-filename.gif]]
"""
        post_path = atomic_path / "complex post with spaces!.md"
        post_path.write_text(post_content)
        
        # Create test images in same folder
        images = [
            'image with spaces.png',
            'über.jpg',
            'test#1.png',
            'very-very-very-very-very-very-long-filename.gif'
        ]
        
        for img in images:
            (atomic_path / img).write_bytes(b'test')
        
        # Run sync
        manager = SyncManager(test_config)
        changes = manager.sync()
        
        # Verify all images were processed
        assert len(changes) == 5  # 1 post + 4 images
        assert len(list(jekyll_path.glob('assets/img/posts/*'))) == 4
        assert (jekyll_path / '_posts/2024-01-15-complex-post-with-spaces.md').exists() 