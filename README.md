# Jekyll-Obsidian Sync

A bidirectional sync engine for Obsidian PKM and Jekyll blog posts. Keep your Obsidian vault and Jekyll blog in sync with automatic conversion of frontmatter, image paths, and more.

## Features

- **Bidirectional Sync**
  - Obsidian → Jekyll: Convert published notes to blog posts
  - Jekyll → Obsidian: Import blog posts into your vault
  - Smart conflict resolution based on modification time

- **Asset Handling**
  - Automatic image path conversion
  - Asset file normalization
  - Proper path handling in both environments

- **Frontmatter Support**
  - Status-based publishing (published/draft)
  - Time format conversion
  - Tag filtering
  - Wikilink handling

- **Safety Features**
  - Dry run mode to preview changes
  - Automatic backups with rotation
  - Detailed logging
  - Error handling

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up your environment:
   ```bash
   export PKM_ROOT=/path/to/obsidian/vault
   export JEKYLL_ROOT=/path/to/jekyll/site
   ```

3. Run the sync:
   ```bash
   # Preview changes with dry run
   python scripts/sync.py --dry-run

   # Run the actual sync
   python scripts/sync.py
   ```

## Documentation

- [Usage Guide](docs/usage.md) - Detailed usage instructions
- [Development Guide](docs/development.md) - Development setup and contribution
- [API Documentation](docs/api.md) - API reference

## Requirements

- Python 3.8+
- python-frontmatter
- pathlib
- typing

## License

MIT License - See [LICENSE](LICENSE) for details
