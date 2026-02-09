"""
NEXUS Web Application

FastAPI-based web interface for NEXUS.
Replaces Tkinter UI for better compatibility and modern design.
"""

import asyncio
import threading
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import uvicorn
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.capture_manager import ScreenCaptureService
from core.analysis_engine import AnalysisEngine
from core.proactive_agent import ProactiveAgent
from core.query_engine import QueryEngine
from services.database import DatabaseService


# Initialize FastAPI
app = FastAPI(title="NEXUS AI OS")

# Setup templates and static files
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Global State
class NexusState:
    def __init__(self):
        self.is_running = False
        self.capture_service: Optional[ScreenCaptureService] = None
        self.analysis_engine: Optional[AnalysisEngine] = None
        self.proactive_agent: Optional[ProactiveAgent] = None
        self.query_engine: Optional[QueryEngine] = None
        self.database = DatabaseService()
        self.loop = None
        self.thread = None
        self.latest_alert = None
        self.recent_activities = []
        self.is_focus_mode = False

state = NexusState()


@app.on_event("startup")
async def startup_event():
    """Initialize engines on startup."""
    state.query_engine = QueryEngine()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render the main dashboard."""
    try:
        # Debug: Print template path
        print(f"[WebUI] Loading template from: {templates.env.loader.searchpath}")
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return HTMLResponse(content=f"<h1>Error loading UI</h1><pre>{e}</pre>", status_code=500)


@app.get("/api/status")
async def get_status():
    """Get current system status."""
    db_stats = state.database.get_stats()
    return {
        "is_running": state.is_running,
        "is_focus_mode": state.is_focus_mode,
        "activity_count": db_stats.get("activity_count", 0),
        "latest_alert": state.latest_alert
    }


@app.post("/api/toggle_focus")
async def toggle_focus():
    """Toggle Focus Mode."""
    state.is_focus_mode = not state.is_focus_mode
    return {"status": "ok", "is_focus_mode": state.is_focus_mode}


@app.post("/api/start")
async def start_monitoring(background_tasks: BackgroundTasks):
    """Start NEXUS monitoring."""
    if state.is_running:
        return {"status": "ok", "message": "Already running"}
    
    state.is_running = True
    
    # Start monitoring in a separate thread
    state.thread = threading.Thread(target=run_nexus_loop, daemon=True)
    state.thread.start()
    
    return {"status": "ok", "message": "Monitoring started"}


@app.post("/api/stop")
async def stop_monitoring():
    """Stop NEXUS monitoring."""
    if not state.is_running:
        return {"status": "ok", "message": "Not running"}
    
    state.is_running = False
    
    if state.capture_service:
        state.capture_service.stop()
    if state.analysis_engine:
        state.analysis_engine.stop()
        
    return {"status": "ok", "message": "Monitoring stopped"}


class QueryRequest(BaseModel):
    query: str

@app.post("/api/query")
async def process_query(request: QueryRequest):
    """Process a natural language query."""
    if not state.query_engine:
        state.query_engine = QueryEngine()
        
    try:
        response = await state.query_engine.process_query(request.query)
        return {"response": response}
    except Exception as e:
        return {"response": f"Error processing query: {str(e)}"}


@app.get("/api/activities")
async def get_activities():
    """Get recent activities."""
    activities = await state.database.get_recent_activities(limit=10)
    return {"activities": activities}


@app.post("/api/dismiss_alert")
async def dismiss_alert():
    """Dismiss current alert."""
    state.latest_alert = None
    return {"status": "ok"}


def run_nexus_loop():
    """Run the main NEXUS processing loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    state.loop = loop
    
    try:
        # Initialize services
        state.capture_service = ScreenCaptureService()
        state.analysis_engine = AnalysisEngine()
        state.proactive_agent = ProactiveAgent()
        
        # Set callbacks
        state.capture_service.set_callback(lambda data: asyncio.run_coroutine_threadsafe(
            on_capture(data), loop
        ))
        
        state.analysis_engine.set_callback(lambda data, analysis: asyncio.run_coroutine_threadsafe(
            on_analysis(data, analysis), loop
        ))
        
        state.proactive_agent.set_alert_callback(lambda alert: asyncio.run_coroutine_threadsafe(
            on_alert(alert), loop
        ))
        
        # Run services
        async def run_services():
            tasks = [
                asyncio.create_task(state.capture_service.start()),
                asyncio.create_task(state.analysis_engine.start())
            ]
            await asyncio.gather(*tasks)
            
        loop.run_until_complete(run_services())
        
    except Exception as e:
        print(f"[WebUI] Loop error: {e}")
    finally:
        loop.close()


async def on_capture(capture_data):
    """Handle capture callback."""
    if state.analysis_engine:
        await state.analysis_engine.queue_capture(capture_data)

async def on_analysis(capture_data, analysis):
    """Handle analysis callback."""
    if state.proactive_agent:
        await state.proactive_agent.evaluate_situation(capture_data, analysis)

async def on_alert(alert_data):
    """Handle alert callback."""
    state.latest_alert = {
        "message": alert_data.get("message"),
        "priority": alert_data.get("priority"),
        "timestamp": datetime.now().isoformat()
    }


def run_server():
    """Run the Uvicorn server."""
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    run_server()
