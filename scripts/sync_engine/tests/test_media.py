"""Media handling tests - imports all media test files"""

from sync_engine.tests.media.test_processing import TestMediaProcessing
from sync_engine.tests.media.test_sync import TestMediaSync
from sync_engine.tests.media.test_references import TestMediaReferences
from sync_engine.tests.media.test_errors import TestMediaErrors
from sync_engine.tests.media.test_performance import TestMediaPerformance

# This file serves as a collector of all media-related tests
# Each test class is defined in its own file for better organization
# Running this file will run all media tests 