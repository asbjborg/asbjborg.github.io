"""Tests for media error handling.

This module tests:
- Error handling (file not found, invalid references)
- Input validation (path validation)
- Security (path traversal prevention)
"""

import pytest
from sync_engine.handlers.media import MediaHandler

class TestMediaErrors:
    """Tests for media error handling"""
    
    def test_missing_file(self, test_config):
        """Test handling of missing media files.
        
        Features tested:
        - Error handling: File not found errors
        - Input validation: File existence checks
        """
        handler = MediaHandler(test_config)
        ref = "atomics/2024/12/03/nonexistent.png"
        with pytest.raises(FileNotFoundError):
            handler.resolve_media_path(ref)

    def test_invalid_reference(self, test_config):
        """Test handling of invalid media references.
        
        Features tested:
        - Error handling: Invalid reference format
        - Input validation: Reference string validation
        - Security: Path traversal prevention
        """
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
                