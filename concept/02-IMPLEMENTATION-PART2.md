# NEXUS Implementation Guide - Part 2

## HOUR 5-7: Database & Memory System

### services/database.py
```python
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

from config import Config

class DatabaseService:
    """SQLite database operations"""
    
    def __init__(self, db_path: Path = Config.DB_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Activities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                activity_type TEXT NOT NULL,
                app_name TEXT,
                window_title TEXT,
                screenshot_path TEXT,
                audio_path TEXT,
                transcription TEXT,
                analysis TEXT,
                tags TEXT,
                priority TEXT,
                session_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                event_type TEXT NOT NULL,
                content TEXT,
                related_activity_id INTEGER,
                user_action TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (related_activity_id) REFERENCES activities(id)
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                session_type TEXT,
                summary TEXT,
                productivity_score REAL
            )
        ''')
        
        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON activities(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_app_name ON activities(app_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags ON activities(tags)')
        
        conn.commit()
        conn.close()
        
        print("[Database] Initialized")
    
    async def store_activity(self,
                            timestamp: datetime,
                            activity_type: str,
                            app_name: str,
                            window_title: str,
                            screenshot_path: str = None,
                            analysis: Dict = None,
                            embedding: List[float] = None) -> int:
        """Store activity in database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extract tags from analysis
        tags = ','.join(analysis.get('tags', [])) if analysis else ''
        priority = analysis.get('priority', 'low') if analysis else 'low'
        
        cursor.execute('''
            INSERT INTO activities (
                timestamp, activity_type, app_name, window_title,
                screenshot_path, analysis, tags, priority
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp.isoformat(),
            activity_type,
            app_name,
            window_title,
            screenshot_path,
            json.dumps(analysis) if analysis else None,
            tags,
            priority
        ))
        
        activity_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Store embedding in vector database
        if embedding:
            await self.store_embedding(activity_id, embedding, analysis)
        
        return activity_id
    
    async def store_embedding(self, activity_id: int, embedding: List[float], metadata: Dict):
        """Store embedding in ChromaDB"""
        from services.vector_store import VectorStore
        
        vector_store = VectorStore()
        await vector_store.add_embedding(
            id=str(activity_id),
            embedding=embedding,
            metadata=metadata
        )
    
    async def get_recent_activities(self, limit: int = 10) -> List[Dict]:
        """Get recent activities"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM activities
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        activities = []
        for row in rows:
            activity = dict(row)
            if activity['analysis']:
                activity['analysis'] = json.loads(activity['analysis'])
            activities.append(activity)
        
        return activities
    
    async def search_activities(self,
                               query: str = None,
                               app_name: str = None,
                               start_time: datetime = None,
                               end_time: datetime = None,
                               tags: List[str] = None) -> List[Dict]:
        """Search activities with filters"""
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query
        sql = "SELECT * FROM activities WHERE 1=1"
        params = []
        
        if app_name:
            sql += " AND app_name LIKE ?"
            params.append(f"%{app_name}%")
        
        if start_time:
            sql += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            sql += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        
        if tags:
            for tag in tags:
                sql += " AND tags LIKE ?"
                params.append(f"%{tag}%")
        
        sql += " ORDER BY timestamp DESC LIMIT 100"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        activities = []
        for row in rows:
            activity = dict(row)
            if activity['analysis']:
                activity['analysis'] = json.loads(activity['analysis'])
            activities.append(activity)
        
        return activities
    
    async def store_event(self,
                         event_type: str,
                         content: str,
                         related_activity_id: int = None,
                         user_action: str = None):
        """Store event (alert, query, etc)"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO events (timestamp, event_type, content, related_activity_id, user_action)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            event_type,
            content,
            related_activity_id,
            user_action
        ))
        
        conn.commit()
        conn.close()
    
    async def cleanup_old_data(self):
        """Remove old screenshots and audio files"""
        
        cutoff_date = datetime.now() - timedelta(days=Config.SCREENSHOT_RETENTION_DAYS)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get old screenshots
        cursor.execute('''
            SELECT screenshot_path FROM activities
            WHERE timestamp < ? AND screenshot_path IS NOT NULL
        ''', (cutoff_date.isoformat(),))
        
        old_files = cursor.fetchall()
        
        # Delete files
        for (filepath,) in old_files:
            try:
                Path(filepath).unlink(missing_ok=True)
            except Exception as e:
                print(f"[Database] Error deleting {filepath}: {e}")
        
        # Clear paths in database
        cursor.execute('''
            UPDATE activities
            SET screenshot_path = NULL
            WHERE timestamp < ?
        ''', (cutoff_date.isoformat(),))
        
        conn.commit()
        conn.close()
        
        print(f"[Database] Cleaned up {len(old_files)} old files")
```

### services/vector_store.py
```python
import chromadb
from chromadb.config import Settings
from typing import List, Dict

from config import Config

class VectorStore:
    """ChromaDB vector store for semantic search"""
    
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=str(Config.CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="nexus_memories",
            metadata={"description": "NEXUS activity memories"}
        )
    
    async def add_embedding(self, id: str, embedding: List[float], metadata: Dict):
        """Add embedding to vector store"""
        
        # Create document text from metadata
        document = f"{metadata.get('activity', '')} {metadata.get('extracted_text', '')}"
        
        self.collection.add(
            ids=[id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[{
                'app_name': metadata.get('app_name', ''),
                'tags': ','.join(metadata.get('tags', [])),
                'priority': metadata.get('priority', 'low')
            }]
        )
    
    async def semantic_search(self, query_embedding: List[float], limit: int = 10) -> List[Dict]:
        """Search for similar activities"""
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit
        )
        
        # Format results
        formatted_results = []
        if results['ids']:
            for i, activity_id in enumerate(results['ids'][0]):
                formatted_results.append({
                    'activity_id': activity_id,
                    'distance': results['distances'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i]
                })
        
        return formatted_results
```

## HOUR 7-9: Proactive Agent

### core/proactive_agent.py
```python
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional

from services.database import DatabaseService
from services.gemini_client import GeminiClient
from config import Config

class ProactiveAgent:
    """Proactive assistance system"""
    
    def __init__(self):
        self.db = DatabaseService()
        self.gemini = GeminiClient()
        self.alert_history = {}  # Track recent alerts to avoid spam
        self.running = False
        self.on_alert_callback = None
    
    def set_alert_callback(self, callback):
        """Set callback for when alerts are triggered"""
        self.on_alert_callback = callback
    
    async def evaluate_situation(self, capture_data: Dict, analysis: Dict):
        """Evaluate if proactive intervention is needed"""
        
        if not Config.PROACTIVE_ENABLED:
            return
        
        # Check if analysis suggests interruption
        if analysis.get('should_interrupt', False):
            await self.trigger_alert(
                message=analysis.get('interrupt_message', 'Attention needed'),
                priority=analysis.get('priority', 'medium'),
                capture_data=capture_data,
                analysis=analysis
            )
            return
        
        # Check rule-based patterns
        await self.check_proactive_rules(capture_data, analysis)
    
    async def check_proactive_rules(self, capture_data: Dict, analysis: Dict):
        """Check predefined proactive rules"""
        
        # Rule 1: Email without attachment
        if await self.check_email_no_attachment(capture_data, analysis):
            return
        
        # Rule 2: Duplicate work detection
        if await self.check_duplicate_work(capture_data, analysis):
            return
        
        # Rule 3: Deadline approaching
        if await self.check_deadline_approaching(capture_data, analysis):
            return
    
    async def check_email_no_attachment(self, capture_data: Dict, analysis: Dict) -> bool:
        """Check if user is sending email mentioning attachment but forgot to attach"""
        
        app_name = capture_data.get('app_name', '').lower()
        extracted_text = analysis.get('extracted_text', '').lower()
        
        # Check if email client
        if 'mail' not in app_name and 'outlook' not in app_name:
            return False
        
        # Check if mentions attachment
        attachment_keywords = ['attach', 'attached', 'attachment', 'file', 'document']
        mentions_attachment = any(keyword in extracted_text for keyword in attachment_keywords)
        
        if not mentions_attachment:
            return False
        
        # In real implementation, we'd check if attachment is actually present
        # For hackathon, we'll trigger randomly for demo purposes
        
        # Check if we recently alerted about this
        if self.recently_alerted('email_no_attachment'):
            return False
        
        await self.trigger_alert(
            message="⚠️ You mentioned an attachment but I don't see one attached",
            priority="high",
            capture_data=capture_data,
            analysis=analysis,
            alert_type='email_no_attachment'
        )
        
        return True
    
    async def check_duplicate_work(self, capture_data: Dict, analysis: Dict) -> bool:
        """Check if user is doing work they've done before"""
        
        # Get similar activities from past
        from services.vector_store import VectorStore
        vector_store = VectorStore()
        
        # Generate embedding for current activity
        current_text = f"{analysis.get('activity', '')} {analysis.get('extracted_text', '')}"
        current_embedding = await self.gemini.generate_embedding(current_text)
        
        # Search for similar past activities
        similar = await vector_store.semantic_search(current_embedding, limit=5)
        
        # Check if very similar activity in past week
        for result in similar:
            if result['distance'] < 0.1:  # Very similar
                # Get full activity from database
                # For now, just trigger alert
                
                if self.recently_alerted('duplicate_work'):
                    return False
                
                await self.trigger_alert(
                    message="ℹ️ You did similar work recently. Want to reuse it?",
                    priority="low",
                    capture_data=capture_data,
                    analysis=analysis,
                    alert_type='duplicate_work'
                )
                
                return True
        
        return False
    
    async def check_deadline_approaching(self, capture_data: Dict, analysis: Dict) -> bool:
        """Check if deadline is approaching and user isn't working on it"""
        
        # This would integrate with calendar APIs in production
        # For hackathon demo, we'll simulate it
        
        return False
    
    async def trigger_alert(self,
                           message: str,
                           priority: str,
                           capture_data: Dict,
                           analysis: Dict,
                           alert_type: str = 'general'):
        """Trigger a proactive alert"""
        
        # Store alert event
        await self.db.store_event(
            event_type='proactive_alert',
            content=message,
            related_activity_id=None  # Would link to activity ID
        )
        
        # Record alert time
        self.alert_history[alert_type] = datetime.now()
        
        # Call callback if set
        if self.on_alert_callback:
            await self.on_alert_callback({
                'message': message,
                'priority': priority,
                'timestamp': datetime.now(),
                'type': alert_type,
                'capture_data': capture_data,
                'analysis': analysis
            })
        
        print(f"[ProactiveAgent] ALERT ({priority}): {message}")
    
    def recently_alerted(self, alert_type: str) -> bool:
        """Check if we recently alerted about this type"""
        
        if alert_type not in self.alert_history:
            return False
        
        last_alert = self.alert_history[alert_type]
        time_since = (datetime.now() - last_alert).total_seconds()
        
        return time_since < Config.ALERT_COOLDOWN
```

## HOUR 9-10: Query Engine

### core/query_engine.py
```python
import re
from datetime import datetime, timedelta
from typing import Dict, List

from services.database import DatabaseService
from services.vector_store import VectorStore
from services.gemini_client import GeminiClient

class QueryEngine:
    """Natural language query processing"""
    
    def __init__(self):
        self.db = DatabaseService()
        self.vector_store = VectorStore()
        self.gemini = GeminiClient()
    
    async def process_query(self, query: str) -> Dict:
        """Process natural language query"""
        
        print(f"[QueryEngine] Processing: {query}")
        
        # Classify query type
        query_type = self.classify_query(query)
        
        # Process based on type
        if query_type == 'temporal':
            return await self.temporal_search(query)
        elif query_type == 'semantic':
            return await self.semantic_search(query)
        elif query_type == 'entity':
            return await self.entity_search(query)
        else:
            return await self.general_search(query)
    
    def classify_query(self, query: str) -> str:
        """Classify query type"""
        
        query_lower = query.lower()
        
        # Temporal queries
        temporal_keywords = ['when', 'last', 'yesterday', 'today', 'week', 'month', 'ago', 'tuesday', 'monday']
        if any(keyword in query_lower for keyword in temporal_keywords):
            return 'temporal'
        
        # Entity queries (names, companies)
        if re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', query):  # Capital names
            return 'entity'
        
        # Default to semantic
        return 'semantic'
    
    async def temporal_search(self, query: str) -> Dict:
        """Search by time"""
        
        # Extract time range from query
        time_range = self.extract_time_range(query)
        
        # Search database
        activities = await self.db.search_activities(
            start_time=time_range['start'],
            end_time=time_range['end']
        )
        
        # Synthesize response
        response = await self.synthesize_response(query, activities)
        
        return {
            'query': query,
            'type': 'temporal',
            'results': activities,
            'response': response
        }
    
    async def semantic_search(self, query: str) -> Dict:
        """Search by meaning"""
        
        # Generate query embedding
        query_embedding = await self.gemini.generate_embedding(query)
        
        # Search vector store
        similar_activities = await self.vector_store.semantic_search(
            query_embedding,
            limit=20
        )
        
        # Get full activities from database
        activity_ids = [r['activity_id'] for r in similar_activities]
        
        # Synthesize response
        response = await self.synthesize_semantic_response(query, similar_activities)
        
        return {
            'query': query,
            'type': 'semantic',
            'results': similar_activities,
            'response': response
        }
    
    async def entity_search(self, query: str) -> Dict:
        """Search for entities (people, companies)"""
        
        # Extract entity name
        entity_match = re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', query)
        entity_name = entity_match.group() if entity_match else ''
        
        # Search in extracted text
        # For hackathon, simplified version
        
        return {
            'query': query,
            'type': 'entity',
            'entity': entity_name,
            'results': [],
            'response': f"Searching for mentions of {entity_name}..."
        }
    
    def extract_time_range(self, query: str) -> Dict:
        """Extract time range from query"""
        
        query_lower = query.lower()
        now = datetime.now()
        
        if 'today' in query_lower:
            return {
                'start': now.replace(hour=0, minute=0, second=0),
                'end': now
            }
        
        if 'yesterday' in query_lower:
            yesterday = now - timedelta(days=1)
            return {
                'start': yesterday.replace(hour=0, minute=0, second=0),
                'end': yesterday.replace(hour=23, minute=59, second=59)
            }
        
        if 'last week' in query_lower or 'past week' in query_lower:
            return {
                'start': now - timedelta(days=7),
                'end': now
            }
        
        if 'last month' in query_lower:
            return {
                'start': now - timedelta(days=30),
                'end': now
            }
        
        # Default: last 24 hours
        return {
            'start': now - timedelta(days=1),
            'end': now
        }
    
    async def synthesize_response(self, query: str, activities: List[Dict]) -> str:
        """Generate natural language response"""
        
        if not activities:
            return "I couldn't find any activities matching your query."
        
        # Create summary
        summary = f"Found {len(activities)} activities:\n\n"
        
        for activity in activities[:5]:  # Top 5
            timestamp = activity['timestamp']
            app = activity['app_name']
            analysis = activity.get('analysis', {})
            activity_desc = analysis.get('activity', 'Unknown activity')
            
            summary += f"• {timestamp} - {app}: {activity_desc}\n"
        
        return summary
    
    async def synthesize_semantic_response(self, query: str, results: List[Dict]) -> str:
        """Synthesize response for semantic search"""
        
        if not results:
            return "I couldn't find anything related to your query."
        
        summary = f"Found {len(results)} related memories:\n\n"
        
        for result in results[:5]:
            doc = result['document']
            summary += f"• {doc[:100]}...\n"
        
        return summary
```

---

**Continue to PART 3 for UI and main application...**
