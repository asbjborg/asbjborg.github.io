# Implementation Checklist

> **Strategy**: Based on [Sync Strategy](../sync-strategy.md)  
> **Tasks**: Detailed in [Core Tasks](core-tasks.md)

## File Structure
- [x] All content under /atomics/YYYY/MM/DD/
  - [x] No special folders for posts/drafts in Obsidian
  - [x] Images live in same daily folder as their posts
  - [x] Posts identified by frontmatter status, not location
  - [x] Preserve original file locations

## Post Detection & Processing
- [x] Detect posts by frontmatter status="published"
  - [x] Recursively scan entire atomics directory
  - [x] Ignore files without status
  - [x] Handle drafts correctly
- [x] Extract date from folder path (YYYY/MM/DD)
- [x] Keep original Obsidian filenames
- [x] Create Jekyll filenames with date prefix

## Media Handling
- [x] Keep images with their posts in daily folders
- [x] Use absolute vault paths in Obsidian (![[atomics/YYYY/MM/DD/image.png]])
- [x] Convert to Jekyll web paths (/assets/img/posts/image.png)
- [x] Only sync media referenced by posts
- [x] Clean up unused media in Jekyll

## Sync Logic
- [x] Bidirectional sync
  - [x] Obsidian → Jekyll: Update content and convert paths
  - [x] Jekyll → Obsidian: Update only content, preserve paths
- [x] Never move files in Obsidian
- [x] Preserve Obsidian frontmatter structure
- [x] Use file timestamps for conflict resolution

## Components to Check
- [x] Core
  - [x] sync.py: Config and initialization
  - [x] changes.py: File scanning logic
  - [x] atomic.py: File operations
  - [x] engine.py: Overall flow
- [x] Handlers
  - [x] post.py: Post processing
  - [x] media.py: Media handling
- [x] Tests
  - [x] test_sync.py: Integration tests
  - [x] test_changes.py: Change detection
  - [x] test_atomic.py: File operations
  - [x] test_post.py: Post handling
  - [x] test_media.py: Media handling

## Test Coverage
- [x] Basic operations
  - [x] Post detection by status
  - [x] Date extraction from paths
  - [x] Path conversion
- [x] Complex scenarios
  - [x] Multiple posts per day
  - [x] Posts with multiple images
  - [x] Unicode filenames
  - [x] Spaces in filenames
- [x] Error handling
  - [x] Invalid frontmatter
  - [x] Missing images
  - [x] Permission issues
- [x] Performance
  - [x] Large vault scanning
  - [x] Multiple date folders
  - [x] Many images per post

## Documentation
- [x] Update all examples to use correct paths
- [x] Document date folder structure
- [x] Document frontmatter requirements
- [x] Document path handling

## Component Documentation
- [x] Change Detection (change-detection.md)
- [x] Atomic Operations (atomic-operations.md)
- [x] Post Handler
- [x] Media Handler

## Guide Documentation
- [x] Configuration (configuration.md)
- [x] Error Handling (error-handling.md)
- [ ] Usage Guide
- [ ] Performance Guide

## See Also
- [Sync Strategy](../sync-strategy.md) - Core strategy document
- [Core Tasks](core-tasks.md) - Implementation tasks
- [Change Detection](../../components/change-detection.md) - File scanning implementation
- [Atomic Operations](../../components/atomic-operations.md) - File operations implementation