# Atomic Operations

## Overview
The atomic operations system ensures safe file operations with automatic backup and rollback capabilities. All file operations are executed as atomic transactions to prevent data loss.

## Core Features
- Automatic backup before operations
- Rollback on failure
- Operation history tracking
- Cleanup of old backups

## Implementation

### AtomicManager Class
```python
class AtomicManager:
    """Manages atomic file operations with backup/rollback"""
    
    def __init__(self, config: Dict):
        """
        Initialize atomic manager
        
        Args:
            config: Configuration with backup settings
            
        Required config:
            - vault_root: Root path for backups
            - backup_count: Number of backups to keep
        """
        
    def execute(self, operation: SyncOperation) -> bool:
        """
        Execute operation with automatic backup/rollback
        
        Args:
            operation: Operation to execute
            
        Returns:
            bool: Success status
            
        Raises:
            AtomicError: If operation fails and rollback needed
        """
```

## Backup Strategy

### Backup Location
```
/vault_root
    /.atomic_backups
        /batch_20240115_123456
            file1.md
            file2.png
```

### Backup Process
1. Create timestamped backup folder
2. Copy files to backup
3. Execute operation
4. On success: Keep backup for history
5. On failure: Restore from backup

## Usage Examples

### Basic Operation
```python
manager = AtomicManager(config)

operation = SyncOperation(
    type=OperationType.UPDATE,
    source=source_path,
    target=target_path
)

try:
    success = manager.execute(operation)
except AtomicError as e:
    print(f"Operation failed and rolled back: {e}")
```

### Batch Operations
```python
operations = [
    SyncOperation(type=OperationType.UPDATE, ...),
    SyncOperation(type=OperationType.CREATE, ...),
]

with manager.batch() as batch:
    for op in operations:
        batch.execute(op)
```

## Error Handling

### Automatic Rollback
```python
try:
    manager.execute(risky_operation)
except AtomicError as e:
    # Files already restored to original state
    logger.error(f"Operation failed: {e}")
```

### Manual Recovery
```python
# List available backups
backups = manager.list_backups()

# Restore specific backup
manager.restore_backup('batch_20240115_123456')
```

## Best Practices

1. Always use with error handling:
```python
try:
    with manager.batch() as batch:
        batch.execute(op1)
        batch.execute(op2)
except AtomicError:
    # Batch rolled back automatically
```

2. Clean up old backups regularly:
```python
if manager.config['auto_cleanup']:
    manager.cleanup_old_backups()
```

3. Use batch operations for related changes:
```python
with manager.batch() as batch:
    # These operations succeed or fail together
    batch.execute(update_post)
    batch.execute(update_image)
```

## See Also
- [Configuration Guide](../guides/configuration.md)
- [Error Handling](../guides/error-handling.md) 