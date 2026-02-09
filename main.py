#!/usr/bin/env python3
"""
NEXUS - Your AI Life Operating System

Main entry point for the NEXUS application.
Built for Google Gemini Hackathon 2026.
"""

import sys
import warnings
import os

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"

from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config



def print_banner():
    """Print startup banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     🧠  NEXUS - Your AI Life Operating System  🧠        ║
    ║                                                           ║
    ║     "An AI that watches everything you do                 ║
    ║      and makes you superhuman."                           ║
    ║                                                           ║
    ║     ✨ Powered by Google Gemini ✨                        ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def validate_config():
    """Validate configuration before starting."""
    if not Config.GOOGLE_API_KEY:
        print("\n⚠️  WARNING: GOOGLE_API_KEY not set!")
        print("   Create a .env file with your API key:")
        print("   GOOGLE_API_KEY=your-key-here")
        print("\n   Get your key at: https://aistudio.google.com/app/apikey")
        print("\n   NEXUS will run in limited mode without AI analysis.\n")
        return False
    return True


def main():
    """Main entry point."""
    print_banner()
    
    print("Initializing NEXUS...")
    
    # Ensure directories exist
    Config.ensure_directories()
    print("✓ Data directories ready")
    
    # Validate config
    if validate_config():
        print(f"✓ Google Gemini API configured ({Config.GEMINI_MODEL})")
    
    print("✓ Starting Web UI...\n")
    
    # Launch Web UI
    try:
        import uvicorn
        from ui.web_app import app
        
        print("\n🌐 NEXUS Web Interface running at http://localhost:8000")
        print("Press Ctrl+C to stop\n")
        
        uvicorn.run(app, host="0.0.0.0", port=8000)
        
    except KeyboardInterrupt:
        print("\nShutting down NEXUS...")
    except ImportError:
        print("\n❌ Error: fastapi/uvicorn not found. Install with: pip install fastapi uvicorn")
    except Exception as e:
        print(f"\n❌ Error starting Web UI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\nGoodbye! 👋")


if __name__ == "__main__":
    main()
