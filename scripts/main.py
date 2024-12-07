import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
from sync.sync import SyncEngine
from utils.backup import BackupHandler

def main():
    # Load environment variables from .env
    load_dotenv()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Sync Obsidian posts with Jekyll')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    args = parser.parse_args()

    # Get environment variables
    vault_root = os.getenv('SYNC_VAULT_ROOT')
    jekyll_root = os.getenv('SYNC_JEKYLL_ROOT')
    debug = os.getenv('SYNC_DEBUG', 'false').lower() == 'true'

    if not vault_root or not jekyll_root:
        print("Error: SYNC_VAULT_ROOT and SYNC_JEKYLL_ROOT must be set")
        return

    # Create backup handler
    backup = BackupHandler(vault_root, jekyll_root, debug=debug, dry_run=args.dry_run)

    # Create sync engine
    engine = SyncEngine(vault_root, jekyll_root, debug=debug, dry_run=args.dry_run)

    # Create backups first
    backup.backup_all()

    # Run sync
    engine.sync()

if __name__ == '__main__':
    main()
