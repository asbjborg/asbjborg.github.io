"""Media functionality tests - imports all media test files.

This module collects:
- Media processing tests (image resizing, format conversion)
- Media reference tests (path handling, frontmatter)
- Media error tests (invalid files, references)
- Media performance tests (batch operations, memory usage)

Features tested across all media modules:
- Image processing and optimization
- Path handling and validation
- Error handling and recovery
- Performance and resource usage
"""

from sync_engine.tests.media.test_processing import TestMediaProcessing
from sync_engine.tests.media.test_references import TestMediaReferences
from sync_engine.tests.media.test_media_errors import TestMediaErrors
from sync_engine.tests.media.test_media_performance import TestMediaPerformance
from sync_engine.tests.media.test_batch_processing import TestMediaBatchProcessing

# This file serves as a collector of all media-related tests
# Each test class is defined in its own file for better organization
# Running this file will run all media tests 