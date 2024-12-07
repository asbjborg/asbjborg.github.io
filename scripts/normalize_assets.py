import os
import re
import argparse
import frontmatter
from pathlib import Path
from typing import List, Tuple, Dict

def is_jekyll_friendly(filename: str) -> bool:
    """Check if a filename is Jekyll-friendly"""
    # Only allow: lowercase letters, numbers, dashes, underscores, dots
    return bool(re.match(r'^[a-z0-9-_.]+$', filename))

def make_jekyll_friendly(filename: str) -> str:
    """Convert a filename to be Jekyll-friendly"""
    # Convert to lowercase
    name = filename.lower()
    # Replace spaces and other characters with dashes
    name = re.sub(r'[^a-z0-9-_.]', '-', name)
    # Replace multiple dashes with single dash
    name = re.sub(r'-+', '-', name)
    # Remove leading/trailing dashes
    name = name.strip('-')
    return name

def extract_image_references(post_path: Path) -> Tuple[List[str], List[str]]:
    """Extract image references from post frontmatter and content"""
    post = frontmatter.load(post_path)
    frontmatter_refs = []
    content_refs = []
    
    # Check frontmatter image field
    if 'image' in post:
        image_ref = post['image']
        if '[[' in image_ref:
            frontmatter_refs.append(image_ref)
    
    # Find all image references in content
    content = post.content
    # Match full wikilinks including the !
    content_refs.extend(re.findall(r'(!\[\[.*?\]\])', content))
    
    return frontmatter_refs, content_refs

def get_image_path(image_ref: str) -> str:
    """Extract image path from wikilink"""
    # Handle both frontmatter and content references
    match = re.match(r'(?:\!?)?\[\[(.*?)\]\]', image_ref)
    if not match:
        raise ValueError(f"Invalid wikilink format: {image_ref}")
    return match.group(1)

def normalize_assets(vault_root: str, debug: bool = False, dry_run: bool = False) -> None:
    """Normalize asset names in Obsidian vault"""
    vault_path = Path(vault_root)
    atomics_dir = vault_path / "atomics"
    
    if debug:
        if dry_run:
            print("\nDRY RUN - No files will be modified\n")
        print(f"Scanning for published posts in: {atomics_dir}")
    
    # Track all renames for consistent updates
    renames: Dict[str, str] = {}
    
    # First pass: collect all assets that need renaming
    for md_file in atomics_dir.rglob("*.md"):
        try:
            post = frontmatter.load(md_file)
            if post.get('status') != 'published':
                continue
                
            if debug:
                print(f"\nChecking post: {md_file.relative_to(vault_path)}")
            
            # Get all image references
            frontmatter_refs, content_refs = extract_image_references(md_file)
            
            # Check each referenced image
            for ref in frontmatter_refs + content_refs:
                try:
                    image_path = get_image_path(ref)
                    image_file = vault_path / image_path
                    
                    if not image_file.exists():
                        if debug:
                            print(f"  Warning: Image not found: {image_path}")
                        continue
                    
                    if not is_jekyll_friendly(image_file.name):
                        new_name = make_jekyll_friendly(image_file.name)
                        renames[str(image_file)] = str(image_file.parent / new_name)
                        if debug:
                            print(f"  Will rename: {image_file.name} -> {new_name}")
                except Exception as e:
                    if debug:
                        print(f"  Error processing reference {ref}: {str(e)}")
                    continue
        except Exception as e:
            if debug:
                print(f"Error processing {md_file}: {str(e)}")
            continue
    
    if not renames:
        if debug:
            print("No assets need renaming.")
        return
    
    if debug:
        print(f"\nFound {len(renames)} assets to rename:")
        for old, new in renames.items():
            print(f"  {Path(old).name} -> {Path(new).name}")
    
    if dry_run:
        return
    
    # Second pass: update references in posts
    for md_file in atomics_dir.rglob("*.md"):
        try:
            post = frontmatter.load(md_file)
            if post.get('status') != 'published':
                continue
            
            content = post.content
            modified = False
            
            # Update frontmatter image reference
            if 'image' in post:
                image_ref = post['image'].strip('"')
                if '[[' in image_ref:
                    image_path = get_image_path(image_ref)
                    image_file = str(atomics_dir / Path(image_path))
                    if image_file in renames:
                        new_path = f'"[[{Path(renames[image_file]).relative_to(vault_path)}]]"'
                        post['image'] = new_path
                        modified = True
            
            # Update content references
            for old_path, new_path in renames.items():
                old_rel = str(Path(old_path).relative_to(vault_path))
                new_rel = str(Path(new_path).relative_to(vault_path))
                content = content.replace(f'![[{old_rel}]]', f'![[{new_rel}]]')
            
            if content != post.content:
                modified = True
                post.content = content
            
            # Save changes if needed
            if modified:
                with open(md_file, 'w') as f:
                    f.write(frontmatter.dumps(post))
                if debug:
                    print(f"Updated references in: {md_file.relative_to(vault_path)}")
        except Exception as e:
            if debug:
                print(f"Error processing {md_file}: {str(e)}")
            continue
    
    # Finally, rename the files
    for old_path, new_path in renames.items():
        try:
            Path(old_path).rename(new_path)
            if debug:
                print(f"Renamed: {Path(old_path).name} -> {Path(new_path).name}")
        except Exception as e:
            if debug:
                print(f"Error renaming {old_path}: {str(e)}")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Normalize asset filenames in Obsidian vault')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be normalized without making changes')
    args = parser.parse_args()
    
    # Get environment variables
    vault_root = os.getenv('SYNC_VAULT_ROOT')
    debug = os.getenv('SYNC_DEBUG', 'false').lower() == 'true' or args.debug
    
    if not vault_root:
        print("Error: SYNC_VAULT_ROOT must be set")
        exit(1)
    
    normalize_assets(vault_root, debug=debug, dry_run=args.dry_run) 