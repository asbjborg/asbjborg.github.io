import os
import re
import frontmatter
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

def is_jekyll_friendly(filename: str) -> bool:
    """Check if a filename is Jekyll-friendly"""
    # Only allow: lowercase letters, numbers, dashes, underscores
    # Note: We don't allow dots in filenames (except extension)
    name, ext = os.path.splitext(filename)
    return bool(re.match(r'^[a-z0-9-_]+$', name))

def make_jekyll_friendly(filename: str) -> str:
    """Convert a filename to be Jekyll-friendly"""
    name, ext = os.path.splitext(filename)
    # Convert to lowercase
    name = name.lower()
    # Replace spaces and other characters with dashes
    name = re.sub(r'[^a-z0-9-_]', '-', name)
    # Replace multiple dashes with single dash
    name = re.sub(r'-+', '-', name)
    # Remove leading/trailing dashes
    name = name.strip('-')
    return f"{name}{ext}"

def extract_date_from_path(file_path: Path) -> str:
    """Extract date from Obsidian path structure (YYYY/MM/DD)"""
    try:
        # Path format: .../YYYY/MM/DD/filename.md
        parts = list(file_path.parts)
        idx = len(parts) - 2  # Start from parent dir
        day = parts[idx]
        month = parts[idx-1]
        year = parts[idx-2]
        # Validate date parts
        date = datetime(int(year), int(month), int(day))
        return f"{year}-{month:0>2}-{day:0>2}"
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid date structure in path: {file_path}")

def normalize_filenames(vault_root: str, debug: bool = False, dry_run: bool = False) -> None:
    """Normalize markdown filenames in Obsidian vault"""
    vault_path = Path(vault_root)
    atomics_dir = vault_path / "atomics"
    
    if debug:
        if dry_run:
            print(f"\nDRY RUN - No files will be modified")
        print(f"\nScanning for published posts in: {atomics_dir}")
    
    # Track all renames for consistent updates
    renames: Dict[str, str] = {}
    
    # First pass: collect all files that need renaming
    for md_file in atomics_dir.rglob("*.md"):
        try:
            post = frontmatter.load(md_file)
            if post.get('status') != 'published':
                continue
                
            if debug:
                print(f"\nChecking post: {md_file.relative_to(vault_path)}")
            
            # Get the date from the path
            try:
                date_prefix = extract_date_from_path(md_file)
            except ValueError as e:
                if debug:
                    print(f"  Warning: {str(e)}")
                continue
            
            # Create Jekyll-friendly filename
            current_name = md_file.name
            jekyll_name = make_jekyll_friendly(current_name)
            
            # Only rename if needed
            if not is_jekyll_friendly(current_name):
                new_path = md_file.parent / jekyll_name
                renames[str(md_file)] = str(new_path)
                if debug:
                    print(f"  Will rename: {current_name} -> {jekyll_name}")
                    print(f"  Jekyll path would be: {date_prefix}-{jekyll_name}")
            
        except Exception as e:
            if debug:
                print(f"Error processing {md_file}: {str(e)}")
            continue
    
    if not renames:
        if debug:
            print("No files need renaming.")
        return
    
    if debug:
        print(f"\nFound {len(renames)} files to rename:")
        for old, new in renames.items():
            print(f"  {Path(old).name} -> {Path(new).name}")
    
    # Finally, rename the files
    if not dry_run:
        for old_path, new_path in renames.items():
            try:
                Path(old_path).rename(new_path)
                if debug:
                    print(f"Renamed: {Path(old_path).name} -> {Path(new_path).name}")
            except Exception as e:
                if debug:
                    print(f"Error renaming {old_path}: {str(e)}")
    elif debug:
        print("\nDry run completed - no files were modified")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Normalize markdown filenames in Obsidian vault')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be renamed without making changes')
    args = parser.parse_args()
    
    vault_root = os.getenv('SYNC_VAULT_ROOT')
    debug = os.getenv('SYNC_DEBUG', 'false').lower() == 'true' or args.debug
    
    if not vault_root:
        print("Error: SYNC_VAULT_ROOT must be set")
        exit(1)
    
    normalize_filenames(vault_root, debug=debug, dry_run=args.dry_run) 