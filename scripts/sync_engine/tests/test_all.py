"""Main test collector - imports all test categories"""

# Core tests
from sync_engine.tests.test_core import (
    TestAtomicOperations,
    TestChangeDetection,
    TestConfigHandling
)

# Media tests
from sync_engine.tests.test_media import (
    TestMediaProcessing,
    TestMediaSync,
    TestMediaReferences,
    TestMediaErrors,
    TestMediaPerformance
)

# Sync tests
from sync_engine.tests.test_sync import (
    TestBasicSync,
    TestSyncErrors,
    TestSyncCleanup,
    TestSyncMedia,
    TestSyncPaths,
    TestSyncPerformance
)

# Handler tests
from sync_engine.tests.test_handlers import TestPostHandling

# This file serves as the main collector of all tests
# Running this file will run the complete test suite 