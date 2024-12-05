"""Test media sync with absolute vault paths"""

import os
import pytest
from pathlib import Path
from dotenv import load_dotenv
from sync_engine.handlers.media import MediaHandler

# Load environment variables
load_dotenv()

# Get paths from environment
VAULT_ROOT = Path(os.getenv('VAULT_ROOT'))
JEKYLL_ASSETS_PATH = VAULT_ROOT / os.getenv('JEKYLL_ASSETS_PATH')
TEST_VAULT_IMAGE = os.getenv('TEST_VAULT_IMAGE')

def test_absolute_path_resolution(tmp_path):
    """Test that absolute vault paths are resolved correctly"""
    # Setup mock vault structure
    vault_root = tmp_path / "vault"
    assets_path = tmp_path / "assets"
    vault_root.mkdir()
    assets_path.mkdir()
    
    # Create test image in vault
    image_path = vault_root / "atomics" / "2024" / "12" / "03"
    image_path.mkdir(parents=True)
    test_image = image_path / "test_image.png"
    test_image.write_bytes(b"fake image data")
    
    handler = MediaHandler(vault_root, assets_path)
    
    # Test absolute path resolution
    ref = "atomics/2024/12/03/test_image.png"
    resolved = handler.resolve_media_path(ref)
    assert resolved == test_image
    assert resolved.exists()

def test_image_frontmatter_handling(tmp_path):
    """Test handling of image paths in frontmatter"""
    vault_root = tmp_path / "vault"
    assets_path = tmp_path / "assets"
    vault_root.mkdir()
    assets_path.mkdir()
    
    # Create test image
    image_path = vault_root / "atomics" / "2024" / "12" / "03"
    image_path.mkdir(parents=True)
    test_image = image_path / "Pasted image 20241203214844.png"
    test_image.write_bytes(b"fake image data")
    
    handler = MediaHandler(vault_root, assets_path)
    
    # Test frontmatter image reference
    frontmatter = {'image': '[[atomics/2024/12/03/Pasted image 20241203214844.png]]'}
    ref = frontmatter['image'].strip('[]')
    resolved = handler.resolve_media_path(ref)
    assert resolved == test_image
    assert resolved.exists()

def test_path_sanitization(tmp_path):
    """Test path sanitization for longer paths"""
    vault_root = tmp_path / "vault"
    assets_path = tmp_path / "assets"
    vault_root.mkdir()
    assets_path.mkdir()
    
    # Create test image with long path
    image_path = vault_root / "atomics" / "2024" / "12" / "03" / "subfolder with spaces"
    image_path.mkdir(parents=True)
    test_image = image_path / "My Cool Test Image With Spaces.png"
    test_image.write_bytes(b"fake image data")
    
    handler = MediaHandler(vault_root, assets_path)
    
    # Test path resolution and sanitization
    ref = "atomics/2024/12/03/subfolder with spaces/My Cool Test Image With Spaces.png"
    resolved = handler.resolve_media_path(ref)
    assert resolved == test_image
    
    # Test Jekyll path generation
    jekyll_path = handler.get_jekyll_media_path(resolved)
    assert jekyll_path.parent == assets_path
    assert "-" in jekyll_path.name  # Should contain hash
    assert not " " in jekyll_path.name  # No spaces
    assert jekyll_path.suffix.lower() == ".png"

def test_bidirectional_sync(tmp_path):
    """Test bidirectional sync with absolute paths"""
    vault_root = tmp_path / "vault"
    assets_path = tmp_path / "assets"
    vault_root.mkdir()
    assets_path.mkdir()
    
    # Create test image in vault
    image_path = vault_root / "atomics" / "2024" / "12" / "03"
    image_path.mkdir(parents=True)
    test_image = image_path / "test_image.png"
    test_image.write_bytes(b"original data")
    
    handler = MediaHandler(vault_root, assets_path)
    
    # Process image to Jekyll
    ref = "atomics/2024/12/03/test_image.png"
    jekyll_url = handler.process_media_file(test_image)
    assert jekyll_url.startswith("/assets/img/posts/")
    
    # Simulate Jekyll edit
    jekyll_file = assets_path / Path(jekyll_url).name
    jekyll_file.write_bytes(b"modified data")
    
    # Sync back to Obsidian
    synced_path = handler.sync_back_to_obsidian(jekyll_url)
    assert synced_path == test_image
    assert test_image.read_bytes() == b"modified data" 

def test_real_vault_paths():
    """Integration test using real vault data"""
    handler = MediaHandler(VAULT_ROOT, JEKYLL_ASSETS_PATH)
    
    # Test with known image from vault
    ref = TEST_VAULT_IMAGE
    resolved = handler.resolve_media_path(ref)
    assert resolved is not None
    assert resolved.exists()
    assert resolved.name == Path(TEST_VAULT_IMAGE).name
    
    # Test frontmatter extraction
    frontmatter = {'image': f'[[{TEST_VAULT_IMAGE}]]'}
    ref = frontmatter['image'].strip('[]')
    resolved = handler.resolve_media_path(ref)
    assert resolved is not None
    assert resolved.exists()
    
    # Test Jekyll path generation
    jekyll_path = handler.get_jekyll_media_path(resolved)
    assert jekyll_path.parent == JEKYLL_ASSETS_PATH
    assert Path(TEST_VAULT_IMAGE).stem.lower().replace(' ', '-') in jekyll_path.name.lower()
    assert jekyll_path.suffix.lower() == ".png" 