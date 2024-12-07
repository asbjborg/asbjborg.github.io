import os
import frontmatter
from typing import List, Dict, Tuple
from pathlib import Path

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class FileHandler:
    def __init__(self, vault_root: str, jekyll_root: str, debug: bool = False):
        self.vault_root = Path(vault_root)
        self.jekyll_root = Path(jekyll_root)
        
        # Get paths from environment variables with defaults
        atomics_path = os.getenv('SYNC_VAULT_ATOMICS', 'atomics')
        posts_path = os.getenv('SYNC_JEKYLL_POSTS', '_posts')
        assets_path = os.getenv('SYNC_JEKYLL_ASSETS', 'assets/img/posts')
        
        self.atomics_dir = self.vault_root / atomics_path
        self.posts_dir = self.jekyll_root / posts_path
        self.assets_dir = self.jekyll_root / assets_path
        self.debug = debug

    def print_info(self, text: str) -> None:
        """Print formatted info"""
        if self.debug:
            print(f"  {text}")
    
    def print_subheader(self, text: str) -> None:
        """Print a formatted subheader"""
        if self.debug:
            print(f"\n{Colors.BLUE}{text}{Colors.ENDC}")

    def get_obsidian_files(self) -> Tuple[List[Path], List[Path]]:
        """Get lists of published and draft files from Obsidian vault"""
        published_files = []
        draft_files = []

        if self.debug:
            self.print_subheader(f"Scanning Obsidian files in: {self.atomics_dir}")

        for md_file in self.atomics_dir.rglob("*.md"):
            try:
                post = frontmatter.load(md_file)
                status = post.get('status', None)
                
                if self.debug:
                    self.print_info(f"Found file: {md_file.relative_to(self.vault_root)}, status: {status}")
                
                if status == "published":
                    published_files.append(md_file)
                elif status == "draft":
                    draft_files.append(md_file)
                # Files with no status or status=private are ignored
                
            except Exception as e:
                if self.debug:
                    print(f"{Colors.RED}Error reading {md_file}: {str(e)}{Colors.ENDC}")
                continue

        if self.debug:
            self.print_info(f"\nFound {len(published_files)} published files")
            self.print_info(f"Found {len(draft_files)} draft files")

        return published_files, draft_files

    def get_jekyll_files(self) -> Tuple[List[Path], List[Path]]:
        """Get lists of posts and assets from Jekyll site"""
        posts = []
        assets = []

        if self.debug:
            self.print_subheader(f"Scanning Jekyll posts in: {self.posts_dir}")

        # Get posts
        if self.posts_dir.exists():
            posts = list(self.posts_dir.glob("*.md"))

        if self.debug:
            self.print_subheader(f"Scanning Jekyll assets in: {self.assets_dir}")

        # Get assets
        if self.assets_dir.exists():
            assets = list(self.assets_dir.glob("*.*"))

        if self.debug:
            self.print_info(f"\nFound {len(posts)} Jekyll posts")
            self.print_info(f"Found {len(assets)} Jekyll assets")

        return posts, assets
