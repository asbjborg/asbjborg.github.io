#!/usr/bin/env python3

import os
import shutil
import sys
import time
import argparse
import frontmatter
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser('~/Library/Logs/obsidian-blog-sync.log'))
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class ObsidianHandler(FileSystemEventHandler):
    def __init__(self, blog_path: Path):
        try:
            self.vault_path = Path(os.getenv('VAULT_PATH')).expanduser().resolve()
            self.atomics_path = self.vault_path / os.getenv('VAULT_ATOMICS_PATH', 'atomics')
            self.blog_path = blog_path
            self.posts_path = blog_path / '_posts'
            self.posts_path.mkdir(exist_ok=True)

            if not self.vault_path.exists():
                raise ValueError(f"Vault path does not exist: {self.vault_path}")
            if not self.atomics_path.exists():
                raise ValueError(f"Atomics path does not exist: {self.atomics_path}")
            
            logger.info(f"Initialized with vault: {self.vault_path}")
            logger.info(f"Watching atomics path: {self.atomics_path}")
            logger.info(f"Publishing to: {self.posts_path}")
        except Exception as e:
            logger.error(f"Failed to initialize ObsidianHandler: {str(e)}")
            raise

    def _should_publish(self, path: Path) -> bool:
        """Check if a file should be published based on frontmatter."""
        if not path.suffix.lower() in ['.md', '.markdown']:
            logger.debug(f"Skipping non-markdown file: {path}")
            return False
        
        try:
            post = frontmatter.load(str(path))
            should_publish = post.get('published', False) is True
            logger.info(f"Checking {path}: published = {should_publish}")
            return should_publish
        except Exception as e:
            logger.error(f"Error reading frontmatter from {path}: {e}")
            return False

    def _get_post_filename(self, path: Path) -> str:
        """Generate Jekyll-compatible filename from Obsidian file path."""
        try:
            # Extract date from path (YYYY/MM/DD)
            try:
                date_parts = [path.parts[-4], path.parts[-3].zfill(2), path.parts[-2].zfill(2)]
                date = '-'.join(date_parts)
            except:
                # Fallback to current date if path doesn't contain date parts
                logger.warning(f"Could not extract date from path {path}, using current date")
                date = time.strftime('%Y-%m-%d')
            
            # Use original filename (without extension) as title part
            safe_title = path.stem.lower().replace(' ', '-')
            safe_title = ''.join(c for c in safe_title if c.isalnum() or c in '-_')
            return f"{date}-{safe_title}.md"
        except Exception as e:
            logger.error(f"Error generating post filename for {path}: {e}")
            raise

    def _sync_file(self, path: Path):
        """Sync a single file if it should be published."""
        try:
            post = frontmatter.load(str(path))
            
            # Check if we should publish or unpublish
            should_publish = self._should_publish(path)
            
            # Generate the Jekyll filename
            jekyll_filename = self._get_post_filename(path)
            target_path = self.posts_path / jekyll_filename
            
            # If unpublishing, remove the post if it exists
            if not should_publish:
                if target_path.exists():
                    try:
                        target_path.unlink()
                        logger.info(f"Unpublished: {jekyll_filename}")
                    except Exception as e:
                        logger.error(f"Failed to remove {target_path}: {e}")
                return

            # Clean up frontmatter
            try:
                clean_post = frontmatter.Post(content=post.content)
                
                # Use title from frontmatter or filename as fallback
                if 'title' in post:
                    clean_post['title'] = post['title']
                else:
                    clean_post['title'] = path.stem.replace('-', ' ').title()
                    logger.warning(f"No title in frontmatter for {path}, using filename")
                
                # Keep original time for update tracking
                if post.get('time'):
                    clean_post['time'] = post.get('time')
                
                # Handle tags - keep all except 'atomic'
                if post.get('tags'):
                    tags = post['tags']
                    if isinstance(tags, list):
                        filtered_tags = [tag for tag in tags if tag != 'atomic']
                        if filtered_tags:
                            clean_post['tags'] = filtered_tags
            except Exception as e:
                logger.error(f"Error processing frontmatter for {path}: {e}")
                raise
            
            # Update or create post
            try:
                if target_path.exists():
                    existing_post = frontmatter.load(str(target_path))
                    # Compare content instead of just timestamp
                    if clean_post.content.strip() != existing_post.content.strip():
                        with open(target_path, 'wb') as f:
                            frontmatter.dump(clean_post, f)
                        logger.info(f"Updated: {jekyll_filename}")
                else:
                    with open(target_path, 'wb') as f:
                        frontmatter.dump(clean_post, f)
                    logger.info(f"Published: {jekyll_filename}")
            except Exception as e:
                logger.error(f"Error writing to {target_path}: {e}")
                raise
                
        except Exception as e:
            logger.error(f"Error processing {path}: {e}")

    def sync_all(self):
        """Initial sync of all markdown files."""
        logger.info(f"Scanning directory: {self.atomics_path}")
        try:
            for path in self.atomics_path.rglob('*.md'):
                logger.debug(f"Found file: {path}")
                self._sync_file(path)
        except Exception as e:
            logger.error(f"Error during sync_all: {e}")
            raise

    def on_modified(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if self.atomics_path in path.parents:
            logger.info(f"File modified: {path}")
            self._sync_file(path)

    def on_created(self, event):
        self.on_modified(event)

def main():
    parser = argparse.ArgumentParser(description='Sync Obsidian vault with Jekyll blog posts')
    parser.add_argument('--watch', '-w', action='store_true', help='Watch for changes after initial sync')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    blog_path = Path(__file__).parent.parent.resolve()
    
    try:
        handler = ObsidianHandler(blog_path)
    except ValueError as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    
    # Initial sync
    logger.info("Performing initial sync...")
    try:
        handler.sync_all()
    except Exception as e:
        logger.error(f"Initial sync failed: {e}")
        sys.exit(1)
    
    if args.watch:
        # Watch for changes
        try:
            observer = Observer()
            observer.schedule(handler, str(handler.atomics_path), recursive=True)
            observer.start()

            logger.info(f"Watching for changes in {handler.atomics_path}...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
                logger.info("\nStopping file watcher...")
            observer.join()
        except Exception as e:
            logger.error(f"Error in file watcher: {e}")
            sys.exit(1)
    else:
        logger.info("One-time sync complete. Use --watch to monitor for changes.")

if __name__ == '__main__':
    main()
