"""
NEXUS User Interface

Tkinter-based desktop application for NEXUS.
"""

import asyncio
import threading
from datetime import datetime
from typing import Dict
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.capture_manager import ScreenCaptureService
from core.analysis_engine import AnalysisEngine
from core.proactive_agent import ProactiveAgent
from core.query_engine import QueryEngine
from services.database import DatabaseService


class NexusUI:
    """
    Main UI for NEXUS desktop application.
    
    Provides interface for monitoring, queries, and alerts.
    """
    
    def __init__(self):
        """Initialize the NEXUS UI."""
        # Create main window
        self.root = tk.Tk()
        self.root.title("NEXUS - AI Life Operating System")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # Set theme colors
        self.bg_color = "#1e1e2e"
        self.fg_color = "#cdd6f4"
        self.accent_color = "#89b4fa"
        self.alert_color = "#f38ba8"
        self.success_color = "#a6e3a1"
        self.warning_color = "#fab387"
        
        # Configure root
        self.root.configure(bg=self.bg_color)
        
        # State
        self.is_running = False
        self.activity_count = 0
        self.loop = None
        self.monitoring_thread = None
        
        # Initialize services (created on demand)
        self.capture_service = None
        self.analysis_engine = None
        self.proactive_agent = None
        self.query_engine = None
        self.db = DatabaseService()
        
        # Build UI
        self._build_ui()
    
    def _build_ui(self):
        """Build all UI components."""
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles
        style.configure('Header.TLabel', 
                       font=('Helvetica', 24, 'bold'),
                       foreground=self.accent_color,
                       background=self.bg_color)
        
        style.configure('Status.TLabel',
                       font=('Helvetica', 12),
                       foreground=self.fg_color,
                       background=self.bg_color)
        
        style.configure('Start.TButton',
                       font=('Helvetica', 11, 'bold'),
                       foreground='white',
                       background=self.success_color)
        
        style.configure('Stop.TButton',
                       font=('Helvetica', 11, 'bold'),
                       foreground='white',
                       background=self.alert_color)
        
        # Main container
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(
            header_frame,
            text="🧠 NEXUS",
            font=('Helvetica', 28, 'bold'),
            fg=self.accent_color,
            bg=self.bg_color
        )
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = tk.Label(
            header_frame,
            text="AI Life Operating System",
            font=('Helvetica', 12),
            fg=self.fg_color,
            bg=self.bg_color
        )
        subtitle_label.pack(side=tk.LEFT, padx=(15, 0), pady=(10, 0))
        
        # Status section
        status_frame = tk.Frame(main_frame, bg=self.bg_color)
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Status indicator
        self.status_indicator = tk.Label(
            status_frame,
            text="● Stopped",
            font=('Helvetica', 14, 'bold'),
            fg=self.alert_color,
            bg=self.bg_color
        )
        self.status_indicator.pack(side=tk.LEFT)
        
        # Activity counter
        self.activity_label = tk.Label(
            status_frame,
            text="Activities: 0",
            font=('Helvetica', 12),
            fg=self.fg_color,
            bg=self.bg_color
        )
        self.activity_label.pack(side=tk.RIGHT)
        
        # Control buttons
        button_frame = tk.Frame(main_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.start_button = tk.Button(
            button_frame,
            text="▶ Start Monitoring",
            font=('Helvetica', 11, 'bold'),
            fg='white',
            bg=self.success_color,
            activebackground='#8bc78b',
            relief=tk.FLAT,
            padx=20,
            pady=8,
            command=self.start_monitoring
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = tk.Button(
            button_frame,
            text="⬛ Stop",
            font=('Helvetica', 11, 'bold'),
            fg='white',
            bg='#555',
            activebackground='#777',
            relief=tk.FLAT,
            padx=20,
            pady=8,
            command=self.stop_monitoring,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT)
        
        # Query section
        query_frame = tk.Frame(main_frame, bg=self.bg_color)
        query_frame.pack(fill=tk.X, pady=(0, 15))
        
        query_label = tk.Label(
            query_frame,
            text="Ask NEXUS:",
            font=('Helvetica', 11),
            fg=self.fg_color,
            bg=self.bg_color
        )
        query_label.pack(anchor=tk.W, pady=(0, 5))
        
        query_input_frame = tk.Frame(query_frame, bg=self.bg_color)
        query_input_frame.pack(fill=tk.X)
        
        self.query_entry = tk.Entry(
            query_input_frame,
            font=('Helvetica', 12),
            fg=self.fg_color,
            bg='#313244',
            insertbackground=self.fg_color,
            relief=tk.FLAT
        )
        self.query_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)
        self.query_entry.bind('<Return>', self.process_query)
        
        send_button = tk.Button(
            query_input_frame,
            text="→",
            font=('Helvetica', 14, 'bold'),
            fg='white',
            bg=self.accent_color,
            activebackground='#7aa4ea',
            relief=tk.FLAT,
            padx=15,
            command=self.process_query
        )
        send_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Activity log
        log_frame = tk.Frame(main_frame, bg=self.bg_color)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        log_label = tk.Label(
            log_frame,
            text="Activity Log:",
            font=('Helvetica', 11),
            fg=self.fg_color,
            bg=self.bg_color
        )
        log_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.activity_log = scrolledtext.ScrolledText(
            log_frame,
            font=('Menlo', 10),
            fg=self.fg_color,
            bg='#313244',
            relief=tk.FLAT,
            height=12,
            wrap=tk.WORD
        )
        self.activity_log.pack(fill=tk.BOTH, expand=True)
        self.activity_log.config(state=tk.DISABLED)
        
        # Alert display
        self.alert_frame = tk.Frame(main_frame, bg=self.warning_color)
        self.alert_frame.pack(fill=tk.X, pady=(15, 0))
        self.alert_frame.pack_forget()  # Hidden initially
        
        self.alert_label = tk.Label(
            self.alert_frame,
            text="",
            font=('Helvetica', 11, 'bold'),
            fg='#1e1e2e',
            bg=self.warning_color,
            wraplength=700,
            justify=tk.LEFT,
            padx=15,
            pady=10
        )
        self.alert_label.pack(fill=tk.X)
        
        dismiss_button = tk.Button(
            self.alert_frame,
            text="Dismiss",
            font=('Helvetica', 10),
            fg='#1e1e2e',
            bg='#e5c07b',
            relief=tk.FLAT,
            padx=10,
            pady=2,
            command=self.dismiss_alert
        )
        dismiss_button.pack(pady=(0, 10))
        
        # Log startup
        self._log_message("NEXUS initialized. Click 'Start Monitoring' to begin.", "info")
        
        # Load existing stats
        stats = self.db.get_stats()
        self.activity_count = stats.get('activity_count', 0)
        self._update_activity_count()
    
    def _log_message(self, message: str, level: str = "info"):
        """
        Add message to activity log.
        
        Args:
            message: Message text
            level: info, success, warning, error
        """
        self.activity_log.config(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add message with timestamp
        if level == "success":
            prefix = "✓"
        elif level == "warning":
            prefix = "⚠"
        elif level == "error":
            prefix = "✗"
        else:
            prefix = "•"
        
        self.activity_log.insert(tk.END, f"[{timestamp}] {prefix} {message}\n")
        self.activity_log.see(tk.END)
        self.activity_log.config(state=tk.DISABLED)
    
    def _update_activity_count(self):
        """Update the activity counter display."""
        self.activity_label.config(text=f"Activities: {self.activity_count:,}")
    
    def start_monitoring(self):
        """Start NEXUS monitoring."""
        if self.is_running:
            return
        
        self.is_running = True
        self._log_message("Starting NEXUS monitoring...", "info")
        
        # Update UI
        self.status_indicator.config(text="● Running", fg=self.success_color)
        self.start_button.config(state=tk.DISABLED, bg='#555')
        self.stop_button.config(state=tk.NORMAL, bg=self.alert_color)
        
        # Start monitoring in background thread
        self.monitoring_thread = threading.Thread(target=self._run_monitoring, daemon=True)
        self.monitoring_thread.start()
        
        self._log_message("Monitoring started!", "success")
    
    def _run_monitoring(self):
        """Run the monitoring loop in a separate thread."""
        # Create new event loop for this thread
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            # Initialize services
            self.capture_service = ScreenCaptureService()
            self.analysis_engine = AnalysisEngine()
            self.proactive_agent = ProactiveAgent()
            self.query_engine = QueryEngine()
            
            # Set callbacks
            self.capture_service.set_callback(self._on_capture)
            self.analysis_engine.set_callback(self._on_analysis)
            self.proactive_agent.set_alert_callback(self._on_alert)
            
            # Create tasks
            async def run_services():
                tasks = [
                    asyncio.create_task(self.capture_service.start()),
                    asyncio.create_task(self.analysis_engine.start())
                ]
                
                try:
                    await asyncio.gather(*tasks)
                except asyncio.CancelledError:
                    pass
            
            self.loop.run_until_complete(run_services())
            
        except Exception as e:
            self.root.after(0, lambda: self._log_message(f"Monitoring error: {e}", "error"))
        finally:
            self.loop.close()
    
    async def _on_capture(self, capture_data: Dict):
        """Callback when capture completes."""
        # Queue for analysis
        await self.analysis_engine.queue_capture(capture_data)
        
        # Update UI (thread-safe)
        self.root.after(0, self._update_on_capture, capture_data)
    
    def _update_on_capture(self, capture_data: Dict):
        """Thread-safe UI update for capture."""
        self.activity_count += 1
        self._update_activity_count()
        
        app = capture_data.get('app_name', 'Unknown')
        self._log_message(f"Captured: {app}", "info")
    
    async def _on_analysis(self, capture_data: Dict, analysis: Dict):
        """Callback when analysis completes."""
        # Evaluate with proactive agent
        await self.proactive_agent.evaluate_situation(capture_data, analysis)
        
        # Update UI (thread-safe)
        activity_desc = analysis.get('activity', 'Activity analyzed')[:50]
        self.root.after(0, lambda: self._log_message(f"Analyzed: {activity_desc}", "success"))
    
    async def _on_alert(self, alert_data: Dict):
        """Callback when alert is triggered."""
        message = alert_data.get('message', 'Alert')
        priority = alert_data.get('priority', 'medium')
        
        # Show alert (thread-safe)
        self.root.after(0, lambda: self._show_alert(message, priority))
    
    def _show_alert(self, message: str, priority: str):
        """Display alert in UI."""
        # Set color based on priority
        if priority == 'critical':
            color = self.alert_color
        elif priority == 'high':
            color = '#f5c2e7'
        elif priority == 'medium':
            color = self.warning_color
        else:
            color = '#89b4fa'
        
        self.alert_frame.config(bg=color)
        self.alert_label.config(text=message, bg=color)
        self.alert_frame.pack(fill=tk.X, pady=(15, 0))
        
        self._log_message(f"ALERT: {message}", "warning")
    
    def dismiss_alert(self):
        """Dismiss the current alert."""
        self.alert_frame.pack_forget()
    
    def stop_monitoring(self):
        """Stop NEXUS monitoring."""
        if not self.is_running:
            return
        
        self.is_running = False
        self._log_message("Stopping monitoring...", "info")
        
        # Stop services
        if self.capture_service:
            self.capture_service.stop()
        if self.analysis_engine:
            self.analysis_engine.stop()
        
        # Update UI
        self.status_indicator.config(text="● Stopped", fg=self.alert_color)
        self.start_button.config(state=tk.NORMAL, bg=self.success_color)
        self.stop_button.config(state=tk.DISABLED, bg='#555')
        
        self._log_message("Monitoring stopped.", "info")
    
    def process_query(self, event=None):
        """Process user query."""
        query = self.query_entry.get().strip()
        if not query:
            return
        
        self._log_message(f"Query: {query}", "info")
        self.query_entry.delete(0, tk.END)
        
        # Process query in background
        def run_query():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                query_engine = QueryEngine()
                response = loop.run_until_complete(query_engine.process_query(query))
                self.root.after(0, lambda: self._log_message(f"NEXUS: {response}", "success"))
            except Exception as e:
                self.root.after(0, lambda: self._log_message(f"Query error: {e}", "error"))
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_query, daemon=True)
        thread.start()
    
    def run(self):
        """Run the UI main loop."""
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Start main loop
        self.root.mainloop()
    
    def _on_close(self):
        """Handle window close."""
        if self.is_running:
            self.stop_monitoring()
        self.root.destroy()


def main():
    """Entry point for UI."""
    app = NexusUI()
    app.run()


if __name__ == "__main__":
    main()
