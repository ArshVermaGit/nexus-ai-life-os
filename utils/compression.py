"""
Image Compression Utilities for NEXUS

Provides functions for compressing images to reduce storage space.
"""

from PIL import Image
import io


def compress_image(img: Image.Image, quality: int = 85) -> bytes:
    """
    Compress a PIL Image to JPEG bytes.
    
    Args:
        img: PIL Image object to compress
        quality: JPEG quality (0-100), default 85
        
    Returns:
        Compressed image as bytes
    """
    buffer = io.BytesIO()
    
    # Convert to RGB if necessary (JPEG doesn't support transparency)
    if img.mode in ('RGBA', 'LA', 'P'):
        img = img.convert('RGB')
    
    img.save(buffer, format='JPEG', quality=quality, optimize=True)
    return buffer.getvalue()


def get_image_dimensions(img: Image.Image) -> tuple:
    """
    Get image dimensions.
    
    Args:
        img: PIL Image object
        
    Returns:
        Tuple of (width, height)
    """
    return img.size
