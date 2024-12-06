"""Tests for path handling.

This module tests:
- Complex path handling (spaces, Unicode, special chars)
- Path normalization (directory traversal, mixed styles)
- Auto cleanup functionality (delayed cleanup)
- File system operations (create, verify, cleanup)
"""

import pytest
import time
from pathlib import Path
from sync_engine.core.sync import SyncManager
from PIL import Image

class TestSyncPaths:
    """Tests for path handling"""
    
    def test_complex_paths(self, test_config, setup_dirs):
        """Test handling of complex file paths.
        
        Features tested:
        - Path handling: Spaces in filenames
        - Path handling: Unicode characters
        - Path handling: Special characters (#, !)
        - Path handling: Very long filenames
        - Path handling: Directory traversal (.., .)
        - Path handling: Mixed path styles (/ and \)
        - Path normalization: URL-safe conversions
        - Debug logging: Path verification
        """
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
4. ![[atomics/2024/01/15/path/../path/test.png]]
5. ![[atomics/2024/01/15/./current/test.jpg]]
6. ![[atomics/2024/01/15/mixed\\path\\style.png]]
"""
        post_path = date_dir / "complex post with spaces!.md"
        post_path.write_text(post_content)
        
        # Create test images in same folder
        images = [
            'image with spaces.png',
            'über.jpg',
            'test#1.png',
            'very-very-very-very-very-very-long-filename.gif',
            'path/test.png',
            'current/test.jpg',
            'mixed/path/style.png'
        ]
        
        # Create test images and directories
        test_img = Image.new('RGB', (100, 100), color='red')
        for img in images:
            img_path = date_dir / img
            img_path.parent.mkdir(parents=True, exist_ok=True)
            if img.endswith('.gif'):
                # Create GIF with one frame
                test_img.save(img_path, format='GIF', save_all=True, append_images=[test_img])
            else:
                # Save as normal image
                test_img.save(img_path)
                
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
        assert len(changes) == 8  # 1 post + 7 images
        
        # Verify files exist in Jekyll with normalized paths
        jekyll_post = jekyll_root / '_posts/2024-01-15-complex-post-with-spaces.md'
        assert jekyll_post.exists()
        
        # Read post content to verify path normalization
        content = jekyll_post.read_text()
        assert '![](../assets/img/posts/über.jpg)' in content
        assert '![](../assets/img/posts/test-1.png)' in content
        assert '![](../assets/img/posts/very-very-very-very-very-very-long-filename.gif)' in content
        assert '![](../assets/img/posts/test.png)' in content  # Normalized path/test.png
        assert '![](../assets/img/posts/test.jpg)' in content  # Normalized current/test.jpg
        assert '![](../assets/img/posts/style.png)' in content  # Normalized mixed/path/style.png
        
        # Verify image files exist with normalized names
        assets_dir = jekyll_root / 'assets/img/posts'
        assert (assets_dir / 'über.jpg').exists()
        assert (assets_dir / 'test-1.png').exists()
        assert (assets_dir / 'very-very-very-very-very-very-long-filename.gif').exists()
        assert (assets_dir / 'test.png').exists()
        assert (assets_dir / 'test.jpg').exists()
        assert (assets_dir / 'style.png').exists()

    def test_auto_cleanup(self, test_config, setup_dirs):
        """Test auto cleanup functionality.
        
        Features tested:
        - Cleanup: Delayed file removal
        - Cleanup: Content verification before cleanup
        - File operations: Content preservation
        - Timing: Cleanup delay handling
        """
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
        
        # Verify file contents before cleanup
        assert jekyll_post.read_text() == post_content.replace('[[atomics/', '![](../assets/img/posts/')
        assert jekyll_img.stat().st_size > 0
        
        # Wait for cleanup
        time.sleep(test_config.cleanup_delay + 0.1)  # Add 0.1s buffer
        
        # Verify files are cleaned up
        assert not jekyll_post.exists()
        assert not jekyll_img.exists() 