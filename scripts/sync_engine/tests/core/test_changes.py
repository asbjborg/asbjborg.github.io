"""Tests for change detection"""

import pytest
import time
from pathlib import Path
from sync_engine.core.changes import ChangeDetector
from sync_engine.core.types import SyncOperation, SyncDirection, PostStatus

class TestChangeDetection:
    """Tests for change detection"""
    
    def test_detect_new_post(self, test_config):
        """Test detection of new post"""
        # Create new post in vault
        post_path = test_config.vault_root / "atomics/2024/01/15/new_post.md"
        post_path.parent.mkdir(parents=True, exist_ok=True)
        post_path.write_text("""---
status: published
---
# New Post
Test content""")
        
        detector = ChangeDetector(test_config)
        changes = detector.detect_changes()
        
        assert len(changes) == 1
        change = changes[0]
        assert change.operation == SyncOperation.CREATE
        assert change.source_path == post_path
        assert change.sync_direction == SyncDirection.OBSIDIAN_TO_JEKYLL
        assert change.status == PostStatus.PUBLISHED

    def test_detect_modified_post(self, test_config):
        """Test detection of modified post"""
        # Create post in both locations
        vault_path = test_config.vault_root / "atomics/2024/01/15/modified.md"
        jekyll_path = test_config.jekyll_root / "_posts/2024-01-15-modified.md"
        
        vault_path.parent.mkdir(parents=True, exist_ok=True)
        jekyll_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write Jekyll file first
        jekyll_path.write_text("""---
status: published
---
# Modified Post
Old content""")
        
        # Wait to ensure timestamp difference
        time.sleep(0.1)
        
        # Write Obsidian file with newer timestamp
        vault_path.write_text("""---
status: published
---
# Modified Post
Updated content""")
        
        detector = ChangeDetector(test_config)
        changes = detector.detect_changes()
        
        assert len(changes) == 1
        change = changes[0]
        assert change.operation == SyncOperation.UPDATE
        assert change.source_path == vault_path
        assert change.target_path == jekyll_path
        assert change.sync_direction == SyncDirection.OBSIDIAN_TO_JEKYLL

    def test_detect_deleted_post(self, test_config):
        """Test detection of deleted post"""
        # Create post only in Jekyll
        jekyll_path = test_config.jekyll_root / "_posts/2024-01-15-deleted.md"
        jekyll_path.parent.mkdir(parents=True, exist_ok=True)
        jekyll_path.write_text("""---
status: published
---
# Deleted Post""")
        
        detector = ChangeDetector(test_config)
        changes = detector.detect_changes()
        
        assert len(changes) == 1
        change = changes[0]
        assert change.operation == SyncOperation.DELETE
        assert change.source_path == jekyll_path
        assert change.sync_direction == SyncDirection.JEKYLL_TO_OBSIDIAN

    def test_detect_draft_post(self, test_config):
        """Test detection of draft post"""
        # Create draft post in vault
        post_path = test_config.vault_root / "atomics/2024/01/15/draft.md"
        post_path.parent.mkdir(parents=True, exist_ok=True)
        post_path.write_text("""---
status: draft
---
# Draft Post""")
        
        detector = ChangeDetector(test_config)
        changes = detector.detect_changes()
        
        assert len(changes) == 1
        change = changes[0]
        assert change.operation == SyncOperation.CREATE
        assert change.source_path == post_path
        assert change.sync_direction == SyncDirection.OBSIDIAN_TO_JEKYLL
        assert change.status == PostStatus.DRAFT

    def test_detect_multiple_changes(self, test_config):
        """Test detection of multiple changes"""
        # Create various changes
        new_post = test_config.vault_root / "atomics/2024/01/15/new.md"
        modified_vault = test_config.vault_root / "atomics/2024/01/15/modified.md"
        modified_jekyll = test_config.jekyll_root / "_posts/2024-01-15-modified.md"
        deleted_jekyll = test_config.jekyll_root / "_posts/2024-01-15-deleted.md"
        
        # Set up test files
        new_post.parent.mkdir(parents=True, exist_ok=True)
        modified_vault.parent.mkdir(parents=True, exist_ok=True)
        modified_jekyll.parent.mkdir(parents=True, exist_ok=True)
        deleted_jekyll.parent.mkdir(parents=True, exist_ok=True)
        
        # Write files in order to ensure proper timestamps
        modified_jekyll.write_text("""---
status: published
---
Old content""")
        
        deleted_jekyll.write_text("""---
status: published
---
To be deleted""")
        
        # Wait to ensure timestamp difference
        time.sleep(0.1)
        
        new_post.write_text("""---
status: published
---
New post""")
        
        modified_vault.write_text("""---
status: published
---
Updated content""")
        
        detector = ChangeDetector(test_config)
        changes = detector.detect_changes()
        
        assert len(changes) == 3  # New, modified, and deleted
        operations = {c.operation for c in changes}
        assert operations == {SyncOperation.CREATE, SyncOperation.UPDATE, SyncOperation.DELETE}