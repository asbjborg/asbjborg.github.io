#!/usr/bin/env python3

import os
import re
import sys
from pathlib import Path

def validate_image_paths(posts_dir="_posts"):
    """Validate image paths in markdown files for Jekyll compatibility."""
    errors = []
    image_pattern = r'!\[(.*?)\]\((.*?)\)'
    
    for post_file in Path(posts_dir).glob("*.md"):
        with open(post_file, 'r') as f:
            content = f.read()
            matches = re.finditer(image_pattern, content)
            
            for match in matches:
                image_path = match.group(2)
                if ' ' in image_path:
                    errors.append(f"Error in {post_file.name}: Image path contains spaces: {image_path}")
                if not image_path.startswith('/'):
                    errors.append(f"Error in {post_file.name}: Image path should start with /: {image_path}")
                
                # Check if referenced image exists
                if image_path.startswith('/'):
                    full_path = Path(os.getcwd()) / image_path.lstrip('/')
                    if not full_path.exists():
                        errors.append(f"Error in {post_file.name}: Image not found: {image_path}")
    
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    
    print("All image paths are valid!")
    sys.exit(0)

if __name__ == "__main__":
    validate_image_paths() 