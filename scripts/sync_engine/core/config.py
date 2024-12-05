"""Configuration handling module"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SyncConfig:
    """Configuration for sync engine"""
    vault_path: Path
    jekyll_path: Path
    vault_posts: str
    vault_media: str
    jekyll_posts: str
    jekyll_assets: str
    
    @property
    def posts_path(self) -> Path:
        """Get full path to vault posts directory"""
        return self.vault_path / self.vault_posts
    
    @property
    def media_path(self) -> Path:
        """Get full path to vault media directory"""
        return self.vault_path / self.vault_media
    
    @property
    def jekyll_posts_path(self) -> Path:
        """Get full path to Jekyll posts directory"""
        return self.jekyll_path / self.jekyll_posts
    
    @property
    def jekyll_assets_path(self) -> Path:
        """Get full path to Jekyll assets directory"""
        return self.jekyll_path / self.jekyll_assets

class ConfigManager:
    """Handles configuration loading and validation"""
    
    @staticmethod
    def load_from_env() -> SyncConfig:
        """Load configuration from environment variables"""
        try:
            # Required paths
            vault_path = os.getenv('VAULT_ROOT')
            jekyll_path = os.getenv('JEKYLL_ROOT')
            
            if not vault_path or not jekyll_path:
                raise ValueError("VAULT_ROOT and JEKYLL_ROOT must be set")
            
            # Optional paths with defaults
            vault_posts = os.getenv('VAULT_POSTS_PATH', '_posts')
            vault_media = os.getenv('VAULT_MEDIA_PATH', 'atomics')
            jekyll_posts = os.getenv('JEKYLL_POSTS_PATH', '_posts')
            jekyll_assets = os.getenv('JEKYLL_ASSETS_PATH', 'assets/img/posts')
            
            config = SyncConfig(
                vault_path=Path(vault_path).expanduser().resolve(),
                jekyll_path=Path(jekyll_path).resolve(),
                vault_posts=vault_posts,
                vault_media=vault_media,
                jekyll_posts=jekyll_posts,
                jekyll_assets=jekyll_assets
            )
            
            ConfigManager._validate_config(config)
            return config
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    @staticmethod
    def load_from_dict(config_dict: Dict) -> SyncConfig:
        """Load configuration from dictionary"""
        try:
            config = SyncConfig(
                vault_path=Path(config_dict['vault_path']).expanduser().resolve(),
                jekyll_path=Path(config_dict['blog_path']).resolve(),
                vault_posts=config_dict.get('vault_posts_path', '_posts'),
                vault_media=config_dict.get('vault_media_path', 'atomics'),
                jekyll_posts=config_dict.get('jekyll_posts_path', '_posts'),
                jekyll_assets=config_dict.get('jekyll_assets_path', 'assets/img/posts')
            )
            
            ConfigManager._validate_config(config)
            return config
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    @staticmethod
    def _validate_config(config: SyncConfig) -> None:
        """Validate configuration paths"""
        # Check vault paths
        if not config.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {config.vault_path}")
        
        # Create necessary directories
        config.posts_path.mkdir(parents=True, exist_ok=True)
        config.media_path.mkdir(parents=True, exist_ok=True)
        config.jekyll_posts_path.mkdir(parents=True, exist_ok=True)
        config.jekyll_assets_path.mkdir(parents=True, exist_ok=True)
        (config.jekyll_path / "_drafts").mkdir(parents=True, exist_ok=True) 