import re
import os
from pathlib import Path
from datetime import datetime

class PathConverter:
    def __init__(self, vault_root: str, jekyll_root: str, debug: bool = False):
        self.vault_root = Path(vault_root)
        self.jekyll_root = Path(jekyll_root)
        self.debug = debug
        
        # Get paths from environment variables with defaults
        self.atomics_path = os.getenv('SYNC_VAULT_ATOMICS', 'atomics')
        self.posts_path = os.getenv('SYNC_JEKYLL_POSTS', '_posts')
        self.assets_path = os.getenv('SYNC_JEKYLL_ASSETS', 'assets/img/posts')
    
    def obsidian_to_jekyll_post(self, obsidian_path: Path) -> Path:
        """Convert Obsidian post path to Jekyll post path"""
        # Extract date from path
        date_match = re.search(r'/(\d{4}/\d{2}/\d{2})/', str(obsidian_path))
        if not date_match:
            raise ValueError(f"Could not extract date from Obsidian path: {obsidian_path}")
        
        date_str = date_match.group(1).replace('/', '-')
        filename = obsidian_path.stem
        
        # Construct Jekyll path
        jekyll_path = self.jekyll_root / self.posts_path / f"{date_str}-{filename}.md"
        
        if self.debug:
            print(f"Converting Obsidian post path: {obsidian_path}")
            print(f"To Jekyll post path: {jekyll_path}")
        
        return jekyll_path

    def jekyll_to_obsidian_post(self, jekyll_path: Path) -> Path:
        """Convert Jekyll post path to Obsidian post path"""
        # Extract date and name from Jekyll filename
        match = re.match(r'(\d{4})-(\d{2})-(\d{2})-(.*?)\.md$', jekyll_path.name)
        if not match:
            raise ValueError(f"Invalid Jekyll post filename: {jekyll_path}")
        
        year, month, day, name = match.groups()
        
        # Construct Obsidian path
        obsidian_path = self.vault_root / self.atomics_path / year / month / day / f"{name}.md"
        
        if self.debug:
            print(f"Converting Jekyll post path: {jekyll_path}")
            print(f"To Obsidian post path: {obsidian_path}")
        
        return obsidian_path

    def obsidian_to_jekyll_image(self, wikilink: str, in_frontmatter: bool = False) -> str:
        """Convert Obsidian image wikilink to Jekyll image path"""
        # Handle quoted wikilinks in frontmatter
        if in_frontmatter:
            wikilink = wikilink.strip('"')
        
        # Extract path from wikilink
        match = re.match(r'\!?\[\[(.*?)\]\]', wikilink)
        if not match:
            raise ValueError(f"Invalid wikilink format: {wikilink}")
        
        image_path = match.group(1)
        filename = Path(image_path).name
        
        # Construct Jekyll path
        jekyll_path = f"/{self.assets_path}/{filename}"
        
        # Add quotes if in frontmatter
        if in_frontmatter:
            jekyll_path = f'"{jekyll_path}"'
        
        if self.debug:
            print(f"Converting Obsidian image wikilink: {wikilink}")
            print(f"To Jekyll image path: {jekyll_path}")
        
        return jekyll_path

    def jekyll_to_obsidian_image(self, jekyll_path: str, post_filename: str, in_frontmatter: bool = False) -> str:
        """Convert Jekyll image path to Obsidian wikilink"""
        # Handle quotes in frontmatter
        if in_frontmatter:
            jekyll_path = jekyll_path.strip('"')
        
        # Extract filename from Jekyll path
        filename = Path(jekyll_path).name
        
        # Extract date from post filename
        match = re.match(r'(\d{4})-(\d{2})-(\d{2})', post_filename)
        if not match:
            raise ValueError(f"Invalid Jekyll post filename: {post_filename}")
        
        year, month, day = match.groups()
        date_path = f"{year}/{month}/{day}"
        
        # Construct Obsidian path
        obsidian_path = f"{self.atomics_path}/{date_path}/{filename}"
        
        # Create wikilink with proper quoting
        wikilink = f"[[{obsidian_path}]]"
        if not in_frontmatter:
            wikilink = f"!{wikilink}"
        else:
            wikilink = f'"{wikilink}"'
        
        if self.debug:
            print(f"Converting Jekyll image path: {jekyll_path}")
            print(f"Using post date from: {post_filename}")
            print(f"To Obsidian wikilink: {wikilink}")
        
        return wikilink
