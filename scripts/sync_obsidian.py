#!/usr/bin/env python3

import os
import shutil
import sys
import time
import argparse
import frontmatter
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ObsidianHandler(FileSystemEventHandler):
    def __init__(self, blog_path: Path):
        self.vault_path = Path(os.getenv('VAULT_PATH')).expanduser().resolve()
        self.atomics_path = self.vault_path / os.getenv('VAULT_ATOMICS_PATH', 'atomics')
        self.blog_path = blog_path
        self.posts_path = blog_path / '_posts'
        self.posts_path.mkdir(exist_ok=True)

        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {self.vault_path}")
        if not self.atomics_path.exists():
            raise ValueError(f"Atomics path does not exist: {self.atomics_path}")

    def _should_publish(self, path: Path) -> bool:
        """Check if a file should be published based on frontmatter."""
        if not path.suffix.lower() in ['.md', '.markdown']:
            print(f"Skipping non-markdown file: {path}")
            return False
        
        try:
            post = frontmatter.load(str(path))
            should_publish = post.get('published', False) is True
            print(f"Checking {path}: published = {should_publish}")
            return should_publish
        except Exception as e:
            print(f"Error reading frontmatter from {path}: {e}")
            return False

    def _get_post_filename(self, path: Path) -> str:
        """Generate Jekyll-compatible filename from Obsidian file path."""
        # Extract date from path (YYYY/MM/DD)
        try:
            date_parts = [path.parts[-4], path.parts[-3].zfill(2), path.parts[-2].zfill(2)]
            date = '-'.join(date_parts)
        except:
            # Fallback to current date if path doesn't contain date parts
            date = time.strftime('%Y-%m-%d')
        
        # Use original filename (without extension) as title part
        safe_title = path.stem.lower().replace(' ', '-')
        safe_title = ''.join(c for c in safe_title if c.isalnum() or c in '-_')
        return f"{date}-{safe_title}.md"

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
                    print(f"Removing {target_path}")
                    target_path.unlink()
                    print(f"Unpublished: {jekyll_filename}")
                return

            # Clean up frontmatter
            clean_post = frontmatter.Post(content=post.content)
            
            # Set title from H1 if present, otherwise use filename
            content_lines = post.content.split('\n')
            title = path.stem  # Default to filename
            for line in content_lines:
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
            clean_post['title'] = title
            
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
            
            # Update or create post
            if target_path.exists():
                existing_post = frontmatter.load(str(target_path))
                # Only update if the new version is newer
                if post.get('time', 0) > existing_post.get('time', 0):
                    with open(target_path, 'wb') as f:
                        frontmatter.dump(clean_post, f)
                    print(f"Updated: {jekyll_filename}")
            else:
                with open(target_path, 'wb') as f:
                    frontmatter.dump(clean_post, f)
                print(f"Published: {jekyll_filename}")
        except Exception as e:
            print(f"Error processing {path}: {e}")

    def sync_all(self):
        """Initial sync of all markdown files."""
        print(f"Scanning directory: {self.atomics_path}")
        for path in self.atomics_path.rglob('*.md'):
            print(f"Found file: {path}")
            self._sync_file(path)

    def on_modified(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if self.atomics_path in path.parents:
            self._sync_file(path)

    def on_created(self, event):
        self.on_modified(event)

def main():
    parser = argparse.ArgumentParser(description='Sync Obsidian vault with Jekyll blog posts')
    parser.add_argument('--watch', '-w', action='store_true', help='Watch for changes after initial sync')
    args = parser.parse_args()

    blog_path = Path(__file__).parent.parent.resolve()
    
    try:
        handler = ObsidianHandler(blog_path)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Initial sync
    print("Performing initial sync...")
    handler.sync_all()
    
    if args.watch:
        # Watch for changes
        observer = Observer()
        observer.schedule(handler, str(handler.atomics_path), recursive=True)
        observer.start()

        print(f"Watching for changes in {handler.atomics_path}...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\nStopping file watcher...")
        observer.join()
    else:
        print("One-time sync complete. Use --watch to monitor for changes.")

if __name__ == '__main__':
    main()
