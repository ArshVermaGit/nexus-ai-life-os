"""
Knowledge Synthesis Engine for NEXUS

Connects insights across memories and generates novel discoveries.
Built for Google Gemini Hackathon 2026.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.gemini_client import GeminiClient
from services.database import DatabaseService
from services.vector_store import VectorStore


class KnowledgeSynthesis:
    """
    Knowledge Synthesis Engine.
    
    Connects ideas across:
    - Articles you've read
    - Videos you've watched
    - Meetings you've attended
    - Documents you've created
    - Conversations you've had
    
    Then generates insights you wouldn't have seen yourself.
    """
    
    def __init__(self):
        """Initialize knowledge synthesis engine."""
        self.gemini = GeminiClient()
        self.db = DatabaseService()
        self.vector_store = VectorStore()
    
    async def find_connections(self, topic: str, days: int = 30) -> Dict:
        """
        Find related ideas across different activities.
        
        Args:
            topic: Topic to find connections for
            days: Number of days to look back
            
        Returns:
            Dictionary with patterns, connections, gaps, insights
        """
        print(f"[KnowledgeSynthesis] Finding connections for: {topic}")
        
        # Get all memories related to topic
        memories = await self.get_topic_memories(topic, days)
        
        if not memories:
            return {
                'patterns': [],
                'connections': [],
                'gaps': ['No memories found for this topic'],
                'insights': [],
                'summary': f'No activities found related to "{topic}" in the past {days} days.'
            }
        
        # Use Gemini to find non-obvious connections
        synthesis = await self.gemini.synthesize_knowledge(memories, topic)
        
        # Add metadata
        synthesis['topic'] = topic
        synthesis['memories_analyzed'] = len(memories)
        synthesis['time_range_days'] = days
        synthesis['generated_at'] = datetime.now().isoformat()
        
        return synthesis
    
    async def get_topic_memories(self, topic: str, days: int = 30) -> List[Dict]:
        """
        Get all memories related to a topic using semantic search.
        
        Args:
            topic: Topic to search for
            days: Number of days to look back
            
        Returns:
            List of relevant memories
        """
        # Generate embedding for the topic
        topic_embedding = await self.gemini.generate_query_embedding(topic)
        
        # Search vector store
        results = await self.vector_store.semantic_search(topic_embedding, limit=50)
        
        # Format results
        memories = []
        for result in results:
            memories.append({
                'activity_id': result.get('activity_id'),
                'activity': result.get('document', ''),
                'timestamp': result.get('metadata', {}).get('timestamp', 'Unknown'),
                'tags': result.get('metadata', {}).get('tags', '').split(',') if result.get('metadata', {}).get('tags') else [],
                'distance': result.get('distance', 0)
            })
        
        return memories
    
    async def daily_insights(self) -> Dict:
        """
        Generate daily insights from recent activity.
        
        Returns:
            Daily insights summary
        """
        # Get today's activities
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        activities = await self.db.search_activities(start_time=today_start)
        
        if not activities:
            return {
                'summary': 'No activities recorded today.',
                'patterns': [],
                'suggestions': []
            }
        
        # Format activities for synthesis
        formatted = []
        for act in activities:
            analysis = act.get('analysis', {})
            if isinstance(analysis, str):
                import json
                try:
                    analysis = json.loads(analysis)
                except:
                    analysis = {}
            
            formatted.append({
                'activity': analysis.get('activity', 'Unknown'),
                'timestamp': act.get('timestamp', 'Unknown'),
                'tags': analysis.get('tags', []),
                'app_name': act.get('app_name', 'Unknown')
            })
        
        # Generate insights
        return await self.gemini.synthesize_knowledge(formatted, "today's activities")
    
    async def find_related_work(self, current_activity: str) -> List[Dict]:
        """
        Find related past work for the current activity.
        
        Args:
            current_activity: Description of current activity
            
        Returns:
            List of related past activities
        """
        # Generate embedding for current activity
        embedding = await self.gemini.generate_query_embedding(current_activity)
        
        # Search for similar past work
        results = await self.vector_store.semantic_search(embedding, limit=10)
        
        # Filter out very recent (to avoid finding the same activity)
        related = []
        for result in results:
            if result.get('distance', 0) < 0.5:  # Only similar activities
                related.append({
                    'activity': result.get('document', ''),
                    'similarity': 1 - result.get('distance', 0),
                    'metadata': result.get('metadata', {})
                })
        
        return related
    
    async def pattern_detection(self, days: int = 7) -> Dict:
        """
        Detect patterns in user behavior over time.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Detected patterns and suggestions
        """
        start_time = datetime.now() - timedelta(days=days)
        activities = await self.db.search_activities(start_time=start_time)
        
        if len(activities) < 5:
            return {
                'patterns': [],
                'suggestions': [],
                'message': 'Not enough data for pattern detection.'
            }
        
        # Analyze app usage patterns
        app_counts = {}
        hour_activity = {}
        
        for act in activities:
            app = act.get('app_name', 'Unknown')
            app_counts[app] = app_counts.get(app, 0) + 1
            
            # Get hour if timestamp is available
            timestamp = act.get('timestamp')
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        from datetime import datetime as dt
                        timestamp = dt.fromisoformat(timestamp.replace('Z', '+00:00'))
                    hour = timestamp.hour
                    hour_activity[hour] = hour_activity.get(hour, 0) + 1
                except:
                    pass
        
        # Find top apps
        top_apps = sorted(app_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Find peak hours
        peak_hours = sorted(hour_activity.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'top_apps': [{'app': app, 'count': count} for app, count in top_apps],
            'peak_hours': [{'hour': hour, 'count': count} for hour, count in peak_hours],
            'total_activities': len(activities),
            'days_analyzed': days,
            'patterns': [
                f"Most used app: {top_apps[0][0]} ({top_apps[0][1]} activities)" if top_apps else "No app data",
                f"Peak productivity: {peak_hours[0][0]}:00" if peak_hours else "No time data"
            ],
            'suggestions': [
                "Consider time-blocking your most productive hours",
                f"You spend the most time in {top_apps[0][0] if top_apps else 'unknown apps'}"
            ]
        }
