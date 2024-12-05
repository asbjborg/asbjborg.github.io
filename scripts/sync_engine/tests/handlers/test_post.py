"""Tests for post handling"""

import pytest
from pathlib import Path
import yaml
from sync_engine.handlers.post import PostHandler
from sync_engine.core.types import PostStatus

class TestPostHandling:
    """Tests for post handling"""
    
    def test_frontmatter_parsing(self, test_config):
        """Test parsing post frontmatter"""
        post_content = """---
title: Test Post
status: published
date: 2024-01-15
tags: [test, python]
---
# Test Post
Content here"""
        
        handler = PostHandler(test_config)
        frontmatter = handler.parse_frontmatter(post_content)
        
        assert frontmatter['title'] == 'Test Post'
        assert frontmatter['status'] == 'published'
        assert frontmatter['date'] == '2024-01-15'
        assert frontmatter['tags'] == ['test', 'python']

    def test_invalid_frontmatter(self, test_config):
        """Test handling invalid frontmatter"""
        invalid_contents = [
            "No frontmatter here",
            "---\nInvalid YAML\n---\nContent",
            "---\n---\nEmpty frontmatter"
        ]
        
        handler = PostHandler(test_config)
        for content in invalid_contents:
            with pytest.raises(ValueError):
                handler.parse_frontmatter(content)

    def test_post_path_handling(self, test_config):
        """Test post path handling"""
        handler = PostHandler(test_config)
        
        # Test published post
        vault_path = test_config.vault_root / "atomics/2024/01/15/test-post.md"
        jekyll_path = handler.get_jekyll_path(vault_path, PostStatus.PUBLISHED)
        assert jekyll_path == test_config.jekyll_root / "_posts/2024-01-15-test-post.md"
        
        # Test draft post
        draft_path = handler.get_jekyll_path(vault_path, PostStatus.DRAFT)
        assert draft_path == test_config.jekyll_root / "_drafts/2024-01-15-test-post.md"

    def test_post_processing(self, test_config):
        """Test post content processing"""
        post_content = """---
status: published
---
# Test Post

Normal paragraph.

```python
def test():
    pass
```

- List item 1
- List item 2

> Quote here"""
        
        handler = PostHandler(test_config)
        processed = handler.process_content(post_content)
        
        # Basic content checks
        assert "# Test Post" in processed
        assert "```python" in processed
        assert "- List item" in processed
        assert "> Quote here" in processed

    def test_post_validation(self, test_config):
        """Test post validation"""
        handler = PostHandler(test_config)
        
        # Valid post
        valid_content = """---
status: published
title: Valid Post
---
Content"""
        assert handler.validate_post(valid_content) is True
        
        # Invalid - no status
        invalid_content = """---
title: Invalid Post
---
Content"""
        with pytest.raises(ValueError):
            handler.validate_post(invalid_content)

    def test_post_cleanup(self, test_config):
        """Test post cleanup operations"""
        handler = PostHandler(test_config)
        
        # Create test posts
        posts_dir = test_config.jekyll_root / "_posts"
        posts_dir.mkdir(parents=True, exist_ok=True)
        
        (posts_dir / "2024-01-15-test1.md").write_text("Test 1")
        (posts_dir / "2024-01-15-test2.md").write_text("Test 2")
        
        # Run cleanup
        handler.cleanup_unused([posts_dir / "2024-01-15-test1.md"])
        
        # Verify only test1.md remains
        assert (posts_dir / "2024-01-15-test1.md").exists()
        assert not (posts_dir / "2024-01-15-test2.md").exists() 