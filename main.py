#!/usr/bin/env python3
"""
NEXUS - Your AI Life Operating System

Main entry point for the NEXUS application.
Built for Google Gemini Hackathon 2026.
"""

import sys
import warnings
import os
import argparse
import asyncio

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"

from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import config



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
    api_key = getattr(config.Config, 'GOOGLE_API_KEY', None)
    if not api_key:
        print("\n⚠️  WARNING: GOOGLE_API_KEY not set!")
        print("   Create a .env file with your API key:")
        print("   GOOGLE_API_KEY=your-key-here")
        print("\n   Get your key at: https://aistudio.google.com/app/apikey")
        print("\n   NEXUS will run in limited mode without AI analysis.\n")
        return False
    return True


def main():
    """Main entry point for NEXUS CLI."""
    parser = argparse.ArgumentParser(description="NEXUS - Your AI Life OS")
    parser.add_argument('command', nargs='?', choices=['chat', 'search', 'summary', 'check', 'start'], default='menu')
    args = parser.parse_args()

    # Ensure directories exist
    
    # Validate config
    api_key = getattr(config.Config, 'GOOGLE_API_KEY', None)
    if not api_key:
        print("\n⚠️  WARNING: GOOGLE_API_KEY not set!")
        print("   Get your key at: https://aistudio.google.com/app/apikey\n")
        
    # Standard CLI launch
    import cli
    import asyncio
    
    nexus_cli = cli.NexusCLI()
    asyncio.run(nexus_cli.main_entry(args.command))

if __name__ == "__main__":
    main()
