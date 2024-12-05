"""Test image processing functionality"""

import os
import pytest
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv
from sync_engine.handlers.media import MediaHandler
from sync_engine.core.config import SyncConfig, ConfigManager

# Load environment variables
load_dotenv()

@pytest.fixture
def test_config(tmp_path):
    """Create test configuration"""
    return ConfigManager.load_from_dict({
        'vault_path': tmp_path / 'vault',
        'jekyll_path': tmp_path / 'jekyll',
        'vault_atomics': 'atomics',
        'jekyll_posts': '_posts',
        'jekyll_assets': 'assets/img/posts',
        'max_image_width': 1200,  # Test image resizing
        'optimize_images': True,  # Test image optimization
        'debug': True  # Enable debug logging for tests
    })

@pytest.fixture
def sample_images(tmp_path):
    """Create sample images for testing"""
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    
    # Create RGB image
    rgb_img = Image.new('RGB', (2000, 1500), color='red')
    rgb_path = images_dir / "large_rgb.jpg"
    rgb_img.save(rgb_path)
    
    # Create RGBA image with transparency
    rgba_img = Image.new('RGBA', (800, 600), color=(255, 0, 0, 128))
    rgba_path = images_dir / "transparent.png"
    rgba_img.save(rgba_path)
    
    # Create grayscale image
    gray_img = Image.new('L', (1000, 750), color=128)
    gray_path = images_dir / "grayscale.png"
    gray_img.save(gray_path)
    
    return {
        'rgb': rgb_path,
        'rgba': rgba_path,
        'gray': gray_path,
        'dir': images_dir
    }

def test_image_resizing(test_config, sample_images):
    """Test that large images are resized correctly"""
    handler = MediaHandler(test_config)
    
    # Process large RGB image
    processed = handler.process_image(sample_images['rgb'], test_config.jekyll_assets_path / "resized.jpg")
    
    # Verify size constraints
    with Image.open(processed) as img:
        assert img.width <= test_config.max_image_width, f"Width should be max {test_config.max_image_width}px"
        assert img.height == int(1500 * (test_config.max_image_width/2000)), "Height should maintain aspect ratio"

def test_rgba_conversion(test_config, sample_images):
    """Test that RGBA images are converted to RGB with white background"""
    handler = MediaHandler(test_config)
    
    # Process RGBA image
    processed = handler.process_image(sample_images['rgba'], test_config.jekyll_assets_path / "rgb.jpg")
    
    # Verify conversion
    with Image.open(processed) as img:
        assert img.mode == 'RGB', "Image should be converted to RGB"
        # Check if background is white where image was transparent
        colors = img.getcolors()
        assert any(count > 0 and color[0] > 240 for count, color in colors), "Should have white background"

def test_format_conversion(test_config, sample_images):
    """Test image format conversion and optimization"""
    handler = MediaHandler(test_config)
    
    # Test PNG to JPEG conversion
    jpeg_out = handler.process_image(sample_images['rgb'], test_config.jekyll_assets_path / "converted.jpg")
    assert jpeg_out.suffix == '.jpg'
    
    # Test optimization (file size should be smaller)
    original_size = sample_images['rgb'].stat().st_size
    converted_size = jpeg_out.stat().st_size
    assert converted_size < original_size, "Converted file should be smaller"

def test_grayscale_handling(test_config, sample_images):
    """Test handling of grayscale images"""
    handler = MediaHandler(test_config)
    
    # Process grayscale image
    processed = handler.process_image(sample_images['gray'], test_config.jekyll_assets_path / "gray.jpg")
    
    # Verify conversion to RGB
    with Image.open(processed) as img:
        assert img.mode == 'RGB', "Grayscale should be converted to RGB" 