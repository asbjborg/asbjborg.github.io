#!/usr/bin/env python3

import os
import re
import sys
from pathlib import Path

def validate_image_paths():
    """Validate that all image paths in posts exist and follow naming conventions."""
    posts_dir = "_posts"
    assets_dir = "assets/img/posts"
    errors = []

    # Check if directories exist
    if not os.path.exists(posts_dir):
        print(f"Posts directory '{posts_dir}' not found")
        return 1
    if not os.path.exists(assets_dir):
        print(f"Assets directory '{assets_dir}' not found")
        return 1

    # Get list of available images
    available_images = set(f.name for f in Path(assets_dir).glob("*") if f.is_file())

    # Check each post
    for post_file in Path(posts_dir).glob("*.md"):
        with open(post_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Check featured image in frontmatter
            featured_match = re.search(r'featured_image:\s*([^\n]+)', content)
            if featured_match:
                image = featured_match.group(1).strip().strip('"\'')
                if not image.startswith('/'):
                    image = image.split('/')[-1]  # Get filename if it's a relative path
                else:
                    image = image.split('/')[-1]  # Get filename from absolute path
                if image not in available_images:
                    errors.append(f"{post_file.name}: Featured image '{image}' not found")

            # Check inline images
            inline_images = re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', content)
            for match in inline_images:
                image_path = match.group(2)
                if 'assets/img/posts' in image_path:
                    image = image_path.split('/')[-1]
                    if image not in available_images:
                        errors.append(f"{post_file.name}: Inline image '{image}' not found")

    # Report errors
    if errors:
        print("Image validation errors found:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("All image paths are valid")
    return 0

if __name__ == "__main__":
    sys.exit(validate_image_paths()) 