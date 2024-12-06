# Testing Guide

## Overview
The sync engine uses pytest for testing and follows a comprehensive testing strategy covering unit tests, integration tests, and end-to-end scenarios.

## Test Structure

```
scripts/sync_engine/tests/
├── test_all.py              # Main test collector
├── test_core.py             # Core test collector
├── test_handlers.py         # Handlers test collector
├── test_sync.py             # Sync test collector
├── test_media.py            # Media test collector
├── conftest.py             # Shared fixtures
│
├── core/                   # Core test modules
│   ├── test_atomic.py     # Atomic operations
│   ├── test_changes.py    # Change detection
│   └── test_config.py     # Configuration handling
│
├── handlers/               # Handler test modules
│   └── test_post.py       # Post handling
│
├── sync/                   # Sync test modules
│   ├── test_basic.py      # Basic sync operations
│   ├── test_errors.py     # Error handling
│   ├── test_cleanup.py    # Cleanup operations
│   ├── test_media.py      # Media handling in sync
│   ├── test_paths.py      # Path handling
│   └── test_performance.py # Performance tests
│
└── media/                  # Media test modules
    ├── test_processing.py # Image processing
    ├── test_sync.py       # Media sync operations
    ├── test_references.py # Media reference handling
    ├── test_errors.py     # Media error cases
    └── test_performance.py # Media performance tests
```

## Running Tests

### Basic Usage
```bash
# Run all tests
pytest scripts/sync_engine/tests/

# Run specific test category
pytest scripts/sync_engine/tests/test_core.py   # All core tests
pytest scripts/sync_engine/tests/test_sync.py   # All sync tests
pytest scripts/sync_engine/tests/test_media.py  # All media tests
pytest scripts/sync_engine/tests/test_handlers.py # All handler tests

# Run specific test module
pytest scripts/sync_engine/tests/sync/test_basic.py
pytest scripts/sync_engine/tests/media/test_processing.py

# Run with coverage
pytest --cov=sync_engine scripts/sync_engine/tests/
```

### Test Categories

#### 1. Sync Tests
Tests in `sync/` directory:
- Basic sync operations and engine initialization
- Error handling and rollback
- Cleanup functionality
- Media handling during sync
- Atomic operations
- Path handling
- Performance testing

#### 2. Media Tests
Tests in `media/` directory:
- Image processing and conversion
- Media sync operations
- Media reference handling
- Error cases
- Performance testing

## Test Fixtures

### Basic Config Setup
```python
@pytest.fixture
def test_config(tmp_path):
    """Create test configuration"""
    vault_root = tmp_path / 'vault'
    jekyll_root = tmp_path / 'jekyll'
    vault_root.mkdir(parents=True)
    jekyll_root.mkdir(parents=True)
    (jekyll_root / 'assets' / 'img' / 'posts').mkdir(parents=True)

    return ConfigManager.load_from_dict({
        'vault_root': vault_root,
        'jekyll_root': jekyll_root,
        'vault_atomics': 'atomics',
        'jekyll_posts': '_posts',
        'jekyll_assets': 'assets/img/posts',
        'debug': True  # Enable debug logging for tests
    })
```

## Writing Tests

### Test Guidelines
1. Use descriptive test names
2. Test one thing per test
3. Use proper fixtures
4. Handle cleanup properly
5. Document complex scenarios
6. Place tests in appropriate subdirectory
7. Import test classes in collector files

### Example Test
```python
# In sync/test_basic.py
class TestBasicSync:
    """Tests for basic sync functionality"""
    
    def test_basic_sync(self, test_config, setup_dirs):
        """Test basic sync operation"""
        vault_root, jekyll_path, atomic_path = setup_dirs
        
        # Create test post
        post_path = atomic_path / "test.md"
        post_path.write_text("""---
status: published
---
Test content""")
        
        # Run sync
        manager = SyncManager(test_config)
        changes = manager.sync()
        
        # Verify changes
        assert len(changes) == 1
        assert (jekyll_path / '_posts/test.md').exists()
```

## Coverage Requirements
- Core modules: >90% coverage
- Handlers: >85% coverage
- Integration tests: >80% coverage

## Common Test Scenarios
1. Basic sync operations
2. Error handling
3. Media processing
4. Path handling
5. Performance testing
6. Atomic operations
7. Cleanup operations