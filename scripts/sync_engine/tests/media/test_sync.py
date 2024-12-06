"""Tests for media synchronization.

This module tests:
- Path resolution (absolute and relative paths)
- Bidirectional sync (vault to Jekyll and back)
- File operations (read/write/verify)
"""

import pytest
from pathlib import Path
from sync_engine.handlers.media import MediaHandler

class TestMediaSync:
    """Tests for media synchronization"""
    
    def test_absolute_path_resolution(self, test_config):
        """Test that absolute vault paths are resolved correctly.
        
        Features tested:
        - Path resolution: Absolute path handling
        - File operations: File creation and verification
        """
        image_path = test_config.atomics_path / "2024" / "12" / "03"
        image_path.mkdir(parents=True)
        test_image = image_path / "test_image.png"
        test_image.write_bytes(b"fake image data")
        
        handler = MediaHandler(test_config)
        ref = "atomics/2024/12/03/test_image.png"
        resolved = handler.resolve_media_path(ref)
        assert resolved == test_image
        assert resolved.exists()

    def test_bidirectional_sync(self, test_config):
        """Test bidirectional sync with absolute paths.
        
        Features tested:
        - Bidirectional sync: Vault to Jekyll conversion
        - Bidirectional sync: Jekyll to vault sync back
        - File operations: Content verification
        - Path resolution: URL to file path mapping
        """
        image_path = test_config.atomics_path / "2024" / "12" / "03"
        image_path.mkdir(parents=True)
        test_image = image_path / "test_image.png"
        test_image.write_bytes(b"original data")
        
        handler = MediaHandler(test_config)
        ref = "atomics/2024/12/03/test_image.png"
        jekyll_url = handler.process_media_file(test_image)
        assert jekyll_url.startswith("/assets/img/posts/")
        
        jekyll_file = test_config.jekyll_assets_path / Path(jekyll_url).name
        jekyll_file.write_bytes(b"modified data")
        
        synced_path = handler.sync_back_to_obsidian(jekyll_url)
        assert synced_path == test_image
        assert test_image.read_bytes() == b"modified data" 