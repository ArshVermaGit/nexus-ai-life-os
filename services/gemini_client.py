"""
Google Gemini Client for NEXUS

Wrapper for Google Gemini API for screen analysis and embeddings.
Built for Google Gemini Hackathon 2026.
"""

import google.generativeai as genai
import base64
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config


class GeminiClient:
    """
    Wrapper for Google Gemini API.
    
    Provides:
    - Vision analysis of screenshots
    - Native embedding generation for semantic search
    - Chat/query capabilities
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to reuse client."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the Gemini client."""
        if self._initialized:
            return
            
        if not Config.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not set. Please set it in .env file.")
        
        # Configure Gemini API
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        
        # Initialize models
        self.vision_model = genai.GenerativeModel(Config.GEMINI_MODEL)
        self.chat_model = genai.GenerativeModel(Config.GEMINI_MODEL)
        
        self._initialized = True
        print(f"[GeminiClient] Initialized with {Config.GEMINI_MODEL}")
    
    async def analyze_screen(self,
                            image_path: str,
                            app_name: str,
                            window_title: str,
                            ocr_text: str = "",
                            recent_context: Optional[List[Dict]] = None) -> Dict:
        """
        Analyze a screenshot using Gemini's vision capabilities.
        
        Args:
            image_path: Path to screenshot file
            app_name: Active application name
            window_title: Active window title
            recent_context: List of recent activities for context
            
        Returns:
            Analysis results dict with activity, intent, issues, tags, priority
        """
        try:
            # Read image file
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Create image part for Gemini
            image_part = {
                "mime_type": "image/jpeg",
                "data": image_data
            }
            
            # Build context from recent activity
            context_text = ""
            if recent_context:
                context_lines = []
                for act in recent_context[-5:]:  # Last 5 activities
                    timestamp = act.get('timestamp', 'Unknown')
                    app = act.get('app_name', 'Unknown')
                    analysis = act.get('analysis', {})
                    activity = analysis.get('activity', 'Unknown') if isinstance(analysis, dict) else 'Unknown'
                    context_lines.append(f"- {timestamp}: {app} - {activity}")
                context_text = "\n".join(context_lines)
            
            # Create analysis prompt
            prompt = f"""You are NEXUS, an AI assistant that watches the user's computer activity to help them be more productive.

Current Context:
- Active Application: {app_name}
- Window Title: {window_title}
- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Recent Activity:
{context_text if context_text else "No recent activity recorded."}

OCR Extracted Text (Fallback):
{ocr_text if ocr_text else "No text extracted by OCR."}

Analyze this screenshot and identify:

1. What is the user doing right now?
2. What are they trying to accomplish?
3. Are there any potential issues or mistakes about to happen?
   - Email without attachment mentioned
   - Wrong recipient
   - About to delete important files
   - Pasting sensitive info in public places
4. Should we interrupt the user with a proactive alert?
5. Relevant tags for this activity

Respond ONLY with valid JSON (no markdown, no explanation):
{{
  "activity": "brief description of what user is doing",
  "intent": "what user is trying to accomplish",
  "issues": ["list any potential issues or empty array"],
  "should_interrupt": false,
  "interrupt_message": "message to show if interrupting, or empty string",
  "tags": ["relevant", "tags"],
  "priority": "low",
  "extracted_text": "any important text visible on screen"
}}"""

            # Call Gemini Vision API
            response = self.vision_model.generate_content([prompt, image_part])
            response_text = response.text
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                analysis = self._default_analysis(app_name)
            
            # Validate and return
            return self._validate_analysis(analysis)
            
        except Exception as e:
            print(f"[GeminiClient] Error analyzing screen: {e}")
            return self._default_analysis(app_name, error=str(e))
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for semantic search using Gemini's native embeddings.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (768 dimensions)
        """
        if not text or not text.strip():
            return [0.0] * 768
        
        try:
            # Use Gemini's embedding model
            result = genai.embed_content(
                model=Config.GEMINI_EMBEDDING_MODEL,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
            
        except Exception as e:
            print(f"[GeminiClient] Embedding error: {e}")
            # Fallback to hash-based embedding
            return self._fallback_embedding(text)
    
    async def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for query (optimized for search).
        
        Args:
            query: Search query text
            
        Returns:
            Embedding vector
        """
        if not query or not query.strip():
            return [0.0] * 768
        
        try:
            result = genai.embed_content(
                model=Config.GEMINI_EMBEDDING_MODEL,
                content=query,
                task_type="retrieval_query"
            )
            return result['embedding']
            
        except Exception as e:
            print(f"[GeminiClient] Query embedding error: {e}")
            return self._fallback_embedding(query)
            
    async def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe an audio file using Gemini.
        
        Args:
            audio_path: Path to the WAV/MP3 file
            
        Returns:
            Transcription text
        """
        try:
            # Upload file to Gemini (or pass data directly if supported/small)
            # For now, we'll use the generative model with audio part
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            audio_part = {
                "mime_type": "audio/wav", # Assuming WAV from AudioCaptureService
                "data": audio_data
            }
            
            prompt = "Transcribe the following audio accurately. If there is speech, write it down. If there is no significant speech, say [No Speech Detected]."
            
            response = self.chat_model.generate_content([prompt, audio_part])
            return response.text.strip()
            
        except Exception as e:
            print(f"[GeminiClient] Audio transcription error: {e}")
            return f"[Error transcribing audio: {str(e)}]"
    
    async def chat(self, message: str, context: Optional[str] = None) -> str:
        """
        Chat with Gemini for query responses.
        
        Args:
            message: User message
            context: Optional context from retrieved memories
            
        Returns:
            Response text
        """
        try:
            prompt = message
            if context:
                prompt = f"""Based on the user's activity history:

{context}

User question: {message}

Provide a helpful, concise response based on the activity history above."""

            response = self.chat_model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            print(f"[GeminiClient] Chat error: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    async def quick_classify(self, text: str) -> Dict:
        """
        Quick classification of text.
        
        Args:
            text: Text to classify
            
        Returns:
            Classification with category, keywords, priority
        """
        try:
            prompt = f"""Classify this activity text briefly. Respond in JSON only:
Text: {text}

{{"category": "work/communication/research/entertainment/coding/other", "keywords": ["key", "words"], "priority": "low/medium/high"}}"""

            response = self.chat_model.generate_content(prompt)
            response_text = response.text
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {'category': 'other', 'keywords': [], 'priority': 'low'}
            
        except Exception as e:
            print(f"[GeminiClient] Classify error: {e}")
            return {'category': 'other', 'keywords': [], 'priority': 'low'}
    
    async def synthesize_knowledge(self, memories: List[Dict], topic: str) -> Dict:
        """
        Synthesize knowledge from multiple memories (for knowledge synthesis feature).
        
        Args:
            memories: List of memory dicts with activity data
            topic: Topic to synthesize around
            
        Returns:
            Synthesis with patterns, connections, insights, gaps
        """
        try:
            # Format memories for context
            memory_text = []
            for i, mem in enumerate(memories[:20]):  # Limit to 20 memories
                activity = mem.get('activity', 'Unknown')
                timestamp = mem.get('timestamp', 'Unknown')
                tags = mem.get('tags', [])
                memory_text.append(f"{i+1}. [{timestamp}] {activity} (tags: {', '.join(tags) if tags else 'none'})")
            
            prompt = f"""Analyze these memories related to "{topic}" and find insights:

{chr(10).join(memory_text)}

Identify:
1. Common patterns and themes
2. Novel connections between seemingly unrelated items
3. Knowledge gaps
4. Actionable insights

Respond in JSON only:
{{
  "patterns": ["pattern 1", "pattern 2"],
  "connections": ["connection between X and Y"],
  "gaps": ["missing knowledge areas"],
  "insights": ["actionable insight 1", "insight 2"],
  "summary": "one paragraph summary"
}}"""

            response = self.chat_model.generate_content(prompt)
            response_text = response.text
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {'patterns': [], 'connections': [], 'gaps': [], 'insights': [], 'summary': 'Unable to synthesize'}
            
        except Exception as e:
            print(f"[GeminiClient] Synthesis error: {e}")
            return {'patterns': [], 'connections': [], 'gaps': [], 'insights': [], 'summary': f'Error: {str(e)}'}
    
    def _validate_analysis(self, analysis: Dict) -> Dict:
        """Ensure analysis has all required fields with proper types."""
        defaults = {
            'activity': 'Unknown activity',
            'intent': 'Unknown',
            'issues': [],
            'should_interrupt': False,
            'interrupt_message': '',
            'tags': [],
            'priority': 'low',
            'extracted_text': ''
        }
        
        for key, default in defaults.items():
            if key not in analysis:
                analysis[key] = default
            if key == 'should_interrupt' and not isinstance(analysis[key], bool):
                analysis[key] = str(analysis[key]).lower() == 'true'
            if key in ['issues', 'tags'] and not isinstance(analysis[key], list):
                analysis[key] = [analysis[key]] if analysis[key] else []
        
        return analysis
    
    def _default_analysis(self, app_name: str = 'Unknown', error: str = None) -> Dict:
        """Return default analysis for error cases."""
        return {
            'activity': f'Using {app_name}',
            'intent': 'Unknown',
            'issues': [],
            'should_interrupt': False,
            'interrupt_message': '',
            'tags': [app_name.lower()] if app_name != 'Unknown' else [],
            'priority': 'low',
            'extracted_text': '',
            'error': error
        }
    
    def _fallback_embedding(self, text: str) -> List[float]:
        """Fallback hash-based embedding if API fails."""
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        embedding = []
        for i in range(768):
            byte_idx = i % 32
            variation = (i // 32) * 0.01
            value = (float(hash_bytes[byte_idx]) / 255.0) + variation
            embedding.append(value % 1.0)
        
        return embedding
