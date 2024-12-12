# Obsidian to Jekyll Sync

A tool to sync Obsidian notes to a Jekyll blog.

## Features

- Syncs Markdown files from Obsidian to Jekyll
- Handles image attachments
- Preserves frontmatter
- Runs automatically every 5 minutes via cron

## Setup

1. Clone this repository
2. Run setup script:

   ```bash
   ./scripts/setup.sh
   ```

3. Configure `.env` with your paths
4. The sync will run automatically every 5 minutes

## Manual Sync

If you need to run a sync manually:

```bash
./scripts/sync_wrapper.sh
```

## Logs

Logs are stored in the `LOGS` directory:

- `sync_YYYYMMDD_HHMMSS.log` - Individual sync logs
- `watch.log` - General sync log
- `watch.error.log` - Error log

## Configuration

Edit `.env` to configure:

- Paths to Obsidian vault and Jekyll site
- Debug and logging options
- Sync interval

## License

MIT
