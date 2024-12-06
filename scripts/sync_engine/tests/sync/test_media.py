"""Tests for sync media handling.

This module tests:
- Media file processing (multiple formats)
- Media reference handling (frontmatter and inline)
- File synchronization (vault to Jekyll)
- Path verification (existence checks)
"""

import pytest
from pathlib import Path
from PIL import Image
from sync_engine.core.sync import SyncManager

class TestSyncMedia:
    """Tests for sync media handling"""
    
    def test_media_handling(self, test_config, setup_dirs):
        """Test media file processing.
        
        Features tested:
        - Media handling: Multiple image formats (JPEG, PNG)
        - Media handling: Frontmatter image references
        - Media handling: Inline image references
        - File operations: Directory creation
        - File operations: Image saving
        - Path handling: Jekyll asset paths
        - Verification: File existence checks
        """
        vault_root, jekyll_path, atomic_path = setup_dirs
        
        # Create post with multiple images
        post_content = """---
status: published
image: "[[atomics/2024/01/15/featured.jpg]]"
---
# Test Post

Image 1: ![[atomics/2024/01/15/test1.png]]
Image 2: ![[atomics/2024/01/15/test2.png]]
"""
        post_path = atomic_path / '2024/01/15/media-test.md'
        post_path.parent.mkdir(parents=True, exist_ok=True)
        post_path.write_text(post_content)
        
        # Create test images in same folder
        img = Image.new('RGB', (100, 100), color='red')
        img.save(post_path.parent / 'featured.jpg', format='JPEG')
        img.save(post_path.parent / 'test1.png')
        img.save(post_path.parent / 'test2.png')
        
        # Run sync
        manager = SyncManager(test_config)
        changes = manager.sync()
        
        # Verify all images were processed
        assert len(changes) == 4  # 1 post + 3 images
        assert len(list(jekyll_path.glob('assets/img/posts/*'))) == 3
        assert (jekyll_path / '_posts/2024-01-15-media-test.md').exists() 