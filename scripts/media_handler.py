#!/usr/bin/env python3

import os
import shutil
import logging
from pathlib import Path
from PIL import Image
import hashlib
import re

logger = logging.getLogger(__name__)

class MediaHandler:
    def __init__(self, attachments_path: Path, assets_path: Path):
        """Initialize MediaHandler with paths."""
        self.attachments_path = attachments_path
        self.assets_path = assets_path
        self.assets_path.mkdir(parents=True, exist_ok=True)

    def process_image(self, image_path: Path, target_path: Path) -> Path:
        """Process and optimize image for web."""
        try:
            with Image.open(image_path) as img:
                # Convert RGBA to RGB if necessary
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                
                # Resize if too large (max 1200px width)
                max_width = 1200
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_size = (max_width, int(img.height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Save with optimization
                img.save(target_path, 'JPEG', quality=85, optimize=True)
                logger.info(f"Processed and optimized image: {target_path}")
                return target_path
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            # Fall back to copying the original file
            shutil.copy2(image_path, target_path)
            return target_path

    def handle_media_file(self, file_path: Path) -> str:
        """Process and copy media file to assets directory, return new path."""
        try:
            # Generate a unique filename based on content hash
            file_hash = hashlib.md5(file_path.read_bytes()).hexdigest()[:8]
            new_filename = f"{file_path.stem}-{file_hash}{file_path.suffix.lower()}"
            target_path = self.assets_path / new_filename
            
            # Process images, copy other files directly
            if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                self.process_image(file_path, target_path)
            else:
                shutil.copy2(file_path, target_path)
            
            # Return the path relative to the Jekyll root
            return f"/assets/img/posts/{new_filename}"
        except Exception as e:
            logger.error(f"Error handling media file {file_path}: {e}")
            return None

    def process_content(self, content: str) -> str:
        """Process content to handle media files and update paths."""
        try:
            # Match Obsidian image/media syntax with optional path: ![[path/to/filename]] or [[path/to/filename]]
            media_pattern = r'!\[\[(.*?)\]\]|\[\[(.*?)\]\]'
            
            def replace_media(match):
                filepath = match.group(1) or match.group(2)
                if not filepath:
                    return match.group(0)
                
                # Extract just the filename from the path
                filename = os.path.basename(filepath)
                
                # Check if it's a media file
                media_path = self.attachments_path / filename
                if not media_path.exists():
                    # Try with the full path
                    media_path = self.attachments_path / filepath
                    if not media_path.exists():
                        return match.group(0)
                
                # Process media file and get new path
                new_path = self.handle_media_file(media_path)
                if not new_path:
                    return match.group(0)
                
                # Return markdown image syntax
                return f"![{filename}]({new_path})"
            
            return re.sub(media_pattern, replace_media, content)
        except Exception as e:
            logger.error(f"Error processing content for media: {e}")
            return content 