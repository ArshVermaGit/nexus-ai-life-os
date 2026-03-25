import pytest
from config import Config

def test_config_initialization():
    """Verify that Config handles the default data directory correctly."""
    assert Config.DATA_DIR.name == "data"

def test_nexus_directories():
    """Verify that Config can ensure required directories exist."""
    Config.ensure_directories()
    assert Config.SCREENSHOTS_DIR.exists()
    assert Config.AUDIO_DIR.exists()
