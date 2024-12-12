#!/usr/bin/env python3

import os
import re
import shutil
from pathlib import Path
from typing import Dict, Set, List, Optional
import time
import yaml
from dotenv import load_dotenv
import json
import sys
import traceback
import logging

def load_env():
    """Load environment variables"""
    load_dotenv()
    vault_root = os.getenv('SYNC_VAULT_ROOT')
    jekyll_root = os.getenv('SYNC_JEKYLL_ROOT')
    
    print(f"Loading environment:")
    print(f"SYNC_VAULT_ROOT: {vault_root}")
    print(f"SYNC_JEKYLL_ROOT: {jekyll_root}")
    
    if not vault_root or not jekyll_root:
        raise ValueError("SYNC_VAULT_ROOT and SYNC_JEKYLL_ROOT must be set in .env")
    
    return Path(vault_root), Path(jekyll_root)

class SyncDB:
    """JSON-based storage for sync state"""
    def __init__(self, root_dir: Path):
        self.posts_file = root_dir / 'sync_posts.json'
        self.assets_file = root_dir / 'sync_assets.json'
        self._posts = self._load_json(self.posts_file)
        self._assets = self._load_json(self.assets_file)
    
    def _load_json(self, path: Path) -> dict:
        """Load JSON file or return empty dict"""
        try:
            if path.exists():
                with open(path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error loading {path}: {e}")
        return {}
    
    def _save_json(self, path: Path, data: dict):
        """Save data to JSON file"""
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving {path}: {e}")
    
    def update_post(self, obsidian_path: str, frontmatter: Dict, last_modified: int):
        """Update post metadata"""
        # Get Jekyll path
        date_str = get_date_from_path(Path(obsidian_path))
        jekyll_name = f"{date_str}-{normalize_filename(Path(obsidian_path).stem)}.md"
        jekyll_path = f"_posts/{jekyll_name}"
        
        # Get featured image path if it exists
        featured_image = None
        if frontmatter.get('image'):
            img_ref = frontmatter['image'].strip('"\' []')
            if img_ref.startswith('atomics/'):
                featured_image = img_ref
        
        # Calculate time in seconds since midnight
        time_seconds = seconds_since_midnight(last_modified)
        
        # Convert tags to list, filtering out system tags
        tags = [tag for tag in frontmatter.get('tags', []) if tag not in ['atomic', 'blog']]
        
        # Store post data
        self._posts[obsidian_path] = {
            'jekyll_path': jekyll_path,
            'title': frontmatter.get('title', ''),
            'tags': tags,
            'time': time_seconds,
            'featured_image': featured_image,
            'status': frontmatter.get('status', ''),
            'last_modified': last_modified
        }
        
        self._save_json(self.posts_file, self._posts)
    
    def update_asset(self, obsidian_path: str, jekyll_path: str, post_path: str, last_modified: int):
        """Update asset metadata"""
        self._assets[obsidian_path] = {
            'jekyll_path': jekyll_path,
            'post_path': post_path,
            'last_modified': last_modified
        }
        self._save_json(self.assets_file, self._assets)
    
    def get_published_posts(self) -> List[tuple]:
        """Get all published posts"""
        result = []
        for obsidian_path, data in self._posts.items():
            if data.get('status') == 'published':
                result.append((
                    obsidian_path,
                    data['jekyll_path'],
                    data['title'],
                    json.dumps(data['tags']),
                    data['time'],
                    data['featured_image'],
                    data['last_modified']
                ))
        return result
    
    def get_post_assets(self, post_path: Optional[str] = None) -> List[tuple]:
        """Get assets for a post or all assets if post_path is None"""
        result = []
        for obsidian_path, data in self._assets.items():
            if post_path is None or data['post_path'] == post_path:
                result.append((
                    obsidian_path,
                    data['jekyll_path'],
                    data['last_modified']
                ))
        return result
    
    def cleanup_assets(self):
        """Remove assets that aren't referenced by any posts"""
        valid_posts = {k for k, v in self._posts.items() if v['status'] in ['published', 'draft']}
        valid_assets = {}
        
        for asset_path, data in self._assets.items():
            if data['post_path'] in valid_posts:
                valid_assets[asset_path] = data
        
        if valid_assets != self._assets:
            self._assets = valid_assets
            self._save_json(self.assets_file, self._assets)

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
        return yaml.safe_load(frontmatter)
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
    new_content = content
    new_frontmatter = frontmatter_data.copy()
    
    # Convert image paths in content
    for match in re.finditer(r'!\[\[(.*?)\]\]', content):
        old_path = match.group(1)
        if old_path.startswith('atomics/'):
            img_name = Path(old_path).name
            normalized_name = normalize_filename(img_name)
            new_path = f'/assets/img/posts/{normalized_name}'
            new_content = new_content.replace(f'![[{old_path}]]', f'![{Path(old_path).stem}]({new_path})')
    
    # Convert frontmatter
    if 'image' in new_frontmatter:
        img_path = new_frontmatter['image'].strip('"\' []')
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
    
    # Remove Obsidian-specific fields
    for field in ['moc', 'upsert', 'upserted', 'synced', 'status', 'date']:
        new_frontmatter.pop(field, None)
    
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
    return time.strftime("%Y-%m-%d")

@safe_time_operation
def get_full_timestamp():
    """Get current time in YYYY-MM-DD HH:MM:SS format"""
    return time.strftime("%Y-%m-%d %H:%M:%S")

@safe_time_operation
def seconds_since_midnight(timestamp: int) -> int:
    """Convert Unix timestamp to seconds since midnight"""
    try:
        t = time.localtime(timestamp)
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
    
    log_file = os.path.join(log_dir, f"sync_{time.strftime('%Y%m%d_%H%M%S')}.log")
    
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

def create_jekyll_frontmatter(post_data, assets_db) -> Dict:
    """Create Jekyll frontmatter with only allowed properties"""
    obsidian_path, jekyll_path, title, tags_json, time, featured_image, last_modified = post_data
    
    frontmatter = {
        'title': title,
        'tags': json.loads(tags_json),
        'time': time  # Already in seconds since midnight
    }
    
    # Convert featured image path if it exists
    if featured_image:
        c = assets_db.cursor()
        c.execute('SELECT jekyll_path FROM assets WHERE obsidian_path = ? AND post_path = ?',
                 (featured_image, obsidian_path))
        result = c.fetchone()
        if result:
            frontmatter['image'] = f"/{result[0]}"
    
    return frontmatter

def sync_files(dry_run: bool = False, debug: bool = False):
    """Sync files from Obsidian to Jekyll"""
    # Get log level from environment
    log_enabled = os.getenv('SYNC_LOG', 'false').lower() == 'true'
    print(f"=== Sync Started at {time.strftime('%a %b %d %H:%M:%S %Z %Y')} ===")
    
    if debug:
        print(f"Debug mode: {debug}")
        print(f"Log mode: {log_enabled}")
    
    # Load paths
    vault_root, jekyll_root = load_env()
    atomics_dir = vault_root / 'atomics'
    posts_dir = jekyll_root / '_posts'
    assets_dir = jekyll_root / 'assets/img/posts'
    
    if debug:
        print(f"Vault root: {vault_root}")
        print(f"Jekyll root: {jekyll_root}")
        print(f"Atomics dir: {atomics_dir}")
        print(f"Posts dir: {posts_dir}")
        print(f"Assets dir: {assets_dir}")
    
    # Create directories if they don't exist
    for dir in [atomics_dir, posts_dir, assets_dir]:
        dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize database
    db = SyncDB(jekyll_root)
    
    # Track valid posts and assets
    valid_posts = set()
    valid_assets = set()
    
    # First pass: Update database from Obsidian
    if log_enabled:
        print("Scanning Obsidian files...")
    if debug:
        print(f"Looking for .md files in: {atomics_dir}")
    
    for md_file in atomics_dir.rglob('*.md'):
        try:
            rel_path = str(md_file.relative_to(vault_root))
            if debug:
                print(f"Found file: {rel_path}")
            
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                frontmatter_data = extract_frontmatter(content)
                
                # Skip if no frontmatter or no status
                if not frontmatter_data:
                    if debug:
                        print(f"Skipping {md_file.name} - no frontmatter")
                    continue
                
                status = frontmatter_data.get('status', '')
                if not status:
                    if debug:
                        print(f"Skipping {md_file.name} - no status")
                    continue
                
                # Update post in database
                last_modified = int(md_file.stat().st_mtime)
                db.update_post(rel_path, frontmatter_data, last_modified)
                
                # Track assets if published/draft
                if status.lower() in ['published', 'draft']:
                    # Extract image references
                    for match in re.finditer(r'!\[\[(.*?)\]\]', content):
                        img_ref = match.group(1)
                        if img_ref and img_ref.startswith('atomics/'):
                            img_path = atomics_dir / '/'.join(img_ref.split('/')[1:])
                            if img_path.exists() and img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                                jekyll_name = normalize_filename(img_path.name)
                                db.update_asset(str(img_path.relative_to(vault_root)),
                                          f"assets/img/posts/{jekyll_name}",
                                          rel_path, int(img_path.stat().st_mtime))
                                valid_assets.add(img_path)
                    
                    # Check frontmatter image
                    if frontmatter_data.get('image'):
                        img_ref = frontmatter_data['image'].strip('"\' []')
                        if img_ref.startswith('atomics/'):
                            img_path = atomics_dir / '/'.join(img_ref.split('/')[1:])
                            if img_path.exists() and img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                                jekyll_name = normalize_filename(img_path.name)
                                db.update_asset(str(img_path.relative_to(vault_root)),
                                          f"assets/img/posts/{jekyll_name}",
                                          rel_path, int(img_path.stat().st_mtime))
                                valid_assets.add(img_path)
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
    
    # Second pass: Sync published posts to Jekyll
    if log_enabled:
        print("Syncing published posts...")
    for post in db.get_published_posts():
        obsidian_path, jekyll_path, title, tags_json, time, featured_image, last_modified = post
        
        # Get full paths
        obsidian_file = vault_root / obsidian_path
        jekyll_file = jekyll_root / jekyll_path
        valid_posts.add(obsidian_path)  # Track by obsidian_path for asset lookup
        
        # Check if Jekyll file needs update
        needs_update = True
        if jekyll_file.exists():
            jekyll_mtime = int(jekyll_file.stat().st_mtime)
            needs_update = last_modified > jekyll_mtime
        
        if needs_update and not dry_run:
            if jekyll_file.exists():
                print(f"[SYNC_CHANGE] Post updated: {jekyll_file.name}")
            else:
                print(f"[SYNC_CHANGE] Post created: {jekyll_file.name}")
            
            # Read and process content
            with open(obsidian_file, 'r', encoding='utf-8') as f:
                content = f.read()
                content_without_frontmatter = extract_content(content)
                
                # Convert image paths in content
                converted_content = convert_image_paths(db, content_without_frontmatter, obsidian_path)
                
                # Create Jekyll frontmatter with only allowed properties
                jekyll_frontmatter = create_jekyll_frontmatter(post, db)
                
                # Write Jekyll file
                jekyll_file.parent.mkdir(parents=True, exist_ok=True)
                with open(jekyll_file, 'w', encoding='utf-8') as jf:
                    jf.write('---\n')
                    yaml.dump(jekyll_frontmatter, jf, allow_unicode=True, sort_keys=False)
                    jf.write('---\n\n')
                    jf.write(converted_content)
                
                # Update file timestamp
                os.utime(jekyll_file, (last_modified, last_modified))
    
    # Third pass: Sync assets
    if log_enabled:
        print("Syncing assets...")
    for post_path in valid_posts:
        for asset in db.get_post_assets(post_path):
            obsidian_path, jekyll_path, last_modified = asset
            
            # Get full paths
            obsidian_file = vault_root / obsidian_path
            jekyll_file = jekyll_root / jekyll_path
            
            # Copy to Jekyll if newer
            if not dry_run and obsidian_file.exists():
                if not jekyll_file.exists() or last_modified > int(jekyll_file.stat().st_mtime):
                    if jekyll_file.exists():
                        print(f"[SYNC_CHANGE] Asset updated: {jekyll_file.name}")
                    else:
                        print(f"[SYNC_CHANGE] Asset created: {jekyll_file.name}")
                    jekyll_file.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.copy2(obsidian_file, jekyll_file)
                    except Exception as e:
                        print(f"Error copying {obsidian_file}: {e}")
    
    # Final pass: Cleanup orphaned assets
    if log_enabled:
        print("Cleaning up orphaned assets...")
    db.cleanup_assets()
    
    # Clean up invalid Jekyll posts
    if log_enabled:
        print("Cleaning up Jekyll posts...")
    if debug:
        print("Valid posts from database:")
        for post in db.get_published_posts():
            print(f"  - {post[1]}")  # jekyll_path
    
    for md_file in posts_dir.glob('*.md'):
        jekyll_path = str(md_file.relative_to(jekyll_root))
        if debug:
            print(f"Checking Jekyll post: {jekyll_path}")
        if jekyll_path not in [post[1] for post in db.get_published_posts()]:
            print(f"[SYNC_CHANGE] Post deleted: {md_file.name}")
            if not dry_run:
                md_file.unlink()
    
    # Clean up unused assets
    if log_enabled:
        print("Cleaning up unused assets...")
    for img_path in assets_dir.glob('*.*'):
        jekyll_path = f"assets/img/posts/{img_path.name}"
        if jekyll_path not in [asset[1] for asset in db.get_post_assets(None)]:
            print(f"[SYNC_CHANGE] Asset deleted: {img_path.name}")
            if not dry_run:
                img_path.unlink()
    
    print(f"=== Sync Completed at {time.strftime('%a %b %d %H:%M:%S %Z %Y')} ===")

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