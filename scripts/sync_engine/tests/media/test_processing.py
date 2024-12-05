"""Tests for media file processing"""

import pytest
from PIL import Image
from sync_engine.handlers.media import MediaHandler

class TestMediaProcessing:
    """Tests for media file processing"""
    
    def test_image_resizing(self, test_config, sample_images):
        """Test that large images are resized correctly"""
        handler = MediaHandler(test_config)
        processed = handler.process_image(sample_images['rgb'], test_config.jekyll_assets_path / "resized.jpg")
        
        with Image.open(processed) as img:
            assert img.width <= test_config.max_image_width
            assert img.height == int(1500 * (test_config.max_image_width/2000))

    def test_rgba_conversion(self, test_config, sample_images):
        """Test that RGBA images are converted to RGB with white background"""
        handler = MediaHandler(test_config)
        processed = handler.process_image(sample_images['rgba'], test_config.jekyll_assets_path / "rgb.jpg")
        
        with Image.open(processed) as img:
            assert img.mode == 'RGB'
            colors = img.getcolors()
            assert any(count > 0 and color[0] > 240 for count, color in colors)

    def test_format_conversion(self, test_config, sample_images):
        """Test image format conversion and optimization"""
        handler = MediaHandler(test_config)
        jpeg_out = handler.process_image(sample_images['rgb'], test_config.jekyll_assets_path / "converted.jpg")
        assert jpeg_out.suffix == '.jpg'
        
        original_size = sample_images['rgb'].stat().st_size
        converted_size = jpeg_out.stat().st_size
        assert converted_size < original_size

    def test_grayscale_handling(self, test_config, sample_images):
        """Test handling of grayscale images"""
        handler = MediaHandler(test_config)
        processed = handler.process_image(sample_images['gray'], test_config.jekyll_assets_path / "gray.jpg")
        
        with Image.open(processed) as img:
            assert img.mode == 'RGB' 