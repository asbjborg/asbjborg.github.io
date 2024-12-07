# Usage Guide

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Basic Usage](#basic-usage)
4. [Advanced Usage](#advanced-usage)
5. [Troubleshooting](#troubleshooting)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/asbjborg/jekyll-obsidian-sync.git
   cd jekyll-obsidian-sync
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### Environment Variables

Set the following environment variables:

```bash
# Required
export PKM_ROOT=/path/to/obsidian/vault
export JEKYLL_ROOT=/path/to/jekyll/site

# Optional
export SYNC_DEBUG=true        # Enable debug logging
export SYNC_MAX_BACKUPS=5     # Number of backups to keep
```

### Obsidian Setup

1. Create an `atomics` folder in your vault for blog posts
2. Add frontmatter to posts you want to sync:
   ```yaml
   ---
   title: My Blog Post
   status: published  # or draft
   tags: [blog, tech]
   image: "[[path/to/header.png]]"  # Optional header image
   ---
   ```

### Jekyll Setup

Ensure your Jekyll site has:
1. A `_posts` directory for blog posts
2. An `assets/img/posts` directory for images

## Basic Usage

### Dry Run

Always start with a dry run to preview changes:

```bash
python scripts/sync.py --dry-run
```

This will show what would be synced without making any changes.

### Full Sync

Run the sync:

```bash
python scripts/sync.py
```

This will:
1. Sync published Obsidian posts to Jekyll
2. Sync Jekyll posts back to Obsidian
3. Convert image paths and copy images
4. Create backups before changes

### Backup Only

Create backups without syncing:

```bash
python scripts/backup.py
```

### Asset Normalization

Normalize image filenames:

```bash
python scripts/normalize_assets.py
```

## Advanced Usage

### Selective Sync

Control what gets synced using frontmatter:

```yaml
---
status: published  # Sync to Jekyll
status: draft      # Keep in Obsidian only
status: private    # Never sync
---
```

### Image Handling

Images can be referenced in two ways:

1. Obsidian style (automatically converted):
   ```markdown
   ![[image.png]]
   ```

2. Jekyll style (automatically converted):
   ```markdown
   ![alt text](/assets/img/posts/image.png)
   ```

### Tag Filtering

System tags are filtered out during sync:
- `atomic` - Used by Obsidian
- Other system tags can be added in `frontmatter.py`

## Troubleshooting

### Common Issues

1. **Files Not Syncing**
   - Check file status in frontmatter
   - Verify file paths
   - Enable debug logging

2. **Image Path Issues**
   - Run normalize_assets.py
   - Check image exists in source
   - Verify image path format

3. **Sync Conflicts**
   - Latest modified file wins
   - Use --dry-run to preview
   - Check file timestamps

### Debug Mode

Enable debug logging:

```bash
export SYNC_DEBUG=true
python scripts/sync.py
```

### File Locations

- Obsidian posts: `$PKM_ROOT/atomics/**/*.md`
- Jekyll posts: `$JEKYLL_ROOT/_posts/*.md`
- Images: `$JEKYLL_ROOT/assets/img/posts/*`
- Backups:
  - PKM: `$PKM_ROOT/../PKM_backup/`
  - Jekyll: `$JEKYLL_ROOT/../jekyll_backup/` 