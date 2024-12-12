# Obsidian to Jekyll Sync

A simple and robust sync engine to publish Obsidian notes to a Jekyll blog.

## Features

- One-way sync from Obsidian to Jekyll
- Automated file watching with batched updates
- Smart path conversion for images
- SQLite-based file mapping
- Template-based configuration

## Requirements

- Python 3.8 or higher
- fswatch (for file monitoring)
- Jekyll site using Chirpy theme

## Quick Start

### 1. Fork and setup

First, fork this repository to create your own copy. Then:

```bash
git clone https://github.com/your-username/obsidian-jekyll-sync.git
cd obsidian-jekyll-sync
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
./scripts/setup.sh
# Edit .env with your paths
```

### 3. Start sync

```bash
./scripts/sync_control.sh start
```

## Documentation

- [Usage Guide](docs/usage.md)
- [Implementation Details](docs/implementation.md)

## License

MIT License - see [LICENSE](LICENSE) for details
