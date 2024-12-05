# Testing Documentation

## Test Coverage

### Media Handling (100%)
- [x] Image processing and optimization
- [x] Error handling for invalid/corrupted images
- [x] Media reference extraction
- [x] Jekyll path generation
- [x] Bidirectional media sync

### Bidirectional Sync (100%)
- [x] Obsidian to Jekyll sync
  - [x] Post conversion
  - [x] Image processing
  - [x] Path resolution
  - [x] Status handling (published/draft/private)

- [x] Jekyll to Obsidian sync
  - [x] Post conversion
  - [x] Image processing
  - [x] Path resolution
  - [x] Frontmatter handling

- [x] Conflict Resolution
  - [x] Timestamp-based resolution
  - [x] Frontmatter modification time
  - [x] File modification time fallback

### Core Engine (75%)
- [x] File change detection
  - [x] New file detection
  - [x] Modified file detection
  - [x] Deleted file detection
  - [x] Status change detection
  - [x] Multiple change detection
- [ ] Atomic operations
- [ ] Configuration handling
- [ ] Error recovery

### End-to-End Tests (Planned)
- [ ] Full sync cycle
- [ ] Migration process
- [ ] Performance testing
- [ ] Real vault data

## Test Files

- `test_media_processing.py`: Image optimization and processing
- `test_media_errors.py`: Error handling for media files
- `test_media_references.py`: Wikilink extraction and conversion
- `test_jekyll_paths.py`: Path generation and resolution
- `test_bidirectional_sync.py`: Core sync functionality
  - Obsidian to Jekyll sync
  - Jekyll to Obsidian sync
  - Conflict resolution
  - Status handling
- `test_file_changes.py`: Change detection
  - New/modified/deleted files
  - Status changes
  - Multiple changes

## Running Tests

```bash
# Run all tests
python -m pytest scripts/sync_engine/tests/

# Run specific test file
python -m pytest scripts/sync_engine/tests/test_bidirectional_sync.py

# Run with coverage
python -m pytest --cov=sync_engine scripts/sync_engine/tests/
```

## Current Coverage: 75%

### High Coverage Areas
- Media handling (100%)
- Bidirectional sync (100%)
- Path resolution (100%)
- File change detection (100%)

### Areas Needing Coverage
- Atomic operations
- Configuration handling
- Error recovery
- End-to-end workflows