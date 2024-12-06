"""Tests for sync performance"""

import pytest
import time
from pathlib import Path
from PIL import Image
from sync_engine.core.sync import SyncManager

class TestSyncPerformance:
    """Tests for sync performance"""
    
    def test_performance(self, test_config, setup_dirs):
        """Test sync performance with large dataset"""
        vault_root, jekyll_path, atomic_path = setup_dirs
        
        # Create multiple date folders for realistic load
        dates = [
            "2024/01/15",
            "2024/01/16",
            "2024/01/17",
        ]
        
        # Create test image once and reuse
        test_img = Image.new('RGB', (100, 100), color='red')
        
        # Create many posts and images across different dates
        for i, date in enumerate(dates):
            date_path = atomic_path / date
            date_path.mkdir(parents=True, exist_ok=True)
            
            # Create posts for this date
            for j in range(33):  # 33 posts per day = ~100 posts
                post_content = f"""---
status: published
image: "[[atomics/{date}/img_{j}_0.png]]"
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
                    test_img.save(date_path / f'img_{j}_{k}.png')
        
        # Time the sync
        start = time.time()
        manager = SyncManager(test_config)
        changes = manager.sync()
        duration = time.time() - start
        
        # Verify performance
        assert len(changes) == 1089  # 99 posts (33 per day * 3 days) + 990 images (10 per post * 99 posts)
        assert duration < 30  # Should complete in under 30 seconds
        
        # Verify correct Jekyll paths
        for date in dates:
            date_str = date.replace('/', '-')
            for j in range(33):
                assert (jekyll_path / '_posts' / f'{date_str}-post_{j}.md').exists() 