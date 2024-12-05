# Error Handling Guide

## Overview
The sync engine uses a comprehensive error handling strategy to ensure data safety and provide clear error reporting.

## Error Types

### 1. Configuration Errors
```python
class ConfigError(Exception):
    """Configuration related errors"""
    pass

# Example usage
if 'vault_root' not in config:
    raise ConfigError("Missing required config: vault_root")
```

### 2. Atomic Operation Errors
```python
class AtomicError(Exception):
    """Atomic operation failures with automatic rollback"""
    def __init__(self, message: str, operation: SyncOperation):
        self.operation = operation
        super().__init__(message)
```

### 3. File Operation Errors
```python
class FileOperationError(Exception):
    """File operation failures"""
    def __init__(self, path: Path, operation: str, reason: str):
        self.path = path
        self.operation = operation
        self.reason = reason
        super().__init__(f"{operation} failed for {path}: {reason}")
```

## Error Handling Strategy

### 1. Validation First
Always validate before operations:
```python
def validate_paths(operation: SyncOperation):
    if not operation.source_path.exists():
        raise FileOperationError(
            path=operation.source_path,
            operation="read",
            reason="File not found"
        )
```

### 2. Atomic Operations
Use atomic operations with rollback:
```python
try:
    with atomic.batch() as batch:
        batch.execute(operation)
except AtomicError as e:
    logger.error(f"Operation failed and rolled back: {e}")
    # Files are already restored
```

### 3. Graceful Degradation
Handle non-critical errors gracefully:
```python
def process_file(path: Path) -> Optional[SyncState]:
    try:
        return process_single_file(path)
    except ValueError as e:
        logger.warning(f"Skipping invalid file {path}: {e}")
        return None
```

## Common Error Scenarios

### 1. File Access Issues
```python
try:
    content = path.read_text()
except PermissionError:
    logger.error(f"Permission denied: {path}")
    raise FileOperationError(path, "read", "Permission denied")
except OSError as e:
    logger.error(f"OS error: {e}")
    raise FileOperationError(path, "read", str(e))
```

### 2. Invalid Content
```python
try:
    post = frontmatter.load(str(path))
except Exception as e:
    logger.warning(f"Invalid frontmatter in {path}: {e}")
    return None
```

### 3. Path Validation
```python
def validate_date_path(path: Path) -> bool:
    try:
        date_parts = list(path.relative_to(atomics_root).parts)[:3]
        datetime.strptime('/'.join(date_parts), '%Y/%m/%d')
        return True
    except (ValueError, IndexError):
        return False
```

## Error Recovery

### 1. Automatic Recovery
The atomic operations system handles most recovery:
```python
try:
    manager.execute(operation)
except AtomicError:
    # Files automatically restored
    pass
```

### 2. Manual Recovery
For manual intervention:
```python
# List available backups
backups = atomic.list_backups()

# Restore specific backup
atomic.restore_backup(backup_id)
```

## Logging Strategy

### 1. Error Levels
```python
# Critical errors (stop execution)
logger.error("Failed to initialize sync engine")

# Warnings (continue with degraded functionality)
logger.warning("Invalid frontmatter, skipping file")

# Info (normal operation)
logger.info("Starting sync operation")

# Debug (development details)
logger.debug(f"Processing file: {path}")
```

### 2. Structured Logging
```python
logger.error("Sync failed", extra={
    'operation': op.type,
    'source': str(op.source_path),
    'target': str(op.target_path),
    'error': str(e)
})
```

## See Also
- [Atomic Operations](../components/atomic-operations.md)
- [Configuration Guide](configuration.md) 