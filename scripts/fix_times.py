#!/usr/bin/env python3

import os
import re
import argparse
import frontmatter
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

def seconds_to_time_str(seconds: int) -> str:
    """Convert seconds since midnight to HH:mm:ss"""
    time = timedelta(seconds=seconds)
    return str(time).zfill(8)  # Pad with zeros if needed

def fix_time(time_value: any) -> Optional[str]:
    """Fix time value to proper format"""
    if isinstance(time_value, int):
        return seconds_to_time_str(time_value)
    elif isinstance(time_value, str):
        # Check if it's already in the correct format
        if re.match(r'^\d{2}:\d{2}:\d{2}$', time_value):
            return time_value
        # Try to convert integer string
        try:
            seconds = int(time_value)
            return seconds_to_time_str(seconds)
        except ValueError:
            pass
    return None

def fix_frontmatter(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Fix frontmatter issues"""
    changes = []
    
    # Fix time property
    if 'time' in metadata:
        time = metadata['time']
        fixed_time = fix_time(time)
        if fixed_time and fixed_time != time:
            metadata['time'] = fixed_time
            changes.append(f"time: {time} -> {fixed_time}")
    
    # Fix synced property
    if 'synced' in metadata:
        status = metadata.get('status')
        if status != 'published':
            del metadata['synced']
            changes.append("removed incorrect synced property")
    
    return metadata, changes

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Fix integer timestamps and incorrect synced properties')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    args = parser.parse_args()
    
    # Get environment variables
    vault_root = os.getenv('SYNC_VAULT_ROOT')
    atomics_path = os.getenv('SYNC_VAULT_ATOMICS', 'atomics')
    debug = os.getenv('SYNC_DEBUG', 'false').lower() == 'true'
    
    if not vault_root:
        print("Error: SYNC_VAULT_ROOT must be set")
        return
    
    vault_root = Path(vault_root)
    atomics_dir = vault_root / atomics_path
    
    # Track stats
    total_files = 0
    fixed_files = 0
    skipped_files = 0
    error_files = 0
    
    if args.dry_run:
        print("DRY RUN MODE - No files will be modified")
    
    print(f"\nScanning files in: {atomics_dir}")
    
    # Process each markdown file
    for md_file in atomics_dir.rglob("*.md"):
        total_files += 1
        try:
            # Read frontmatter
            post = frontmatter.load(md_file)
            
            # Fix frontmatter
            fixed_metadata, changes = fix_frontmatter(post.metadata)
            
            if not changes:
                if debug:
                    print(f"Skipping {md_file.relative_to(vault_root)}: No changes needed")
                skipped_files += 1
                continue
            
            # Update frontmatter
            post.metadata = fixed_metadata
            
            # Write back to file
            if not args.dry_run:
                with open(md_file, 'w', encoding='utf-8') as f:
                    yaml_lines = []
                    yaml_lines.append('---')
                    for key, value in post.metadata.items():
                        if key == 'synced':
                            yaml_lines.append(f'synced: "{value}"')
                        else:
                            yaml_lines.append(f'{key}: {value}')
                    yaml_lines.append('---')
                    yaml_lines.append('')
                    yaml_lines.append(post.content)
                    f.write('\n'.join(yaml_lines))
            
            fixed_files += 1
            print(f"{'WOULD fix' if args.dry_run else 'Fixed'} {md_file.relative_to(vault_root)}:")
            for change in changes:
                print(f"  - {change}")
            
        except Exception as e:
            error_files += 1
            print(f"Error processing {md_file.relative_to(vault_root)}: {str(e)}")
    
    # Print summary
    print("\nSummary:")
    print(f"  Total files: {total_files}")
    print(f"  {'Would fix' if args.dry_run else 'Fixed'} files: {fixed_files}")
    print(f"  Skipped files: {skipped_files}")
    print(f"  Error files: {error_files}")
    if args.dry_run:
        print("\nDry run completed - no files were modified")

if __name__ == '__main__':
    main() 