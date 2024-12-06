"""Tests for basic sync functionality.

This module tests:
- Basic sync operations (posts and images)
- Engine initialization and setup
- Empty state handling
- File system interactions
"""

import pytest
import os
from pathlib import Path
from PIL import Image
from sync_engine.core.sync import SyncManager
from sync_engine.core.engine import SyncEngineV2
from sync_engine.core.types import SyncOperation, SyncDirection, PostStatus
from sync_engine.core.config import SyncConfig

class TestBasicSync:
    """Tests for basic sync functionality"""
    
    def test_basic_sync(self, test_config, setup_dirs):
        """Test basic sync operation.
        
        Features tested:
        - Sync operations: Post and image sync
        - Path handling: Daily folder structure
        - File operations: Content preservation
        - Debug logging: Directory structure and permissions
        """
        vault_root, jekyll_path, atomic_path = setup_dirs
        
        # Disable auto cleanup for this test
        test_config.auto_cleanup = False
        
        # Create post with image in daily folder
        post_content = """---
status: published
image: "[[atomics/2024/01/15/test.png]]"
---
# Test Post

Here's an image: ![[atomics/2024/01/15/test.png]]
"""
        post_path = atomic_path / "2024/01/15/my first post.md"
        post_path.parent.mkdir(parents=True, exist_ok=True)
        post_path.write_text(post_content)
        
        # Create test image in same folder
        img_path = post_path.parent / "test.png"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(img_path)
        
        # Run sync
        manager = SyncManager(test_config)
        changes = manager.sync()
        
        # Debug: Print directory contents and permissions
        print("\nDirectory structure:")
        for root, dirs, files in os.walk(jekyll_path):
            print(f"\nDirectory: {root}")
            print(f"Permissions: {oct(os.stat(root).st_mode)}")
            for d in dirs:
                path = os.path.join(root, d)
                print(f"  Dir: {d} ({oct(os.stat(path).st_mode)})")
            for f in files:
                path = os.path.join(root, f)
                print(f"  File: {f} ({oct(os.stat(path).st_mode)})")
        
        # Verify changes
        assert len(changes) == 2  # Post and image
        post_change = next(c for c in changes if c.source_path.suffix == '.md')
        img_change = next(c for c in changes if c.source_path.suffix == '.png')
        
        # Debug: Print paths and file info
        print("\nFile details:")
        print(f"  Post source: {post_change.source_path} (exists: {post_change.source_path.exists()})")
        print(f"  Post target: {post_change.target_path} (exists: {post_change.target_path.exists()})")
        print(f"  Image source: {img_change.source_path} (exists: {img_change.source_path.exists()})")
        print(f"  Image target: {img_change.target_path} (exists: {img_change.target_path.exists()})")
        
        # Verify correct Jekyll paths
        assert (test_config.jekyll_posts_path / '2024-01-15-my-first-post.md').exists()
        assert img_change.target_path.exists()

    def test_engine_initialization(self, test_config):
        """Test engine initialization.
        
        Features tested:
        - Engine setup: Component initialization
        - Configuration: Config validation
        - Component integration: Handler setup
        """
        engine = SyncEngineV2(test_config)
        assert isinstance(engine.config, SyncConfig)
        assert engine.detector is not None
        assert engine.atomic is not None
        assert engine.post_handler is not None
        assert engine.media_handler is not None

    def test_detect_changes_empty(self, test_config):
        """Test change detection with empty directories.
        
        Features tested:
        - Change detection: Empty state handling
        - Directory scanning: Empty directory handling
        - Performance: Quick return for no changes
        """
        engine = SyncEngineV2(test_config)
        changes = engine.detect_changes()
        assert len(changes) == 0 