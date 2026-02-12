"""
OCR Service for NEXUS

Extracts text from screenshots using Tesseract OCR.
Provides fallback text for Gemini and empowers direct text-based search.
"""

import pytesseract
from PIL import Image
from pathlib import Path
from typing import Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config

class OCRService:
    """
    Service for Optical Character Recognition.
    """
    
    def __init__(self):
        """Initialize the OCR service."""
        # On Mac, tesseract is usually in the path if installed via brew
        # But we allow overriding in config
        if Config.TESSERACT_PATH != "tesseract":
            pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_PATH
            
        self.enabled = Config.OCR_ENABLED
        if self.enabled:
            print("[OCRService] Initialized")
        else:
            print("[OCRService] Disabled in config")

    def extract_text(self, image_path: str) -> str:
        """
        Extract text from an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text string
        """
        if not self.enabled:
            return ""
            
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception as e:
            print(f"[OCRService] Error extracting text: {e}")
            return ""

    def extract_text_from_image(self, img: Image.Image) -> str:
        """
        Extract text from a PIL Image object.
        
        Args:
            img: PIL Image object
            
        Returns:
            Extracted text string
        """
        if not self.enabled:
            return ""
            
        try:
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception as e:
            print(f"[OCRService] Error extracting text from image: {e}")
            return ""
