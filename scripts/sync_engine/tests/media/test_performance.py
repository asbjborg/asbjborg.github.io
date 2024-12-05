"""Tests for media handling performance"""

import pytest
from PIL import Image
from sync_engine.handlers.media import MediaHandler

class TestMediaPerformance:
    """Tests for media handling performance"""
    
    def test_many_images(self, test_config):
        """Test handling many images in a post"""
        handler = MediaHandler(test_config)
        post_path = test_config.atomics_path / "2024/01/15/many_images.md"
        post_path.parent.mkdir(parents=True, exist_ok=True)
        
        image_refs = []
        for i in range(10):
            image_refs.append(f"![[atomics/2024/01/15/img_{i}.png]]")
        
        post_content = "---\nstatus: published\n---\n# Many Images\n\n" + "\n".join(image_refs)
        post_path.write_text(post_content)
        
        for i in range(10):
            img = Image.new('RGB', (100, 100), color='red')
            img_path = post_path.parent / f"img_{i}.png"
            img.save(img_path)
            
            target = test_config.jekyll_assets_path / f"img_{i}.jpg"
            handler.process_image(img_path, target)

    def test_performance_with_images(self, test_config):
        """Test performance with many images per post"""
        date_path = test_config.atomics_path / "2024/01/15"
        date_path.mkdir(parents=True)

        for post_num in range(10):
            content = ["""---
status: published
image: "![[atomics/2024/01/15/featured.png]]"
---
# Post with many images
"""]

            for img_num in range(100):
                content.append(f'\n![[atomics/2024/01/15/image_{post_num}_{img_num}.png]]')

            (date_path / f'post_{post_num}.md').write_text(''.join(content)) 