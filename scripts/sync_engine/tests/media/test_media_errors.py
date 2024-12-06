"""Tests for media error handling"""

import pytest
from sync_engine.handlers.media import MediaHandler

class TestMediaErrors:
    """Tests for media error handling"""
    
    def test_missing_file(self, test_config):
        """Test handling of missing media files"""
        handler = MediaHandler(test_config)
        ref = "atomics/2024/12/03/nonexistent.png"
        with pytest.raises(FileNotFoundError):
            handler.resolve_media_path(ref)

    def test_invalid_reference(self, test_config):
        """Test handling of invalid media references"""
        handler = MediaHandler(test_config)
        invalid_refs = [
            "",  # Empty string
            "[[]]",  # Empty wikilink
            "/absolute/path/image.png",  # Absolute path
            "../outside/vault.png",  # Path traversal
        ]
        
        for ref in invalid_refs:
            with pytest.raises(ValueError):
                handler.resolve_media_path(ref) 