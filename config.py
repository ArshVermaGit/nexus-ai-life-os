"""
NEXUS Configuration Module

Centralized configuration for NEXUS - Your AI Life Operating System.
Built for Google Gemini Hackathon 2026.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """
    Configuration settings for NEXUS.
    All settings can be overridden via environment variables.
    """
    
    # ============================================
    # Google Gemini API Configuration
    # ============================================
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL = "gemini-2.0-flash"  # Latest Gemini model with vision
    GEMINI_EMBEDDING_MODEL = "models/text-embedding-004"  # For semantic search
    
    # ============================================
    # Screen Capture Settings
    # ============================================
    SCREEN_CAPTURE_INTERVAL = int(os.getenv("SCREEN_CAPTURE_INTERVAL", "10"))  # seconds
    SCREEN_CAPTURE_QUALITY = 85  # JPEG quality 0-100
    MAX_SCREENSHOT_WIDTH = 1920
    MAX_SCREENSHOT_HEIGHT = 1080
    
    # ============================================
    # Audio Settings (Future Feature)
    # ============================================
    AUDIO_ENABLED = os.getenv("AUDIO_ENABLED", "false").lower() == "true"
    AUDIO_SAMPLE_RATE = 16000
    AUDIO_CHUNK_DURATION = 30  # seconds
    
    # ============================================
    # Storage Settings
    # ============================================
    DATA_DIR = Path(__file__).parent / "data"
    SCREENSHOTS_DIR = DATA_DIR / "screenshots"
    AUDIO_DIR = DATA_DIR / "audio"
    DB_PATH = DATA_DIR / "db" / "nexus.db"
    CHROMA_DIR = DATA_DIR / "db" / "chroma"
    
    # ============================================
    # Memory & Retention Settings
    # ============================================
    SCREENSHOT_RETENTION_DAYS = 7
    AUDIO_RETENTION_DAYS = 7
    MAX_CONTEXT_ACTIVITIES = 10  # Recent activities for context
    
    # ============================================
    # Proactive Agent Settings
    # ============================================
    PROACTIVE_ENABLED = os.getenv("PROACTIVE_ENABLED", "true").lower() == "true"
    ALERT_COOLDOWN = 300  # seconds between similar alerts (5 minutes)
    BREAK_REMINDER_MINUTES = 90  # Remind to take break after this
    DUPLICATE_SIMILARITY_THRESHOLD = 0.1  # Distance threshold for duplicate detection
    
    # ============================================
    # Privacy Settings
    # ============================================
    EXCLUDED_APPS = {
        "Keychain", "Keychain Access",
        "Password Manager", "1Password", "LastPass", "Dashlane", "Bitwarden", "KeePass",
        "Banking", "Bank of America", "Chase", "Wells Fargo",
    }
    
    REDACT_PATTERNS = [
        r'\b\d{16}\b',  # Credit card numbers (16 digits)
        r'\b\d{15}\b',  # Amex cards (15 digits)
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b\d{9}\b',  # SSN without dashes
        r'password[:\s]*\S+',  # Passwords
        r'api[_-]?key[:\s]*\S+',  # API keys
        r'secret[:\s]*\S+',  # Secrets
        r'token[:\s]*\S+',  # Tokens
        r'bearer\s+\S+',  # Bearer tokens
    ]
    
    AUTO_PAUSE_KEYWORDS = [
        'private', 'incognito', 'password', 'keychain',
        'secure', 'vault', 'banking', 'login',
    ]
    
    # ============================================
    # UI Settings
    # ============================================
    UI_THEME = "dark"
    UI_WINDOW_WIDTH = 900
    UI_WINDOW_HEIGHT = 650
    
    # ============================================
    # Methods
    # ============================================
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist."""
        cls.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def is_valid(cls) -> bool:
        """Check if configuration is valid."""
        return bool(cls.GOOGLE_API_KEY)
    
    @classmethod
    def get_summary(cls) -> dict:
        """Get configuration summary for debugging."""
        return {
            "api_key_set": bool(cls.GOOGLE_API_KEY),
            "gemini_model": cls.GEMINI_MODEL,
            "embedding_model": cls.GEMINI_EMBEDDING_MODEL,
            "capture_interval": cls.SCREEN_CAPTURE_INTERVAL,
            "proactive_enabled": cls.PROACTIVE_ENABLED,
            "data_dir": str(cls.DATA_DIR),
        }


# Initialize directories when module is imported
Config.ensure_directories()
