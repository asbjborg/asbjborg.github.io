"""Custom exceptions for sync engine"""

class SyncEngineError(Exception):
    """Base exception for sync engine errors"""
    pass

class ConfigError(SyncEngineError):
    """Configuration related errors"""
    pass

class SyncError(SyncEngineError):
    """Sync operation errors"""
    pass

class MediaError(SyncEngineError):
    """Media processing errors"""
    pass

class PostError(SyncEngineError):
    """Post processing errors"""
    pass

class ConflictError(SyncEngineError):
    """Sync conflict errors"""
    pass

class ValidationError(SyncEngineError):
    """Validation errors"""
    pass

class FileOperationError(SyncEngineError):
    """File operation errors"""
    pass

class InvalidImageError(MediaError):
    """Invalid image file errors"""
    pass

class UnsupportedFormatError(MediaError):
    """Unsupported media format errors"""
    pass

class ImageProcessingError(MediaError):
    """Image processing errors"""
    pass 