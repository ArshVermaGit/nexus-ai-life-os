#!/usr/bin/env python3
"""
NEXUS CLI - Interactive Terminal Interface
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from services.gemini_client import GeminiClient
from core.query_engine import QueryEngine
from core.capture_manager import ScreenCaptureService
from core.analysis_engine import AnalysisEngine
from core.proactive_agent import ProactiveAgent
from config import Config

class NexusCLI:
    def __init__(self):
        self.query_engine = QueryEngine()
        self.gemini = GeminiClient()
        self.running_processes = {}

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_banner(self):
        banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     🧠  NEXUS - Terminal Intelligence Interface           ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
        """
        print(banner)

    async def chat_loop(self):
        """Interactive chat loop in the terminal."""
        self.clear_screen()
        self.print_banner()
        print("Type 'exit' or 'quit' to return to menu.\n")
        
        while True:
            try:
                query = input("\033[1;36mNEXUS > \033[0m").strip()
                if query.lower() in ['exit', 'quit']:
                    break
                if not query:
                    continue

                print("\033[1;30mThinking...\033[0m")
                response = await self.query_engine.query(query)
                
                print(f"\n\033[1;32m{response}\033[0m\n")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\033[1;31mError: {str(e)}\033[0m")

    async def start_services(self):
        """Start background capture services."""
        print("🚀 Initializing Peripheral Intelligence...")
        
        # Initialize Core Services
        capture_service = ScreenCaptureService()
        analysis_engine = AnalysisEngine()
        proactive_agent = ProactiveAgent()

        # Link everything
        capture_service.set_callback(analysis_engine.queue_capture)
        capture_service.set_audio_callback(analysis_engine.queue_audio)
        
        print("✓ Capture Engine Ready")
        print("✓ Analysis Pipeline Online")
        print("✓ Proactive Agent Armed")
        
        # This will run forever in the background
        # In a real CLI, we would use a process manager or daemonize this
        # For this version, we'll run it as a detached task
        asyncio.create_task(capture_service.start())
        asyncio.create_task(analysis_engine.start())
        
        print("\n\033[1;32mNEXUS is now watching and listening in the background.\033[0m")

    def show_status(self):
        """Show system status."""
        print("\n--- NEXUS System Status ---")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Model: {Config.GEMINI_MODEL}")
        print(f"Audio Capture: {'ENABLED' if Config.AUDIO_ENABLED else 'DISABLED'}")
        print(f"OCR Engine: {'ENABLED' if Config.OCR_ENABLED else 'DISABLED'}")
        print("---------------------------\n")

async def main():
    parser = argparse.ArgumentParser(description="NEXUS CLI")
    parser.add_argument('command', nargs='?', choices=['chat', 'start', 'status', 'help'], default='help')
    
    args = parser.parse_args()
    cli = NexusCLI()

    if args.command == 'chat':
        await cli.chat_loop()
    elif args.command == 'start':
        await cli.start_services()
        # Keep alive if started from here
        while True:
            await asyncio.sleep(3600)
    elif args.command == 'status':
        cli.show_status()
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
