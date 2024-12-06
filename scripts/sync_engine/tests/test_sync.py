"""Sync functionality tests - imports all sync test files"""

from sync_engine.tests.sync.test_basic import TestBasicSync
from sync_engine.tests.sync.test_errors import TestSyncErrors
from sync_engine.tests.sync.test_cleanup import TestSyncCleanup
from sync_engine.tests.sync.test_media import TestSyncMedia
from sync_engine.tests.sync.test_paths import TestSyncPaths
from sync_engine.tests.sync.test_performance import TestSyncPerformance

# This file serves as a collector of all sync-related tests
# Each test class is defined in its own file for better organization
# Running this file will run all sync tests 