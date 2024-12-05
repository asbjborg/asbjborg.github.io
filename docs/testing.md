# Testing Documentation

## Media Handler Tests

### Test Environment Setup
- Using pytest with tmp_path fixture for isolation
- Real vault integration tests using actual paths from `.env`
- Mock data follows actual vault patterns
- Package installed in development mode with `pip install -e .`

### Test Cases & Results

#### 1. Image Processing (✅ DONE)
- **Mock Test**: `test_image_resizing`
  - [x] Max width constraint (1200px)
  - [x] Aspect ratio preservation
  - Status: ✅ PASSED

- **Mock Test**: `test_rgba_conversion`
  - [x] RGBA to RGB conversion
  - [x] White background for transparency
  - Status: ✅ PASSED

- **Mock Test**: `test_format_conversion`
  - [x] Format conversion (PNG → JPEG)
  - [x] File size optimization
  - Status: ✅ PASSED

- **Mock Test**: `test_grayscale_handling`
  - [x] Grayscale to RGB conversion
  - Status: ✅ PASSED

#### 2. Error Handling (✅ DONE)
- **Mock Tests**: Various error cases
  - [x] Corrupted images
  - [x] Empty files
  - [x] Wrong extensions
  - [x] Permission errors
  - [x] Missing files
  - [x] Unsupported formats
  - Status: ✅ ALL PASSED

#### 3. Media References (🔄 IN PROGRESS)
- **Needed Tests**:
  - [x] Extract wikilinks from content
  - [x] Handle various link formats
  - [x] Handle malformed links
  - Lines to cover: 123-134
  - Status: 3/4 tests passing
  - Current Issue:
    ```python
    # Test failing because regex matches regular markdown images
    Old: r'!\[\[(.*?)\]\]'  # Too permissive
    New: r'!\[\[([^[\]]+?)\]\]'  # Only matches valid wikilinks
    ```
  - Fix Applied:
    - Updated regex to exclude regular markdown images
    - Added better pattern documentation
    - Improved validation of extracted paths

#### 4. Jekyll Path Generation (⏳ TODO)
- **Needed Tests**:
  - [ ] Generate valid Jekyll paths
  - [ ] Handle complex filenames
  - [ ] Preserve directory structure
  - Lines to cover: 145-166

#### 5. Content Processing (⏳ TODO)
- **Needed Tests**:
  - [ ] Process markdown content
  - [ ] Update image references
  - [ ] Handle multiple images
  - Lines to cover: 178-212

#### 6. Asset Management (⏳ TODO)
- **Needed Tests**:
  - [ ] Track used assets
  - [ ] Clean up unused files
  - [ ] Handle duplicates
  - Lines to cover: 224-245

#### 7. Bidirectional Sync (⏳ TODO)
- **Needed Tests**:
  - [ ] Sync Jekyll → Obsidian
  - [ ] Handle modified images
  - [ ] Preserve metadata
  - Lines to cover: 257-281

### Current Coverage
- Lines Covered: 66/165 (40%)
- Target: >90%
- Missing Coverage:
  ```
  Name                                    Stmts   Miss  Cover   Missing
  ---------------------------------------------------------------------
  scripts/sync_engine/handlers/media.py     165     99    40%   
  - Media references: 98-101, 123-134
  - Jekyll paths: 145-166
  - Content processing: 178-212
  - Asset cleanup: 224-245
  - Sync back: 257-281, 290-298, 310-331
  ```

### Next Steps
1. Create test files:
   - `test_media_references.py`
   - `test_media_paths.py`
   - `test_media_content.py`
   - `test_media_assets.py`
   - `test_media_sync.py`

2. Add test fixtures:
   - Sample markdown content
   - Various wikilink formats
   - Complex directory structures
   - Modified image scenarios

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

3. Error Handling
   - Issue: Exceptions not propagating correctly
   - Solution:
     1. Create custom exceptions in `exceptions.py`
     2. Use specific exceptions for each error case
     3. Let certain errors (like FileNotFoundError) propagate

### Running Tests
```bash
# Run all media tests
python -m pytest scripts/sync_engine/tests/test_media_*.py -v

# Run specific test
python -m pytest scripts/sync_engine/tests/test_media_processing.py::test_image_resizing -v

# Run with coverage
python -m pytest scripts/sync_engine/tests/test_media_*.py -v --cov=sync_engine.handlers.media --cov-report=term-missing
``` 