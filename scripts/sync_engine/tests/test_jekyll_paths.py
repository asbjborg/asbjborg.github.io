"""Test Jekyll path generation functionality"""

import pytest
from pathlib import Path
from dotenv import load_dotenv
from sync_engine.handlers.media import MediaHandler
from sync_engine.core.config import SyncConfig, ConfigManager

# Load environment variables
load_dotenv()

@pytest.fixture
def test_config(tmp_path):
    """Create test configuration"""
    return ConfigManager.load_from_dict({
        'vault_path': tmp_path / 'vault',
        'jekyll_path': tmp_path / 'jekyll',
        'vault_atomics': 'atomics',
        'jekyll_posts': '_posts',
        'jekyll_assets': 'assets/img/posts',
        'debug': True  # Enable debug logging for tests
    })

@pytest.fixture
def sample_files(test_config):
    """Create sample files for testing"""
    files = {}
    
    # Create test files with content
    def create_test_file(path: Path, content: bytes = b'test content'):
        full_path = test_config.vault_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return full_path
    
    # Create all test files
    files['simple'] = create_test_file(Path('image.png'))
    files['spaces'] = create_test_file(Path('my image.png'))
    files['complex'] = create_test_file(Path('folder with spaces/my complex image.png'))
    files['absolute'] = create_test_file(Path('atomics/2024/12/03/Pasted image 20241203214844.png'))
    files['special_chars'] = create_test_file(Path('folder/my-image-#1@2023.png'))
    files['unicode'] = create_test_file(Path('folder/résumé.jpg'))
    files['dots'] = create_test_file(Path('folder/my..multiple...dots.png'))
    files['long'] = create_test_file(Path('very/long/path/that/might/exceed/filesystem/limits/image.png'))
    
    return files

def test_basic_path_generation(test_config, sample_files):
    """Test basic path generation"""
    handler = MediaHandler(test_config)
    
    # Simple filename
    jekyll_path = handler.get_jekyll_media_path(sample_files['simple'])
    assert jekyll_path.suffix == '.png'
    assert jekyll_path.name.startswith('image-')  # Should have hash
    assert len(jekyll_path.name) <= 100  # Reasonable length
    
    # Path with spaces
    jekyll_path = handler.get_jekyll_media_path(sample_files['spaces'])
    assert '-' in jekyll_path.stem  # Spaces converted to dashes
    assert ' ' not in jekyll_path.name  # No spaces in final name

def test_complex_path_handling(test_config, sample_files):
    """Test handling of complex paths"""
    handler = MediaHandler(test_config)
    
    # Complex nested path
    jekyll_path = handler.get_jekyll_media_path(sample_files['complex'])
    assert jekyll_path.parent == test_config.jekyll_assets_path  # Should be flat
    assert 'folder-with-spaces' in jekyll_path.stem  # Keep path info in name
    assert 'complex-image' in jekyll_path.stem  # Keep original name
    
    # Absolute vault path
    jekyll_path = handler.get_jekyll_media_path(sample_files['absolute'])
    assert not any(p in jekyll_path.stem for p in ['atomics', 'attachments'])  # Skip common dirs
    assert '2024' in jekyll_path.stem  # Keep date info
    assert 'pasted-image' in jekyll_path.stem.lower()  # Keep descriptive name

def test_special_character_handling(test_config, sample_files):
    """Test handling of special characters"""
    handler = MediaHandler(test_config)
    
    # Special characters
    jekyll_path = handler.get_jekyll_media_path(sample_files['special_chars'])
    assert '#' not in jekyll_path.name  # Remove special chars
    assert '@' not in jekyll_path.name
    
    # Check base name (without extension) is alphanumeric + dashes
    base = jekyll_path.stem
    assert base.replace('-', '').isalnum()  # Only alphanumeric + dashes
    
    # Unicode characters
    jekyll_path = handler.get_jekyll_media_path(sample_files['unicode'])
    assert 'resume' in jekyll_path.stem.lower()  # Normalize unicode
    assert all(c.isascii() for c in jekyll_path.name)  # ASCII only
    
    # Multiple dots
    jekyll_path = handler.get_jekyll_media_path(sample_files['dots'])
    assert jekyll_path.name.count('.') == 1  # Only extension dot
    assert '..' not in jekyll_path.name  # No consecutive dots

def test_collision_handling(test_config):
    """Test handling of potential filename collisions"""
    handler = MediaHandler(test_config)
    
    # Create files with same name in different folders
    paths = []
    for i in range(3):
        path = test_config.atomics_path / f'folder{i}/image.png'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f'content{i}'.encode())
        paths.append(path)
    
    # Get Jekyll paths for all
    jekyll_paths = [handler.get_jekyll_media_path(p) for p in paths]
    
    # Verify all paths are unique
    assert len(set(jekyll_paths)) == len(paths)
    
    # Verify hash is used for uniqueness
    stems = [p.stem for p in jekyll_paths]
    assert all('-' in s for s in stems)  # All have hash
    assert len(set(stems)) == len(paths)  # All unique

def test_long_path_handling(test_config, sample_files):
    """Test handling of very long paths"""
    handler = MediaHandler(test_config)
    
    # Very long path
    jekyll_path = handler.get_jekyll_media_path(sample_files['long'])
    assert len(jekyll_path.name) <= 100  # Reasonable length
    assert jekyll_path.name.endswith('.png')  # Keep extension
    assert 'image-' in jekyll_path.name  # Keep meaningful part