import pytest
from pathlib import Path
import frontmatter
import time
from sync_engine.core.sync import SyncManager
from sync_engine.core.types import SyncOperation, SyncDirection, PostStatus
import shutil

@pytest.fixture
def config(tmp_path):
    return {
        'vault_root': str(tmp_path / 'vault'),
        'jekyll_root': str(tmp_path / 'jekyll'),
        'posts_path': '_posts',
        'jekyll_posts': '_posts',
        'jekyll_assets': 'assets/img/posts'
    }

@pytest.fixture
def setup_dirs(config):
    """Create test directories matching real vault structure"""
    vault_path = Path(config['vault_root'])
    jekyll_path = Path(config['jekyll_root'])
    
    # Create Jekyll structure
    (jekyll_path / '_posts').mkdir(parents=True)
    (jekyll_path / '_drafts').mkdir(parents=True)
    (jekyll_path / 'assets/img/posts').mkdir(parents=True)
    
    # Create Obsidian structure (atomics/YYYY/MM/DD)
    test_date = "2024/01/15"  # Use fixed date for tests
    atomic_path = vault_path / 'atomics' / test_date
    atomic_path.mkdir(parents=True)
    
    return vault_path, jekyll_path, atomic_path

def test_basic_sync(config, setup_dirs):
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
    manager = SyncManager(config)
    changes = manager.sync()
    
    # Verify changes
    assert len(changes) == 2  # Post and image
    post_change = next(c for c in changes if c.source_path.suffix == '.md')
    img_change = next(c for c in changes if c.source_path.suffix == '.png')
    
    # Verify correct Jekyll paths
    assert (jekyll_path / '_posts/2024-01-15-my-first-post.md').exists()
    assert list(jekyll_path.glob('assets/img/posts/*.png'))

def test_non_post_ignored(config, setup_dirs):
    """Test that regular notes without status are ignored"""
    vault_path, jekyll_path, atomic_path = setup_dirs
    
    # Create regular note without status
    note_content = """---
tags:
    - personal
---
# Regular Note
Just a personal note
"""
    note_path = atomic_path / "regular note.md"
    note_path.write_text(note_content)
    
    # Run sync
    manager = SyncManager(config)
    changes = manager.sync()
    
    # Verify no changes (not a post)
    assert len(changes) == 0
    assert not list(jekyll_path.glob('_posts/*'))

def test_sync_with_errors(config, setup_dirs):
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
    manager = SyncManager(config)
    changes = manager.sync()
    
    # Verify only valid post was synced
    assert len(changes) == 1
    assert changes[0].source_path.name == 'valid-note.md'
    assert (jekyll_path / '_posts/2024-01-15-valid-note.md').exists()

def test_cleanup(config, setup_dirs):
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
    manager = SyncManager(config)
    manager.sync()  # First sync to establish post
    manager.cleanup()
    
    # Verify cleanup - unused image should be removed
    assert not (jekyll_path / 'assets/img/posts/old.png').exists()
    assert not (vault_path / '.atomic_backups/batch_123').exists()

def test_media_handling(config, setup_dirs):
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
    manager = SyncManager(config)
    changes = manager.sync()
    
    # Verify all images were processed
    assert len(changes) == 4  # 1 post + 3 images
    assert len(list(jekyll_path.glob('assets/img/posts/*'))) == 3
    assert (jekyll_path / '_posts/2024-01-15-media-test.md').exists()

def test_atomic_rollback(config, setup_dirs):
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
    manager = SyncManager(config)
    manager.media_handler = ErrorMediaHandler()
    
    # Run sync and verify rollback
    with pytest.raises(Exception):
        manager.sync()
    
    # Verify no files were created
    assert not list(jekyll_path.glob('_posts/*'))
    assert not list(jekyll_path.glob('assets/img/posts/*'))

def test_complex_paths(config, setup_dirs):
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
    manager = SyncManager(config)
    changes = manager.sync()
    
    # Verify all images were processed
    assert len(changes) == 5  # 1 post + 4 images
    assert len(list(jekyll_path.glob('assets/img/posts/*'))) == 4
    assert (jekyll_path / '_posts/2024-01-15-complex-post-with-spaces.md').exists()

def test_performance(config, setup_dirs):
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
    manager = SyncManager(config)
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

@pytest.mark.integration
def test_end_to_end_sync_cycle(config, setup_dirs):
    """Test complete end-to-end sync cycle"""
    vault_path, jekyll_path, atomic_path = setup_dirs
    
    # 1. Create initial content in Obsidian
    post = atomic_path / 'test.md'
    post.write_text("""---
status: published
modified: 1234
---
Initial content""")
    
    # 2. Sync to Jekyll
    manager = SyncManager(config)
    manager.sync()
    
    # Verify Jekyll path
    jekyll_post = jekyll_path / '_posts/2024-01-15-test.md'
    assert jekyll_post.exists()
    
    # 3. Modify in Jekyll
    jekyll_content = frontmatter.load(str(jekyll_post))
    jekyll_content.content = "Modified in Jekyll"
    jekyll_content.metadata['modified'] = time.time()
    frontmatter.dump(jekyll_content, str(jekyll_post))
    
    # 4. Sync back to Obsidian
    manager.sync()
    
    # 5. Modify in Obsidian
    obsidian_content = frontmatter.load(str(post))
    obsidian_content.content = "Modified in Obsidian"
    obsidian_content.metadata['modified'] = time.time()
    frontmatter.dump(obsidian_content, str(post))
    
    # 6. Final sync
    changes = manager.sync()
    
    # Verify final state
    assert frontmatter.load(str(jekyll_post)).content == "Modified in Obsidian"
    assert len(changes) == 1

def test_real_vault_scenarios(config, setup_dirs):
    """Test real-world vault scenarios"""
    vault_path, jekyll_path, atomic_path = setup_dirs
    
    # Create a realistic post structure with internal links
    post_content = """---
status: published
tags:
    - python
    - automation
image: ![[atomics/2024/01/15/featured.png]]
---
# Testing the Sync Engine

Here's a test with:
- Internal link to [[another note]]  # Links stay as Obsidian format
- Multiple images:
  ![[atomics/2024/01/15/diagram.png]]
  ![[atomics/2024/01/15/screenshot.png]]
- Code blocks:
```python
def test():
    pass
```
- Nested lists
  - With items
  - And more items
    - Even deeper
"""
    post_path = atomic_path / 'test-post.md'
    post_path.write_text(post_content)
    
    # Create referenced files in same folder
    for img in ['featured.png', 'diagram.png', 'screenshot.png']:
        (atomic_path / img).write_bytes(b'test image')
    
    # Create referenced note (not a post)
    (atomic_path / 'another note.md').write_text("""---
tags: [notes]
---
Just a regular note, not a post""")
    
    # Run sync
    manager = SyncManager(config)
    changes = manager.sync()
    
    # Verify
    assert len(changes) == 4  # 1 post + 3 images
    jekyll_post = frontmatter.load(str(jekyll_path / '_posts/2024-01-15-test-post.md'))
    assert len(jekyll_post.metadata['tags']) == 2
    assert '```python' in jekyll_post.content  # Code block preserved
    assert '[[another note]]' in jekyll_post.content  # Internal link preserved

def test_error_recovery(config, setup_dirs):
    """Test recovery from various error conditions"""
    vault_path, jekyll_path, atomic_path = setup_dirs
    
    # Create test post
    post = atomic_path / 'test.md'
    post.write_text("""---
status: published
image: ![[atomics/2024/01/15/test.png]]
---
Test content
""")
    
    # Create image
    (atomic_path / 'test.png').write_bytes(b'test')
    
    # Simulate various error conditions
    manager = SyncManager(config)
    
    # 1. Test with read-only target directory
    jekyll_path.chmod(0o444)  # Make read-only
    with pytest.raises(Exception):
        manager.sync()
    jekyll_path.chmod(0o777)  # Restore permissions
    
    # 2. Test with corrupted backup
    manager.sync()  # First successful sync
    shutil.rmtree(vault_path / '.atomic_backups')  # Corrupt backup
    
    # Should still work
    changes = manager.sync()
    assert len(changes) == 0  # No changes needed

def test_concurrent_modifications(config, setup_dirs):
    """Test handling of concurrent modifications"""
    vault_path, jekyll_path, atomic_path = setup_dirs
    
    # Create initial post
    post = atomic_path / 'test.md'
    post.write_text("""---
status: published
modified: 1234
---
Initial content""")
    
    # First sync
    manager = SyncManager(config)
    manager.sync()
    
    jekyll_post = jekyll_path / '_posts/2024-01-15-test.md'
    assert jekyll_post.exists()
    
    # Modify both sides with different content
    # Obsidian side (newer)
    obsidian_content = frontmatter.load(str(post))
    obsidian_content.content = "Modified in Obsidian"
    obsidian_content.metadata['modified'] = time.time()
    frontmatter.dump(obsidian_content, str(post))
    
    # Jekyll side (older)
    jekyll_content = frontmatter.load(str(jekyll_post))
    jekyll_content.content = "Modified in Jekyll"
    jekyll_content.metadata['modified'] = time.time() - 100
    frontmatter.dump(jekyll_content, str(jekyll_post))
    
    # Sync should prefer Obsidian changes
    changes = manager.sync()
    assert len(changes) == 1
    final_content = frontmatter.load(str(jekyll_post))
    assert final_content.content == "Modified in Obsidian"

def test_config_validation(config, setup_dirs):
    """Test configuration validation"""
    vault_path, jekyll_path, atomic_path = setup_dirs
    
    # Test missing required config
    with pytest.raises(ValueError):
        SyncManager({})
    
    # Test invalid paths
    with pytest.raises(ValueError):
        SyncManager({
            'vault_root': '/nonexistent',
            'jekyll_root': '/nonexistent'
        })
    
    # Test with valid minimal config
    minimal_config = {
        'vault_root': str(vault_path),
        'jekyll_root': str(jekyll_path)
    }
    manager = SyncManager(minimal_config)
    
    # Verify required directories exist
    assert manager.atomics_root.exists()
    assert manager.jekyll_posts.exists()
    assert (manager.jekyll_path / manager.config['jekyll_assets']).exists()

def test_config_defaults(config, setup_dirs):
    """Test configuration defaults"""
    vault_path, jekyll_path, atomic_path = setup_dirs
    
    minimal_config = {
        'vault_root': str(vault_path),
        'jekyll_root': str(jekyll_path)
    }
    manager = SyncManager(minimal_config)
    
    # Verify default paths
    assert manager.atomics_root.name == 'atomics'  # Root for all content
    assert manager.jekyll_posts.name == '_posts'
    assert manager.media_handler.assets_path.name == 'posts'
    
    # Verify default settings
    assert manager.config['jekyll_posts'] == '_posts'
    assert manager.config['jekyll_assets'] == 'assets/img/posts'
    assert manager.config['backup_count'] == 5
    assert manager.config['auto_cleanup'] is True
    assert manager.config['max_image_width'] == 1200
    assert manager.config['optimize_images'] is True 