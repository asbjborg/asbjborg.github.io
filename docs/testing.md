# Testing Documentation

## Media Handler Tests

### Test Environment Setup
- Using pytest with tmp_path fixture for isolation
- Real vault integration tests using actual paths from `.env`
- Mock data follows actual vault patterns

### Test Cases & Results

#### 1. Absolute Path Resolution
- **Mock Test**: `test_absolute_path_resolution`
  - [ ] Resolves absolute vault paths
  - [ ] Handles non-existent files gracefully
  - [ ] Preserves case sensitivity
  - Expected patterns:
    ```python
    # Input: atomics/2024/12/03/image.png
    # Expected: /full/path/to/vault/atomics/2024/12/03/image.png
    ```

#### 2. Frontmatter Image Handling
- **Mock Test**: `test_image_frontmatter_handling`
  - [ ] Extracts image paths from frontmatter
  - [ ] Handles wikilink syntax
  - [ ] Preserves original paths
  - Expected patterns:
    ```yaml
    image: ![[atomics/2024/12/03/Pasted image 20241203214844.png]]
    ```

#### 3. Path Sanitization
- **Mock Test**: `test_path_sanitization`
  - [ ] Handles spaces in filenames
  - [ ] Preserves directory structure
  - [ ] Generates valid Jekyll paths
  - Expected patterns:
    ```python
    # Input: atomics/2024/12/03/My Cool Image.png
    # Expected: atomics-2024-12-03-my-cool-image-[hash].png
    ```

#### 4. Bidirectional Sync
- **Mock Test**: `test_bidirectional_sync`
  - [ ] Syncs Obsidian → Jekyll
  - [ ] Syncs Jekyll → Obsidian
  - [ ] Preserves file integrity
  - Expected patterns:
    ```python
    # Original: atomics/2024/12/03/image.png
    # Jekyll: /assets/img/posts/atomics-2024-12-03-image-[hash].png
    # Sync back: Should match original
    ```

#### 5. Real Vault Integration
- **Integration Test**: `test_real_vault_paths`
  - [ ] Resolves actual vault paths
  - [ ] Handles real image files
  - [ ] Generates correct Jekyll paths
  - Expected patterns:
    ```python
    # Using actual image from vault
    # atomics/2024/12/03/Pasted image 20241203214844.png
    ```

### Common Issues & Solutions
1. Path Resolution
   - Issue: ...
   - Solution: ...

2. File Handling
   - Issue: ...
   - Solution: ...

### Test Coverage Goals
- [ ] >90% coverage for media handler
- [ ] All edge cases covered
- [ ] Real vault scenarios tested

### Running Tests
```bash
# Run all media tests
python -m pytest scripts/sync_engine/tests/test_media_sync.py -v

# Run specific test
python -m pytest scripts/sync_engine/tests/test_media_sync.py::test_real_vault_paths -v

# Run with coverage
python -m pytest --cov=sync_engine.handlers.media scripts/sync_engine/tests/test_media_sync.py
``` 