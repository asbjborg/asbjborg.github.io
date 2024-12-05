"""Test media handler error cases"""

import os
import pytest
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv
from sync_engine.handlers.media import MediaHandler
from sync_engine.core.exceptions import InvalidImageError, UnsupportedFormatError, ImageProcessingError

# Load environment variables
load_dotenv()

@pytest.fixture
def bad_images(tmp_path):
    """Create problematic images for testing"""
    images_dir = tmp_path / "bad_images"
    images_dir.mkdir()
    
    # Create corrupted JPEG
    corrupt_jpg = images_dir / "corrupt.jpg"
    corrupt_jpg.write_bytes(b"Not a real JPEG file")
    
    # Create empty file
    empty_file = images_dir / "empty.png"
    empty_file.touch()
    
    # Create file with wrong extension
    wrong_ext = images_dir / "actually_txt.png"
    wrong_ext.write_text("I'm not really a PNG")
    
    # Create valid but tiny image
    tiny_img = Image.new('RGB', (1, 1), color='red')
    tiny_path = images_dir / "tiny.png"
    tiny_img.save(tiny_path)
    
    return {
        'corrupt': corrupt_jpg,
        'empty': empty_file,
        'wrong_ext': wrong_ext,
        'tiny': tiny_path,
        'dir': images_dir
    }

def test_corrupted_image(tmp_path, bad_images):
    """Test handling of corrupted image files"""
    handler = MediaHandler(tmp_path, tmp_path / "assets")
    
    # Should handle corrupted file gracefully
    with pytest.raises(InvalidImageError) as exc_info:
        handler.process_image(bad_images['corrupt'], tmp_path / "out.jpg")
    assert "corrupted" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

def test_empty_file(tmp_path, bad_images):
    """Test handling of empty files"""
    handler = MediaHandler(tmp_path, tmp_path / "assets")
    
    # Should handle empty file gracefully
    with pytest.raises(InvalidImageError) as exc_info:
        handler.process_image(bad_images['empty'], tmp_path / "out.png")
    assert "empty" in str(exc_info.value).lower()

def test_wrong_extension(tmp_path, bad_images):
    """Test handling of files with incorrect extensions"""
    handler = MediaHandler(tmp_path, tmp_path / "assets")
    
    # Should detect incorrect file type
    with pytest.raises(InvalidImageError) as exc_info:
        handler.process_image(bad_images['wrong_ext'], tmp_path / "out.png")
    assert "invalid" in str(exc_info.value).lower() or "corrupted" in str(exc_info.value).lower()

def test_permission_error(tmp_path, bad_images):
    """Test handling of permission errors"""
    handler = MediaHandler(tmp_path, tmp_path / "assets")
    
    # Make output directory read-only
    output_dir = tmp_path / "readonly"
    output_dir.mkdir()
    os.chmod(output_dir, 0o444)  # Read-only
    
    # Should handle permission error gracefully
    with pytest.raises(ImageProcessingError) as exc_info:
        handler.process_image(bad_images['tiny'], output_dir / "out.png")
    assert "permission" in str(exc_info.value).lower()
    
    # Cleanup
    os.chmod(output_dir, 0o777)  # Restore permissions

def test_missing_file(tmp_path):
    """Test handling of non-existent files"""
    handler = MediaHandler(tmp_path, tmp_path / "assets")
    
    # Should handle missing file gracefully
    with pytest.raises(FileNotFoundError):
        handler.process_image(tmp_path / "doesnt_exist.jpg", tmp_path / "out.jpg")

def test_unsupported_format(tmp_path, bad_images):
    """Test handling of unsupported image formats"""
    handler = MediaHandler(tmp_path, tmp_path / "assets")
    
    # Create file with unsupported extension
    unsupported = tmp_path / "test.xyz"
    unsupported.write_bytes(b"Not a real image format")
    
    # Should reject unsupported format
    with pytest.raises(UnsupportedFormatError) as exc_info:
        handler.process_image(unsupported, tmp_path / "out.xyz")
    assert "unsupported" in str(exc_info.value).lower()