"""Core functionality tests - imports all core test files"""

from sync_engine.tests.core.test_atomic import TestAtomicOperations
from sync_engine.tests.core.test_changes import TestChangeDetection
from sync_engine.tests.core.test_config import TestConfigHandling

# This file serves as a collector of all core-related tests
# Each test class is defined in its own file for better organization
# Running this file will run all core tests 