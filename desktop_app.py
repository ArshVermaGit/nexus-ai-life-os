"""
NEXUS Desktop Wrapper

Launches the NEXUS FastAPI server in the background and opens a 
native window using pywebview.
"""

import multiprocessing
import threading
import time
import sys
import os
import signal
from pathlib import Path
import webview
import uvicorn
from ui.web_app import app

def run_server():
    """Run the FastAPI server."""
    print("[DesktopApp] Starting back-end server...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

def main():
    """Launch the desktop application."""
    # Start server in a background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to initialize
    time.sleep(2)
    
    print("[DesktopApp] Opening native window...")
    
    # Create window
    window = webview.create_window(
        'NEXUS - AI Life OS',
        'http://127.0.0.1:8000',
        width=1200,
        height=800,
        background_color='#050508',
        min_size=(1000, 700)
    )
    
    # Set window hooks if needed
    def on_closed():
        print("[DesktopApp] Window closed. Shutting down...")
        # Since server is daemon, it will exit with parent
        os._exit(0)
        
    window.events.closed += on_closed
    
    # Start the webview loop
    webview.start(debug=False)

if __name__ == '__main__':
    # On Windows, multiprocessing might need this
    if sys.platform == 'win32':
        multiprocessing.freeze_support()
        
    main()
