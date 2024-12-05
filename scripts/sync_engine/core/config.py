"""Configuration handling module"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

from .exceptions import ConfigError
from .logging_config import setup_logging

logger = logging.getLogger(__name__)

@dataclass
class SyncConfig:
    """Configuration for sync engine"""
    # Required paths
    vault_path: Path
    jekyll_path: Path
    
    # Optional paths with defaults
    vault_atomics: str = "atomics"
    jekyll_posts: str = "_posts"
    jekyll_assets: str = "assets/img/posts"
    
    # Optional settings
    backup_count: int = 5
    auto_cleanup: bool = True
    max_image_width: int = 1200
    optimize_images: bool = True
    debug: bool = False
    log_dir: Optional[Path] = None
    continue_on_error: bool = False
    
    # Computed properties
    atomics_path: Path = field(init=False)
    jekyll_posts_path: Path = field(init=False)
    jekyll_assets_path: Path = field(init=False)
    
    def __post_init__(self):
        """Initialize computed paths and validate configuration"""
        # Convert string paths to Path objects if needed
        if isinstance(self.vault_path, str):
            self.vault_path = Path(self.vault_path).expanduser().resolve()
        if isinstance(self.jekyll_path, str):
            self.jekyll_path = Path(self.jekyll_path).resolve()
        if isinstance(self.log_dir, str):
            self.log_dir = Path(self.log_dir).expanduser().resolve()
            
        # Set computed paths
        self.atomics_path = self.vault_path / self.vault_atomics
        self.jekyll_posts_path = self.jekyll_path / self.jekyll_posts
        self.jekyll_assets_path = self.jekyll_path / self.jekyll_assets
        
        # Validate configuration
        self._validate()
        
        # Set up logging
        setup_logging(debug=self.debug, log_dir=self.log_dir)
    
    def _validate(self):
        """Validate configuration"""
        # Check required paths exist
        if not self.vault_path.exists():
            raise ConfigError(f"Vault path does not exist: {self.vault_path}")
        if not self.jekyll_path.exists():
            raise ConfigError(f"Jekyll path does not exist: {self.jekyll_path}")
            
        # Create necessary directories
        self.atomics_path.mkdir(parents=True, exist_ok=True)
        self.jekyll_posts_path.mkdir(parents=True, exist_ok=True)
        self.jekyll_assets_path.mkdir(parents=True, exist_ok=True)
        (self.jekyll_path / "_drafts").mkdir(parents=True, exist_ok=True)
        
        # Validate numeric values
        if self.backup_count < 1:
            raise ConfigError("backup_count must be at least 1")
        if self.max_image_width < 100:
            raise ConfigError("max_image_width must be at least 100")

class ConfigManager:
    """Handles configuration loading and validation"""
    
    ENV_PREFIX = "SYNC_"
    
    @staticmethod
    def load_from_env() -> SyncConfig:
        """Load configuration from environment variables"""
        # Load .env file if it exists
        load_dotenv()
        
        try:
            # Required paths
            vault_path = os.getenv(f"{ConfigManager.ENV_PREFIX}VAULT_ROOT")
            jekyll_path = os.getenv(f"{ConfigManager.ENV_PREFIX}JEKYLL_ROOT")
            
            if not vault_path or not jekyll_path:
                raise ConfigError(f"{ConfigManager.ENV_PREFIX}VAULT_ROOT and {ConfigManager.ENV_PREFIX}JEKYLL_ROOT must be set")
            
            # Optional settings with defaults
            config_dict = {
                "vault_path": vault_path,
                "jekyll_path": jekyll_path,
                "vault_atomics": os.getenv(f"{ConfigManager.ENV_PREFIX}VAULT_ATOMICS", "atomics"),
                "jekyll_posts": os.getenv(f"{ConfigManager.ENV_PREFIX}JEKYLL_POSTS", "_posts"),
                "jekyll_assets": os.getenv(f"{ConfigManager.ENV_PREFIX}JEKYLL_ASSETS", "assets/img/posts"),
                "backup_count": int(os.getenv(f"{ConfigManager.ENV_PREFIX}BACKUP_COUNT", "5")),
                "auto_cleanup": os.getenv(f"{ConfigManager.ENV_PREFIX}AUTO_CLEANUP", "true").lower() == "true",
                "max_image_width": int(os.getenv(f"{ConfigManager.ENV_PREFIX}MAX_IMAGE_WIDTH", "1200")),
                "optimize_images": os.getenv(f"{ConfigManager.ENV_PREFIX}OPTIMIZE_IMAGES", "true").lower() == "true",
                "debug": os.getenv(f"{ConfigManager.ENV_PREFIX}DEBUG", "false").lower() == "true",
                "log_dir": os.getenv(f"{ConfigManager.ENV_PREFIX}LOG_DIR"),
                "continue_on_error": os.getenv(f"{ConfigManager.ENV_PREFIX}CONTINUE_ON_ERROR", "false").lower() == "true"
            }
            
            return SyncConfig(**config_dict)
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise ConfigError(f"Failed to load configuration: {e}") from e
    
    @staticmethod
    def load_from_dict(config_dict: Dict) -> SyncConfig:
        """Load configuration from dictionary"""
        try:
            return SyncConfig(**config_dict)
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise ConfigError(f"Failed to load configuration: {e}") from e