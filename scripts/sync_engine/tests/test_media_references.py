"""Test media reference extraction and handling"""

import pytest
from pathlib import Path
from dotenv import load_dotenv
from sync_engine.handlers.media import MediaHandler

# Load environment variables
load_dotenv()

@pytest.fixture
def sample_content():
    """Create sample markdown content with various media references"""
    return """
# Test Document

Regular image: ![[image.png]]
Image in folder: ![[folder/image.jpg]]
Absolute path: ![[atomics/2024/12/03/image.png]]
Pasted image: ![[Pasted image 20241203214844.png]]

Multiple on one line: ![[image1.png]] and ![[image2.jpg]]

Complex paths:
- ![[folder with spaces/my image.png]]
- ![[folder/subfolder/image with spaces.jpg]]
- ![[atomics/2024/12/03/Pasted image 20241203214844.png]]

Invalid references:
- ![[]]  # Empty
- ![[missing closing bracket]
- [[not an image]]  # Regular link
- ![regular markdown](regular-markdown.png)  # Regular markdown
"""

def test_extract_media_references(tmp_path, sample_content):
    """Test extraction of media references from content"""
    handler = MediaHandler(tmp_path, tmp_path / "assets")
    
    refs = handler.get_media_references(sample_content)
    
    # Should find all valid references
    assert "image.png" in refs
    assert "folder/image.jpg" in refs
    assert "atomics/2024/12/03/image.png" in refs
    assert "Pasted image 20241203214844.png" in refs
    assert "image1.png" in refs
    assert "image2.jpg" in refs
    assert "folder with spaces/my image.png" in refs
    assert "folder/subfolder/image with spaces.jpg" in refs
    assert "atomics/2024/12/03/Pasted image 20241203214844.png" in refs
    
    # Should not include invalid references
    assert "" not in refs  # Empty reference
    assert "missing closing bracket" not in refs
    assert "not an image" not in refs
    assert "regular-markdown.png" not in refs  # Regular markdown style

def test_frontmatter_image_references(tmp_path):
    """Test extraction of image references from frontmatter"""
    handler = MediaHandler(tmp_path, tmp_path / "assets")
    frontmatter = {
        'title': 'Test Post',
        'image': '![[featured/image.jpg]]',
        'gallery': [
            '![[gallery/image1.png]]',
            '![[gallery/image2.jpg]]'
        ]
    }
    
    refs = handler.get_media_references(str(frontmatter))
    
    assert "featured/image.jpg" in refs
    assert "gallery/image1.png" in refs
    assert "gallery/image2.jpg" in refs

def test_duplicate_references(tmp_path):
    """Test handling of duplicate references"""
    handler = MediaHandler(tmp_path, tmp_path / "assets")
    content = """
    First reference: ![[image.png]]
    Same image again: ![[image.png]]
    Different path: ![[folder/image.png]]
    """
    
    refs = handler.get_media_references(content)
    
    # Should only include unique references
    assert len([r for r in refs if r.endswith("image.png")]) == 2
    assert "image.png" in refs
    assert "folder/image.png" in refs

def test_malformed_references(tmp_path):
    """Test handling of malformed references"""
    handler = MediaHandler(tmp_path, tmp_path / "assets")
    content = """
    Malformed references:
    ![[]]
    ![[missing bracket
    ![[]
    ![[space at end ]]
    ![[/starts/with/slash]]
    ![[ends/with/slash/]]
    ![[../relative/path]]
    ![[./current/path]]
    """
    
    refs = handler.get_media_references(content)
    
    # Should handle malformed references gracefully
    for ref in refs:
        assert not ref.startswith('/')  # No absolute paths
        assert not ref.endswith('/')  # No trailing slashes
        assert not ref.startswith('.')  # No relative paths
        assert not ref.isspace()  # No whitespace-only refs
        assert ref.strip() == ref  # No leading/trailing whitespace