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
from core.knowledge_synthesis import KnowledgeSynthesis
from config import Config

console = Console()

class NexusCLI:
    def __init__(self):
        self.query_engine = QueryEngine()
        self.gemini = GeminiClient()
        self.synthesis = KnowledgeSynthesis()
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

    async def run_search(self, query: str):
        """Perform semantic search and display results in a table."""
        console.print(f"\n[bold cyan]Searching Neural Memory for:[/bold cyan] '{query}'...\n")
        
        # We'll use the query engine's db logic but format it for CLI
        activities = await self.query_engine.db.search_activities(query=query, limit=10)
        
        if not activities:
            console.print("[yellow]No matching memories found.[/yellow]")
            return

        table = Table(title=f"Search Results: {query}")
        table.add_column("Time", style="dim")
        table.add_column("App", style="cyan")
        table.add_column("Activity Insight", style="white")
        
        for act in activities:
            import json
            analysis = act.get('analysis', {})
            if isinstance(analysis, str):
                try: analysis = json.loads(analysis)
                except: analysis = {}
            
            insight = analysis.get('activity', 'No details')
            time_str = act['timestamp'].split('.')[0] if isinstance(act['timestamp'], str) else "Recent"
            
            table.add_row(time_str, act['app_name'], insight[:60] + "...")
        
        console.print(table)

    async def run_summary(self):
        """Generate a daily summary report."""
        console.print("\n[bold cyan]Synthesizing Daily Intelligence Report...[/bold cyan]\n")
        
        with console.status("[bold white]Crunching activities...", spinner="brain"):
            summary_data = await self.synthesis.daily_insights()
        
        console.print(Panel.fit(
            Markdown(summary_data.get('summary', 'No summary available.')),
            title="[bold magenta]Daily Intelligence Highlight[/bold magenta]"
        ))
        
        if summary_data.get('insights'):
            console.print("\n[bold cyan]Key Insights:[/bold cyan]")
            for insight in summary_data['insights']:
                console.print(f" • {insight}")

    async def run_diagnostics(self):
        """Check system health and dependencies."""
        console.print("\n[bold cyan]NEXUS System Diagnostics[/bold cyan]\n")
        
        checks = [
            ("Gemini API", self._check_api),
            ("OCR Engine (Tesseract)", self._check_ocr),
            ("Audio Stream (PyAudio)", self._check_audio),
            ("Database (SQLite)", self._check_db),
            ("Vector Store (Chroma)", self._check_vector)
        ]
        
        table = Table(show_header=False, box=None)
        
        for name, check_fn in checks:
            status, msg = await check_fn()
            icon = "[bold green]✓[/bold green]" if status else "[bold red]✗[/bold red]"
            table.add_row(f"{icon} {name}", f"[dim]{msg}[/dim]")
            
        console.print(table)
        console.print("\n[dim]If services are missing, re-run './install.sh'[/dim]\n")

    async def _check_api(self):
        if not Config.GOOGLE_API_KEY: return False, "API Key missing in .env"
        return True, f"Configured ({Config.GEMINI_MODEL})"

    async def _check_ocr(self):
        import shutil
        if shutil.which("tesseract"): return True, "Command found in PATH"
        return False, "Tesseract binary not found"

    async def _check_audio(self):
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            count = p.get_device_count()
            p.terminate()
            if count > 0: return True, f"{count} devices found"
            return False, "No audio input devices"
        except ImportError: return False, "PyAudio not installed"
        except Exception as e: return False, str(e)

    async def _check_db(self):
        path = Path(Config.DB_PATH)
        if path.exists(): return True, f"DB ready ({path.stat().st_size // 1024} KB)"
        return True, "Will initialize on start"

    async def _check_vector(self):
        path = Path(Config.CHROMA_PATH)
        if path.exists(): return True, "Syncing to persistent store"
        return True, "Will initialize on start"

    async def main_menu(self):
        """Main CLI Menu."""
        self.print_banner()
        
        # Auto-start engine if not running
        if not self.running:
            await self.start_background_engine()

        while True:
            console.print("\n[bold]Commands:[/bold]")
            console.print(" [cyan]s[/cyan] - Show system health check")
            console.print(" [cyan]f[/cyan] - Find/Search memories")
            console.print(" [cyan]r[/cyan] - Generate daily Report")
            console.print(" [cyan]l[/cyan] - View live cortex logs")
            console.print(" [cyan]q[/cyan] - Terminate NEXUS")
            
            choice = Prompt.ask("\n[bold]Action[/bold]", choices=['c', 's', 'f', 'r', 'l', 'q', 'chat', 'status', 'search', 'summary', 'logs', 'quit'])
            
            if choice in ['c', 'chat']:
                await self.chat_interface()
            elif choice in ['s', 'status', 'check']:
                await self.run_diagnostics()
            elif choice in ['f', 'search']:
                query = Prompt.ask("[bold cyan]Search term[/bold cyan]")
                await self.run_search(query)
            elif choice in ['r', 'summary', 'report']:
                await self.run_summary()
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

    async def main_entry(self, command: str = 'menu'):
        """Primary entrance point for the CLI."""
        if command == 'chat':
            await self.chat_interface()
        elif command == 'search':
            # Handle args here if needed
            pass
        elif command == 'summary':
            await self.run_summary()
        elif command == 'check':
            await self.run_diagnostics()
        else:
            await self.main_menu()

if __name__ == "__main__":
    cli = NexusCLI()
    asyncio.run(cli.main_entry())
