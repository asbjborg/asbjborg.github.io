"""Media handler module"""

import os
import re
import logging
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Union
from PIL import Image, UnidentifiedImageError
from ..core.exceptions import InvalidImageError, UnsupportedFormatError, ImageProcessingError
from ..core.config import SyncConfig
from ..core.atomic import AtomicUtils
import gc
import time

logger = logging.getLogger(__name__)

class MediaError(Exception):
    """Media handling error"""
    pass

class UnsupportedFormatError(MediaError):
    """Unsupported image format error"""
    pass

class InvalidImageError(MediaError):
    """Invalid image error"""
    pass

class MediaHandler:
    """Handles media file processing and path management"""
    
    # Supported image formats
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    
    def __init__(self, config: Union[Dict, SyncConfig]):
        """
        Initialize media handler
        
        Args:
            config: Sync configuration (dict or SyncConfig)
        """
        # Convert dict to SyncConfig if needed
        if isinstance(config, dict):
            from ..core.config import ConfigManager
            self.config = ConfigManager.load_from_dict(config)
        else:
            self.config = config
            
        self.vault_root = Path(self.config.vault_root)
        self.jekyll_root = Path(self.config.jekyll_root)
        self.jekyll_assets = Path(self.config.jekyll_root) / self.config.jekyll_assets
        self.jekyll_assets.mkdir(parents=True, exist_ok=True)
        
        # Track processed files to avoid duplicates
        self.processed_files: Set[Path] = set()
        # Map original paths to new paths
        self.path_mapping: Dict[str, str] = {}
        
        # Supported image formats
        self.image_extensions = self.SUPPORTED_FORMATS
    
    def validate_image(self, image_path: Path) -> None:
        """Validate image file before processing"""
        from ..core.exceptions import InvalidImageError, UnsupportedFormatError
        
        logger.debug(f"Validating image: {image_path}")
        
        if not image_path.exists():
            logger.debug(f"Image not found: {image_path}")
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        if image_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            logger.debug(f"Unsupported format: {image_path.suffix}")
            raise UnsupportedFormatError(f"Unsupported image format: {image_path.suffix}")
        
        if image_path.stat().st_size == 0:
            logger.debug(f"Empty file: {image_path}")
            raise InvalidImageError(f"Empty image file: {image_path}")
        
        try:
            # Try to open and verify it's a valid image
            logger.debug(f"Attempting to open and verify: {image_path}")
            with Image.open(image_path) as img:
                img.verify()
                logger.debug(f"Image verified successfully: {image_path} (mode={img.mode}, size={img.size})")
        except (UnidentifiedImageError, OSError, ValueError, TypeError) as e:
            logger.error(f"Failed to validate image {image_path}: {e}")
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
            logger.debug(f"Processing image {image_path} -> {target_path}")
            
            # Validate image first
            self.validate_image(image_path)
            logger.debug(f"Image validation passed for {image_path}")
            
            # Use a context manager for better resource cleanup
            with Image.open(image_path) as img:
                logger.debug(f"Opened image: {image_path} (mode={img.mode}, size={img.size})")
                
                # Convert to RGB if needed
                if img.mode in ('RGBA', 'LA'):
                    logger.debug(f"Converting {img.mode} image to RGB with white background")
                    with Image.new('RGB', img.size, (255, 255, 255)) as background:
                        background.paste(img, mask=img.split()[-1])
                        img = background.copy()
                elif img.mode != 'RGB':
                    logger.debug(f"Converting {img.mode} image to RGB")
                    img = img.convert('RGB')
                
                # Resize if too large
                max_width = 1200
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_size = (max_width, int(img.height * ratio))
                    logger.debug(f"Resizing image from {img.size} to {new_size}")
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Save with optimization
                target_dir = target_path.parent
                target_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created target directory: {target_dir}")
                
                # Check directory permissions
                try:
                    test_file = target_dir / ".write_test"
                    test_file.touch()
                    test_file.unlink()
                    logger.debug(f"Directory is writable: {target_dir}")
                except Exception as e:
                    logger.error(f"Directory not writable: {target_dir} - {e}")
                    raise
                
                logger.debug(f"Saving image to {target_path}")
                
                try:
                    # Use a temporary file for atomic save
                    temp_path = target_path.with_suffix('.tmp')
                    
                    if target_path.suffix.lower() in {'.jpg', '.jpeg'}:
                        logger.debug("Saving as JPEG with optimization")
                        img.save(temp_path, 'JPEG', quality=85, optimize=True)
                    elif target_path.suffix.lower() == '.png':
                        logger.debug("Saving as PNG with optimization")
                        img.save(temp_path, 'PNG', optimize=True)
                    elif target_path.suffix.lower() == '.webp':
                        logger.debug("Saving as WebP")
                        img.save(temp_path, 'WEBP', quality=85)
                    else:
                        logger.debug(f"Saving with default format {target_path.suffix}")
                        img.save(temp_path)
                    
                    # Atomic move
                    temp_path.replace(target_path)
                    
                    # Verify file
                    if not target_path.exists():
                        raise IOError(f"File not created: {target_path}")
                    
                    logger.debug(f"Successfully saved image: {target_path} ({target_path.stat().st_size} bytes)")
                    return target_path
                    
                except Exception as e:
                    logger.error(f"Failed to save image {target_path}: {e}", exc_info=True)
                    if temp_path.exists():
                        temp_path.unlink()
                    raise
                
        except (InvalidImageError, UnsupportedFormatError, FileNotFoundError) as e:
            logger.error(str(e))
            raise
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}", exc_info=True)
            raise ImageProcessingError(f"Failed to process image: {e}") from e
        finally:
            # Force cleanup of any remaining image objects
            gc.collect()
    
    def get_media_references(self, content: str) -> Set[str]:
        """Extract media references from content"""
        references = set()
        
        # Match Obsidian image syntax: ![[path/to/image.png]]
        obsidian_pattern = r'!\[\[([^[\]]+?)\]\]'
        
        # Match Jekyll image syntax: ![alt](/assets/img/posts/image.png)
        jekyll_pattern = r'!\[.*?\]\(/assets/img/posts/([^)]+?)\)'
        
        # Find Obsidian references
        for match in re.finditer(obsidian_pattern, content):
            filepath = match.group(1)
            if filepath and filepath.strip():  # Skip empty or whitespace-only
                # Clean and validate path
                clean_path = filepath.strip()
                if (
                    not clean_path.startswith('/')  # No absolute paths
                    and not clean_path.startswith('.')  # No relative paths
                    and not clean_path.startswith('..')  # No parent paths
                    and '[' not in clean_path  # No nested brackets
                    and ']' not in clean_path  # No nested brackets
                ):
                    # Remove trailing slashes
                    while clean_path.endswith('/'):
                        clean_path = clean_path[:-1]
                    if clean_path:  # Only add if not empty after cleaning
                        references.add(clean_path)
        
        # Find Jekyll references
        for match in re.finditer(jekyll_pattern, content):
            filepath = match.group(1)
            if filepath and filepath.strip():  # Skip empty or whitespace-only
                references.add(filepath)
        
        return references
    
    def resolve_media_path(self, reference: str) -> Optional[Path]:
        """
        Resolve media reference to actual file path
        
        Handles:
        - Absolute vault paths: [[atomics/2024/12/03/image.png]]
        - Relative paths: [[image.png]]
        - Sanitized paths: [[my-image.png]]
        
        Raises:
            ValueError: If reference is invalid
            FileNotFoundError: If file doesn't exist
        """
        if not reference or not reference.strip():
            raise ValueError("Empty media reference")
            
        if (
            reference.startswith('/')  # No absolute paths
            or reference.startswith('.')  # No relative paths
            or reference.startswith('..')  # No parent paths
            or '[' in reference  # No nested brackets
            or ']' in reference  # No nested brackets
        ):
            raise ValueError(f"Invalid media reference format: {reference}")
        
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
            
            raise FileNotFoundError(f"Could not find media file: {reference}")
            
        except (ValueError, FileNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error resolving media path: {e}")
            raise ValueError(f"Invalid media reference: {reference}") from e
    
    def get_jekyll_media_path(self, original_path: Path) -> Path:
        """
        Generate Jekyll-compatible media path
        
        Args:
            original_path: Original media file path
            
        Returns:
            Jekyll-compatible path
            
        Example:
            atomics/2024/01/15/über.jpg -> assets/img/posts/uber.jpg
        """
        try:
            # Get relative path from vault root
            rel_path = original_path.relative_to(self.vault_root)
            
            # Get filename and clean it
            filename = rel_path.name
            base, ext = os.path.splitext(filename)
            
            # Convert to ASCII but preserve Unicode letters
            import unicodedata
            clean_base = unicodedata.normalize('NFKD', base)
            clean_base = ''.join(c for c in clean_base if not unicodedata.combining(c))
            
            # Replace spaces with hyphens and remove special characters
            clean_base = re.sub(r'[^\w\s-]', '', clean_base)
            clean_base = re.sub(r'[-\s]+', '-', clean_base).strip('-').lower()
            
            # Return Jekyll assets path
            return self.jekyll_assets / f"{clean_base}{ext}"
            
        except Exception as e:
            logger.error(f"Error generating Jekyll path for {original_path}: {e}")
            raise ValueError(f"Failed to generate Jekyll path: {e}") from e
    
    def sync_media(self, source_path: Path) -> Optional[Path]:
        """
        Sync a media file to Jekyll assets
        
        Args:
            source_path: Source media file path
            
        Returns:
            Target path in Jekyll assets
        """
        try:
            logger.debug(f"Syncing media file: {source_path}")
            
            # Get Jekyll path
            target_path = self.get_jekyll_media_path(source_path)
            logger.debug(f"Target path: {target_path}")
            
            # Create parent directories
            target_path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created parent directory: {target_path.parent}")
            
            # Process image if needed
            if source_path.suffix.lower() in self.SUPPORTED_FORMATS:
                logger.debug(f"Processing supported image: {source_path.suffix}")
                result = self.process_image(source_path, target_path)
                logger.debug(f"Image processing result: {result}")
                return result
            else:
                logger.debug(f"Copying non-image file directly: {source_path}")
                # Copy non-image files directly
                shutil.copy2(source_path, target_path)
                logger.debug(f"File copied: {target_path}")
                return target_path
            
        except Exception as e:
            logger.error(f"Failed to sync media file {source_path}: {e}", exc_info=True)
            raise MediaError(f"Failed to sync media: {e}") from e
            
    def process_media_file(self, file_path: Path) -> Optional[str]:
        """
        Process a media file and return its new path
        
        Args:
            file_path: Path to media file
            
        Returns:
            New path as string or None if failed
        """
        try:
            # Skip if already processed
            if file_path in self.processed_files:
                return self.path_mapping.get(str(file_path))
                
            # Get Jekyll path
            target_path = self.get_jekyll_media_path(file_path)
            
            # Process file
            if file_path.suffix.lower() in self.SUPPORTED_FORMATS:
                self.process_image(file_path, target_path)
            else:
                # Copy non-image files directly
                shutil.copy2(file_path, target_path)
                
            # Update tracking
            self.processed_files.add(file_path)
            self.path_mapping[str(file_path)] = str(target_path)
            
            return str(target_path)
            
        except Exception as e:
            logger.error(f"Failed to process media file {file_path}: {e}")
            return None
            
    def update_references(self, content: str) -> str:
        """
        Update media references in content
        
        Args:
            content: Content with media references
            
        Returns:
            Content with updated references
        """
        try:
            # Get all references
            references = self.get_media_references(content)
            
            # Process each reference
            for ref in references:
                try:
                    # Resolve actual file path
                    file_path = self.resolve_media_path(ref)
                    if not file_path:
                        continue
                        
                    # Process media file
                    new_path = self.process_media_file(file_path)
                    if not new_path:
                        continue
                        
                    # Update reference in content
                    old_ref = f"![[{ref}]]"
                    new_ref = f"![](/assets/img/posts/{Path(new_path).name})"
                    content = content.replace(old_ref, new_ref)
                    
                except (ValueError, FileNotFoundError) as e:
                    logger.warning(f"Skipping invalid reference '{ref}': {e}")
                    continue
                    
            return content
            
        except Exception as e:
            logger.error(f"Failed to update references: {e}")
            return content
    
    def cleanup_unused_assets(self, used_paths: Set[str]):
        """
        Remove unused media files from Jekyll assets
        
        Args:
            used_paths: Set of media paths currently in use
        """
        try:
            for asset in self.jekyll_assets.iterdir():
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
            asset_path = self.jekyll_assets / asset_name
            
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
    
    def process_references(self, source_path: Path) -> None:
        """Process media references in a file"""
        try:
            # Skip non-markdown files
            if source_path.suffix.lower() != '.md':
                return
                
            # Read file content
            content = source_path.read_text()
            
            # Extract media references
            references = self._extract_references(content)
            
            # Process each reference
            for ref in references:
                try:
                    # Get source and target paths
                    source = self._resolve_source_path(ref)
                    target = self._resolve_target_path(ref)
                    
                    # Create target directory
                    target.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file if it doesn't exist or is outdated
                    if not target.exists() or source.stat().st_mtime > target.stat().st_mtime:
                        self._process_image(source, target)
                        
                except Exception as e:
                    logger.error(f"Failed to process reference {ref}: {e}")
                    if not self.config.continue_on_error:
                        raise
                        
        except Exception as e:
            logger.error(f"Failed to process media references in {source_path}: {e}")
            raise MediaError(f"Failed to process media references: {e}") from e
            
    def _resolve_target_path(self, ref: str) -> Path:
        """Resolve target path for media file"""
        # Remove Obsidian link syntax
        ref = ref.strip('[]!')
        
        # Get filename
        filename = Path(ref).name
        
        # Create target path in Jekyll assets
        return self.config.jekyll_root / 'assets' / 'img' / 'posts' / filename
    
    def _process_image(self, source: Path, target: Path) -> None:
        """Process image and copy to target path"""
        try:
            # Create target directory if it doesn't exist
            target.parent.mkdir(parents=True, exist_ok=True)
            
            # Process images, copy other files directly
            if source.suffix.lower() in self.SUPPORTED_FORMATS:
                try:
                    # Open and process image
                    with Image.open(source) as img:
                        # Convert RGBA to RGB if needed
                        if img.mode == 'RGBA':
                            img = img.convert('RGB')
                            
                        # Resize if needed
                        if self.config.optimize_images and img.width > self.config.max_image_width:
                            ratio = self.config.max_image_width / img.width
                            new_size = (self.config.max_image_width, int(img.height * ratio))
                            img = img.resize(new_size, Image.Resampling.LANCZOS)
                            
                        # Save with optimized settings
                        if target.suffix.lower() in {'.jpg', '.jpeg'}:
                            img.save(target, 'JPEG', quality=85, optimize=True)
                        else:
                            img.save(target, optimize=True)
                            
                except (InvalidImageError, UnsupportedFormatError) as e:
                    # For test files or non-image files, just copy
                    shutil.copy2(source, target)
            else:
                shutil.copy2(source, target)
                
        except Exception as e:
            logger.error(f"Failed to process image {source}: {e}")
            raise MediaError(f"Failed to process image: {e}") from e
    
    def cleanup_unused(self):
        """Clean up unused media files"""
        try:
            # Get all media files in Jekyll assets
            assets = set(self.jekyll_assets.glob('*.*'))
            
            # Get all referenced media files
            referenced = set()
            for post in self.jekyll_root.glob('_posts/*.md'):
                with open(post) as f:
                    content = f.read()
                    for match in re.finditer(r'!\[.*?\]\((.*?)\)', content):
                        path = match.group(1)
                        if path.startswith('/'):
                            path = path[1:]
                        referenced.add(self.jekyll_root / path)
            
            # Delete unreferenced files
            for asset in assets:
                if asset not in referenced:
                    asset.unlink()
                    
        except Exception as e:
            logger.error(f"Error cleaning up media: {e}")
            raise
    
    def _extract_references(self, content: str) -> list[str]:
        """Extract media references from content"""
        references = []
        
        # Match Obsidian image links: ![[path/to/image.ext]]
        pattern = r'!\[\[(.*?)\]\]'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            ref = match.group(1)
            if any(ref.lower().endswith(ext) for ext in self.SUPPORTED_FORMATS):
                references.append(ref)
                
        return references
        
    def _resolve_source_path(self, ref: str) -> Path:
        """Resolve source path for media file"""
        # Remove Obsidian link syntax
        ref = ref.strip('[]!')
        
        # Handle absolute and relative paths
        if ref.startswith('atomics/'):
            return self.config.vault_root / ref
        else:
            return self.config.vault_root / 'atomics' / ref
    
    def process_batch(self, images: List[tuple[Path, Path]], chunk_size: int = 10) -> List[Path]:
        """
        Process multiple images in batches for better memory management
        
        Args:
            images: List of (source_path, target_path) tuples
            chunk_size: Number of images to process in each batch
            
        Returns:
            List of successfully processed image paths
            
        Raises:
            InvalidImageError: If an invalid image is encountered
            UnsupportedFormatError: If an unsupported format is encountered
            ImageProcessingError: If processing fails
        """
        from ..core.exceptions import InvalidImageError, UnsupportedFormatError, ImageProcessingError
        
        processed = []
        total = len(images)
        
        logger.info(f"Processing {total} images in batches of {chunk_size}")
        
        # Process in chunks for memory efficiency
        for i in range(0, total, chunk_size):
            chunk = images[i:i + chunk_size]
            logger.debug(f"Processing batch {i//chunk_size + 1}/{(total + chunk_size - 1)//chunk_size}")
            
            # Process each image in chunk
            batch_processed = []
            for source, target in chunk:
                try:
                    # Validate and process image
                    logger.debug(f"Processing image: {source} -> {target}")
                    self.validate_image(source)
                    if processed_path := self.process_image(source, target):
                        batch_processed.append(processed_path)
                        logger.debug(f"Successfully processed: {processed_path}")
                except (InvalidImageError, UnsupportedFormatError) as e:
                    logger.error(f"Validation error for {source}: {e}")
                    # Clean up any partial results from this batch
                    for path in batch_processed:
                        try:
                            if path.exists():
                                logger.debug(f"Cleaning up: {path}")
                                path.unlink()
                        except Exception as cleanup_err:
                            logger.error(f"Failed to clean up {path}: {cleanup_err}")
                    # Re-raise the original error
                    raise
                except Exception as e:
                    logger.error(f"Processing error for {source}: {e}")
                    # Clean up any partial results from this batch
                    for path in batch_processed:
                        try:
                            if path.exists():
                                logger.debug(f"Cleaning up: {path}")
                                path.unlink()
                        except Exception as cleanup_err:
                            logger.error(f"Failed to clean up {path}: {cleanup_err}")
                    raise ImageProcessingError(f"Failed to process {source}: {e}") from e
            
            processed.extend(batch_processed)
            logger.debug(f"Batch complete. Total processed: {len(processed)}")
            
            # Force cleanup after each batch
            gc.collect()
            
            # Small delay to allow memory to stabilize
            time.sleep(0.1)
        
        logger.info(f"Processing complete. Total images processed: {len(processed)}")
        return processed