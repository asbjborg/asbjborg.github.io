"""Tests for path handling"""

import pytest
from pathlib import Path
from sync_engine.core.sync import SyncManager
from PIL import Image

class TestSyncPaths:
    """Tests for path handling"""
    
    def test_complex_paths(self, test_config, setup_dirs):
        """Test handling of complex file paths"""
        vault_root, jekyll_path, atomic_path = setup_dirs
        
        # Create post with complex paths
        post_content = """---
status: published
image: "[[atomics/2024/01/15/image with spaces.png]]"
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
        
        # Create date directory
        img_dir = atomic_path / '2024/01/15'
        img_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test images
        test_img = Image.new('RGB', (100, 100), color='red')
        for img in images:
            if img.endswith('.gif'):
                # Create GIF with one frame
                test_img.save(img_dir / img, format='GIF', save_all=True, append_images=[test_img])
            else:
                # Save as normal image
                test_img.save(img_dir / img)
        
        # Run sync
        manager = SyncManager(test_config)
        changes = manager.sync()
        
        # Verify all images were processed
        assert len(changes) == 5  # 1 post + 4 images
        
        # Verify files exist in Jekyll
        assert (jekyll_path / '_posts/complex-post-with-spaces.md').exists()
        for change in changes:
            if change.target_path:
                assert change.target_path.exists() 