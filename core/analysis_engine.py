"""
Analysis Engine for NEXUS

Coordinates the capture → analysis → storage pipeline.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Callable
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from services.gemini_client import GeminiClient
from services.database import DatabaseService
from utils.privacy import redact_sensitive_data


class AnalysisEngine:
    """
    Main analysis engine coordinating Gemini API calls and storage.
    
    Processes captures from a queue, analyzes with AI, and stores results.
    """
    
    def __init__(self):
        """Initialize the analysis engine."""
        self.gemini = GeminiClient()
        self.db = DatabaseService()
        self.analysis_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.processed_count = 0
        self.on_analysis_callback: Optional[Callable] = None
    
    def set_callback(self, callback: Callable):
        """
        Set callback for when analysis completes.
        
        Args:
            callback: Async function receiving (capture_data, analysis)
        """
        self.on_analysis_callback = callback
    
    async def start(self):
        """Start processing the analysis queue."""
        self.running = True
        print("[AnalysisEngine] Started")
        
        while self.running:
            try:
                # Get next item from queue (with timeout to check running)
                try:
                    capture_data = await asyncio.wait_for(
                        self.analysis_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Analyze
                analysis = await self.analyze_capture(capture_data)
                
                # Store results
                await self.store_analysis(capture_data, analysis)
                
                # Call callback if set
                if self.on_analysis_callback:
                    try:
                        await self.on_analysis_callback(capture_data, analysis)
                    except Exception as e:
                        print(f"[AnalysisEngine] Callback error: {e}")
                
                # Mark task as done
                self.analysis_queue.task_done()
                self.processed_count += 1
                
            except asyncio.CancelledError:
                print("[AnalysisEngine] Cancelled")
                break
            except Exception as e:
                print(f"[AnalysisEngine] Error: {e}")
                await asyncio.sleep(1)
    
    async def queue_capture(self, capture_data: Dict):
        """
        Add capture to analysis queue.
        
        Args:
            capture_data: Capture data from ScreenCaptureService
        """
        await self.analysis_queue.put(capture_data)
    
    async def analyze_capture(self, capture_data: Dict) -> Dict:
        """
        Analyze a single capture.
        
        Args:
            capture_data: Capture data dict
            
        Returns:
            Analysis results dict
        """
        # Get recent context
        recent_context = await self.db.get_recent_activities(limit=10)
        
        # Analyze with Gemini
        analysis = await self.gemini.analyze_screen(
            image_path=capture_data['filepath'],
            app_name=capture_data['app_name'],
            window_title=capture_data['window_title'],
            recent_context=recent_context
        )
        
        # Redact sensitive data from extracted text
        if 'extracted_text' in analysis and analysis['extracted_text']:
            analysis['extracted_text'] = redact_sensitive_data(
                analysis['extracted_text']
            )
        
        return analysis
    
    async def store_analysis(self, capture_data: Dict, analysis: Dict):
        """
        Store analysis results in database.
        
        Args:
            capture_data: Original capture data
            analysis: Analysis results from Gemini
        """
        # Generate embedding for semantic search
        search_text = f"{analysis.get('activity', '')} {analysis.get('extracted_text', '')} {capture_data.get('window_title', '')}"
        embedding = await self.gemini.generate_embedding(search_text)
        
        # Store in database
        await self.db.store_activity(
            timestamp=capture_data['timestamp'],
            activity_type='screen',
            app_name=capture_data['app_name'],
            window_title=capture_data['window_title'],
            screenshot_path=capture_data['filepath'],
            analysis=analysis,
            embedding=embedding
        )
    
    def stop(self):
        """Stop analysis engine."""
        self.running = False
        print(f"[AnalysisEngine] Stopped (processed {self.processed_count} captures)")
    
    def get_stats(self) -> Dict:
        """Get engine statistics."""
        return {
            'running': self.running,
            'queue_size': self.analysis_queue.qsize(),
            'processed_count': self.processed_count
        }
    
    async def analyze_now(self, capture_data: Dict) -> Dict:
        """
        Analyze capture immediately (bypass queue).
        
        Args:
            capture_data: Capture data
            
        Returns:
            Analysis results
        """
        analysis = await self.analyze_capture(capture_data)
        await self.store_analysis(capture_data, analysis)
        return analysis
