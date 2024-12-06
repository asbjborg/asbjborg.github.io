# Testing Guide

## Overview
The sync engine uses pytest for testing and follows a comprehensive testing strategy covering unit tests, integration tests, and end-to-end scenarios.

## File Structure

```
tests/
├── conftest.py         # Shared fixtures
├── requirements.py     # Test requirements system
├── test_all.py         # Main test runner
├── test_media.py       # Media test collector
├── test_sync.py        # Sync test collector
├── test_handlers.py    # Handler test collector
├── sync/
│   ├── test_basic.py     # Basic sync tests
│   ├── test_sync_errors.py     # Error handling
│   ├── test_cleanup.py   # Cleanup tests
│   ├── test_media.py     # Media sync tests
│   ├── test_paths.py     # Path handling
│   ├── test_sync_performance.py # Performance tests
│   ├── test_paths_requirements.yaml      # Path test requirements
│   └── test_sync_performance_requirements.yaml  # Performance test requirements
├── media/
│   ├── test_processing.py # Image processing
│   ├── test_references.py # Media references
│   ├── test_media_errors.py     # Media error cases
│   └── test_media_performance.py # Media performance tests
└── handlers/
    ├── test_post.py      # Post handler tests
    └── test_media.py     # Media handler tests
```

## Test Requirements

### Overview
Each test module can have an accompanying YAML file that defines its requirements, edge cases, and dependencies. This helps with:
- Documenting test coverage
- Tracking dependencies between components
- Ensuring edge cases are tested
- Maintaining test quality

### Requirements File Structure
```yaml
test_name:
  features:
    - "Feature 1"
    - "Feature 2"
  edge_cases:
    - "Edge case 1"
    - "Edge case 2"
  dependencies:
    - "Component 1"
    - "Component 2"
  expected_coverage: 85.0
  description: >
    Detailed description of what the test covers
    and why it's important.
```

### Using Requirements
Requirements can be specified in two ways:

1. YAML File:
```yaml
# test_module_requirements.yaml
test_complex_paths:
  features: ["Path normalization", "Unicode handling"]
  edge_cases: ["Very long filenames", "Special characters"]
  dependencies: ["PostHandler", "MediaHandler"]
  expected_coverage: 90.0
  description: "Tests complex path handling scenarios"
```

2. Decorator:
```python
@test_requirements(
    features=["Path normalization", "Unicode handling"],
    edge_cases=["Very long filenames", "Special characters"],
    dependencies=["PostHandler", "MediaHandler"],
    expected_coverage=90.0,
    description="Tests complex path handling scenarios"
)
def test_complex_paths():
    # Test implementation
```

### Running Tests with Requirements
```bash
# Run tests for a specific feature
pytest -m "requirement('Path normalization')"

# Run tests with specific dependencies
pytest -m "requirement('PostHandler')"
```

## Running Tests

### Basic Usage
```bash
# Run all tests
pytest tests/

# Run specific test category
pytest tests/test_core.py   # All core tests
pytest tests/test_sync.py   # All sync tests
pytest tests/test_media.py  # All media tests
pytest tests/test_handlers.py # All handler tests

# Run specific test module
pytest tests/sync/test_basic.py
pytest tests/media/test_processing.py

# Run with coverage
pytest --cov=sync_engine tests/
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