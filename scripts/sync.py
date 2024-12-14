#!/usr/bin/env python3

import os
import re
import shutil
from pathlib import Path
from typing import Dict, Set, List, Optional
import time as time_module
import yaml
from dotenv import load_dotenv
import json
import sys
import traceback
import logging
import hashlib

def load_env():
    """Load environment variables"""
    load_dotenv()
    vault_root = os.getenv('SYNC_VAULT_ROOT')
    jekyll_root = os.getenv('SYNC_JEKYLL_ROOT')
    
    print(f"Loading environment:")
    print(f"SYNC_VAULT_ROOT: {vault_root}")
    print(f"SYNC_JEKYLL_ROOT: {jekyll_root}")
    print(f"Current working directory: {os.getcwd()}")
    print(f".env file exists: {os.path.exists('.env')}")
    
    if not vault_root or not jekyll_root:
        raise ValueError("SYNC_VAULT_ROOT and SYNC_JEKYLL_ROOT must be set in .env")
    
    return Path(vault_root), Path(jekyll_root)

class SyncDB:
    """Database for tracking synced files"""
    def __init__(self, db_dir: str):
        self.db_dir = db_dir
        self.posts_file = os.path.join(db_dir, 'sync_posts.json')
        self._ensure_files_exist()
        self.posts = []  # Initialize as empty list
        self.load()  # Load data from file

    def _ensure_files_exist(self):
        """Ensure database files exist"""
        if not os.path.exists(self.posts_file):
            with open(self.posts_file, 'w') as f:
                json.dump([], f)

    def _datetime_to_str(self, obj):
        """Convert datetime objects to ISO format strings"""
        if isinstance(obj, dict):
            return {k: self._datetime_to_str(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._datetime_to_str(v) for v in obj]
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return obj

    def load(self):
        """Load data from file"""
        try:
            with open(self.posts_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.posts = data
                else:
                    self.posts = []
        except:
            self.posts = []

    def save(self):
        """Save data to file"""
        with open(self.posts_file, 'w') as f:
            # Convert datetime objects to strings before saving
            json_data = self._datetime_to_str(self.posts)
            json.dump(json_data, f, indent=2)

    def get_post(self, file_path: str) -> Optional[Dict]:
        """Get post data by file path"""
        for post in self.posts:
            if isinstance(post, dict) and post.get('file_path') == file_path:
                return post
        return None

    def update_post(self, file_path: str, frontmatter: Dict, content_hash: str):
        """Add or update post data"""
        post = self.get_post(file_path)
        if post:
            post['frontmatter'] = frontmatter
            post['content_hash'] = content_hash
        else:
            self.posts.append({
                'file_path': file_path,
                'frontmatter': frontmatter,
                'content_hash': content_hash,
                'obsidian_path': file_path,
                'jekyll_path': normalize_filename(os.path.basename(file_path)),
                'title': frontmatter.get('title', ''),
                'tags': frontmatter.get('tags', []),
                'time': frontmatter.get('time', 0),
                'featured_image': frontmatter.get('image', ''),
                'last_modified': time_module.time()
            })
        self.save()

    def update_asset(self, obsidian_path: str, jekyll_path: str, post_path: str = None, content_hash: str = None, last_modified: float = None):
        """Update asset mapping - no-op since we handle assets in cleanup_assets"""
        pass

    def get_published_posts(self) -> List[Dict]:
        """Get all published posts"""
        published = []
        for post in self.posts:
            if (isinstance(post, dict) and 
                isinstance(post.get('frontmatter'), dict) and 
                post.get('frontmatter', {}).get('status') == 'published'):
                # Extract date from file path
                path_parts = post['file_path'].split('/')
                if len(path_parts) >= 4 and path_parts[-4].isdigit() and path_parts[-3].isdigit() and path_parts[-2].isdigit():
                    year = path_parts[-4]
                    month = path_parts[-3].zfill(2)
                    day = path_parts[-2].zfill(2)
                    jekyll_name = f"{year}-{month}-{day}-{normalize_filename(os.path.basename(post['file_path']))}"
                else:
                    # Fallback to current date if path doesn't contain date
                    current_time = time_module.localtime()
                    jekyll_name = f"{current_time.tm_year}-{current_time.tm_mon:02d}-{current_time.tm_mday:02d}-{normalize_filename(os.path.basename(post['file_path']))}"
                
                published.append({
                    'obsidian_path': post['file_path'],
                    'jekyll_path': jekyll_name,
                    'title': post['frontmatter'].get('title', ''),
                    'tags': post['frontmatter'].get('tags', []),
                    'time': post['frontmatter'].get('time', 0),
                    'featured_image': post['frontmatter'].get('image', ''),
                    'last_modified': post.get('last_modified', time_module.time())
                })
        return published

    def get_content_hash(self, file_path: str) -> Optional[str]:
        """Get content hash for a post"""
        post = self.get_post(file_path)
        return post['content_hash'] if post else None

    def remove_post(self, file_path: str):
        """Remove post data"""
        self.posts = [post for post in self.posts if isinstance(post, dict) and post.get('file_path') != file_path]
        self.save()

    def cleanup_assets(self):
        """Clean up orphaned assets that are no longer referenced by any posts"""
        # Get all referenced image paths from posts
        referenced_images = set()
        for post in self.posts:
            if not isinstance(post, dict) or not isinstance(post.get('frontmatter'), dict):
                continue
                
            # Check frontmatter image
            if 'image' in post['frontmatter']:
                img_path = str(post['frontmatter']['image']).strip('"\' []')
                if img_path.startswith('/assets/img/posts/'):
                    referenced_images.add(os.path.basename(img_path))

            # Check content for images
            if 'content' in post:
                for match in re.finditer(r'!\[.*?\]\((.*?)\)', str(post.get('content', ''))):
                    img_path = match.group(1)
                    if img_path.startswith('/assets/img/posts/'):
                        referenced_images.add(os.path.basename(img_path))

        # Get all existing assets
        assets_dir = os.path.join(os.getenv('SYNC_JEKYLL_ROOT'), 'assets', 'img', 'posts')
        if not os.path.exists(assets_dir):
            return

        existing_assets = set(f for f in os.listdir(assets_dir) if os.path.isfile(os.path.join(assets_dir, f)))

        # Remove orphaned assets
        for asset in existing_assets:
            if asset not in referenced_images:
                asset_path = os.path.join(assets_dir, asset)
                try:
                    os.remove(asset_path)
                    print(f"Removed orphaned asset: {asset}")
                except Exception as e:
                    print(f"Error removing asset {asset}: {e}")

def normalize_filename(filename: str) -> str:
    """Normalize filename for Jekyll compatibility"""
    # Split name and extension
    name = filename.rsplit('.', 1)[0]
    ext = filename.rsplit('.', 1)[1] if '.' in filename else ''
    
    # Convert to lowercase
    normalized = name.lower()
    
    # Replace spaces and other special characters with dashes
    normalized = re.sub(r'[^a-z0-9]+', '-', normalized)
    
    # Remove leading/trailing dashes
    normalized = normalized.strip('-')
    
    # Collapse multiple dashes into one
    normalized = re.sub(r'-+', '-', normalized)
    
    # Add extension back if it exists
    if ext:
        normalized = f"{normalized}.{ext}"
    
    return normalized

def extract_frontmatter(content: str) -> Dict:
    """Extract frontmatter from content"""
    if not content.startswith('---\n'):
        return {}
    
    try:
        # Find the second '---'
        end = content.find('\n---\n', 4)
        if end == -1:
            return {}
        
        # Extract and parse frontmatter
        frontmatter = content[4:end]
        return yaml.safe_load(frontmatter) or {}
    except yaml.YAMLError as e:
        print(f"Warning: Error parsing frontmatter: {e}")
        return {}

def extract_content(content: str) -> str:
    """Extract content without frontmatter"""
    if not content.startswith('---\n'):
        return content
    
    # Find the second '---'
    end = content.find('\n---\n', 4)
    if end == -1:
        return content
    
    # Return content after frontmatter
    return content[end + 5:]

def convert_content(content: str, frontmatter_data: Dict) -> tuple[str, Dict]:
    """Convert content and frontmatter from Obsidian to Jekyll format"""
    # Extract content without frontmatter
    content_without_frontmatter = extract_content(content)
    new_content = content_without_frontmatter
    
    # Start with empty frontmatter and only copy whitelisted properties
    new_frontmatter = {}
    allowed_properties = {
        'title',      # Post title
        'tags',       # Post tags
        'time',       # Reading time
        'image',      # Featured image
        'status',     # Post status (published/draft)
        'excerpt',    # Post excerpt/description
        'categories', # Post categories
        'author',     # Post author
        'pin',        # Whether to pin the post
        'math',       # Whether post contains math
        'mermaid',    # Whether post contains mermaid diagrams
        'comments',   # Whether to enable comments
        'toc'         # Whether to show table of contents
    }
    
    # Copy only allowed properties
    for prop in allowed_properties:
        if prop in frontmatter_data:
            new_frontmatter[prop] = frontmatter_data[prop]
    
    # Convert image paths in content
    for match in re.finditer(r'!\[\[(.*?)\]\]', new_content):
        old_path = match.group(1)
        if old_path.startswith('atomics/'):
            img_name = Path(old_path).name
            normalized_name = normalize_filename(img_name)
            new_path = f'/assets/img/posts/{normalized_name}'
            new_content = new_content.replace(f'![[{old_path}]]', f'![{Path(old_path).stem}]({new_path})')
    
    # Convert frontmatter image if present
    if 'image' in new_frontmatter:
        img_path = str(new_frontmatter['image']).strip('"\' []')
        if img_path.startswith('atomics/'):
            img_name = Path(img_path).name
            normalized_name = normalize_filename(img_name)
            new_frontmatter['image'] = f'/assets/img/posts/{normalized_name}'
    
    # Convert time if present
    if 'time' in new_frontmatter and isinstance(new_frontmatter['time'], str):
        try:
            h, m, s = map(int, new_frontmatter['time'].split(':'))
            new_frontmatter['time'] = h * 3600 + m * 60 + s
        except:
            del new_frontmatter['time']
    
    # Filter system tags
    if 'tags' in new_frontmatter:
        new_frontmatter['tags'] = [
            tag for tag in new_frontmatter['tags']
            if tag not in ['atomic', 'blog']
        ]
    
    return new_content, new_frontmatter

def safe_time_operation(func):
    """Decorator for safe time operations"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in time operation: {e}")
            return None
    return wrapper

@safe_time_operation
def get_timestamp():
    """Get current time in YYYY-MM-DD format"""
    return time_module.strftime("%Y-%m-%d")

@safe_time_operation
def get_full_timestamp():
    """Get current time in YYYY-MM-DD HH:MM:SS format"""
    return time_module.strftime("%Y-%m-%d %H:%M:%S")

@safe_time_operation
def seconds_since_midnight(timestamp: int) -> int:
    """Convert Unix timestamp to seconds since midnight"""
    try:
        t = time_module.localtime(timestamp)
        return t.tm_hour * 3600 + t.tm_min * 60 + t.tm_sec
    except Exception as e:
        logging.error(f"Error converting timestamp: {e}")
        return 0

@safe_time_operation
def get_date_from_path(path: Path) -> str:
    """Extract date from Obsidian path"""
    try:
        # First try to get date from path
        parts = path.parts
        for i in range(len(parts)):
            if parts[i] == 'atomics' and i + 3 < len(parts):
                year = parts[i+1]
                month = parts[i+2]
                day = parts[i+3]
                return f"{year}-{month}-{day}"
    except Exception as e:
        logging.error(f"Error extracting date from path {path}: {e}")
    
    # Default to current date
    return get_timestamp()

def setup_logging():
    log_dir = os.getenv('SYNC_LOG_DIR', 'LOGS')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"sync_{time_module.strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=logging.DEBUG if os.getenv('SYNC_DEBUG') else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def safe_file_operation(func):
    """Decorator for safe file operations"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error in file operation: {e}")
            traceback.print_exc()
            return None
    return wrapper

@safe_file_operation
def write_file(path: Path, content: str, frontmatter: Dict, dry_run: bool = False) -> None:
    """Write content and frontmatter to file"""
    if not dry_run:
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure YAML dumper
        def str_presenter(dumper, data):
            """Configure string handling in YAML"""
            if len(data.split('\n')) > 1:  # check for multiline string
                return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
            if any(c in data for c in '[]|>\'\"{}:,#'):  # check for special characters
                return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')
            return dumper.represent_scalar('tag:yaml.org,2002:str', data)
        
        yaml.add_representer(str, str_presenter)
        
        try:
            # Convert frontmatter to YAML
            frontmatter_yaml = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, width=float("inf"), sort_keys=False)
            
            # Write file with frontmatter
            with open(path, 'w', encoding='utf-8') as f:
                f.write('---\n')
                f.write(frontmatter_yaml)
                f.write('---\n\n')
                f.write(content.split('\n---\n', 1)[-1].lstrip())
        except Exception as e:
            print(f"Error writing file {path}: {e}")
            raise

def convert_image_paths(db: SyncDB, content: str, post_path: str) -> str:
    """Convert Obsidian image paths to Jekyll paths using the database"""
    
    # Function to get Jekyll path for an asset
    def get_jekyll_path(obsidian_path: str) -> str:
        for asset in db.get_post_assets(post_path):
            if asset[0] == obsidian_path:  # asset[0] is obsidian_path
                return f"/{asset[1]}"  # asset[1] is jekyll_path
        return obsidian_path
    
    # Convert inline images: ![[path]] -> ![alt](/jekyll/path)
    def replace_inline(match):
        obsidian_path = match.group(1)
        if obsidian_path.startswith('atomics/'):
            jekyll_path = get_jekyll_path(obsidian_path)
            return f"![{Path(obsidian_path).stem}]({jekyll_path})"
        return match.group(0)
    
    # Convert all image references
    content = re.sub(r'!\[\[(.*?)\]\]', replace_inline, content)
    
    return content

def create_jekyll_frontmatter(post_data: tuple, db: SyncDB) -> Dict:
    """Create Jekyll frontmatter from post data tuple"""
    obsidian_path, jekyll_path, title, tags_json, time, featured_image, last_modified = post_data
    
    # Create frontmatter with only allowed properties
    frontmatter_dict = {
        'title': title,
        'tags': json.loads(tags_json) if tags_json else [],
        'time': time or 0  # Default to 0 if not set
    }
    
    # Handle featured image
    if featured_image:
        # Look up the image path in the assets database
        assets_data = db.get_assets_data()
        for asset in assets_data:
            if asset['obsidian_path'] == featured_image and asset['post_path'] == obsidian_path:
                frontmatter_dict['image'] = f"/{asset['jekyll_path']}"
                break
    
    return frontmatter_dict

def sync_files(dry_run: bool = False, debug: bool = False):
    """Sync files between Obsidian and Jekyll"""
    # Load environment variables first
    load_dotenv()
    
    vault_root = os.getenv('SYNC_VAULT_ROOT')
    jekyll_root = os.getenv('SYNC_JEKYLL_ROOT')
    
    print(f"Loading environment:")
    print(f"SYNC_VAULT_ROOT: {vault_root}")
    print(f"SYNC_JEKYLL_ROOT: {jekyll_root}")
    print(f"Current working directory: {os.getcwd()}")
    print(f".env file exists: {os.path.exists('.env')}")
    
    if not vault_root or not jekyll_root:
        raise ValueError("SYNC_VAULT_ROOT and SYNC_JEKYLL_ROOT must be set in .env")
    
    vault_root = Path(vault_root)
    jekyll_root = Path(jekyll_root)
    atomics_dir = vault_root / 'atomics'
    posts_dir = jekyll_root / '_posts'
    assets_dir = jekyll_root / 'assets' / 'img' / 'posts'
    db_dir = jekyll_root / '.sync'

    print(f"Vault root: {vault_root}")
    print(f"Jekyll root: {jekyll_root}")
    print(f"Atomics dir: {atomics_dir}")
    print(f"Posts dir: {posts_dir}")
    print(f"Assets dir: {assets_dir}")

    # Create directories if they don't exist
    os.makedirs(db_dir, exist_ok=True)
    os.makedirs(posts_dir, exist_ok=True)
    os.makedirs(assets_dir, exist_ok=True)

    # Initialize database
    db = SyncDB(str(db_dir))

    # Track valid posts for cleanup
    valid_posts = set()
    valid_assets = set()

    # Track images referenced in published posts
    referenced_images = set()

    # First pass: scan published posts to collect referenced images
    print("Scanning published posts for image references...")
    for root, _, files in os.walk(atomics_dir):
        for file in files:
            if not file.endswith('.md'):
                continue

            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, vault_root)

            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract frontmatter
                frontmatter = extract_frontmatter(content)
                if frontmatter.get('status') != 'published':
                    continue

                # Check frontmatter for image references
                if 'image' in frontmatter:
                    img_path = str(frontmatter['image']).strip('"\' []')
                    if img_path.startswith('/assets/img/posts/'):
                        referenced_images.add(os.path.basename(img_path))

                # Check content for image references
                for match in re.finditer(r'!\[\[(.*?)\]\]', content):
                    img_path = match.group(1)
                    if img_path.startswith('atomics/'):
                        referenced_images.add(normalize_filename(Path(img_path).name))

                # Also check for standard markdown image syntax
                for match in re.finditer(r'!\[.*?\]\((.*?)\)', content):
                    img_path = match.group(1)
                    if img_path.startswith('/assets/img/posts/'):
                        referenced_images.add(os.path.basename(img_path))

            except Exception as e:
                print(f"Error scanning {file_path} for images: {e}")
                if debug:
                    traceback.print_exc()

    # Second pass: process files and copy only referenced images
    print("Processing files and copying referenced images...")
    for root, _, files in os.walk(atomics_dir):
        print(f"Looking for .md files and images in: {root}")
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, vault_root)
            
            # Handle markdown files
            if file.endswith('.md'):
                print(f"Found file: {rel_path}")

                try:
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Extract frontmatter
                    frontmatter = extract_frontmatter(content)
                    if not frontmatter.get('status'):
                        print(f"Skipping {file} - no status")
                        continue

                    # Calculate content hash
                    content_hash = hashlib.md5(content.encode()).hexdigest()

                    # Check if content has changed
                    if content_hash == db.get_content_hash(rel_path):
                        continue

                    # Convert content
                    new_content, new_frontmatter = convert_content(content, frontmatter)

                    # Update database
                    db.update_post(rel_path, frontmatter, content_hash)

                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    if debug:
                        traceback.print_exc()
            
            # Handle image files
            elif file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                try:
                    # Only copy image if it's referenced in a published post
                    normalized_name = normalize_filename(file)
                    if normalized_name in referenced_images:
                        dst = assets_dir / normalized_name
                        shutil.copy2(file_path, dst)
                        valid_assets.add(normalized_name)
                        print(f"Copied referenced image: {normalized_name}")
                except Exception as e:
                    print(f"Error copying image {file}: {e}")
                    if debug:
                        traceback.print_exc()

    # Sync published posts
    print("Syncing published posts...")
    for post in db.get_published_posts():
        try:
            # Read Obsidian file
            obsidian_file = os.path.join(vault_root, post['obsidian_path'])
            with open(obsidian_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Convert content
            frontmatter = extract_frontmatter(content)
            new_content, new_frontmatter = convert_content(content, frontmatter)

            # Write Jekyll file
            jekyll_file = os.path.join(posts_dir, post['jekyll_path'])
            valid_posts.add(post['jekyll_path'])
            if not dry_run:
                os.makedirs(os.path.dirname(jekyll_file), exist_ok=True)
                with open(jekyll_file, 'w', encoding='utf-8') as f:
                    f.write('---\n')
                    f.write(yaml.dump(new_frontmatter, allow_unicode=True))
                    f.write('---\n')
                    f.write(new_content)
                print(f"[SYNC_CHANGE] Post created: {post['jekyll_path']}")

        except Exception as e:
            print(f"Error syncing post {post['obsidian_path']}: {e}")
            if debug:
                traceback.print_exc()

    # Clean up orphaned posts
    print("Cleaning up orphaned posts...")
    for post_file in os.listdir(posts_dir):
        if post_file not in valid_posts:
            post_path = os.path.join(posts_dir, post_file)
            try:
                os.remove(post_path)
                print(f"Removed orphaned post: {post_file}")
            except Exception as e:
                print(f"Error removing post {post_file}: {e}")

    # Clean up orphaned assets
    print("Cleaning up orphaned assets...")
    for asset_file in os.listdir(assets_dir):
        if asset_file not in valid_assets:
            asset_path = os.path.join(assets_dir, asset_file)
            try:
                os.remove(asset_path)
                print(f"Removed orphaned asset: {asset_file}")
            except Exception as e:
                print(f"Error removing asset {asset_file}: {e}")

def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description='Sync Obsidian vault with Jekyll site')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be synced without making changes')
    args = parser.parse_args()
    
    # Get debug flag from environment or command line
    debug = os.getenv('SYNC_DEBUG', 'false').lower() == 'true' or args.debug
    
    try:
        sync_files(dry_run=args.dry_run, debug=debug)
    except Exception as e:
        print(f"Fatal error in sync script: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 