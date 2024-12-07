# Development Guide

## Table of Contents

1. [Development Setup](#development-setup)
2. [Project Structure](#project-structure)
3. [Testing](#testing)
4. [Contributing](#contributing)
5. [Code Style](#code-style)

## Development Setup

1. Clone and setup:
   ```bash
   git clone https://github.com/asbjborg/jekyll-obsidian-sync.git
   cd jekyll-obsidian-sync
   pip install -r requirements.txt
   ```

2. Set up test environment:
   ```bash
   # Create test directories
   mkdir -p test_pkm/atomics
   mkdir -p test_jekyll/_posts
   mkdir -p test_jekyll/assets/img/posts
   
   # Set environment variables
   export PKM_ROOT=test_pkm
   export JEKYLL_ROOT=test_jekyll
   export SYNC_DEBUG=true
   ```

## Project Structure

```
.
├── scripts/
│   ├── sync/               # Core sync functionality
│   │   ├── sync.py        # Main sync engine
│   │   └── file_handler.py # File operations
│   ├── utils/             # Utility modules
│   │   ├── backup.py      # Backup functionality
│   │   ├── frontmatter.py # Frontmatter handling
│   │   └── path_converter.py # Path conversion
│   └── normalize_assets.py # Asset normalization
├── docs/                  # Documentation
├── tests/                 # Test files
└── requirements.txt       # Dependencies
```

### Key Components

1. **Sync Engine** (`sync.py`)
   - Main sync logic
   - Conflict resolution
   - Error handling

2. **File Handler** (`file_handler.py`)
   - File operations
   - Directory scanning
   - File type detection

3. **Path Converter** (`path_converter.py`)
   - Path format conversion
   - Image path handling
   - Wikilink processing

4. **Frontmatter Handler** (`frontmatter.py`)
   - Frontmatter parsing
   - Format conversion
   - Tag filtering

5. **Backup Handler** (`backup.py`)
   - Backup creation
   - Rotation handling
   - Directory management

## Testing

### Running Tests

Run all tests:
```bash
python -m pytest scripts/test_*.py -v
```

Run specific test:
```bash
python scripts/test_sync.py
python scripts/test_backup.py
python scripts/test_frontmatter.py
```

### Test Structure

Each component has a corresponding test file:
- `test_sync.py` - Sync engine tests
- `test_backup.py` - Backup functionality tests
- `test_frontmatter.py` - Frontmatter handling tests
- `test_path_converter.py` - Path conversion tests

### Test Guidelines

1. **Use Standardized Test Cases**
   - Create test files programmatically
   - Clean up after tests
   - Use consistent test data

2. **Test Edge Cases**
   - Missing files/directories
   - Invalid frontmatter
   - Special characters in paths
   - Conflicting timestamps

3. **Test Dry Run Mode**
   - Verify no changes in dry run
   - Check correct action reporting
   - Test with various scenarios

## Contributing

### Development Workflow

1. Create feature branch:
   ```bash
   git checkout -b feature/name-v2
   ```

2. Update checklist:
   - Add tasks to `docs/strategy/implementation/checklist.json`
   - Track progress

3. Implement changes:
   - Add tests first
   - Implement feature
   - Update documentation

4. Submit PR:
   - Update checklist
   - Add test results
   - Document changes

### Code Guidelines

1. **Error Handling**
   - Use custom exceptions
   - Add debug logging
   - Provide clear error messages

2. **Testing**
   - Add tests for new features
   - Update existing tests
   - Test edge cases

3. **Documentation**
   - Update relevant docs
   - Add docstrings
   - Include examples

## Code Style

### Python Style

- Follow PEP 8
- Use type hints
- Add docstrings
- Keep functions focused

### Naming Conventions

- Classes: `PascalCase`
- Functions: `snake_case`
- Constants: `UPPER_CASE`
- Private methods: `_leading_underscore`

### Comments

- Add docstrings to all public functions
- Explain complex logic
- Document assumptions
- Note edge cases

### Example

```python
class PathConverter:
    """Converts paths between Obsidian and Jekyll formats."""
    
    def __init__(self, vault_root: str, jekyll_root: str, debug: bool = False):
        """Initialize path converter.
        
        Args:
            vault_root: Root directory of Obsidian vault
            jekyll_root: Root directory of Jekyll site
            debug: Enable debug logging
        """
        self.vault_root = Path(vault_root)
        self.jekyll_root = Path(jekyll_root)
        self.debug = debug
    
    def convert_path(self, path: Path) -> Path:
        """Convert path between formats.
        
        Handles:
        - Wikilinks
        - Image paths
        - Special characters
        
        Args:
            path: Path to convert
            
        Returns:
            Converted path
            
        Raises:
            ValueError: If path format is invalid
        """
        # Implementation
        pass
``` 