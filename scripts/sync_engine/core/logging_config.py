"""Logging configuration for sync engine"""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

def setup_logging(debug: bool = False, log_dir: Optional[Path] = None) -> None:
    """
    Configure logging for the sync engine
    
    Args:
        debug: Enable debug logging
        log_dir: Custom log directory path. If None, uses ~/Library/Logs/obsidian-blog-sync/
    """
    # Set up log directory
    if log_dir is None:
        log_dir = Path.home() / "Library/Logs/obsidian-blog-sync"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (rotating)
    file_handler = RotatingFileHandler(
        log_dir / "sync.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)  # Always log debug to file
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Set specific levels for noisy modules
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('frontmatter').setLevel(logging.WARNING) 