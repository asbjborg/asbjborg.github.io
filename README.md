# asbjborg.github.io

My personal blog, built with Jekyll and enhanced with Obsidian sync functionality. The blog automatically syncs content from my Obsidian vault, handling both posts and media files.

## Features

### Obsidian Integration

The blog includes automatic syncing from Obsidian vault to Jekyll posts with the following features:

- **Automatic Post Sync**: Posts marked with `published: true` in Obsidian are automatically synced
- **Media Handling**:
  - Supports Obsidian image syntax (`![[image.png]]`)
  - Automatically processes and optimizes images
  - Handles featured images in frontmatter
- **File Organization**:
  - Maintains proper Jekyll post naming convention
  - Organizes media files in assets directory
  - Handles file conflicts with content hashing
- **Quality Control**:
  - Markdown linting
  - Image optimization
  - Proper newline handling

### Configuration

The sync functionality requires the following environment variables in `.env`:

```shell
SYNC_VAULT_ROOT=/path/to/obsidian/vault
SYNC_JEKYLL_ROOT=/path/to/jekyll/site
SYNC_DEBUG=false
SYNC_BACKUP_COUNT=5
SYNC_AUTO_CLEANUP=true
SYNC_MAX_IMAGE_WIDTH=1200
SYNC_OPTIMIZE_IMAGES=true
```

### Automatic Sync

The blog uses a cron job to automatically sync posts every 5 minutes. The sync script:

1. Checks for new/updated posts in Obsidian
2. Processes any media files
3. Updates the Jekyll blog
4. Commits and pushes changes

## Acknowledgments

This blog is powered by [Jekyll](https://jekyllrb.com/) and uses the beautiful [Chirpy theme](https://github.com/cotes2020/jekyll-theme-chirpy/). Big thanks to both projects for making this blog possible! ❤️

## License

This work is published under [MIT][mit] License.

[mit]: https://github.com/cotes2020/chirpy-starter/blob/master/LICENSE
