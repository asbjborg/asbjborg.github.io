import pytest
from pathlib import Path
import frontmatter
import time
from datetime import datetime

from sync_engine.core.changes import ChangeDetector
from sync_engine.core.types import SyncOperation, SyncDirection, PostStatus

@pytest.fixture
def setup_test_vault(tmp_path):
    """Create test vault with realistic structure"""
    vault = tmp_path / 'vault'
    jekyll = tmp_path / 'jekyll'
    
    # Create Jekyll structure
    (jekyll / '_posts').mkdir(parents=True)
    (jekyll / '_drafts').mkdir(parents=True)
    
    # Create Obsidian structure with multiple dates
    dates = ["2024/01/15", "2024/01/16"]
    for date in dates:
        (vault / 'atomics' / date).mkdir(parents=True)
    
    return vault, jekyll

def test_post_detection(setup_test_vault):
    """Test post detection by frontmatter status"""
    vault, jekyll = setup_test_vault
    date_path = vault / 'atomics/2024/01/15'
    
    # Create various files
    files = {
        'published.md': """---
status: published
---
# Published Post""",
        'draft.md': """---
status: draft
---
# Draft Post""",
        'private.md': """---
status: private
---
# Private Post""",
        'regular.md': """---
tags: [notes]
---
# Regular Note""",
        'invalid.md': "Not even frontmatter"
    }
    
    for name, content in files.items():
        (date_path / name).write_text(content)
    
    # Initialize detector
    detector = ChangeDetector({
        'vault_root': str(vault),
        'jekyll_root': str(jekyll)
    })
    
    # Get states
    states = detector._get_obsidian_states()
    
    # Verify only published post was detected
    assert len(states) == 1
    state = next(iter(states.values()))
    assert state.source_path.name == 'published.md'
    assert state.target_path.name == '2024-01-15-published.md'

def test_date_extraction(setup_test_vault):
    """Test date extraction from folder paths"""
    vault, jekyll = setup_test_vault
    
    # Create posts in different date folders
    posts = {
        '2024/01/15': 'first post.md',
        '2024/01/16': 'second post.md',
        'invalid/path': 'wrong.md',  # Invalid date path
        'atomics': 'root.md'  # No date path
    }
    
    for path, name in posts.items():
        post_path = vault / 'atomics' / path
        post_path.mkdir(parents=True, exist_ok=True)
        (post_path / name).write_text("""---
status: published
---
Test""")
    
    detector = ChangeDetector({
        'vault_root': str(vault),
        'jekyll_root': str(jekyll)
    })
    
    states = detector._get_obsidian_states()
    
    # Verify only posts in valid date folders were detected
    assert len(states) == 2
    filenames = {s.target_path.name for s in states.values()}
    assert '2024-01-15-first-post.md' in filenames
    assert '2024-01-16-second-post.md' in filenames

def test_bidirectional_path_preservation(setup_test_vault):
    """Test path preservation during bidirectional sync"""
    vault, jekyll = setup_test_vault
    date_path = vault / 'atomics/2024/01/15'
    
    # Create post in Obsidian
    post_path = date_path / 'test post.md'
    post_path.write_text("""---
status: published
modified: 1234
---
Original""")
    
    detector = ChangeDetector({
        'vault_root': str(vault),
        'jekyll_root': str(jekyll)
    })
    
    # First sync (Obsidian → Jekyll)
    states = detector._get_obsidian_states()
    assert len(states) == 1
    jekyll_path = states[next(iter(states))].target_path
    assert jekyll_path.name == '2024-01-15-test-post.md'
    
    # Create Jekyll post
    jekyll_path.parent.mkdir(parents=True, exist_ok=True)
    jekyll_path.write_text("""---
status: published
modified: 5678
---
Modified""")
    
    # Get Jekyll states
    jekyll_states = detector._get_jekyll_states()
    assert len(jekyll_states) == 1
    
    # Verify Jekyll → Obsidian path matches original
    state = next(iter(jekyll_states.values()))
    assert state.target_path == post_path

def test_complex_filenames(setup_test_vault):
    """Test handling of complex filenames"""
    vault, jekyll = setup_test_vault
    date_path = vault / 'atomics/2024/01/15'
    
    # Create posts with challenging names
    files = {
        'post with spaces.md': 'Published post with spaces',
        'über_post_åäö.md': 'Unicode characters',
        'very-very-very-very-very-very-long-filename.md': 'Long filename',
        'post#1_[test].md': 'Special characters'
    }
    
    for name, content in files.items():
        (date_path / name).write_text(f"""---
status: published
---
{content}""")
    
    detector = ChangeDetector({
        'vault_root': str(vault),
        'jekyll_root': str(jekyll)
    })
    
    states = detector._get_obsidian_states()
    
    # Verify all posts were detected and named correctly
    assert len(states) == 4
    filenames = {s.target_path.name for s in states.values()}
    assert '2024-01-15-post-with-spaces.md' in filenames
    assert '2024-01-15-uber-post-aao.md' in filenames
    assert '2024-01-15-very-very-very-very-very-very-long-filename.md' in filenames
    assert '2024-01-15-post-1-test.md' in filenames

def test_multiple_posts_per_day(setup_test_vault):
    """Test handling multiple posts in same day folder"""
    vault, jekyll = setup_test_vault
    date_path = vault / 'atomics/2024/01/15'
    
    # Create multiple posts for same day
    for i in range(5):
        (date_path / f'post_{i}.md').write_text(f"""---
status: published
modified: {1000 + i}
---
Post {i}""")
    
    detector = ChangeDetector({
        'vault_root': str(vault),
        'jekyll_root': str(jekyll)
    })
    
    states = detector._get_obsidian_states()
    
    # Verify all posts detected with correct dates
    assert len(states) == 5
    for i in range(5):
        assert any(s.target_path.name == f'2024-01-15-post_{i}.md' for s in states.values())

def test_error_handling(setup_test_vault):
    """Test handling of various error conditions"""
    vault, jekyll = setup_test_vault
    date_path = vault / 'atomics/2024/01/15'
    
    # Create test cases
    error_cases = {
        # Invalid frontmatter
        'invalid_yaml.md': """---
status: published
tags: [unclosed, array
---
Bad YAML""",
        # Corrupted frontmatter
        'corrupted.md': """--
partial frontmatter
Content""",
        # No frontmatter at all
        'no_frontmatter.md': "Just content\nNo frontmatter",
        # Valid post for comparison
        'valid.md': """---
status: published
---
Valid post"""
    }
    
    for name, content in error_cases.items():
        (date_path / name).write_text(content)
    
    detector = ChangeDetector({
        'vault_root': str(vault),
        'jekyll_root': str(jekyll)
    })
    
    # Should handle errors gracefully and continue processing
    states = detector._get_obsidian_states()
    
    # Only valid post should be detected
    assert len(states) == 1
    assert next(iter(states.values())).source_path.name == 'valid.md'

def test_permission_errors(setup_test_vault):
    """Test handling of permission issues"""
    vault, jekyll = setup_test_vault
    date_path = vault / 'atomics/2024/01/15'
    
    # Create test post
    post_path = date_path / 'test.md'
    post_path.write_text("""---
status: published
---
Test content""")
    
    # Make post read-only
    post_path.chmod(0o444)
    
    detector = ChangeDetector({
        'vault_root': str(vault),
        'jekyll_root': str(jekyll)
    })
    
    # Should still be able to read
    states = detector._get_obsidian_states()
    assert len(states) == 1
    
    # Make directory read-only
    date_path.chmod(0o444)
    
    # Should handle directory permission errors
    states = detector._get_obsidian_states()
    assert len(states) == 1  # Still able to read existing files
    
    # Restore permissions for cleanup
    date_path.chmod(0o777)
    post_path.chmod(0o777)

def test_invalid_date_paths(setup_test_vault):
    """Test handling of invalid date paths"""
    vault, jekyll = setup_test_vault
    
    # Create posts in invalid date paths
    invalid_paths = [
        'atomics/not/a/date',           # Wrong format
        'atomics/2024/13/01',           # Invalid month
        'atomics/2024/01/32',           # Invalid day
        'atomics/202A/01/01',           # Non-numeric
        'atomics/2024/1/1',             # Missing padding
        'atomics/2024/01',              # Missing day
        'atomics/2024',                 # Missing month/day
        'atomics/2024/01/15/subdir'     # Too deep
    ]
    
    for path in invalid_paths:
        full_path = vault / path
        full_path.mkdir(parents=True, exist_ok=True)
        (full_path / 'post.md').write_text("""---
status: published
---
Test post""")
    
    detector = ChangeDetector({
        'vault_root': str(vault),
        'jekyll_root': str(jekyll)
    })
    
    # Should ignore all invalid paths
    states = detector._get_obsidian_states()
    assert len(states) == 0

def test_large_vault_performance(setup_test_vault):
    """Test performance with large vault"""
    vault, jekyll = setup_test_vault
    
    # Create a year's worth of daily folders
    dates = []
    for month in range(1, 13):
        for day in range(1, 28):  # 27 days per month
            date = f"2024/{month:02d}/{day:02d}"
            dates.append(date)
            (vault / 'atomics' / date).mkdir(parents=True)
    
    # Create posts and regular notes in each folder
    total_posts = 0
    for date in dates:
        date_path = vault / 'atomics' / date
        
        # Create 3 posts per day
        for i in range(3):
            (date_path / f'post_{i}.md').write_text(f"""---
status: published
modified: {time.time()}
---
Post {i} for {date}""")
            total_posts += 1
        
        # Create some regular notes too
        for i in range(2):
            (date_path / f'note_{i}.md').write_text(f"""---
tags: [notes]
---
Regular note {i}""")
    
    # Time the scan
    start = time.time()
    detector = ChangeDetector({
        'vault_root': str(vault),
        'jekyll_root': str(jekyll)
    })
    states = detector._get_obsidian_states()
    duration = time.time() - start
    
    # Verify performance
    assert len(states) == total_posts  # Should find all posts
    assert duration < 2.0  # Should complete in under 2 seconds
    
    # Verify correct date handling
    for date in dates:
        date_str = date.replace('/', '-')
        for i in range(3):
            expected = f"{date_str}-post_{i}.md"
            assert any(s.target_path.name == expected for s in states.values())

def test_performance_with_images(setup_test_vault):
    """Test performance with many images per post"""
    vault, jekyll = setup_test_vault
    date_path = vault / 'atomics/2024/01/15'
    
    # Create posts with many image references
    for post_num in range(10):  # 10 posts
        content = ["""---
status: published
image: ![[atomics/2024/01/15/featured.png]]
---
# Post with many images
"""]
        
        # Add 100 image references per post
        for img_num in range(100):
            content.append(f"\n![[atomics/2024/01/15/image_{post_num}_{img_num}.png]]")
        
        (date_path / f'post_{post_num}.md').write_text(''.join(content))
    
    # Time the scan
    start = time.time()
    detector = ChangeDetector({
        'vault_root': str(vault),
        'jekyll_root': str(jekyll)
    })
    states = detector._get_obsidian_states()
    duration = time.time() - start
    
    # Verify performance
    assert len(states) == 10  # Should find all posts
    assert duration < 1.0  # Should complete in under 1 second