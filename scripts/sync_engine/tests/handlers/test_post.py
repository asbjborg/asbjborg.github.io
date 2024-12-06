"""Tests for post handling"""

import pytest
from pathlib import Path
import yaml
from datetime import date
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
        frontmatter = handler.extract_frontmatter(post_content)
        
        assert frontmatter['title'] == 'Test Post'
        assert frontmatter['status'] == 'published'
        assert frontmatter['date'] == date(2024, 1, 15)
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
            assert handler.extract_frontmatter(content) is None

    def test_post_path_handling(self, test_config):
        """Test post path handling"""
        handler = PostHandler(test_config)
        
        # Test published post
        vault_path = test_config.vault_root / "atomics/2024/01/15/test-post.md"
        jekyll_path = handler.get_jekyll_path(vault_path)
        assert jekyll_path == test_config.jekyll_root / "_posts/2024-01-15-test-post.md"

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
        
        # Create test file
        source_path = test_config.vault_root / "test.md"
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(post_content)
        
        handler = PostHandler(test_config)
        processed = handler.process(source_path, test_config.jekyll_root / "test.md")
        
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
        assert handler.extract_frontmatter(valid_content) is not None
        
        # Invalid - no status
        invalid_content = """---
title: Invalid Post
---
Content"""
        frontmatter = handler.extract_frontmatter(invalid_content)
        assert frontmatter is not None
        assert 'status' not in frontmatter 