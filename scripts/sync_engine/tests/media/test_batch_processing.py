"""Tests for media batch processing.

This module tests:
- Batch image processing
- Memory usage during batch operations
- Resource cleanup
- Error handling in batches
"""

import pytest
import time
import psutil
import os
import gc
from pathlib import Path
from PIL import Image
from sync_engine.core.exceptions import InvalidImageError
from sync_engine.handlers.media import MediaHandler
import logging

def get_memory_mb():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

class TestMediaBatchProcessing:
    """Tests for media batch processing"""
    
    def test_batch_processing(self, test_config):
        """Test batch processing of multiple images.
        
        Features tested:
        - Batch operations: Process multiple images efficiently
        - Memory cleanup: Verify memory usage between batches
        - Error handling: Handle individual image failures
        """
        # Set cleanup delay to ensure files exist for verification
        test_config.cleanup_delay = 1.0
        
        handler = MediaHandler(test_config)
        test_dir = test_config.atomics_path / "2024/01/15"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test image pairs (source, target)
        image_pairs = []
        initial_memory = get_memory_mb()
        
        # Create 30 test images of varying sizes
        sizes = [(800, 600), (1600, 1200), (2400, 1800)]
        for i in range(30):
            size = sizes[i % len(sizes)]
            source = test_dir / f"test_image_{i}.png"
            target = test_config.jekyll_assets_path / f"test_image_{i}.jpg"
            
            # Create test image with solid color
            img = Image.new('RGB', size, color=f'#{i*8:06x}')
            img.save(str(source))
            img.close()
            image_pairs.append((source, target))
            
            # Force cleanup after creating each image
            gc.collect()
        
        # Process in batches of 5
        processed = handler.process_batch(image_pairs, chunk_size=5)
        
        # Allow memory to stabilize
        time.sleep(0.5)
        gc.collect()
        final_memory = get_memory_mb()
        
        # Verify results
        assert len(processed) == 30, "All images should be processed"
        for path in processed:
            assert path.exists(), f"Processed image should exist: {path}"
            assert path.stat().st_size > 0, f"Processed image should not be empty: {path}"
        
        # Verify memory cleanup (allow for some overhead)
        assert final_memory < initial_memory * 3, "Memory usage should not grow excessively"
    
    def test_batch_error_handling(self, test_config):
        """Test error handling during batch processing.
        
        Features tested:
        - Error handling: Graceful handling of invalid images
        - Batch recovery: Continue processing after errors
        - Cleanup: Proper cleanup of failed operations
        """
        logger = logging.getLogger(__name__)
        
        # Set cleanup delay to ensure files exist for verification
        test_config.cleanup_delay = 1.0
        logger.debug("Test config initialized")
        
        handler = MediaHandler(test_config)
        test_dir = test_config.atomics_path / "2024/01/15"
        test_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created test directory: {test_dir}")
        
        # Create mix of valid and invalid image pairs
        image_pairs = []
        
        # Valid images
        for i in range(5):
            source = test_dir / f"valid_{i}.png"
            target = test_config.jekyll_assets_path / f"valid_{i}.jpg"
            img = Image.new('RGB', (100, 100), color='red')
            img.save(str(source))
            img.close()
            image_pairs.append((source, target))
            logger.debug(f"Created valid image: {source}")
        
        # Invalid images (not actual image files)
        for i in range(3):
            source = test_dir / f"invalid_{i}.png"
            target = test_config.jekyll_assets_path / f"invalid_{i}.jpg"
            # Create an invalid image file (not a PNG)
            source.write_bytes(b'NOT A VALID PNG FILE')
            image_pairs.append((source, target))
            logger.debug(f"Created invalid image: {source}")
        
        logger.debug(f"Created {len(image_pairs)} image pairs")
        
        # Process with error handling
        try:
            logger.debug("Starting batch processing")
            handler.process_batch(image_pairs, chunk_size=2)
            pytest.fail("Expected InvalidImageError but no exception was raised")
        except Exception as e:
            logger.info(f"\nCaught exception: {type(e).__name__} - {str(e)}")
            logger.info(f"Exception hierarchy: {type(e).__mro__}")
            assert isinstance(e, InvalidImageError), f"Expected InvalidImageError but got {type(e).__name__}"
            
            # Check valid images were processed before error
            valid_count = 0
            for i in range(5):
                target = test_config.jekyll_assets_path / f"valid_{i}.jpg"
                if target.exists():
                    valid_count += 1
                    size = target.stat().st_size
                    logger.debug(f"Found valid target: {target} (size={size})")
                    assert size > 0, f"Valid image should not be empty: {target}"
            
            logger.debug(f"Found {valid_count} valid processed images")
            assert valid_count > 0, "Some valid images should be processed before error"
            
            # Check invalid targets don't exist
            for i in range(3):
                invalid_target = test_config.jekyll_assets_path / f"invalid_{i}.jpg"
                exists = invalid_target.exists()
                logger.debug(f"Invalid target {invalid_target} exists: {exists}")
                assert not exists, f"Invalid target should not exist: {invalid_target}"
    
    def test_memory_optimization(self, test_config):
        """Test memory usage during batch processing.
        
        Features tested:
        - Memory usage: Stay within reasonable limits
        - Garbage collection: Effective cleanup between batches
        - Batch sizes: Impact of different batch sizes on memory
        """
        # Set cleanup delay to ensure files exist for verification
        test_config.cleanup_delay = 1.0
        
        handler = MediaHandler(test_config)
        test_dir = test_config.atomics_path / "2024/01/15"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Create large test images
        image_pairs = []
        for i in range(20):
            source = test_dir / f"large_{i}.png"
            target = test_config.jekyll_assets_path / f"large_{i}.jpg"
            
            # Create a large test image (10MB+)
            img = Image.new('RGB', (3000, 2000), color=f'#{i*12:06x}')
            img.save(str(source))
            img.close()
            image_pairs.append((source, target))
            
            # Force cleanup after creating each image
            gc.collect()
        
        # Track memory usage during processing
        initial_memory = get_memory_mb()
        memory_samples = []
        
        # Process in small batches
        chunk_sizes = [2, 5, 10]
        for chunk_size in chunk_sizes:
            # Clear previous results
            for _, target in image_pairs:
                if target.exists():
                    target.unlink()
            
            # Allow memory to stabilize
            gc.collect()
            time.sleep(0.5)
            
            # Process batch
            memory_before = get_memory_mb()
            processed = handler.process_batch(image_pairs, chunk_size=chunk_size)
            
            # Allow memory to stabilize
            gc.collect()
            time.sleep(0.5)
            memory_after = get_memory_mb()
            
            memory_samples.append((chunk_size, abs(memory_after - memory_before)))
            
            # Verify processing
            assert len(processed) == 20, f"All images should be processed with chunk_size={chunk_size}"
            for path in processed:
                assert path.exists(), f"Processed image should exist: {path}"
                assert path.stat().st_size > 0, f"Processed image should not be empty: {path}"
        
        # Verify memory usage patterns
        final_memory = get_memory_mb()
        
        # Memory usage assertions (allow for some overhead)
        assert final_memory < initial_memory * 3, "Memory usage should not grow excessively"
        
        # Memory usage should be measurable for all batch sizes
        for chunk_size, memory_delta in memory_samples:
            assert memory_delta > 0, f"Memory usage for chunk_size={chunk_size} should be measurable"
            assert memory_delta < 100, f"Memory usage for chunk_size={chunk_size} should be reasonable"