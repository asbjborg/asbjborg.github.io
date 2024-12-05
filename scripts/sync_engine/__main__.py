"""Main entry point for sync engine"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional

from .core.engine import SyncEngineV2
from .core.types import SyncDirection
from .core.exceptions import SyncEngineError

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

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Obsidian to Jekyll sync engine')
    
    parser.add_argument(
        '--vault',
        type=str,
        help='Path to Obsidian vault'
    )
    parser.add_argument(
        '--jekyll',
        type=str,
        help='Path to Jekyll site'
    )
    parser.add_argument(
        '--vault-posts',
        type=str,
        default='_posts',
        help='Path to posts in vault (relative to vault root)'
    )
    parser.add_argument(
        '--vault-media',
        type=str,
        default='atomics',
        help='Path to media in vault (relative to vault root)'
    )
    parser.add_argument(
        '--jekyll-posts',
        type=str,
        default='_posts',
        help='Path to posts in Jekyll (relative to Jekyll root)'
    )
    parser.add_argument(
        '--jekyll-assets',
        type=str,
        default='assets/img/posts',
        help='Path to assets in Jekyll (relative to Jekyll root)'
    )
    parser.add_argument(
        '--direction',
        type=str,
        choices=['obsidian', 'jekyll', 'both'],
        default='both',
        help='Sync direction (default: both)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    return parser.parse_args()

def main():
    """Main entry point"""
    try:
        args = parse_args()
        
        # Determine sync direction
        direction = None
        if args.direction == 'obsidian':
            direction = SyncDirection.OBSIDIAN_TO_JEKYLL
        elif args.direction == 'jekyll':
            direction = SyncDirection.JEKYLL_TO_OBSIDIAN
        
        # Initialize engine
        engine = SyncEngineV2(
            vault_root=Path(args.vault) if args.vault else None,
            jekyll_root=Path(args.jekyll) if args.jekyll else None,
            vault_posts=args.vault_posts,
            vault_media=args.vault_media,
            jekyll_posts=args.jekyll_posts,
            jekyll_assets=args.jekyll_assets
        )
        
        # Detect changes
        changes = engine.detect_changes()
        
        if args.dry_run:
            # Just show what would be done
            if not changes:
                print("No changes detected")
                return 0
            
            print("\nChanges that would be made:")
            for change in changes:
                print(f"\n{change.operation.name}:")
                print(f"  From: {change.source_path}")
                print(f"  To: {change.target_path}")
                if change.status:
                    print(f"  Status: {change.status.name}")
                print(f"  Direction: {change.sync_direction.name}")
        else:
            # Perform sync
            changes = engine.sync(direction)
            
            if not changes:
                print("No changes made")
                return 0
            
            print("\nChanges made:")
            for change in changes:
                print(f"\n{change.operation.name}:")
                print(f"  From: {change.source_path}")
                print(f"  To: {change.target_path}")
                if change.status:
                    print(f"  Status: {change.status.name}")
                print(f"  Direction: {change.sync_direction.name}")
        
        return 0
        
    except SyncEngineError as e:
        logger.error(str(e))
        return 1
    except Exception as e:
        logger.exception("Unexpected error")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 