# Testing Guide

## Overview
The sync engine uses pytest for testing and follows a comprehensive testing strategy covering unit tests, integration tests, and end-to-end scenarios.

## Test Structure

```
scripts/sync_engine/tests/
├── test_sync.py       # Integration tests
├── test_changes.py    # Change detection tests
├── test_atomic.py     # Atomic operations tests
├── test_post.py       # Post handling tests
└── test_media.py      # Media handling tests
```

## Running Tests

### Basic Usage
```bash
# Run all tests
pytest scripts/sync_engine/tests/

# Run specific test file
pytest scripts/sync_engine/tests/test_changes.py

# Run with coverage
pytest --cov=sync_engine scripts/sync_engine/tests/
```

### Test Categories

#### 1. Change Detection Tests
Tests in `test_changes.py`:
- Post detection by status
- Date path extraction
- Complex filenames
- Error handling
- Performance testing

#### 2. Integration Tests
Tests in `test_sync.py`:
- Full sync cycles
- Bidirectional updates
- Conflict resolution
- Error recovery

#### 3. Performance Tests
- Large vault scanning (>1000 files)
- Multiple date folders
- Many images per post
- Memory usage monitoring

## Test Fixtures

### Basic Vault Setup
```python
@pytest.fixture
def setup_test_vault(tmp_path):
    """Create test vault with realistic structure"""
    vault = tmp_path / 'vault'
    jekyll = tmp_path / 'jekyll'
    
    # Create date folders
    date_path = vault / 'atomics/2024/01/15'
    date_path.mkdir(parents=True)
    
    return vault, jekyll, date_path
```

## Writing Tests

### Test Guidelines
1. Use descriptive test names
2. Test one thing per test
3. Use proper fixtures
4. Handle cleanup properly
5. Document complex scenarios

### Example Test
```python
def test_post_detection(setup_test_vault):
    """Test post detection by frontmatter status"""
    vault, jekyll, date_path = setup_test_vault
    
    # Create test post
    (date_path / 'test.md').write_text("""---
status: published
---
Test content""")
    
    detector = ChangeDetector({
        'vault_root': str(vault),
        'jekyll_root': str(jekyll)
    })
    
    states = detector._get_obsidian_states()
    assert len(states) == 1
```

## Coverage Requirements
- Core modules: >90% coverage
- Handlers: >85% coverage
- Integration tests: >80% coverage

## Common Test Scenarios
1. Valid post detection
2. Invalid frontmatter handling
3. Complex filenames
4. Permission issues
5. Path validation
6. Date format validation
7. Performance with large datasets 