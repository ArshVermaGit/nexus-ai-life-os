"""
Audio Capture Service for NEXUS

Records system/microphone audio in chunks for Gemini transcription.
Enables NEXUS to 'hear' meetings, videos, and conversations.
"""

import asyncio
import wave
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
import threading

try:
    import pyaudio
except ImportError:
    pyaudio = None

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config

class AudioCaptureService:
    """
    Service for continuous audio recording in chunks.
    """
    
    def __init__(self, sample_rate: int = None, chunk_duration: int = None):
        """
        Initialize the audio capture service.
        """
        self.sample_rate = sample_rate or Config.AUDIO_SAMPLE_RATE
        self.chunk_duration = chunk_duration or Config.AUDIO_CHUNK_DURATION
        self.running = False
        self.pa = None
        self.stream = None
        self.on_chunk_callback: Optional[Callable] = None
        self.recording_thread = None
        
        self.enabled = Config.AUDIO_ENABLED
        if self.enabled and pyaudio is None:
            print("[AudioCapture] WARNING: pyaudio not installed. Audio capture will be disabled.")
            self.enabled = False
            
        if self.enabled:
            print(f"[AudioCapture] Initialized (rate: {self.sample_rate}Hz, chunk: {self.chunk_duration}s)")
        else:
            print("[AudioCapture] Disabled")

    def set_callback(self, callback: Callable):
        """Set callback for when an audio chunk is ready."""
        self.on_chunk_callback = callback

    async def start(self):
        """Start continuous audio recording."""
        if not self.enabled:
            return

        self.running = True
        self.pa = pyaudio.PyAudio()
        
        # Start the background recording thread
        self.recording_thread = threading.Thread(target=self._record_loop, daemon=True)
        self.recording_thread.start()
        print("[AudioCapture] Started recording loop")

    def _record_loop(self):
        """Internal recording loop that runs in a thread."""
        try:
            self.stream = self.pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=1024
            )
            
            while self.running:
                frames = []
                # Record for chunk_duration
                start_time = time.time()
                num_frames = int(self.sample_rate / 1024 * self.chunk_duration)
                
                for _ in range(num_frames):
                    if not self.running:
                        break
                    try:
                        data = self.stream.read(1024, exception_on_overflow=False)
                        frames.append(data)
                    except Exception as e:
                        print(f"[AudioCapture] Stream read error: {e}")
                        break
                
                if frames and self.running:
                    # Save chunk to file
                    self._save_chunk(frames)
                    
        except Exception as e:
            print(f"[AudioCapture] Fatal error in record loop: {e}")
        finally:
            self._cleanup()

    def _save_chunk(self, frames):
        """Save captured frames to a WAV file."""
        timestamp = datetime.now()
        filename = f"audio_{timestamp.strftime('%Y%m%d_%H%M%S')}.wav"
        filepath = Config.AUDIO_DIR / filename
        
        try:
            with wave.open(str(filepath), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(self.pa.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(frames))
            
            # Prepare metadata
            audio_data = {
                'timestamp': timestamp,
                'type': 'audio',
                'filepath': str(filepath),
                'duration': self.chunk_duration
            }
            
            # Trigger callback if set (using loop.call_soon_threadsafe if needed, 
            # but we'll assume the callback handles its own async context)
            if self.on_chunk_callback:
                # We are in a thread, so we need to be careful with async callbacks
                # Most NEXUS services use asyncio queue for processing
                asyncio.run_coroutine_threadsafe(self.on_chunk_callback(audio_data), asyncio.get_event_loop())
                
        except Exception as e:
            print(f"[AudioCapture] Error saving audio chunk: {e}")

    def stop(self):
        """Stop recording."""
        self.running = False
        print("[AudioCapture] Stopped")

    def _cleanup(self):
        """Cleanup resources."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.pa:
            self.pa.terminate()
        print("[AudioCapture] Resources cleaned up")
