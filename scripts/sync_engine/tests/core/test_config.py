"""Tests for configuration handling"""

import pytest
from pathlib import Path
from sync_engine.core.config import SyncConfig, ConfigManager

class TestConfigHandling:
    """Tests for configuration handling"""
    
    def test_config_loading(self, tmp_path):
        """Test loading configuration from dict"""
        config_dict = {
            'vault_root': tmp_path / 'vault',
            'jekyll_root': tmp_path / 'jekyll',
            'vault_atomics': 'atomics',
            'jekyll_posts': '_posts',
            'jekyll_assets': 'assets/img/posts',
            'debug': True
        }
        
        config = ConfigManager.load_from_dict(config_dict)
        assert isinstance(config, SyncConfig)
        assert config.vault_root == tmp_path / 'vault'
        assert config.jekyll_root == tmp_path / 'jekyll'
        assert config.vault_atomics == 'atomics'
        assert config.jekyll_posts == '_posts'
        assert config.jekyll_assets == 'assets/img/posts'
        assert config.debug is True

    def test_config_validation(self, tmp_path):
        """Test configuration validation"""
        # Test missing required field
        with pytest.raises(ValueError):
            ConfigManager.load_from_dict({
                'vault_root': tmp_path / 'vault',
                # Missing jekyll_root
                'vault_atomics': 'atomics'
            })
        
        # Test invalid path type
        with pytest.raises(TypeError):
            ConfigManager.load_from_dict({
                'vault_root': 123,  # Should be Path
                'jekyll_root': tmp_path / 'jekyll',
                'vault_atomics': 'atomics'
            })

    def test_computed_paths(self, tmp_path):
        """Test computed configuration paths"""
        config = ConfigManager.load_from_dict({
            'vault_root': tmp_path / 'vault',
            'jekyll_root': tmp_path / 'jekyll',
            'vault_atomics': 'atomics',
            'jekyll_posts': '_posts',
            'jekyll_assets': 'assets/img/posts'
        })
        
        # Test computed paths
        assert config.atomics_path == tmp_path / 'vault/atomics'
        assert config.posts_path == tmp_path / 'jekyll/_posts'
        assert config.jekyll_assets_path == tmp_path / 'jekyll/assets/img/posts'

    def test_config_defaults(self, tmp_path):
        """Test configuration defaults"""
        config = ConfigManager.load_from_dict({
            'vault_root': tmp_path / 'vault',
            'jekyll_root': tmp_path / 'jekyll',
            'vault_atomics': 'atomics',
            'jekyll_posts': '_posts',
            'jekyll_assets': 'assets/img/posts'
        })
        
        # Test default values
        assert config.debug is False
        assert config.max_image_width == 1200
        assert config.optimize_images is True

    def test_config_overrides(self, tmp_path):
        """Test configuration value overrides"""
        config = ConfigManager.load_from_dict({
            'vault_root': tmp_path / 'vault',
            'jekyll_root': tmp_path / 'jekyll',
            'vault_atomics': 'atomics',
            'jekyll_posts': '_posts',
            'jekyll_assets': 'assets/img/posts',
            'debug': True,
            'max_image_width': 800,
            'optimize_images': False
        })
        
        # Test overridden values
        assert config.debug is True
        assert config.max_image_width == 800
        assert config.optimize_images is False 