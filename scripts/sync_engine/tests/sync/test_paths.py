"""Tests for path handling"""

import pytest
import time
from pathlib import Path
from sync_engine.core.sync import SyncManager
from PIL import Image

class TestSyncPaths:
    """Tests for path handling"""
    
    def test_complex_paths(self, test_config, setup_dirs):
        """Test handling of complex file paths"""
        # Disable auto cleanup for this test
        test_config.auto_cleanup = False
        
        vault_root, jekyll_root, atomic_path = setup_dirs
        
        # Create date directory
        date_dir = atomic_path / '2024/01/15'
        date_dir.mkdir(parents=True, exist_ok=True)
        
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
        post_path = date_dir / "complex post with spaces!.md"
        post_path.write_text(post_content)
        
        # Create test images in same folder
        images = [
            'image with spaces.png',
            'über.jpg',
            'test#1.png',
            'very-very-very-very-very-very-long-filename.gif'
        ]
        
        # Create test images
        test_img = Image.new('RGB', (100, 100), color='red')
        for img in images:
            if img.endswith('.gif'):
                # Create GIF with one frame
                test_img.save(date_dir / img, format='GIF', save_all=True, append_images=[test_img])
            else:
                # Save as normal image
                test_img.save(date_dir / img)
                
        # Print paths for debugging
        print(f"\nTest file paths:")
        print(f"vault_root: {vault_root}")
        print(f"jekyll_root: {jekyll_root}")
        print(f"atomic_path: {atomic_path}")
        print(f"date_dir: {date_dir}")
        print(f"post_path: {post_path}")
        for img in images:
            print(f"image: {date_dir / img}")
        print()
        
        # Run sync
        manager = SyncManager(test_config)
        changes = manager.sync()
        
        # Print changes for debugging
        print("\nSync changes:")
        for change in changes:
            print(f"source: {change.source_path}")
            print(f"target: {change.target_path}")
            print(f"exists: {change.target_path.exists()}")
            print()
            
        # Verify all images were processed
        assert len(changes) == 5  # 1 post + 4 images
        
        # Verify files exist in Jekyll
        assert (jekyll_root / '_posts/2024-01-15-complex-post-with-spaces.md').exists()
        for change in changes:
            if change.target_path:
                assert change.target_path.exists()

    def test_auto_cleanup(self, test_config, setup_dirs):
        """Test auto cleanup functionality"""
        # Enable auto cleanup for this test
        test_config.auto_cleanup = True
        test_config.cleanup_delay = 0.5  # Half second delay
        
        vault_root, jekyll_root, atomic_path = setup_dirs
        
        # Create test post with image
        date_dir = atomic_path / '2024/01/15'
        date_dir.mkdir(parents=True, exist_ok=True)
        
        post_content = """---
status: published
image: "[[atomics/2024/01/15/test.png]]"
---
# Test Post

![[atomics/2024/01/15/test.png]]
"""
        post_path = date_dir / "test_post.md"
        post_path.write_text(post_content)
        
        # Create test image
        test_img = Image.new('RGB', (100, 100), color='red')
        img_path = date_dir / 'test.png'
        test_img.save(img_path)
        
        # Run sync
        manager = SyncManager(test_config)
        changes = manager.sync()
        
        # Verify files exist immediately after sync
        jekyll_post = jekyll_root / '_posts/2024-01-15-test_post.md'
        jekyll_img = jekyll_root / 'assets/img/posts/test.png'
        
        assert jekyll_post.exists()
        assert jekyll_img.exists()
        
        # Wait for cleanup
        time.sleep(test_config.cleanup_delay + 0.1)  # Add 0.1s buffer
        
        # Verify files are cleaned up
        assert not jekyll_post.exists()
        assert not jekyll_img.exists() 