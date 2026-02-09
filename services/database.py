"""
Database Service for NEXUS

SQLite database operations for storing activities, events, sessions, and settings.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config


class DatabaseService:
    """
    SQLite database operations for NEXUS.
    
    Manages storage and retrieval of activities, events, and sessions.
    """
    
    def __init__(self, db_path: Path = None):
        """
        Initialize database service.
        
        Args:
            db_path: Path to SQLite database (default from Config)
        """
        self.db_path = db_path or Config.DB_PATH
        self.init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a new database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database schema."""
        conn = self._get_connection()
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
                priority TEXT DEFAULT 'low',
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
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON activities(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_activities_app_name ON activities(app_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_activities_tags ON activities(tags)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)')
        
        conn.commit()
        conn.close()
        
        print("[Database] Initialized")
    
    async def store_activity(self,
                            timestamp: datetime,
                            activity_type: str,
                            app_name: str,
                            window_title: str,
                            screenshot_path: str = None,
                            audio_path: str = None,
                            transcription: str = None,
                            analysis: Dict = None,
                            embedding: List[float] = None,
                            session_id: str = None) -> int:
        """
        Store an activity in the database.
        
        Args:
            timestamp: When activity occurred
            activity_type: Type of activity ('screen', 'audio', 'event')
            app_name: Application name
            window_title: Window title
            screenshot_path: Path to screenshot file
            audio_path: Path to audio file
            transcription: Audio transcription
            analysis: Gemini analysis results (dict)
            embedding: Vector embedding for semantic search
            session_id: Current session ID
            
        Returns:
            Activity ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Extract tags and priority from analysis
        tags = ','.join(analysis.get('tags', [])) if analysis else ''
        priority = analysis.get('priority', 'low') if analysis else 'low'
        
        cursor.execute('''
            INSERT INTO activities (
                timestamp, activity_type, app_name, window_title,
                screenshot_path, audio_path, transcription, analysis,
                tags, priority, session_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp.isoformat(),
            activity_type,
            app_name,
            window_title,
            screenshot_path,
            audio_path,
            transcription,
            json.dumps(analysis) if analysis else None,
            tags,
            priority,
            session_id
        ))
        
        activity_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Store embedding in vector database if provided
        if embedding:
            await self._store_embedding(activity_id, embedding, analysis or {})
        
        return activity_id
    
    async def _store_embedding(self, activity_id: int, embedding: List[float], metadata: Dict):
        """Store embedding in ChromaDB."""
        try:
            from services.vector_store import VectorStore
            vector_store = VectorStore()
            await vector_store.add_embedding(
                id=str(activity_id),
                embedding=embedding,
                metadata=metadata
            )
        except Exception as e:
            print(f"[Database] Error storing embedding: {e}")
    
    async def get_recent_activities(self, limit: int = 10) -> List[Dict]:
        """
        Get recent activities.
        
        Args:
            limit: Maximum number of activities to return
            
        Returns:
            List of activity dicts
        """
        conn = self._get_connection()
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
                try:
                    activity['analysis'] = json.loads(activity['analysis'])
                except json.JSONDecodeError:
                    activity['analysis'] = {}
            activities.append(activity)
        
        return activities
    
    async def search_activities(self,
                               query: str = None,
                               app_name: str = None,
                               start_time: datetime = None,
                               end_time: datetime = None,
                               tags: List[str] = None,
                               limit: int = 100) -> List[Dict]:
        """
        Search activities with filters.
        
        Args:
            query: Text to search for
            app_name: Filter by app name
            start_time: Start of time range
            end_time: End of time range
            tags: Filter by tags
            limit: Maximum results
            
        Returns:
            List of matching activities
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Build query dynamically
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
        
        if query:
            sql += " AND (window_title LIKE ? OR analysis LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])
        
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        activities = []
        for row in rows:
            activity = dict(row)
            if activity['analysis']:
                try:
                    activity['analysis'] = json.loads(activity['analysis'])
                except json.JSONDecodeError:
                    activity['analysis'] = {}
            activities.append(activity)
        
        return activities
    
    async def store_event(self,
                         event_type: str,
                         content: str,
                         related_activity_id: int = None,
                         user_action: str = None) -> int:
        """
        Store an event (alert, query, etc).
        
        Args:
            event_type: Type of event ('alert', 'query', 'reminder')
            content: Event content/message
            related_activity_id: Related activity ID
            user_action: User response ('accepted', 'dismissed', 'ignored')
            
        Returns:
            Event ID
        """
        conn = self._get_connection()
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
        
        event_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return event_id
    
    async def get_events(self, event_type: str = None, limit: int = 50) -> List[Dict]:
        """Get events, optionally filtered by type."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if event_type:
            cursor.execute('''
                SELECT * FROM events WHERE event_type = ?
                ORDER BY timestamp DESC LIMIT ?
            ''', (event_type, limit))
        else:
            cursor.execute('''
                SELECT * FROM events
                ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    async def cleanup_old_data(self):
        """Remove old screenshots and audio files based on retention settings."""
        cutoff_date = datetime.now() - timedelta(days=Config.SCREENSHOT_RETENTION_DAYS)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get old screenshots
        cursor.execute('''
            SELECT screenshot_path FROM activities
            WHERE timestamp < ? AND screenshot_path IS NOT NULL
        ''', (cutoff_date.isoformat(),))
        
        old_files = cursor.fetchall()
        deleted_count = 0
        
        # Delete files
        for (filepath,) in old_files:
            try:
                path = Path(filepath)
                if path.exists():
                    path.unlink()
                    deleted_count += 1
            except Exception as e:
                print(f"[Database] Error deleting {filepath}: {e}")
        
        # Clear paths in database
        cursor.execute('''
            UPDATE activities
            SET screenshot_path = NULL
            WHERE timestamp < ?
        ''', (cutoff_date.isoformat(),))
        
        # Same for audio
        cursor.execute('''
            SELECT audio_path FROM activities
            WHERE timestamp < ? AND audio_path IS NOT NULL
        ''', (cutoff_date.isoformat(),))
        
        old_audio = cursor.fetchall()
        for (filepath,) in old_audio:
            try:
                path = Path(filepath)
                if path.exists():
                    path.unlink()
                    deleted_count += 1
            except Exception:
                pass
        
        cursor.execute('''
            UPDATE activities
            SET audio_path = NULL
            WHERE timestamp < ?
        ''', (cutoff_date.isoformat(),))
        
        conn.commit()
        conn.close()
        
        print(f"[Database] Cleaned up {deleted_count} old files")
        return deleted_count
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM activities")
        activity_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM events")
        event_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM activities")
        time_range = cursor.fetchone()
        
        conn.close()
        
        return {
            'activity_count': activity_count,
            'event_count': event_count,
            'earliest_activity': time_range[0],
            'latest_activity': time_range[1]
        }
