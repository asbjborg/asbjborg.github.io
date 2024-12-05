"""Configuration management module"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union, Dict, Optional

@dataclass
class SyncConfig:
    """Sync engine configuration"""
    # Required paths
    vault_root: Union[str, Path]
    jekyll_root: Union[str, Path]
    
    # Optional paths with defaults
    vault_atomics: str = 'atomics'
    jekyll_posts: str = '_posts'
    jekyll_assets: str = 'assets/img/posts'
    
    # Behavior settings
    debug: bool = False
    continue_on_error: bool = False
    auto_cleanup: bool = True
    
    # Media settings
    optimize_images: bool = True
    max_image_width: int = 1200
    
    # Backup settings
    backup_count: int = 5
    backup_dir: str = '.atomic_backups'
    
    # Computed paths (set in post_init)
    atomics_path: Path = field(init=False)
    jekyll_posts_path: Path = field(init=False)
    jekyll_assets_path: Path = field(init=False)
    
    def __post_init__(self):
        """Convert paths and set computed fields"""
        # Convert string paths to Path objects
        if isinstance(self.vault_root, str):
            self.vault_root = Path(self.vault_root)
        if isinstance(self.jekyll_root, str):
            self.jekyll_root = Path(self.jekyll_root)
            
        # Set computed paths
        self.atomics_path = self.vault_root / self.vault_atomics
        self.jekyll_posts_path = self.jekyll_root / self.jekyll_posts
        self.jekyll_assets_path = self.jekyll_root / self.jekyll_assets
        
        # Validate paths
        if not self.vault_root.exists():
            raise ValueError(f"Vault root not found: {self.vault_root}")
        if not self.jekyll_root.exists():
            raise ValueError(f"Jekyll root not found: {self.jekyll_root}")
            
        # Create required directories
        self.atomics_path.mkdir(parents=True, exist_ok=True)
        self.jekyll_posts_path.mkdir(parents=True, exist_ok=True)
        self.jekyll_assets_path.mkdir(parents=True, exist_ok=True)

class ConfigManager:
    """Configuration management utilities"""
    
    @staticmethod
    def load_from_env() -> SyncConfig:
        """Load configuration from environment variables"""
        required = {
            'vault_root': os.environ.get('SYNC_VAULT_ROOT'),
            'jekyll_root': os.environ.get('SYNC_JEKYLL_ROOT')
        }
        
        if not all(required.values()):
            missing = [k for k, v in required.items() if not v]
            raise ValueError(f"Missing required environment variables: {missing}")
            
        optional = {
            'vault_atomics': os.environ.get('SYNC_VAULT_ATOMICS'),
            'jekyll_posts': os.environ.get('SYNC_JEKYLL_POSTS'),
            'jekyll_assets': os.environ.get('SYNC_JEKYLL_ASSETS'),
            'debug': os.environ.get('SYNC_DEBUG', '').lower() == 'true',
            'auto_cleanup': os.environ.get('SYNC_AUTO_CLEANUP', '').lower() == 'true',
            'optimize_images': os.environ.get('SYNC_OPTIMIZE_IMAGES', '').lower() == 'true',
            'max_image_width': int(os.environ.get('SYNC_MAX_IMAGE_WIDTH', 1200)),
            'backup_count': int(os.environ.get('SYNC_BACKUP_COUNT', 5))
        }
        
        # Remove None values to use defaults
        optional = {k: v for k, v in optional.items() if v is not None}
        
        return SyncConfig(**required, **optional)
    
    @staticmethod
    def load_from_dict(config: Dict) -> SyncConfig:
        """Load configuration from dictionary"""
        required = {'vault_root', 'jekyll_root'}
        if not all(k in config for k in required):
            missing = required - set(config.keys())
            raise ValueError(f"Missing required config keys: {missing}")
            
        return SyncConfig(**config)