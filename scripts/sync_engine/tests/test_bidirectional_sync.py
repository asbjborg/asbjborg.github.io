"""Test bidirectional sync functionality"""

import pytest
from pathlib import Path
from dotenv import load_dotenv
from sync_engine.core.engine import SyncEngineV2
from sync_engine.core.types import SyncDirection, SyncOperation, PostStatus
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
    
    # Create standard structure
    (vault_root / "_posts").mkdir(parents=True)
    (vault_root / "atomics").mkdir()
    (jekyll_root / "_posts").mkdir(parents=True)
    (jekyll_root / "assets/img/posts").mkdir(parents=True)
    
    # Initialize engine
    engine = SyncEngineV2(
        vault_root=vault_root,
        jekyll_root=jekyll_root,
        vault_posts="_posts",
        vault_media="atomics",
        jekyll_posts="_posts",
        jekyll_assets="assets/img/posts"
    )
    
    return {
        'engine': engine,
        'vault': vault_root,
        'jekyll': jekyll_root
    }

@pytest.fixture
def test_image():
    """Create a valid test image"""
    img = Image.new('RGB', (100, 100), color='red')
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    return img_io.getvalue()

def test_obsidian_to_jekyll_sync(sync_setup, test_image):
    """Test syncing changes from Obsidian to Jekyll"""
    # Create test post in Obsidian
    post_content = """---
title: Test Post
status: published
date: 2024-01-01
---

# Test Post

This is a test post with an image:

![[atomics/test-image.png]]
"""
    
    # Create test image
    image_path = sync_setup['vault'] / "atomics/test-image.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(test_image)
    
    # Create post in Obsidian
    post_path = sync_setup['vault'] / "_posts/2024-01-01-test-post.md"
    post_path.write_text(post_content)
    
    # Run sync
    engine = sync_setup['engine']
    changes = engine.sync(direction=SyncDirection.OBSIDIAN_TO_JEKYLL)
    
    # Verify changes
    assert len(changes) == 2  # Post and image
    assert any(c.operation == SyncOperation.CREATE and "test-post.md" in str(c.target_path) for c in changes)
    assert any(c.operation == SyncOperation.CREATE and "test-image" in str(c.target_path) for c in changes)
    
    # Verify files exist in Jekyll
    jekyll_post = sync_setup['jekyll'] / "_posts/2024-01-01-test-post.md"
    assert jekyll_post.exists()
    
    # Verify image was processed
    assert any((sync_setup['jekyll'] / "assets/img/posts").glob("*test-image*.png"))

def test_jekyll_to_obsidian_sync(sync_setup, test_image):
    """Test syncing changes from Jekyll to Obsidian"""
    # Create test post in Jekyll
    post_content = """---
title: Test Post
status: published
date: 2024-01-01
image: /assets/img/posts/test-image-123.jpg
---

# Test Post

This is a test post with an image:

![Test Image](/assets/img/posts/test-image-123.jpg)
"""
    
    # Create test image
    image_path = sync_setup['jekyll'] / "assets/img/posts/test-image-123.jpg"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(test_image)
    
    # Create post in Jekyll
    post_path = sync_setup['jekyll'] / "_posts/2024-01-01-test-post.md"
    post_path.write_text(post_content)
    
    # Run sync
    engine = sync_setup['engine']
    changes = engine.sync(direction=SyncDirection.JEKYLL_TO_OBSIDIAN)
    
    # Debug print
    print("\nChanges:")
    for c in changes:
        print(f"Operation: {c.operation}, Target: {c.target_path}")
    
    # Verify changes
    assert len(changes) == 2  # Post and image
    assert any(c.operation == SyncOperation.CREATE and "test-post.md" in str(c.target_path) for c in changes)
    assert any(c.operation == SyncOperation.CREATE and "test-image" in str(c.target_path) for c in changes)
    
    # Verify files exist in Obsidian
    obsidian_post = sync_setup['vault'] / "_posts/2024-01-01-test-post.md"
    assert obsidian_post.exists()
    
    # Verify image was processed
    assert any((sync_setup['vault'] / "atomics").glob("*test-image*.jpg"))
    
    # Verify image reference was converted to Obsidian format
    post_text = obsidian_post.read_text()
    assert "![[" in post_text
    assert "]]" in post_text
    assert "/assets/img/posts" not in post_text

def test_conflict_resolution(sync_setup):
    """Test handling of conflicting changes"""
    # Create post in both locations with different content
    obsidian_content = """---
title: Test Post
status: published
date: 2024-01-01
modified: 2024-01-02T10:00:00
---

# Test Post

Obsidian version
"""
    
    jekyll_content = """---
title: Test Post
status: published
date: 2024-01-01
modified: 2024-01-02T09:00:00
---

# Test Post

Jekyll version
"""
    
    # Create posts
    obsidian_post = sync_setup['vault'] / "_posts/2024-01-01-test-post.md"
    jekyll_post = sync_setup['jekyll'] / "_posts/2024-01-01-test-post.md"
    obsidian_post.write_text(obsidian_content)
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

def test_status_handling(sync_setup):
    """Test handling of different post statuses"""
    # Create posts with different statuses
    posts = [
        ("published-post.md", PostStatus.PUBLISHED),
        ("draft-post.md", PostStatus.DRAFT),
        ("private-post.md", PostStatus.PRIVATE)
    ]
    
    # Create in Obsidian
    for filename, status in posts:
        content = f"""---
title: {status.value.title()} Post
status: {status.value}
date: 2024-01-01
---

# {status.value.title()} Post

Test content
"""
        post_path = sync_setup['vault'] / "_posts" / filename
        post_path.write_text(content)
    
    # Run sync
    engine = sync_setup['engine']
    changes = engine.sync(direction=SyncDirection.OBSIDIAN_TO_JEKYLL)
    
    # Verify status handling
    assert len(changes) == 2  # Only published and draft should sync
    
    # Check Jekyll directory
    jekyll_posts = list((sync_setup['jekyll'] / "_posts").glob("*.md"))
    assert len(jekyll_posts) == 1  # Only published posts in _posts
    
    jekyll_drafts = list((sync_setup['jekyll'] / "_drafts").glob("*.md"))
    assert len(jekyll_drafts) == 1  # Drafts in _drafts
    
    # Private posts should not be synced
    assert not any((sync_setup['jekyll'] / "_posts").glob("*private*.md"))
    assert not any((sync_setup['jekyll'] / "_drafts").glob("*private*.md")) 