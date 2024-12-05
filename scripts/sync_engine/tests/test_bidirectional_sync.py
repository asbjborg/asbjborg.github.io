"""Test bidirectional sync functionality"""

import pytest
from pathlib import Path
from dotenv import load_dotenv
from sync_engine.core.engine import SyncEngineV2
from sync_engine.core.types import SyncDirection, SyncOperation, PostStatus
from sync_engine.core.config import SyncConfig, ConfigManager
from PIL import Image
import io

# Load environment variables
load_dotenv()

@pytest.fixture
def sync_setup(tmp_path):
    """Create test directories and engine instance"""
    # Create test directories
    vault_root = tmp_path / "vault"
    jekyll_root = tmp_path / "jekyll"
    
    # Create config
    config = ConfigManager.load_from_dict({
        'vault_path': vault_root,
        'jekyll_path': jekyll_root,
        'vault_atomics': "atomics",
        'jekyll_posts': "_posts",
        'jekyll_assets': "assets/img/posts",
        'debug': True  # Enable debug logging for tests
    })
    
    # Create standard structure
    config.atomics_path.mkdir(parents=True)
    config.jekyll_posts_path.mkdir(parents=True)
    (config.jekyll_path / "_drafts").mkdir(parents=True)
    config.jekyll_assets_path.mkdir(parents=True)
    
    # Initialize engine with config
    engine = SyncEngineV2(config=config)
    
    return {
        'engine': engine,
        'vault': config.vault_path,
        'jekyll': config.jekyll_path,
        'config': config
    }

@pytest.fixture
def test_image():
    """Create a valid test image"""
    img = Image.new('RGB', (100, 100), color='red')
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    return img_io.getvalue()

def test_obsidian_to_jekyll_sync(sync_setup, test_image):
    """Test sync from Obsidian to Jekyll"""
    # Create post in daily folder
    date_path = sync_setup['vault'] / "atomics/2024/01/15"
    date_path.mkdir(parents=True)
    
    post = date_path / "test-post.md"
    post.write_text("""---
status: published
image: ![[atomics/2024/01/15/test-image.jpg]]
---
# Test Post

Here's an image: ![[atomics/2024/01/15/test-image.jpg]]
""")
    
    # Create image in same folder
    (date_path / "test-image.jpg").write_bytes(test_image)
    
    # Run sync
    changes = sync_setup['engine'].sync(direction=SyncDirection.OBSIDIAN_TO_JEKYLL)
    
    # Verify changes
    assert len(changes) == 2  # Post and image
    assert (sync_setup['jekyll'] / "_posts/2024-01-15-test-post.md").exists()
    assert any((sync_setup['jekyll'] / "assets/img/posts").glob("*test-image*.jpg"))

def test_jekyll_to_obsidian_sync(sync_setup, test_image):
    """Test sync from Jekyll to Obsidian"""
    # Create post in Jekyll
    post = sync_setup['jekyll'] / "_posts/2024-01-15-test-post.md"
    post.write_text("""---
status: published
image: /assets/img/posts/test-image.jpg
---
# Test Post

Here's an image: ![](/assets/img/posts/test-image.jpg)
""")
    
    # Create image in Jekyll
    (sync_setup['jekyll'] / "assets/img/posts/test-image.jpg").write_bytes(test_image)
    
    # Run sync
    changes = sync_setup['engine'].sync(direction=SyncDirection.JEKYLL_TO_OBSIDIAN)
    
    # Verify changes
    assert len(changes) == 2  # Post and image
    
    # Post should be in correct daily folder
    obsidian_post = sync_setup['vault'] / "atomics/2024/01/15/test-post.md"
    assert obsidian_post.exists()
    
    # Image should be in same folder
    assert any((sync_setup['vault'] / "atomics/2024/01/15").glob("*test-image*.jpg"))
    
    # Verify image reference was converted to Obsidian format
    post_text = obsidian_post.read_text()
    assert "![[" in post_text
    assert "]]" in post_text
    assert "/assets/img/posts" not in post_text
    
    # Verify conflict resolution
    assert len(changes) == 2  # One post update
    change = changes[0]
    assert change.operation == SyncOperation.UPDATE
    assert change.sync_direction == SyncDirection.OBSIDIAN_TO_JEKYLL  # Newer version wins
    
    # Verify content was synchronized
    jekyll_text = post.read_text()
    assert "Obsidian version" in jekyll_text  # Newer version won
    assert "Jekyll version" not in jekyll_text

def test_status_handling(sync_setup):
    """Test handling of different post statuses"""
    # Create posts with different statuses in atomic notes structure
    date_path = sync_setup['vault'] / "atomics/2024/01/15"
    date_path.mkdir(parents=True)
    
    posts = [
        ("published-post.md", PostStatus.PUBLISHED),
        ("draft-post.md", PostStatus.DRAFT),
        ("private-post.md", PostStatus.PRIVATE)
    ]
    
    # Create in Obsidian's atomic notes structure
    for filename, status in posts:
        content = f"""---
title: {status.value.title()} Post
status: {status.value}
---

# {status.value.title()} Post

Test content
"""
        post_path = date_path / filename
        post_path.write_text(content)
    
    # Run sync
    engine = sync_setup['engine']
    changes = engine.sync(direction=SyncDirection.OBSIDIAN_TO_JEKYLL)
    
    # Verify status handling
    assert len(changes) == 2  # Only published and draft should sync
    
    # Check Jekyll directory structure
    jekyll_posts = list((sync_setup['jekyll'] / "_posts").glob("*.md"))
    assert len(jekyll_posts) == 1  # Only published posts in _posts
    
    jekyll_drafts = list((sync_setup['jekyll'] / "_drafts").glob("*.md"))
    assert len(jekyll_drafts) == 1  # Drafts in _drafts
    
    # Private posts should not be synced
    assert not any((sync_setup['jekyll'] / "_posts").glob("*private*.md"))
    assert not any((sync_setup['jekyll'] / "_drafts").glob("*private*.md"))

def test_conflict_resolution(sync_setup):
    """Test handling of conflicting changes"""
    # Create post in Obsidian's atomic notes structure
    date_path = sync_setup['vault'] / "atomics/2024/01/15"
    date_path.mkdir(parents=True)
    
    obsidian_content = """---
title: Test Post
status: published
modified: 2024-01-02T10:00:00
---

# Test Post

Obsidian version
"""
    
    jekyll_content = """---
title: Test Post
status: published
modified: 2024-01-02T09:00:00
---

# Test Post

Jekyll version
"""
    
    # Create posts
    obsidian_post = date_path / "test-post.md"
    jekyll_post = sync_setup['jekyll'] / "_posts/2024-01-15-test-post.md"
    obsidian_post.write_text(obsidian_content)
    jekyll_post.parent.mkdir(parents=True, exist_ok=True)
    jekyll_post.write_text(jekyll_content)
    
    # Run sync
    engine = sync_setup['engine']
    changes = engine.sync()  # No direction = bidirectional
    
    # Verify conflict resolution
    assert len(changes) == 1  # One post update
    change = changes[0]
    assert change.operation == SyncOperation.UPDATE
    assert change.sync_direction == SyncDirection.OBSIDIAN_TO_JEKYLL  # Newer version wins
    
    # Verify content was synchronized
    jekyll_text = jekyll_post.read_text()
    assert "Obsidian version" in jekyll_text  # Newer version won
    assert "Jekyll version" not in jekyll_text 