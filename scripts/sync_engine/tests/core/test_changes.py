"""Tests for change detection and handling"""

import pytest
from pathlib import Path
from sync_engine.core.changes import ChangeDetector
from sync_engine.core.types import SyncOperation, SyncDirection, PostStatus

class TestChangeDetection:
    """Tests for change detection"""
    
    def test_detect_new_post(self, test_config):
        """Test detection of new post"""
        # Create new post in vault
        post_path = test_config.vault_root / "atomics/2024/01/15/new_post.md"
        post_path.parent.mkdir(parents=True)
        post_path.write_text("""---
status: published
---
# New Post
Test content""")
        
        detector = ChangeDetector(test_config)
        changes = detector.detect_changes()
        
        assert len(changes) == 1
        assert changes[0].operation == SyncOperation.WRITE
        assert changes[0].source_path == post_path
        assert changes[0].target_path == test_config.jekyll_root / "_posts/2024-01-15-new_post.md"

    def test_detect_modified_post(self, test_config):
        """Test detection of modified post"""
        # Create post in both locations
        vault_path = test_config.vault_root / "atomics/2024/01/15/modified.md"
        jekyll_path = test_config.jekyll_root / "_posts/2024-01-15-modified.md"
        
        vault_path.parent.mkdir(parents=True)
        vault_path.write_text("""---
status: published
---
# Modified Post
Updated content""")
        
        jekyll_path.parent.mkdir(parents=True)
        jekyll_path.write_text("""---
status: published
---
# Modified Post
Old content""")
        
        detector = ChangeDetector(test_config)
        changes = detector.detect_changes()
        
        assert len(changes) == 1
        assert changes[0].operation == SyncOperation.WRITE
        assert changes[0].source_path == vault_path
        assert changes[0].target_path == jekyll_path

    def test_detect_deleted_post(self, test_config):
        """Test detection of deleted post"""
        # Create post only in Jekyll
        jekyll_path = test_config.jekyll_root / "_posts/2024-01-15-deleted.md"
        jekyll_path.parent.mkdir(parents=True)
        jekyll_path.write_text("""---
status: published
---
# Deleted Post""")
        
        detector = ChangeDetector(test_config)
        changes = detector.detect_changes()
        
        assert len(changes) == 1
        assert changes[0].operation == SyncOperation.DELETE
        assert changes[0].target_path == jekyll_path

    def test_detect_draft_post(self, test_config):
        """Test detection of draft post"""
        # Create draft post in vault
        post_path = test_config.vault_root / "atomics/2024/01/15/draft.md"
        post_path.parent.mkdir(parents=True)
        post_path.write_text("""---
status: draft
---
# Draft Post""")
        
        detector = ChangeDetector(test_config)
        changes = detector.detect_changes()
        
        assert len(changes) == 1
        assert changes[0].operation == SyncOperation.WRITE
        assert changes[0].source_path == post_path
        assert changes[0].target_path == test_config.jekyll_root / "_drafts/2024-01-15-draft.md"

    def test_detect_multiple_changes(self, test_config):
        """Test detection of multiple changes"""
        # Create various changes
        new_post = test_config.vault_root / "atomics/2024/01/15/new.md"
        modified_vault = test_config.vault_root / "atomics/2024/01/15/modified.md"
        modified_jekyll = test_config.jekyll_root / "_posts/2024-01-15-modified.md"
        deleted_jekyll = test_config.jekyll_root / "_posts/2024-01-15-deleted.md"
        
        # Set up test files
        new_post.parent.mkdir(parents=True)
        new_post.write_text("New post")
        modified_vault.write_text("Updated content")
        modified_jekyll.parent.mkdir(parents=True)
        modified_jekyll.write_text("Old content")
        deleted_jekyll.write_text("To be deleted")
        
        detector = ChangeDetector(test_config)
        changes = detector.detect_changes()
        
        assert len(changes) == 3  # New, modified, and deleted
        operations = {c.operation for c in changes}
        assert SyncOperation.WRITE in operations
        assert SyncOperation.DELETE in operations 