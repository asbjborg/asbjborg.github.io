"""Tests for basic sync functionality"""

import pytest
from pathlib import Path
from sync_engine.core.sync import SyncManager
from sync_engine.core.engine import SyncEngineV2
from sync_engine.core.types import SyncOperation, SyncDirection, PostStatus

class TestBasicSync:
    """Tests for basic sync functionality"""
    
    def test_basic_sync(self, test_config, setup_dirs):
        """Test basic sync operation"""
        vault_root, jekyll_path, atomic_path = setup_dirs
        
        # Create post with image in daily folder
        post_content = """---
status: published
image: ![[atomics/2024/01/15/test.png]]
---
# Test Post

Here's an image: ![[atomics/2024/01/15/test.png]]
"""
        post_path = atomic_path / "my first post.md"
        post_path.write_text(post_content)
        
        # Create test image in same folder
        img_path = atomic_path / "test.png"
        img_path.write_bytes(b'fake png data')
        
        # Run sync
        manager = SyncManager(test_config)
        changes = manager.sync()
        
        # Verify changes
        assert len(changes) == 2  # Post and image
        post_change = next(c for c in changes if c.source_path.suffix == '.md')
        img_change = next(c for c in changes if c.source_path.suffix == '.png')
        
        # Verify correct Jekyll paths
        assert (jekyll_path / '_posts/2024-01-15-my-first-post.md').exists()
        assert list(jekyll_path.glob('assets/img/posts/*.png'))

    def test_engine_initialization(self, test_config):
        """Test engine initialization"""
        engine = SyncEngineV2(test_config)
        assert isinstance(engine.config, SyncConfig)
        assert engine.detector is not None
        assert engine.atomic is not None
        assert engine.post_handler is not None
        assert engine.media_handler is not None

    def test_detect_changes_empty(self, test_config):
        """Test change detection with empty directories"""
        engine = SyncEngineV2(test_config)
        changes = engine.detect_changes()
        assert len(changes) == 0 