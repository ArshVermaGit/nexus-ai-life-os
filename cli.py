#!/usr/bin/env python3
"""
NEXUS CLI - Pure Terminal Intelligence
"""

import os
import sys
import asyncio
import argparse
import signal
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.live import Live
    from rich.table import Table
    from rich.markdown import Markdown
    from rich.prompt import Prompt
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    # Fallback for simple print if rich is missing during install
    class Console:
        def print(self, *args, **kwargs): print(*args)
    class Panel:
        @staticmethod
        def fit(text, title=None): return text

from services.gemini_client import GeminiClient
from core.query_engine import QueryEngine
from core.capture_manager import ScreenCaptureService
from core.analysis_engine import AnalysisEngine
from core.proactive_agent import ProactiveAgent
from config import Config

console = Console()

class NexusCLI:
    def __init__(self):
        self.query_engine = QueryEngine()
        self.gemini = GeminiClient()
        self.capture_service: Optional[ScreenCaptureService] = None
        self.analysis_engine: Optional[AnalysisEngine] = None
        self.running = False

    def print_banner(self):
        banner = """
   _  _______  _   _ ___ 
  || |____|| |||
  |||||||
  |||||||
  |||||||
  ||| ||
        """
        console.print(Panel.fit(
            "[bold cyan]NEXUS - Pure Terminal Intelligence[/bold cyan]\n"
            "[italic white]An AI that watches everything you do and makes you superhuman.[/italic white]",
            title="[bold magenta]Cortex v2.0[/bold magenta]"
        ))

    async def start_background_engine(self):
        """Initialize and start the background capture engine."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Waking up nerves...", total=None)
            self.capture_service = ScreenCaptureService()
            self.analysis_engine = AnalysisEngine()
            
            progress.add_task(description="Connecting cortex...", total=None)
            self.capture_service.set_callback(self.analysis_engine.queue_capture)
            self.capture_service.set_audio_callback(self.analysis_engine.queue_audio)
            
            progress.add_task(description="Priming proactive agent...", total=None)
            # Create a silent proactive agent for CLI
            pd = ProactiveAgent()
            # In CLI mode, we might want to log alerts instead of showing popups
            pd.set_alert_callback(lambda a: console.print(f"\n[bold yellow]PROACTIVE ALERT:[/bold yellow] {a['message']}"))
            self.analysis_engine.on_analysis_callback = pd.evaluate_situation
            
            # Start background tasks
            asyncio.create_task(self.capture_service.start())
            asyncio.create_task(self.analysis_engine.start())
            self.running = True
            
        console.print("[bold green]✓ NEXUS Background Engine is now ACTIVE.[/bold green]")
        console.print("[dim]Watching screen and listening to audio to build your memory...[/dim]\n")

    async def chat_interface(self):
        """Interactive chat in the terminal."""
        console.print("\n[bold cyan]Entering Neural Chat...[/bold cyan] (Type 'exit' to quit)\n")
        
        while True:
            try:
                query = Prompt.ask("[bold magenta]Query[/bold magenta]")
                if query.lower() in ['exit', 'quit', 'back']:
                    break
                if not query:
                    continue

                with console.status("[bold white]Accessing memory...", spinner="dots12"):
                    response = await self.query_engine.query(query)
                
                console.print("\n[bold green]NEXUS:[/bold green]")
                console.print(Markdown(response))
                console.print("\n" + "─" * 40 + "\n")
            except KeyboardInterrupt:
                break

    async def main_menu(self):
        """Main CLI Menu."""
        self.print_banner()
        
        # Auto-start engine if not running
        if not self.running:
            await self.start_background_engine()

        while True:
            console.print("\n[bold]Commands:[/bold]")
            console.print(" [cyan]c[/cyan] - Chat with your memory")
            console.print(" [cyan]s[/cyan] - Show system status")
            console.print(" [cyan]l[/cyan] - View live cortex logs")
            console.print(" [cyan]q[/cyan] - Terminate NEXUS")
            
            choice = Prompt.ask("\n[bold]Action[/bold]", choices=['c', 's', 'l', 'q', 'chat', 'status', 'logs', 'quit'])
            
            if choice in ['c', 'chat']:
                await self.chat_interface()
            elif choice in ['s', 'status']:
                self.show_status()
            elif choice in ['l', 'logs']:
                await self.view_logs()
            elif choice in ['q', 'quit']:
                console.print("\n[bold red]Shutting down NEXUS...[/bold red]")
                if self.capture_service: self.capture_service.stop()
                if self.analysis_engine: self.analysis_engine.stop()
                break

    def show_status(self):
        table = Table(title="NEXUS System Status")
        table.add_column("Service", style="cyan")
        table.add_column("State", style="magenta")
        table.add_column("Details", style="white")
        
        table.add_row("Cortex Engine", "ONLINE", Config.GEMINI_MODEL)
        table.add_row("Vision (OCR)", "ACTIVE", "Tesseract Engine")
        table.add_row("Audio Stream", "ACTIVE", f"{Config.AUDIO_SAMPLE_RATE}Hz")
        table.add_row("Proactive Agent", "ARMED", "Deadline/Duplication rules active")
        
        console.print(table)

    async def view_logs(self):
        console.print("\n[bold yellow]Streaming Cortex Logs...[/bold yellow] (Ctrl+C to stop)\n")
        # In a real app we'd tail the DB or a log file
        # Here we just show a placeholder since we don't have a real-time log event stream yet
        console.print("[dim]Recent activities:[/dim]")
        activities = await self.query_engine.db.get_recent_activities(limit=5)
        for act in activities:
            time_str = act['timestamp'].split('.')[0] if isinstance(act['timestamp'], str) else "Recent"
            console.print(f"[dim]{time_str}[/dim] [cyan]{act['app_name']}[/cyan] - {act['window_title'][:40]}...")
        
        # Wait for Ctrl+C
        try:
            while True: await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass

    async def main_entry(self):
        """Primary entrance point for the CLI."""
        await self.main_menu()

if __name__ == "__main__":
    cli = NexusCLI()
    asyncio.run(cli.main_entry())
