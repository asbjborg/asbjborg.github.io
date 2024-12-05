"""Test file change detection functionality"""

import pytest
import time
from pathlib import Path
from sync_engine.core.engine import SyncEngineV2
from sync_engine.core.types import SyncOperation, SyncDirection, PostStatus
from sync_engine.core.config import SyncConfig, ConfigManager

@pytest.fixture
def change_setup(tmp_path):
    """Create test directories and engine instance"""
    # Create test directories
    vault_root = tmp_path / "vault"
    jekyll_root = tmp_path / "jekyll"
    
    # Create standard structure
    (vault_root / "atomics").mkdir(parents=True)
    (jekyll_root / "_posts").mkdir(parents=True)
    (jekyll_root / "assets/img/posts").mkdir(parents=True)
    
    # Create config
    config = ConfigManager.load_from_dict({
        'vault_path': vault_root,
        'jekyll_path': jekyll_root,
        'vault_atomics': "atomics",
        'jekyll_posts': "_posts",
        'jekyll_assets': "assets/img/posts",
        'debug': True  # Enable debug logging for tests
    })
    
    # Initialize engine with config
    engine = SyncEngineV2(config=config)
    
    return {
        'engine': engine,
        'vault': vault_root,
        'jekyll': jekyll_root,
        'config': config
    }

def test_detect_new_file(change_setup):
    """Test detection of new files"""
    # Create new post in daily folder
    date_path = change_setup['vault'] / "atomics/2024/01/15"
    date_path.mkdir(parents=True)
    
    post_content = """---
title: New Post
status: published
---

# New Post

Test content
"""
    post_path = date_path / "new-post.md"
    post_path.write_text(post_content)
    
    # Run change detection
    engine = change_setup['engine']
    changes = engine.detect_changes()
    
    # Verify changes
    assert len(changes) == 1
    change = changes[0]
    assert change.operation == SyncOperation.CREATE
    assert change.source_path == post_path
    assert change.sync_direction == SyncDirection.OBSIDIAN_TO_JEKYLL

def test_detect_modified_file(change_setup):
    """Test detection of modified files"""
    # Create initial post in daily folder
    date_path = change_setup['vault'] / "atomics/2024/01/15"
    date_path.mkdir(parents=True)
    
    post_content = """---
title: Test Post
status: published
---

# Test Post

Initial content
"""
    post_path = date_path / "test-post.md"
    post_path.write_text(post_content)
    
    # Initial sync
    engine = change_setup['engine']
    engine.sync(direction=SyncDirection.OBSIDIAN_TO_JEKYLL)
    
    # Wait a bit to ensure different modification time
    time.sleep(0.1)
    
    # Modify post
    modified_content = """---
title: Test Post
status: published
modified: 2024-01-02
---

# Test Post

Updated content
"""
    post_path.write_text(modified_content)
    
    # Run change detection
    changes = engine.detect_changes()
    
    # Verify changes
    assert len(changes) == 1
    change = changes[0]
    assert change.operation == SyncOperation.UPDATE
    assert change.source_path == post_path
    assert change.sync_direction == SyncDirection.OBSIDIAN_TO_JEKYLL

def test_detect_deleted_file(change_setup):
    """Test detection of deleted files"""
    # Create initial post in daily folder
    date_path = change_setup['vault'] / "atomics/2024/01/15"
    date_path.mkdir(parents=True)
    
    post_content = """---
title: Test Post
status: published
---

# Test Post

Test content
"""
    post_path = date_path / "test-post.md"
    post_path.write_text(post_content)
    
    # Initial sync
    engine = change_setup['engine']
    engine.sync(direction=SyncDirection.OBSIDIAN_TO_JEKYLL)
    
    # Delete post
    post_path.unlink()
    
    # Run change detection
    changes = engine.detect_changes()
    
    # Verify changes
    assert len(changes) == 1
    change = changes[0]
    assert change.operation == SyncOperation.DELETE
    assert str(change.source_path).endswith("test-post.md")
    assert change.sync_direction == SyncDirection.OBSIDIAN_TO_JEKYLL

def test_detect_status_change(change_setup):
    """Test detection of post status changes"""
    # Create initial post as published in daily folder
    date_path = change_setup['vault'] / "atomics/2024/01/15"
    date_path.mkdir(parents=True)
    
    post_content = """---
title: Test Post
status: published
---

# Test Post

Test content
"""
    post_path = date_path / "test-post.md"
    post_path.write_text(post_content)
    
    # Initial sync
    engine = change_setup['engine']
    engine.sync(direction=SyncDirection.OBSIDIAN_TO_JEKYLL)
    
    # Change status to draft
    draft_content = """---
title: Test Post
status: draft
---

# Test Post

Test content
"""
    post_path.write_text(draft_content)
    
    # Run change detection
    changes = engine.detect_changes()
    
    # Verify changes
    assert len(changes) == 1
    change = changes[0]
    assert change.operation == SyncOperation.UPDATE
    assert change.source_path == post_path
    assert change.status == PostStatus.DRAFT
    assert change.sync_direction == SyncDirection.OBSIDIAN_TO_JEKYLL

def test_detect_multiple_changes(change_setup):
    """Test detection of multiple changes"""
    # Create daily folder
    date_path = change_setup['vault'] / "atomics/2024/01/15"
    date_path.mkdir(parents=True)
    
    # Create initial posts
    posts = [
        ("post1.md", "published"),
        ("post2.md", "draft"),
        ("post3.md", "published")
    ]
    
    for filename, status in posts:
        content = f"""---
title: {filename}
status: {status}
---

# {filename}

Test content
"""
        post_path = date_path / filename
        post_path.write_text(content)
    
    # Initial sync
    engine = change_setup['engine']
    engine.sync(direction=SyncDirection.OBSIDIAN_TO_JEKYLL)
    
    # Make various changes:
    # 1. Modify post1
    (date_path / "post1.md").write_text("""---
title: Post 1 Updated
status: published
---

Updated content
""")
    
    # 2. Delete post2
    (date_path / "post2.md").unlink()
    
    # 3. Create new post4
    (date_path / "post4.md").write_text("""---
title: Post 4
status: published
---

New post
""")
    
    # Run change detection
    changes = engine.detect_changes()
    
    # Verify changes
    assert len(changes) == 3
    operations = {c.operation for c in changes}
    assert SyncOperation.UPDATE in operations  # post1
    assert SyncOperation.DELETE in operations  # post2
    assert SyncOperation.CREATE in operations  # post4 