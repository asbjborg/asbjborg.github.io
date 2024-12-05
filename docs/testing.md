# Testing Documentation

## Media Handler Tests

### Test Environment Setup
- Using pytest with tmp_path fixture for isolation
- Real vault integration tests using actual paths from `.env`
- Mock data follows actual vault patterns
- Package installed in development mode with `pip install -e .`

### Test Cases & Results

#### 1. Absolute Path Resolution
- **Mock Test**: `test_absolute_path_resolution`
  - [x] Resolves absolute vault paths
  - [x] Handles non-existent files gracefully
  - [x] Preserves case sensitivity
  - Expected patterns:
    ```python
    # Input: atomics/2024/12/03/image.png
    # Expected: /full/path/to/vault/atomics/2024/12/03/image.png
    ```
  - Status: ✅ PASSED

#### 2. Frontmatter Image Handling
- **Mock Test**: `test_image_frontmatter_handling`
  - [x] Extracts image paths from frontmatter
  - [x] Handles wikilink syntax
  - [x] Preserves original paths
  - Expected patterns:
    ```yaml
    image: ![[atomics/2024/12/03/Pasted image 20241203214844.png]]
    ```
  - Status: ✅ PASSED

#### 3. Path Sanitization
- **Mock Test**: `test_path_sanitization`
  - [x] Handles spaces in filenames
  - [x] Preserves directory structure
  - [x] Generates valid Jekyll paths
  - Expected patterns:
    ```python
    # Input: atomics/2024/12/03/My Cool Image.png
    # Expected: atomics-2024-12-03-my-cool-image-[hash].png
    ```
  - Status: ✅ PASSED

#### 4. Bidirectional Sync
- **Mock Test**: `test_bidirectional_sync`
  - [x] Syncs Obsidian → Jekyll
  - [x] Syncs Jekyll → Obsidian
  - [x] Preserves file integrity
  - Expected patterns:
    ```python
    # Original: atomics/2024/12/03/image.png
    # Jekyll: /assets/img/posts/atomics-2024-12-03-image-[hash].png
    # Sync back: Should match original
    ```
  - Status: ✅ PASSED

#### 5. Real Vault Integration
- **Integration Test**: `test_real_vault_paths`
  - [x] Resolves actual vault paths
  - [x] Handles real image files
  - [x] Generates correct Jekyll paths
  - Expected patterns:
    ```python
    # Using actual image from vault
    # atomics/2024/12/03/Pasted image 20241203214844.png
    ```
  - Status: ✅ PASSED
  - Note: Test requires correct vault path in .env pointing to actual Obsidian vault

### Test Results

#### Image Processing Tests
- ✅ Image resizing works correctly
- ✅ RGBA to RGB conversion works
- ✅ Format conversion and optimization works
- ❌ Grayscale to RGB conversion fails
  - Issue: Images stay in grayscale mode
  - Fix needed in `process_image()` to force RGB conversion

#### Error Handling Tests
- ✅ Permission errors handled correctly
- ✅ Missing files handled correctly
- ❌ Corrupted images not handled strictly
- ❌ Empty files not rejected
- ❌ Wrong extensions not validated
  - Issue: MediaHandler logs errors but doesn't raise exceptions
  - Fix needed to validate files before processing
  - Need to add proper exception types

### Common Issues & Solutions
1. Package Import Error
   - Issue: `ModuleNotFoundError: No module named 'sync_engine'`
   - Solution: 
     1. Create `pyproject.toml` with correct package structure
     2. Add `pythonpath = ["scripts"]` to pytest config
     3. Install package in dev mode with `pip install -e .`
     4. Ensure `__init__.py` exists in all package directories

2. Build System Error
   - Issue: `ERROR: neither 'setup.py' nor 'pyproject.toml' found`
   - Solution:
     1. Create `pyproject.toml` with build system config:
        ```toml
        [build-system]
        requires = ["hatchling"]
        build-backend = "hatchling.build"
        ```
     2. Install build dependency: `pip install hatchling`

3. Real Vault Integration
   - Issue: `Could not resolve media reference: atomics/2024/12/03/Pasted image 20241203214844.png`
   - Solution:
     1. Check if image exists: `ls -l $VAULT_ROOT/atomics/2024/12/03/`
     2. Verify .env VAULT_ROOT points to actual Obsidian vault
     3. Ensure test image path matches real vault structure

### Test Coverage Results
- Current Coverage: 50%
- Missing Coverage Areas:
  1. Image Processing (lines 53-76)
     - [ ] Test image resizing
     - [ ] Test format conversion
     - [ ] Test optimization settings
  
  2. Error Handling (lines 94-105)
     - [ ] Test invalid file types
     - [ ] Test corrupted images
     - [ ] Test permission errors
  
  3. Path Resolution Edge Cases (lines 123-137)
     - [ ] Test Unicode filenames
     - [ ] Test very long paths
     - [ ] Test special characters
  
  4. Asset Management (lines 228-252)
     - [ ] Test cleanup of unused assets
     - [ ] Test duplicate handling
     - [ ] Test asset tracking
  
  5. Sync Edge Cases (lines 261-269)
     - [ ] Test concurrent modifications
     - [ ] Test partial sync failures
     - [ ] Test recovery scenarios

### Next Steps
1. Create additional test files:
   - `test_media_processing.py` - Image processing tests
   - `test_media_errors.py` - Error handling tests
   - `test_media_edge_cases.py` - Edge case tests
   - `test_media_assets.py` - Asset management tests

2. Add test fixtures:
   - Sample images in various formats
   - Corrupted image files
   - Unicode and special character filenames
   - Mock file system for edge cases

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