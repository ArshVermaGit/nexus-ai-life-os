"""
Screen Capture Manager for NEXUS

Handles continuous screenshot capture with configurable interval,
privacy filtering, and callback mechanism.
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional

import mss
import mss.tools
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config
from utils.compression import compress_image
from utils.privacy import should_capture, get_active_window_info


class ScreenCaptureService:
    """
    Captures screenshots at regular intervals.
    
    Attributes:
        interval: Time between captures in seconds
        running: Whether capture is currently active
    """
    
    def __init__(self, interval: float = None):
        """
        Initialize the screen capture service.
        
        Args:
            interval: Capture interval in seconds (default from Config)
        """
        self.interval = interval or Config.SCREEN_CAPTURE_INTERVAL
        self.running = False
        self.sct = None
        self.last_capture_time = 0
        self.on_capture_callback: Optional[Callable] = None
        self.capture_count = 0
        
    def set_callback(self, callback: Callable):
        """
        Set callback function called after each successful capture.
        
        Args:
            callback: Async function that receives capture_data dict
        """
        self.on_capture_callback = callback
        
    async def start(self):
        """Start continuous screen capture."""
        self.running = True
        self.sct = mss.mss()
        print(f"[ScreenCapture] Started (interval: {self.interval}s)")
        
        while self.running:
            try:
                # Capture screen
                capture_data = await self.capture_frame()
                
                # Call callback if set and capture was successful
                if self.on_capture_callback and capture_data:
                    await self.on_capture_callback(capture_data)
                
                # Wait for next interval
                await asyncio.sleep(self.interval)
                
            except asyncio.CancelledError:
                print("[ScreenCapture] Cancelled")
                break
            except Exception as e:
                print(f"[ScreenCapture] Error: {e}")
                await asyncio.sleep(1)  # Brief pause on error
    
    async def capture_frame(self) -> Optional[Dict]:
        """
        Capture a single screenshot with context.
        
        Returns:
            Dict with capture data, or None if capture skipped/failed
        """
        try:
            # Get active window info
            window_info = get_active_window_info()
            
            # Check if we should capture this app
            if not should_capture(window_info['app_name']):
                return None
            
            # Ensure mss is initialized
            if self.sct is None:
                self.sct = mss.mss()
            
            # Capture screenshot of primary monitor
            monitor = self.sct.monitors[1]  # Primary monitor
            screenshot = self.sct.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            # Resize if needed
            img = self._resize_image(img)
            
            # Generate filename and save
            timestamp = datetime.now()
            filename = f"screen_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.jpg"
            filepath = Config.SCREENSHOTS_DIR / filename
            
            # Compress and save
            compressed_data = compress_image(img, quality=Config.SCREEN_CAPTURE_QUALITY)
            with open(filepath, 'wb') as f:
                f.write(compressed_data)
            
            # Prepare capture data
            capture_data = {
                'timestamp': timestamp,
                'type': 'screen',
                'filepath': str(filepath),
                'app_name': window_info['app_name'],
                'window_title': window_info['window_title'],
                'screen_size': img.size,
                'file_size': len(compressed_data)
            }
            
            self.last_capture_time = time.time()
            self.capture_count += 1
            
            return capture_data
            
        except Exception as e:
            print(f"[ScreenCapture] Capture failed: {e}")
            return None
    
    def _resize_image(self, img: Image.Image) -> Image.Image:
        """
        Resize image if it exceeds max dimensions while maintaining aspect ratio.
        
        Args:
            img: PIL Image to resize
            
        Returns:
            Resized image (or original if no resize needed)
        """
        if (img.width > Config.MAX_SCREENSHOT_WIDTH or 
            img.height > Config.MAX_SCREENSHOT_HEIGHT):
            
            # Calculate new size maintaining aspect ratio
            ratio = min(
                Config.MAX_SCREENSHOT_WIDTH / img.width,
                Config.MAX_SCREENSHOT_HEIGHT / img.height
            )
            new_size = (int(img.width * ratio), int(img.height * ratio))
            return img.resize(new_size, Image.Resampling.LANCZOS)
        
        return img
    
    def stop(self):
        """Stop capture."""
        self.running = False
        if self.sct:
            self.sct.close()
            self.sct = None
        print(f"[ScreenCapture] Stopped (captured {self.capture_count} frames)")
    
    def get_stats(self) -> Dict:
        """
        Get capture statistics.
        
        Returns:
            Dict with capture stats
        """
        return {
            'running': self.running,
            'capture_count': self.capture_count,
            'last_capture_time': self.last_capture_time,
            'interval': self.interval
        }
