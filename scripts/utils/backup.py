import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional

class BackupHandler:
    def __init__(self, vault_root: str, jekyll_root: str, debug: bool = False, dry_run: bool = False):
        self.vault_root = Path(vault_root)
        self.jekyll_root = Path(jekyll_root)
        self.debug = debug
        self.dry_run = dry_run
        
        # Set up backup directories
        self.pkm_backup_dir = self.vault_root.parent / "PKM_backup"
        self.jekyll_backup_dir = self.jekyll_root.parent / "jekyll_backup"
        
        # Default to keeping 5 most recent backups
        self.max_backups = 5
    
    def print_info(self, text: str) -> None:
        """Print formatted info"""
        if self.debug:
            print(f"  {text}")
    
    def print_action(self, text: str) -> None:
        """Print a formatted action message"""
        if self.debug:
            prefix = "WOULD" if self.dry_run else "WILL"
            print(f"  {prefix}: {text}")
    
    def create_backup_dir(self, backup_dir: Path) -> None:
        """Create backup directory if it doesn't exist"""
        if not backup_dir.exists():
            self.print_action(f"Create backup directory: {backup_dir}")
            if not self.dry_run:
                backup_dir.mkdir(parents=True)
    
    def get_backup_timestamp(self) -> str:
        """Get formatted timestamp for backup directory name"""
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    
    def rotate_backups(self, backup_dir: Path) -> None:
        """Remove old backups keeping only max_backups most recent"""
        # Skip rotation in dry run mode if directory doesn't exist
        if self.dry_run and not backup_dir.exists():
            return
            
        # List all backup directories
        backups = sorted([d for d in backup_dir.iterdir() if d.is_dir()], 
                        key=lambda x: x.name, reverse=True)
        
        # Remove old backups
        for old_backup in backups[self.max_backups:]:
            self.print_action(f"Remove old backup: {old_backup}")
            if not self.dry_run:
                shutil.rmtree(old_backup)
    
    def backup_pkm(self) -> None:
        """Create backup of PKM files"""
        if self.debug:
            print("\nBacking up PKM files:")
        
        # Create backup directory
        self.create_backup_dir(self.pkm_backup_dir)
        
        # Create timestamped backup directory
        timestamp = self.get_backup_timestamp()
        backup_path = self.pkm_backup_dir / timestamp
        
        # Copy files
        self.print_action(f"Create PKM backup in: {backup_path}")
        if not self.dry_run:
            shutil.copytree(self.vault_root / "atomics", backup_path / "atomics")
        
        # Rotate old backups
        self.rotate_backups(self.pkm_backup_dir)
    
    def backup_jekyll(self) -> None:
        """Create backup of Jekyll files"""
        if self.debug:
            print("\nBacking up Jekyll files:")
        
        # Create backup directory
        self.create_backup_dir(self.jekyll_backup_dir)
        
        # Create timestamped backup directory
        timestamp = self.get_backup_timestamp()
        backup_path = self.jekyll_backup_dir / timestamp
        
        # Copy files
        self.print_action(f"Create Jekyll backup in: {backup_path}")
        if not self.dry_run:
            # Copy posts and assets
            shutil.copytree(self.jekyll_root / "_posts", backup_path / "_posts")
            shutil.copytree(self.jekyll_root / "assets/img/posts", 
                           backup_path / "assets/img/posts")
        
        # Rotate old backups
        self.rotate_backups(self.jekyll_backup_dir)
    
    def backup_all(self) -> None:
        """Create backups of both PKM and Jekyll files"""
        self.backup_pkm()
        self.backup_jekyll() 