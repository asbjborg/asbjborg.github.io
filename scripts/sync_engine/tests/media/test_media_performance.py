"""Tests for media handling performance.

This module tests:
- Performance optimization (timing and benchmarking)
- Memory usage (resource tracking)
- Image processing (format conversion)
"""

import pytest
import time
import psutil
import os
import gc
from contextlib import contextmanager
from typing import Dict, Any
from pathlib import Path
from PIL import Image
from sync_engine.handlers.media import MediaHandler

class PerformanceMetrics:
    """Helper class to track performance metrics"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.get_memory_usage()
        self.peak_memory = self.initial_memory
        self.start_time = time.time()
        self.operation_times: Dict[str, float] = {}
        self.operation_memory: Dict[str, float] = {}
    
    def get_memory_usage(self) -> int:
        """Get current memory usage in bytes"""
        return self.process.memory_info().rss
    
    def update_peak_memory(self):
        """Update peak memory usage"""
        current = self.get_memory_usage()
        self.peak_memory = max(self.peak_memory, current)
        return current
    
    @contextmanager
    def track_operation(self, name: str):
        """Track time and memory for an operation"""
        gc.collect()  # Clean up before measuring
        start_mem = self.get_memory_usage()
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            end_mem = self.update_peak_memory()
            self.operation_times[name] = duration
            self.operation_memory[name] = end_mem - start_mem
    
    def print_metrics(self, total_files: int):
        """Print performance metrics"""
        duration = time.time() - self.start_time
        memory_used = self.peak_memory - self.initial_memory
        
        print(f"\nPerformance metrics:")
        print(f"Total time: {duration:.2f} seconds")
        print(f"Peak memory: {memory_used / 1024 / 1024:.2f} MB")
        print(f"Files processed: {total_files}")
        print(f"Processing rate: {total_files / duration:.2f} files/second")
        print("\nOperation breakdown:")
        for op, time_taken in self.operation_times.items():
            mem_used = self.operation_memory[op] / 1024 / 1024
            print(f"- {op}:")
            print(f"  Time: {time_taken:.2f}s")
            print(f"  Memory: {mem_used:.2f} MB")

class TestMediaPerformance:
    """Tests for media handling performance"""
    
    def test_many_images(self, test_config):
        """Test handling many images in a post.
        
        Features tested:
        - Image processing: Format conversion and optimization
        - Memory usage: Per-operation tracking
        - Performance: Operation timing
        """
        metrics = PerformanceMetrics()
        handler = MediaHandler(test_config)
        post_path = test_config.atomics_path / "2024/01/15/many_images.md"
        
        with metrics.track_operation("setup"):
            post_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create multiple image references
            image_refs = []
            for i in range(10):
                image_refs.append(f"![[atomics/2024/01/15/img_{i}.png]]")
            
            post_content = "---\nstatus: published\n---\n# Many Images\n\n" + "\n".join(image_refs)
            post_path.write_text(post_content)
        
        # Create and process images
        with metrics.track_operation("image_processing"):
            for i in range(10):
                img = Image.new('RGB', (100, 100), color='red')
                img_path = post_path.parent / f"img_{i}.png"
                img.save(img_path)
                img.close()
                
                target = test_config.jekyll_assets_path / f"img_{i}.jpg"
                handler.process_image(img_path, target)
        
        metrics.print_metrics(total_files=11)  # 1 post + 10 images
