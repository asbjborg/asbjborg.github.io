"""Main test collector - imports all test categories.

This module organizes:
- Core tests (atomic operations, change detection, config)
- Media tests (processing, references, errors, performance)
- Sync tests (basic, errors, cleanup, paths, performance)
- Handler tests (post handling)

Test organization follows:
- Logical grouping by component
- Clear separation of concerns
- Focused test categories
- Comprehensive coverage
"""

# Core tests
from sync_engine.tests.test_core import (
    TestAtomicOperations,  # Atomic file operations
    TestChangeDetection,   # File change tracking
    TestConfigHandling     # Configuration management
)

# Media tests
from sync_engine.tests.test_media import (
    TestMediaProcessing,   # Image processing and optimization
    TestMediaReferences,   # Media path and reference handling
    TestMediaErrors,       # Error cases and validation
    TestMediaPerformance   # Performance and resource usage
)

# Sync tests
from sync_engine.tests.test_sync import (
    TestBasicSync,         # Basic sync functionality
    TestSyncErrors,        # Error handling and recovery
    TestSyncCleanup,       # Resource cleanup
    TestSyncMedia,         # Media synchronization
    TestSyncPaths,         # Path handling and normalization
    TestSyncPerformance    # Performance and scaling
)

# Handler tests
from sync_engine.tests.test_handlers import TestPostHandling  # Post processing and validation

# This file serves as the main collector of all tests
# Running this file will run the complete test suite 