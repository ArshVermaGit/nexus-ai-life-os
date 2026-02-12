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
        self.audio_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.processed_count = 0
        self.audio_processed_count = 0
        self.on_analysis_callback: Optional[Callable] = None
    
    def set_callback(self, callback: Callable):
        """
        Set callback for when analysis completes.
        
        Args:
            callback: Async function receiving (capture_data, analysis)
        """
        self.on_analysis_callback = callback
    
    async def start(self):
        """Start processing analysis queues."""
        self.running = True
        print("[AnalysisEngine] Started")
        
        # Start background tasks for each queue
        tasks = [
            asyncio.create_task(self._process_screen_queue()),
            asyncio.create_task(self._process_audio_queue())
        ]
        await asyncio.gather(*tasks)

    async def _process_screen_queue(self):
        """Process screen captures from queue."""
        while self.running:
            try:
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
                
                # Call callback
                if self.on_analysis_callback:
                    await self.on_analysis_callback(capture_data, analysis)
                
                self.analysis_queue.task_done()
                self.processed_count += 1
            except Exception as e:
                print(f"[AnalysisEngine] Screen queue error: {e}")
                await asyncio.sleep(1)

    async def _process_audio_queue(self):
        """Process audio chunks from queue."""
        while self.running:
            try:
                try:
                    audio_data = await asyncio.wait_for(
                        self.audio_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Transcribe with Gemini
                transcription = await self.gemini.transcribe_audio(audio_data['filepath'])
                
                # Store in database
                await self.db.store_activity(
                    timestamp=audio_data['timestamp'],
                    activity_type='audio',
                    app_name='System Audio',
                    window_title='Audio Chunk',
                    audio_path=audio_data['filepath'],
                    transcription=transcription,
                    analysis={'activity': 'Listening to audio', 'transcription': transcription}
                )
                
                # Internal callback for audio
                if self.on_analysis_callback:
                    await self.on_analysis_callback(audio_data, {'activity': 'audio', 'transcription': transcription})
                
                self.audio_queue.task_done()
                self.audio_processed_count += 1
            except Exception as e:
                print(f"[AnalysisEngine] Audio queue error: {e}")
                await asyncio.sleep(1)
    
    async def queue_capture(self, capture_data: Dict):
        """Add capture to analysis queue."""
        await self.analysis_queue.put(capture_data)

    async def queue_audio(self, audio_data: Dict):
        """Add audio chunk to analysis queue."""
        await self.audio_queue.put(audio_data)
    
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
            ocr_text=capture_data.get('ocr_text', ''),
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
        print(f"[AnalysisEngine] Stopped (processed {self.processed_count} captures, {self.audio_processed_count} audio chunks)")
    
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
