"""Custom exceptions for sync engine"""

class SyncEngineError(Exception):
    """Base exception for sync engine errors"""
    pass

class MediaError(SyncEngineError):
    """Base exception for media handling errors"""
    pass

class InvalidImageError(MediaError):
    """Raised when an image file is invalid or corrupted"""
    pass

class UnsupportedFormatError(MediaError):
    """Raised when an image format is not supported"""
    pass

class ImageProcessingError(MediaError):
    """Raised when image processing fails"""
    pass 