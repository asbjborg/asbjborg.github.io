"""Test media sync with absolute vault paths"""

import os
import pytest
from pathlib import Path
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
        'debug': True  # Enable debug logging for tests
    })

def test_absolute_path_resolution(test_config):
    """Test that absolute vault paths are resolved correctly"""
    # Create test image in vault
    image_path = test_config.atomics_path / "2024" / "12" / "03"
    image_path.mkdir(parents=True)
    test_image = image_path / "test_image.png"
    test_image.write_bytes(b"fake image data")
    
    handler = MediaHandler(test_config)
    
    # Test absolute path resolution
    ref = "atomics/2024/12/03/test_image.png"
    resolved = handler.resolve_media_path(ref)
    assert resolved == test_image
    assert resolved.exists()

def test_image_frontmatter_handling(test_config):
    """Test handling of image paths in frontmatter"""
    # Create test image
    image_path = test_config.atomics_path / "2024" / "12" / "03"
    image_path.mkdir(parents=True)
    test_image = image_path / "Pasted image 20241203214844.png"
    test_image.write_bytes(b"fake image data")
    
    handler = MediaHandler(test_config)
    
    # Test frontmatter image reference
    frontmatter = {'image': '[[atomics/2024/12/03/Pasted image 20241203214844.png]]'}
    ref = frontmatter['image'].strip('[]')
    resolved = handler.resolve_media_path(ref)
    assert resolved == test_image
    assert resolved.exists()

def test_path_sanitization(test_config):
    """Test path sanitization for longer paths"""
    # Create test image with long path
    image_path = test_config.atomics_path / "2024" / "12" / "03" / "subfolder with spaces"
    image_path.mkdir(parents=True)
    test_image = image_path / "My Cool Test Image With Spaces.png"
    test_image.write_bytes(b"fake image data")
    
    handler = MediaHandler(test_config)
    
    # Test path resolution and sanitization
    ref = "atomics/2024/12/03/subfolder with spaces/My Cool Test Image With Spaces.png"
    resolved = handler.resolve_media_path(ref)
    assert resolved == test_image
    
    # Test Jekyll path generation
    jekyll_path = handler.get_jekyll_media_path(resolved)
    assert jekyll_path.parent == test_config.jekyll_assets_path
    assert "-" in jekyll_path.name  # Should contain hash
    assert not " " in jekyll_path.name  # No spaces
    assert jekyll_path.suffix.lower() == ".png"

def test_bidirectional_sync(test_config):
    """Test bidirectional sync with absolute paths"""
    # Create test image in vault
    image_path = test_config.atomics_path / "2024" / "12" / "03"
    image_path.mkdir(parents=True)
    test_image = image_path / "test_image.png"
    test_image.write_bytes(b"original data")
    
    handler = MediaHandler(test_config)
    
    # Process image to Jekyll
    ref = "atomics/2024/12/03/test_image.png"
    jekyll_url = handler.process_media_file(test_image)
    assert jekyll_url.startswith("/assets/img/posts/")
    
    # Simulate Jekyll edit
    jekyll_file = test_config.jekyll_assets_path / Path(jekyll_url).name
    jekyll_file.write_bytes(b"modified data")
    
    # Sync back to Obsidian
    synced_path = handler.sync_back_to_obsidian(jekyll_url)
    assert synced_path == test_image
    assert test_image.read_bytes() == b"modified data"

def test_real_vault_paths():
    """Integration test using real vault data"""
    # Load real config from environment
    config = ConfigManager.load_from_env()
    handler = MediaHandler(config)
    
    # Test with known image from vault
    ref = os.getenv('TEST_VAULT_IMAGE')
    resolved = handler.resolve_media_path(ref)
    assert resolved is not None
    assert resolved.exists()
    assert resolved.name == Path(ref).name
    
    # Test frontmatter extraction
    frontmatter = {'image': f'[[{ref}]]'}
    ref = frontmatter['image'].strip('[]')
    resolved = handler.resolve_media_path(ref)
    assert resolved is not None
    assert resolved.exists()
    
    # Test Jekyll path generation
    jekyll_path = handler.get_jekyll_media_path(resolved)
    assert jekyll_path.parent == config.jekyll_assets_path
    assert Path(ref).stem.lower().replace(' ', '-') in jekyll_path.name.lower()
    assert jekyll_path.suffix.lower() == ".png" 