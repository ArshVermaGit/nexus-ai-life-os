# NEXUS Implementation Guide

## 🚀 Quick Start Implementation

This guide provides step-by-step implementation details with actual code for building NEXUS in 12 hours.

## 📋 Prerequisites

### Required Tools
```bash
# Python 3.10+
python --version

# pip packages
pip install anthropic mss pyautogui pillow chromadb sqlite3 numpy opencv-python pytesseract pyaudio

# System dependencies
# macOS:
brew install tesseract portaudio

# Linux:
sudo apt-get install tesseract-ocr portaudio19-dev

# Windows:
# Download and install tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
```

### API Keys
```bash
# Get Gemini API key from: https://aistudio.google.com/app/apikey
export ANTHROPIC_API_KEY="your-key-here"
```

## 🏗 Project Structure

```
nexus/
├── main.py                 # Application entry point
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
│
├── core/
│   ├── __init__.py
│   ├── capture_manager.py     # Screen/audio capture
│   ├── analysis_engine.py     # Gemini integration
│   ├── memory_system.py       # Storage layer
│   ├── proactive_agent.py     # Proactive assistance
│   ├── query_engine.py        # Natural language queries
│   └── knowledge_synthesis.py # Insight generation
│
├── models/
│   ├── __init__.py
│   ├── activity.py        # Activity data models
│   └── schemas.py         # Database schemas
│
├── services/
│   ├── __init__.py
│   ├── gemini_client.py   # Gemini API wrapper
│   ├── database.py        # SQLite operations
│   └── vector_store.py    # ChromaDB operations
│
├── ui/
│   ├── __init__.py
│   ├── app.py            # Main UI application
│   ├── timeline.py       # Timeline viewer
│   └── search.py         # Search interface
│
└── utils/
    ├── __init__.py
    ├── privacy.py        # Privacy filters
    ├── compression.py    # Image/audio compression
    └── helpers.py        # Utility functions
```

## 📝 Step-by-Step Implementation

### HOUR 0-1: Project Setup & Core Structure

#### 1. Create Project Structure
```bash
mkdir nexus
cd nexus
mkdir -p core models services ui utils data/{screenshots,audio,db}
touch main.py config.py requirements.txt
```

#### 2. requirements.txt
```txt
anthropic>=0.40.0
mss>=9.0.1
pillow>=10.0.0
chromadb>=0.4.0
numpy>=1.24.0
opencv-python>=4.8.0
pytesseract>=0.3.10
pyaudio>=0.2.13
python-dotenv>=1.0.0
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.5.0
```

#### 3. config.py
```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Configuration
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    # Capture Settings
    SCREEN_CAPTURE_INTERVAL = 2  # seconds
    SCREEN_CAPTURE_QUALITY = 85  # JPEG quality 0-100
    MAX_SCREENSHOT_WIDTH = 1920
    MAX_SCREENSHOT_HEIGHT = 1080
    
    # Audio Settings
    AUDIO_SAMPLE_RATE = 16000
    AUDIO_CHUNK_DURATION = 30  # seconds
    
    # Storage Settings
    DATA_DIR = Path("data")
    SCREENSHOTS_DIR = DATA_DIR / "screenshots"
    AUDIO_DIR = DATA_DIR / "audio"
    DB_PATH = DATA_DIR / "db" / "nexus.db"
    CHROMA_DIR = DATA_DIR / "db" / "chroma"
    
    # Memory Settings
    SCREENSHOT_RETENTION_DAYS = 7
    AUDIO_RETENTION_DAYS = 7
    
    # Proactive Settings
    PROACTIVE_ENABLED = True
    ALERT_COOLDOWN = 300  # seconds between similar alerts
    
    # Privacy Settings
    EXCLUDED_APPS = {"Keychain", "Password Manager", "Banking"}
    REDACT_PATTERNS = [
        r'\b\d{16}\b',  # Credit cards
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'password[:\s]*\S+',
        r'api[_-]?key[:\s]*\S+',
    ]
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        cls.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Initialize
Config.ensure_directories()
```

### HOUR 1-3: Screen Capture System

#### core/capture_manager.py
```python
import asyncio
import time
from datetime import datetime
from pathlib import Path
import mss
import mss.tools
from PIL import Image
import io

from config import Config
from utils.compression import compress_image
from utils.privacy import should_capture, get_active_window_info

class ScreenCaptureService:
    """Captures screenshots at regular intervals"""
    
    def __init__(self, interval: float = Config.SCREEN_CAPTURE_INTERVAL):
        self.interval = interval
        self.running = False
        self.sct = mss.mss()
        self.last_capture_time = 0
        self.on_capture_callback = None
        
    def set_callback(self, callback):
        """Set callback function called after each capture"""
        self.on_capture_callback = callback
        
    async def start(self):
        """Start continuous screen capture"""
        self.running = True
        print(f"[ScreenCapture] Started (interval: {self.interval}s)")
        
        while self.running:
            try:
                # Capture screen
                capture_data = await self.capture_frame()
                
                # Call callback if set
                if self.on_capture_callback and capture_data:
                    await self.on_capture_callback(capture_data)
                
                # Wait for next interval
                await asyncio.sleep(self.interval)
                
            except Exception as e:
                print(f"[ScreenCapture] Error: {e}")
                await asyncio.sleep(1)  # Brief pause on error
    
    async def capture_frame(self):
        """Capture single screenshot with context"""
        try:
            # Get active window info
            window_info = get_active_window_info()
            
            # Check if we should capture this app
            if not should_capture(window_info['app_name']):
                return None
            
            # Capture screenshot
            monitor = self.sct.monitors[1]  # Primary monitor
            screenshot = self.sct.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            # Resize if needed
            img = self._resize_image(img)
            
            # Save to file
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
            return capture_data
            
        except Exception as e:
            print(f"[ScreenCapture] Capture failed: {e}")
            return None
    
    def _resize_image(self, img: Image.Image) -> Image.Image:
        """Resize image if larger than max dimensions"""
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
        """Stop capture"""
        self.running = False
        print("[ScreenCapture] Stopped")
```

#### utils/privacy.py
```python
import re
import subprocess
from typing import Dict
from config import Config

def get_active_window_info() -> Dict[str, str]:
    """Get information about the currently active window"""
    try:
        # macOS
        script = '''
        tell application "System Events"
            set frontApp to name of first application process whose frontmost is true
            set frontWindow to name of front window of application process frontApp
            return frontApp & "|||" & frontWindow
        end tell
        '''
        result = subprocess.check_output(['osascript', '-e', script])
        app_name, window_title = result.decode('utf-8').strip().split('|||')
        
        return {
            'app_name': app_name,
            'window_title': window_title
        }
    except:
        # Fallback
        return {
            'app_name': 'Unknown',
            'window_title': 'Unknown'
        }

def should_capture(app_name: str) -> bool:
    """Check if we should capture this application"""
    # Check excluded apps
    for excluded in Config.EXCLUDED_APPS:
        if excluded.lower() in app_name.lower():
            return False
    
    # Check for private/incognito indicators
    private_keywords = ['private', 'incognito', 'password', 'keychain']
    for keyword in private_keywords:
        if keyword in app_name.lower():
            return False
    
    return True

def redact_sensitive_data(text: str) -> str:
    """Remove sensitive information from text"""
    redacted = text
    
    for pattern in Config.REDACT_PATTERNS:
        redacted = re.sub(pattern, '[REDACTED]', redacted, flags=re.IGNORECASE)
    
    return redacted
```

#### utils/compression.py
```python
from PIL import Image
import io

def compress_image(img: Image.Image, quality: int = 85) -> bytes:
    """Compress PIL Image to JPEG bytes"""
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=quality, optimize=True)
    return buffer.getvalue()
```

### HOUR 3-5: Gemini Integration & Analysis

#### services/gemini_client.py
```python
import anthropic
import base64
from typing import Dict, List, Optional
from config import Config

class GeminiClient:
    """Wrapper for Anthropic/Gemini API"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-20250514"  # Use latest Sonnet
    
    async def analyze_screen(self, 
                            image_path: str,
                            app_name: str,
                            window_title: str,
                            recent_context: Optional[List[Dict]] = None) -> Dict:
        """Analyze screenshot with Gemini"""
        
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')
        
        # Build context from recent activity
        context_text = ""
        if recent_context:
            context_text = "\n".join([
                f"- {act['timestamp']}: {act['app_name']} - {act.get('activity', 'Unknown')}"
                for act in recent_context[-5:]  # Last 5 activities
            ])
        
        # Create prompt
        prompt = f"""You are NEXUS, an AI assistant watching the user's computer activity.

Current Context:
- Active Application: {app_name}
- Window Title: {window_title}
- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Recent Activity:
{context_text}

Analyze the screenshot and provide:

1. **Activity Description**: What is the user doing?
2. **Intent**: What are they trying to accomplish?
3. **Potential Issues**: Any mistakes about to happen? (email without attachment, wrong recipient, etc.)
4. **Should Interrupt**: Should we proactively alert the user? (true/false)
5. **Interrupt Message**: If interrupting, what should we say?
6. **Tags**: Relevant tags for categorizing this activity
7. **Priority**: low/medium/high

Respond in JSON format ONLY:
{{
  "activity": "description",
  "intent": "user's goal",
  "issues": ["list of potential issues"],
  "should_interrupt": true/false,
  "interrupt_message": "message to show user",
  "tags": ["tag1", "tag2"],
  "priority": "low/medium/high",
  "extracted_text": "any important text from screen"
}}"""

        try:
            # Call Gemini API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }]
            )
            
            # Parse response
            response_text = message.content[0].text
            
            # Extract JSON from response (might have markdown formatting)
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                # Fallback
                analysis = {
                    "activity": "Unknown",
                    "intent": "Unknown",
                    "issues": [],
                    "should_interrupt": False,
                    "tags": [],
                    "priority": "low"
                }
            
            return analysis
            
        except Exception as e:
            print(f"[GeminiClient] Error analyzing screen: {e}")
            return {
                "activity": "Error during analysis",
                "intent": "Unknown",
                "issues": [],
                "should_interrupt": False,
                "tags": [],
                "priority": "low",
                "error": str(e)
            }
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for semantic search"""
        # Note: Claude doesn't have native embeddings yet
        # Use a simple approach or integrate with another service
        # For hackathon, we can use a simple hash-based approach
        # In production, use a proper embedding model
        
        # Placeholder - in real implementation, use proper embeddings
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to 768-dim vector (normalize)
        embedding = [float(b) / 255.0 for b in hash_bytes]
        embedding = embedding + [0.0] * (768 - len(embedding))
        
        return embedding[:768]
```

#### core/analysis_engine.py
```python
import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from services.gemini_client import GeminiClient
from services.database import DatabaseService
from utils.privacy import redact_sensitive_data

class AnalysisEngine:
    """Main analysis engine coordinating Gemini API calls"""
    
    def __init__(self):
        self.gemini = GeminiClient()
        self.db = DatabaseService()
        self.analysis_queue = asyncio.Queue()
        self.running = False
    
    async def start(self):
        """Start processing analysis queue"""
        self.running = True
        print("[AnalysisEngine] Started")
        
        while self.running:
            try:
                # Get next item from queue
                capture_data = await self.analysis_queue.get()
                
                # Analyze
                analysis = await self.analyze_capture(capture_data)
                
                # Store results
                await self.store_analysis(capture_data, analysis)
                
                # Mark task as done
                self.analysis_queue.task_done()
                
            except Exception as e:
                print(f"[AnalysisEngine] Error: {e}")
                await asyncio.sleep(1)
    
    async def queue_capture(self, capture_data: Dict):
        """Add capture to analysis queue"""
        await self.analysis_queue.put(capture_data)
    
    async def analyze_capture(self, capture_data: Dict) -> Dict:
        """Analyze a single capture"""
        
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
        if 'extracted_text' in analysis:
            analysis['extracted_text'] = redact_sensitive_data(
                analysis['extracted_text']
            )
        
        return analysis
    
    async def store_analysis(self, capture_data: Dict, analysis: Dict):
        """Store analysis results in database"""
        
        # Generate embedding for semantic search
        search_text = f"{analysis.get('activity', '')} {analysis.get('extracted_text', '')}"
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
        """Stop analysis engine"""
        self.running = False
        print("[AnalysisEngine] Stopped")
```

---

**This is Part 1 of the Implementation Guide. Continue to next file for remaining hours (5-12).**
