# File Structure

## Overview
The sync engine uses a strict atomic-based approach where all content lives in daily folders. This structure ensures content is organized by creation date and keeps related files together.

## Obsidian Structure

```
/vault_root
    /atomics                    # Root for all atomic notes
        /YYYY                   # Year folder
            /MM                 # Month folder (01-12)
                /DD            # Day folder (01-31)
                    post.md              # Blog post
                    image.png           # Images used in post
                    another-post.md     # Another post same day
```

### Key Points
- All content lives under `/atomics`
- Date-based folder structure: `/YYYY/MM/DD`
- Posts and their images stay together in daily folders
- No special folders for posts/drafts
- Original filenames preserved

## Jekyll Structure

```
/jekyll_root
    /_posts
        YYYY-MM-DD-post.md      # Posts with date prefix
    /assets
        /img
            /posts              # Processed images
                image.png
```

### Key Points
- Posts use Jekyll's date prefix format
- Images moved to assets folder
- Paths converted for web use

## File Identification

### Posts
- Identified by frontmatter `status: "published"`
- Date extracted from folder path
- Example:
  ```yaml
  ---
  status: published
  title: My First Post
  image: ![[atomics/2024/01/15/cover.png]]
  ---
  ```

### Media Files
- Live alongside their posts
- Referenced using Obsidian's absolute vault paths
- Example: `![[atomics/2024/01/15/image.png]]`

## Path Handling

### Obsidian Paths
- Always use absolute vault paths
- Format: `![[atomics/YYYY/MM/DD/filename]]`
- Preserves original filenames

### Jekyll Paths
- Posts: `YYYY-MM-DD-sanitized-filename.md`
- Images: `/assets/img/posts/sanitized-filename.png`
- All paths web-friendly (no spaces/special chars)

## Migration Notes
- Old posts will be updated to use absolute paths
- Images will be moved to daily folders
- Frontmatter will be standardized 