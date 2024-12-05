# Core Component Tasks

> These tasks detail the implementation requirements from our [Strategy Checklist](strategy-checklist.md).
> Each component maps to specific strategy requirements.

## sync.py - Configuration & Initialization
Maps to: "Components to Check > Core > sync.py"

- [ ] Configuration Validation
  - [ ] Required paths validation (vault_root, jekyll_root)
  - [ ] Optional settings validation (backup_count, image settings)
  - [ ] Environment variable support (.env file)
  - [ ] Type checking for config values

- [ ] Path Initialization
  - [ ] Verify vault structure exists ← "File Structure" requirements
  - [ ] Create missing Jekyll directories
  - [ ] Set up backup directories
  - [ ] Validate write permissions

- [ ] Environment Setup
  - [ ] Logger configuration
  - [ ] Error reporting setup
  - [ ] Debug mode handling
  - [ ] Dry-run capability

## atomic.py - File Operations
Maps to: "Components to Check > Core > atomic.py" and "Sync Logic" requirements

- [ ] Backup System
  - [ ] Timestamped backup folders
  - [ ] Backup before operations
  - [ ] Automatic cleanup of old backups
  - [ ] Backup verification

- [ ] Operation History
  - [ ] Track all operations ← "Sync Logic > Use file timestamps"
  - [ ] Store operation metadata
  - [ ] Query operation history
  - [ ] Clean old history entries

- [ ] Batch Operations
  - [ ] Group related operations
  - [ ] All-or-nothing transactions
  - [ ] Rollback on partial failure
  - [ ] Operation ordering

## engine.py - Sync Flow
Maps to: "Components to Check > Core > engine.py" and "Sync Logic" requirements

- [ ] Bidirectional Sync ← "Sync Logic > Bidirectional sync"
  - [ ] Obsidian → Jekyll
    - [ ] Content updates
    - [ ] Path conversion ← "Media Handling" requirements
    - [ ] Media handling
    - [ ] Frontmatter preservation ← "Sync Logic > Preserve Obsidian frontmatter"
  - [ ] Jekyll → Obsidian
    - [ ] Content-only updates
    - [ ] Path preservation ← "Sync Logic > Never move files in Obsidian"
    - [ ] No file moves
    - [ ] Frontmatter merging

- [ ] Conflict Resolution ← "Sync Logic > Use file timestamps"
  - [ ] Timestamp-based detection
  - [ ] User notification
  - [ ] Resolution strategies
  - [ ] History tracking

- [ ] Transaction Management
  - [ ] Pre-sync validation
  - [ ] Atomic operations
  - [ ] Rollback support
  - [ ] Success verification

## Testing Requirements
Maps to: "Test Coverage" requirements

- [ ] sync.py Tests
  - [ ] Config validation
  - [ ] Path initialization ← "Test Coverage > Basic operations"
  - [ ] Error conditions ← "Test Coverage > Error handling"

- [ ] atomic.py Tests
  - [ ] Backup/restore
  - [ ] Operation history
  - [ ] Batch operations

- [ ] engine.py Tests
  - [ ] Bidirectional sync ← "Test Coverage > Basic operations"
  - [ ] Conflict handling ← "Test Coverage > Complex scenarios"
  - [ ] Transaction management