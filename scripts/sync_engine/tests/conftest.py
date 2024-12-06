"""Shared test fixtures"""

import pytest
from pathlib import Path
from PIL import Image
from sync_engine.core.config import ConfigManager
from sync_engine.core.atomic import AtomicManager

@pytest.fixture
def setup_dirs(tmp_path):
    """Create test directories"""
    # Create test directories
    vault_root = tmp_path / 'vault'
    jekyll_root = tmp_path / 'jekyll'
    
    # Create required directories
    vault_root.mkdir(parents=True, exist_ok=True)
    jekyll_root.mkdir(parents=True, exist_ok=True)
    (jekyll_root / '_posts').mkdir(parents=True, exist_ok=True)
    (jekyll_root / 'assets' / 'img' / 'posts').mkdir(parents=True, exist_ok=True)
    (vault_root / 'atomics').mkdir(parents=True, exist_ok=True)
    (jekyll_root / '_drafts').mkdir(parents=True, exist_ok=True)
    
    return vault_root, jekyll_root, vault_root / 'atomics'

@pytest.fixture
def test_config(setup_dirs):
    """Create test configuration"""
    vault_root, jekyll_root, _ = setup_dirs

    config = ConfigManager.load_from_dict({
        'vault_root': str(vault_root),
        'jekyll_root': str(jekyll_root),
        'vault_atomics': 'atomics',
        'jekyll_posts': '_posts',
        'jekyll_assets': 'assets/img/posts',
        'debug': True,  # Enable debug logging for tests
        'validate_paths': False  # Disable path validation for tests
    })
    
    # Ensure paths are set correctly
    assert config.vault_root == vault_root
    assert config.jekyll_root == jekyll_root
    assert config.atomics_path == vault_root / 'atomics'
    assert config.jekyll_posts_path == jekyll_root / '_posts'
    assert config.jekyll_assets_path == jekyll_root / 'assets/img/posts'
    
    return config

@pytest.fixture
def atomic_manager(test_config, tmp_path):
    """Create atomic manager with test config"""
    manager = AtomicManager(config=test_config)
    manager.backup_dir = tmp_path / ".atomic_backups"
    manager.backup_dir.mkdir(exist_ok=True)
    return manager

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