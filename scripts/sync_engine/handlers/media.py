"""
Media handler for processing images and attachments
"""

import os
import re
import shutil
import logging
import hashlib
from pathlib import Path
from typing import Optional, Set, Dict, List
from PIL import Image, UnidentifiedImageError
from ..core.exceptions import InvalidImageError, UnsupportedFormatError, ImageProcessingError

logger = logging.getLogger(__name__)

class MediaHandler:
    """Handles media file processing and synchronization"""
    
    # Supported image formats
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    
    def __init__(self, vault_root: Path, assets_path: Path):
        """
        Initialize MediaHandler
        
        Args:
            vault_root: Root path of Obsidian vault
            assets_path: Path to Jekyll assets
        """
        self.vault_root = vault_root
        self.assets_path = assets_path
        self.assets_path.mkdir(parents=True, exist_ok=True)
        
        # Track processed files to avoid duplicates
        self.processed_files: Set[Path] = set()
        # Map original paths to new paths
        self.path_mapping: Dict[str, str] = {}
        
        # Supported image formats
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    
    def validate_image(self, image_path: Path) -> None:
        """Validate image file before processing"""
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
            
        if image_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise UnsupportedFormatError(f"Unsupported image format: {image_path.suffix}")
            
        if image_path.stat().st_size == 0:
            raise InvalidImageError(f"Empty image file: {image_path}")
            
        try:
            # Try to open and verify it's a valid image
            with Image.open(image_path) as img:
                img.verify()
        except (UnidentifiedImageError, OSError) as e:
            raise InvalidImageError(f"Invalid or corrupted image: {image_path}") from e
    
    def process_image(self, image_path: Path, target_path: Path) -> Optional[Path]:
        """
        Process and optimize image for web
        
        Args:
            image_path: Source image path
            target_path: Target path for processed image
            
        Returns:
            Path to processed image or None if failed
        """
        try:
            # Validate image first
            self.validate_image(image_path)
            
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large
                max_width = 1200
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_size = (max_width, int(img.height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Save with optimization
                target_path.parent.mkdir(parents=True, exist_ok=True)
                if target_path.suffix.lower() in {'.jpg', '.jpeg'}:
                    img.save(target_path, 'JPEG', quality=85, optimize=True)
                elif target_path.suffix.lower() == '.png':
                    img.save(target_path, 'PNG', optimize=True)
                elif target_path.suffix.lower() == '.webp':
                    img.save(target_path, 'WEBP', quality=85)
                else:
                    img.save(target_path)
                
                logger.info(f"Processed and optimized image: {target_path}")
                return target_path
                
        except (InvalidImageError, UnsupportedFormatError, FileNotFoundError) as e:
            logger.error(str(e))
            raise
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            raise ImageProcessingError(f"Failed to process image: {e}") from e
    
    def get_media_references(self, content: str) -> Set[str]:
        """Extract all media references from content"""
        references = set()
        
        # Match Obsidian image syntax only: ![[path/to/image.png]]
        # Exclude:
        # - Regular links: [[not an image]]
        # - Regular markdown: ![alt](image.png)
        # - Malformed wikilinks: ![[missing bracket, ![[], etc.
        media_pattern = r'!\[\[([^[\]]+?)\]\]'
        
        for match in re.finditer(media_pattern, content):
            filepath = match.group(1)
            if filepath and filepath.strip():  # Skip empty or whitespace-only
                # Clean and validate path
                clean_path = filepath.strip()
                if (
                    not clean_path.startswith('/')  # No absolute paths
                    and not clean_path.endswith('/')  # No trailing slashes
                    and not clean_path.startswith('.')  # No relative paths
                    and not clean_path.startswith('..')  # No parent paths
                    and '[' not in clean_path  # No nested brackets
                    and ']' not in clean_path  # No nested brackets
                ):
                    references.add(clean_path)
        
        return references
    
    def resolve_media_path(self, reference: str) -> Optional[Path]:
        """
        Resolve media reference to actual file path
        
        Handles:
        - Absolute vault paths: [[atomics/2024/12/03/image.png]]
        - Relative paths: [[image.png]]
        - Sanitized paths: [[my-image.png]]
        """
        try:
            # Try absolute vault path
            abs_path = self.vault_root / reference
            if abs_path.exists():
                return abs_path
            
            # Try just filename in current post's directory
            filename = Path(reference).name
            # TODO: Get post's directory when needed
            
            # Try normalized path
            normalized = reference.replace(' ', '-').lower()
            normalized_path = self.vault_root / normalized
            if normalized_path.exists():
                return normalized_path
            
            logger.warning(f"Could not resolve media reference: {reference}")
            return None
            
        except Exception as e:
            logger.error(f"Error resolving media path: {e}")
            return None
    
    def get_jekyll_media_path(self, original_path: Path) -> Path:
        """
        Generate Jekyll-compatible media path
        
        Args:
            original_path: Original media file path
            
        Returns:
            Jekyll-compatible path
        """
        try:
            # Generate content hash for uniqueness
            file_hash = hashlib.md5(original_path.read_bytes()).hexdigest()[:8]
            
            # Get relative path from vault root
            rel_path = original_path.relative_to(self.vault_root)
            
            # Clean filename parts
            clean_parts = []
            for part in rel_path.parts:
                # Skip common parent directories
                if part in {'atomics', 'attachments'}:
                    continue
                # Clean part name
                clean_part = part.lower().replace(' ', '-')
                clean_part = ''.join(c for c in clean_part if c.isalnum() or c in '-_.')
                clean_parts.append(clean_part)
            
            # Combine parts with hash
            stem = '-'.join(clean_parts[:-1]) if len(clean_parts) > 1 else ''
            name = clean_parts[-1]
            if stem:
                new_name = f"{stem}-{name}"
            else:
                new_name = name
            
            # Add hash before extension
            base, ext = os.path.splitext(new_name)
            new_filename = f"{base}-{file_hash}{ext}"
            
            return self.assets_path / new_filename
            
        except Exception as e:
            logger.error(f"Error generating Jekyll path: {e}")
            raise
    
    def process_media_file(self, file_path: Path) -> Optional[str]:
        """
        Process a media file and move to Jekyll assets
        
        Args:
            file_path: Path to media file
            
        Returns:
            Jekyll path to media file or None if failed
        """
        try:
            if file_path in self.processed_files:
                return self.path_mapping.get(str(file_path))
            
            target_path = self.get_jekyll_media_path(file_path)
            
            # Process images, copy other files directly
            if file_path.suffix.lower() in self.image_extensions:
                self.process_image(file_path, target_path)
            else:
                shutil.copy2(file_path, target_path)
            
            # Track processed file
            self.processed_files.add(file_path)
            jekyll_path = f"/assets/img/posts/{target_path.name}"
            self.path_mapping[str(file_path)] = jekyll_path
            
            return jekyll_path
            
        except Exception as e:
            logger.error(f"Error processing media file {file_path}: {e}")
            return None
    
    def process_content(self, content: str) -> str:
        """
        Process content and handle all media references
        
        Args:
            content: Post content to process
            
        Returns:
            Processed content with updated media references
        """
        try:
            # Get all media references
            references = self.get_media_references(content)
            
            # Process each reference
            for ref in references:
                media_path = self.resolve_media_path(ref)
                if not media_path:
                    continue
                
                # Process media file
                jekyll_path = self.process_media_file(media_path)
                if not jekyll_path:
                    continue
                
                # Replace in content
                # Handle both ![[ref]] and [[ref]] patterns
                content = content.replace(f"![[{ref}]]", f"![{ref}]({jekyll_path})")
                content = content.replace(f"[[{ref}]]", f"[{ref}]({jekyll_path})")
            
            return content
            
        except Exception as e:
            logger.error(f"Error processing content for media: {e}")
            return content
    
    def cleanup_unused_assets(self, used_paths: Set[str]):
        """
        Remove unused media files from Jekyll assets
        
        Args:
            used_paths: Set of media paths currently in use
        """
        try:
            for asset in self.assets_path.iterdir():
                if asset.is_file():
                    jekyll_path = f"/assets/img/posts/{asset.name}"
                    if jekyll_path not in used_paths:
                        asset.unlink()
                        logger.info(f"Removed unused asset: {asset}")
        except Exception as e:
            logger.error(f"Error during assets cleanup: {e}")
    
    def sync_back_to_obsidian(self, jekyll_path: str) -> Optional[Path]:
        """
        Sync media file back to Obsidian if modified in Jekyll
        
        Args:
            jekyll_path: Jekyll path to media file
            
        Returns:
            Path in Obsidian or None if failed
        """
        try:
            # Convert Jekyll path to actual path
            asset_name = Path(jekyll_path).name
            asset_path = self.assets_path / asset_name
            
            if not asset_path.exists():
                return None
            
            # Find original path from mapping
            for orig_path, jekyll in self.path_mapping.items():
                if jekyll == jekyll_path:
                    obsidian_path = Path(orig_path)
                    if asset_path.stat().st_mtime > obsidian_path.stat().st_mtime:
                        shutil.copy2(asset_path, obsidian_path)
                        logger.info(f"Synced media back to Obsidian: {obsidian_path}")
                    return obsidian_path
            
            return None
            
        except Exception as e:
            logger.error(f"Error syncing media back to Obsidian: {e}")
            return None 