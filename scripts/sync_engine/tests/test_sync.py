import pytest
from pathlib import Path
import frontmatter
import time
from sync_engine.core.sync import SyncManager
from sync_engine.core.types import SyncOperation, SyncDirection, PostStatus
from sync_engine.core.config import SyncConfig, ConfigManager
import shutil

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
def setup_dirs(test_config):
    """Create test directories matching real vault structure"""
    # Create Jekyll structure
    test_config.jekyll_posts_path.mkdir(parents=True)
    (test_config.jekyll_path / '_drafts').mkdir(parents=True)
    test_config.jekyll_assets_path.mkdir(parents=True)
    
    # Create Obsidian structure (atomics/YYYY/MM/DD)
    test_date = "2024/01/15"  # Use fixed date for tests
    atomic_path = test_config.atomics_path / test_date
    atomic_path.mkdir(parents=True)
    
    return test_config.vault_path, test_config.jekyll_path, atomic_path

def test_basic_sync(test_config, setup_dirs):
    """Test basic sync operation"""
    vault_path, jekyll_path, atomic_path = setup_dirs
    
    # Create post with image in daily folder
    post_content = """---
status: published
image: ![[atomics/2024/01/15/test.png]]
---
# Test Post

Here's an image: ![[atomics/2024/01/15/test.png]]
"""
    post_path = atomic_path / "my first post.md"
    post_path.write_text(post_content)
    
    # Create test image in same folder
    img_path = atomic_path / "test.png"
    img_path.write_bytes(b'fake png data')
    
    # Run sync
    manager = SyncManager(test_config)
    changes = manager.sync()
    
    # Verify changes
    assert len(changes) == 2  # Post and image
    post_change = next(c for c in changes if c.source_path.suffix == '.md')
    img_change = next(c for c in changes if c.source_path.suffix == '.png')
    
    # Verify correct Jekyll paths
    assert (jekyll_path / '_posts/2024-01-15-my-first-post.md').exists()
    assert list(jekyll_path.glob('assets/img/posts/*.png'))
    
    # Verify no changes (not a post)
    assert len(changes) == 0
    assert not list(jekyll_path.glob('_posts/*'))

def test_sync_with_errors(test_config, setup_dirs):
    """Test sync with some errors"""
    vault_path, jekyll_path, atomic_path = setup_dirs
    
    # Create valid post
    post1 = atomic_path / 'valid-note.md'
    post1.write_text("""---
status: published
---
Valid post""")
    
    # Create invalid post
    post2 = atomic_path / 'invalid-note.md'
    post2.write_text("Invalid frontmatter")
    
    # Run sync
    manager = SyncManager(test_config)
    changes = manager.sync()
    
    # Verify only valid post was synced
    assert len(changes) == 1
    assert changes[0].source_path.name == 'valid-note.md'
    assert (jekyll_path / '_posts/2024-01-15-valid-note.md').exists()

def test_cleanup(test_config, setup_dirs):
    """Test cleanup functionality"""
    vault_path, jekyll_path, atomic_path = setup_dirs
    
    # Create some test files
    (jekyll_path / 'assets/img/posts/old.png').write_bytes(b'old')
    (vault_path / '.atomic_backups/batch_123').mkdir(parents=True)
    
    # Create a post that doesn't reference the image
    post_path = atomic_path / 'test.md'
    post_path.write_text("""---
status: published
---
# Test Post
No images here
""")
    
    # Run cleanup
    manager = SyncManager(test_config)
    manager.sync()  # First sync to establish post
    manager.cleanup()
    
    # Verify cleanup - unused image should be removed
    assert not (jekyll_path / 'assets/img/posts/old.png').exists()
    assert not (vault_path / '.atomic_backups/batch_123').exists()

def test_media_handling(test_config, setup_dirs):
    """Test media file processing"""
    vault_path, jekyll_path, atomic_path = setup_dirs
    
    # Create post with multiple images
    post_content = """---
status: published
image: ![[atomics/2024/01/15/featured.jpg]]
---
# Test Post

Image 1: ![[atomics/2024/01/15/test1.png]]
Image 2: ![[atomics/2024/01/15/test2.png]]
"""
    post_path = atomic_path / 'media-test.md'
    post_path.write_text(post_content)
    
    # Create test images in same folder
    (atomic_path / 'featured.jpg').write_bytes(b'jpg data')
    (atomic_path / 'test1.png').write_bytes(b'png1 data')
    (atomic_path / 'test2.png').write_bytes(b'png2 data')
    
    # Run sync
    manager = SyncManager(test_config)
    changes = manager.sync()
    
    # Verify all images were processed
    assert len(changes) == 4  # 1 post + 3 images
    assert len(list(jekyll_path.glob('assets/img/posts/*'))) == 3
    assert (jekyll_path / '_posts/2024-01-15-media-test.md').exists()

def test_atomic_rollback(test_config, setup_dirs):
    """Test atomic rollback on error"""
    vault_path, jekyll_path, atomic_path = setup_dirs
    
    # Create post and image
    post_path = atomic_path / 'test-rollback.md'
    post_path.write_text("""---
status: published
---
Test with ![[atomics/2024/01/15/test.png]]""")
    
    img_path = atomic_path / 'test.png'
    img_path.write_bytes(b'png data')
    
    # Create MediaHandler that raises an error
    class ErrorMediaHandler:
        def get_media_references(self, _):
            raise Exception("Simulated error")
    
    # Create manager with error-prone handler
    manager = SyncManager(test_config)
    manager.media_handler = ErrorMediaHandler()
    
    # Run sync and verify rollback
    with pytest.raises(Exception):
        manager.sync()
    
    # Verify no files were created
    assert not list(jekyll_path.glob('_posts/*'))
    assert not list(jekyll_path.glob('assets/img/posts/*'))

def test_complex_paths(test_config, setup_dirs):
    """Test handling of complex file paths"""
    vault_path, jekyll_path, atomic_path = setup_dirs
    
    # Create post with complex paths
    post_content = """---
status: published
image: ![[atomics/2024/01/15/image with spaces.png]]
---
# Complex Paths

1. ![[atomics/2024/01/15/über.jpg]]
2. ![[atomics/2024/01/15/test#1.png]]
3. ![[atomics/2024/01/15/very-very-very-very-very-very-long-filename.gif]]
"""
    post_path = atomic_path / "complex post with spaces!.md"
    post_path.write_text(post_content)
    
    # Create test images in same folder
    images = [
        'image with spaces.png',
        'über.jpg',
        'test#1.png',
        'very-very-very-very-very-very-long-filename.gif'
    ]
    
    for img in images:
        (atomic_path / img).write_bytes(b'test')
    
    # Run sync
    manager = SyncManager(test_config)
    changes = manager.sync()
    
    # Verify all images were processed
    assert len(changes) == 5  # 1 post + 4 images
    assert len(list(jekyll_path.glob('assets/img/posts/*'))) == 4
    assert (jekyll_path / '_posts/2024-01-15-complex-post-with-spaces.md').exists()

def test_performance(test_config, setup_dirs):
    """Test sync performance with large dataset"""
    vault_path, jekyll_path, atomic_path = setup_dirs
    
    # Create multiple date folders for realistic load
    dates = [
        "2024/01/15",
        "2024/01/16",
        "2024/01/17",
    ]
    
    # Create many posts and images across different dates
    for i, date in enumerate(dates):
        date_path = vault_path / 'atomics' / date
        date_path.mkdir(parents=True, exist_ok=True)
        
        # Create posts for this date
        for j in range(33):  # 33 posts per day = ~100 posts
            post_content = f"""---
status: published
image: ![[atomics/{date}/img_{j}_0.png]]
---
# Post {i}_{j}

"""
            # Add 10 image references
            for k in range(1, 10):  # Skip 0 as it's in frontmatter
                post_content += f"\n![[atomics/{date}/img_{j}_{k}.png]]"
            
            # Create post
            post_path = date_path / f'post_{j}.md'
            post_path.write_text(post_content)
            
            # Create images in same folder
            for k in range(10):
                (date_path / f'img_{j}_{k}.png').write_bytes(b'test')
    
    # Time the sync
    start = time.time()
    manager = SyncManager(test_config)
    changes = manager.sync()
    duration = time.time() - start
    
    # Verify performance
    assert len(changes) == 1100  # ~100 posts + 1000 images
    assert duration < 30  # Should complete in under 30 seconds
    
    # Verify correct Jekyll paths
    for date in dates:
        date_str = date.replace('/', '-')
        for j in range(33):
            assert (jekyll_path / '_posts' / f'{date_str}-post_{j}.md').exists() 