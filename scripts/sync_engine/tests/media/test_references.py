"""Tests for media reference handling"""

import pytest
from pathlib import Path
from sync_engine.handlers.media import MediaHandler

class TestMediaReferences:
    """Tests for media reference handling"""
    
    def test_image_frontmatter_handling(self, test_config):
        """Test handling of image paths in frontmatter"""
        image_path = test_config.atomics_path / "2024" / "12" / "03"
        image_path.mkdir(parents=True)
        test_image = image_path / "Pasted image 20241203214844.png"
        test_image.write_bytes(b"fake image data")
        
        handler = MediaHandler(test_config)
        frontmatter = {'image': '[[atomics/2024/12/03/Pasted image 20241203214844.png]]'}
        ref = frontmatter['image'].strip('[]')
        resolved = handler.resolve_media_path(ref)
        assert resolved == test_image
        assert resolved.exists()

    def test_path_sanitization(self, test_config):
        """Test path sanitization for longer paths"""
        image_path = test_config.atomics_path / "2024" / "12" / "03" / "subfolder with spaces"
        image_path.mkdir(parents=True)
        test_image = image_path / "My Cool Test Image With Spaces.png"
        test_image.write_bytes(b"fake image data")
        
        handler = MediaHandler(test_config)
        ref = "atomics/2024/12/03/subfolder with spaces/My Cool Test Image With Spaces.png"
        resolved = handler.resolve_media_path(ref)
        assert resolved == test_image
        
        jekyll_path = handler.get_jekyll_media_path(resolved)
        assert jekyll_path.parent == test_config.jekyll_assets_path
        assert "-" in jekyll_path.name
        assert not " " in jekyll_path.name
        assert jekyll_path.suffix.lower() == ".png" 