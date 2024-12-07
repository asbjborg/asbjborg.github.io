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
        
        # Test file patterns to ignore
        self.test_patterns = [
            'test', 
            'testing',
            'jekyll only post',
            'jekyll-only-post',
            'private post',
            'no status post',
            'draft post'
        ]

    def print_info(self, text: str) -> None:
        """Print formatted info"""
        if self.debug:
            print(f"  {text}")
    
    def print_subheader(self, text: str) -> None:
        """Print a formatted subheader"""
        if self.debug:
            print(f"\n{Colors.BLUE}{text}{Colors.ENDC}")
    
    def is_test_file(self, path: Path) -> bool:
        """Check if a file is a test file"""
        name = path.stem.lower()
        return any(pattern.lower() in name for pattern in self.test_patterns)

    def get_obsidian_files(self) -> Tuple[List[Path], List[Path]]:
        """Get lists of published and draft files from Obsidian vault"""
        published_files = []
        draft_files = []

        if self.debug:
            self.print_subheader(f"Scanning Obsidian files in: {self.atomics_dir}")

        for md_file in self.atomics_dir.rglob("*.md"):
            try:
                # Skip test files
                if self.is_test_file(md_file):
                    if self.debug:
                        rel_path = md_file.relative_to(self.vault_root)
                        self.print_info(f"Skipping test file: {rel_path}")
                    continue
                
                post = frontmatter.load(md_file)
                status = post.get('status', None)
                
                if self.debug:
                    rel_path = md_file.relative_to(self.vault_root)
                    self.print_info(f"Found file: {rel_path}, status: {status}")
                
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
            for post_file in self.posts_dir.glob("*.md"):
                # Skip test files
                if self.is_test_file(post_file):
                    if self.debug:
                        rel_path = post_file.relative_to(self.jekyll_root)
                        self.print_info(f"Skipping test file: {rel_path}")
                    continue
                posts.append(post_file)

        if self.debug:
            self.print_subheader(f"Scanning Jekyll assets in: {self.assets_dir}")

        # Get assets
        if self.assets_dir.exists():
            for asset_file in self.assets_dir.glob("*.*"):
                # Skip test files
                if self.is_test_file(asset_file):
                    if self.debug:
                        rel_path = asset_file.relative_to(self.jekyll_root)
                        self.print_info(f"Skipping test file: {rel_path}")
                    continue
                assets.append(asset_file)

        if self.debug:
            self.print_info(f"\nFound {len(posts)} Jekyll posts")
            self.print_info(f"Found {len(assets)} Jekyll assets")

        return posts, assets
