"""
Query Engine for NEXUS

Natural language query processing for searching and synthesizing 
information from user's activity history.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from services.database import DatabaseService
from services.vector_store import VectorStore
from services.gemini_client import GeminiClient


class QueryEngine:
    """
    Natural language query processor.
    
    Handles user queries about their activity history.
    """
    
    def __init__(self):
        """Initialize the query engine."""
        self.db = DatabaseService()
        self.vector_store = VectorStore()
        self.gemini = GeminiClient()
    
    async def process_query(self, query: str) -> str:
        """
        Process a natural language query.
        
        Args:
            query: User's natural language question
            
        Returns:
            Natural language response
        """
        query_lower = query.lower().strip()
        
        # Determine query type
        query_type, params = self.classify_query(query_lower)
        
        # Execute appropriate search
        if query_type == 'temporal':
            activities = await self.temporal_search(params)
        elif query_type == 'semantic':
            activities = await self.semantic_search(query, params)
        elif query_type == 'entity':
            activities = await self.entity_search(params)
        elif query_type == 'stats':
            return await self.get_activity_stats()
        else:
            # Default to semantic search
            activities = await self.semantic_search(query, {})
        
        # Synthesize response
        response = await self.synthesize_response(query, activities)
        
        return response
    
    def classify_query(self, query: str) -> Tuple[str, Dict]:
        """
        Classify the type of query.
        
        Args:
            query: Lowercase query string
            
        Returns:
            Tuple of (query_type, params)
        """
        # Temporal queries
        temporal_patterns = [
            (r'today', 'today'),
            (r'yesterday', 'yesterday'),
            (r'this morning', 'this_morning'),
            (r'this afternoon', 'this_afternoon'),
            (r'this hour', 'this_hour'),
            (r'last hour', 'last_hour'),
            (r'last (\d+) hours?', 'last_n_hours'),
            (r'last week', 'last_week'),
            (r'this week', 'this_week'),
            (r'(\d+) minutes? ago', 'minutes_ago'),
            (r'just now', 'just_now'),
            (r'recently', 'recent'),
        ]
        
        for pattern, time_type in temporal_patterns:
            match = re.search(pattern, query)
            if match:
                params = {'time_type': time_type}
                if match.groups():
                    params['value'] = match.group(1)
                return ('temporal', params)
        
        # Entity queries
        entity_patterns = [
            r'about ([a-zA-Z]+)',
            r'with ([a-zA-Z]+)',
            r'from ([a-zA-Z]+)',
            r'in ([a-zA-Z]+)',
        ]
        
        if 'who' in query or 'person' in query or 'email from' in query:
            for pattern in entity_patterns:
                match = re.search(pattern, query)
                if match:
                    return ('entity', {'name': match.group(1)})
        
        # Stats queries
        # Stats queries - Only trigger for system-level stats
        system_stats_terms = ['activity stats', 'system stats', 'how many memories', 'total events', 'database size']
        if any(term in query for term in system_stats_terms):
            return ('stats', {})
        
        # Default semantic
        return ('semantic', {})
    
    async def temporal_search(self, params: Dict) -> List[Dict]:
        """
        Search activities by time range.
        
        Args:
            params: Time parameters from classify_query
            
        Returns:
            List of activities in time range
        """
        start_time, end_time = self.extract_time_range(params)
        
        activities = await self.db.search_activities(
            start_time=start_time,
            end_time=end_time,
            limit=50
        )
        
        return activities
    
    def extract_time_range(self, params: Dict) -> Tuple[datetime, datetime]:
        """
        Extract time range from parameters.
        
        Args:
            params: Time parameters
            
        Returns:
            Tuple of (start_time, end_time)
        """
        now = datetime.now()
        time_type = params.get('time_type', 'today')
        value = params.get('value')
        
        if time_type == 'today':
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif time_type == 'yesterday':
            yesterday = now - timedelta(days=1)
            start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = yesterday.replace(hour=23, minute=59, second=59)
        elif time_type == 'this_morning':
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(hour=12, minute=0, second=0, microsecond=0)
        elif time_type == 'this_afternoon':
            start = now.replace(hour=12, minute=0, second=0, microsecond=0)
            end = now
        elif time_type == 'this_hour':
            start = now.replace(minute=0, second=0, microsecond=0)
            end = now
        elif time_type == 'last_hour':
            start = now - timedelta(hours=1)
            end = now
        elif time_type == 'last_n_hours' and value:
            start = now - timedelta(hours=int(value))
            end = now
        elif time_type == 'last_week':
            start = now - timedelta(weeks=1)
            end = now
        elif time_type == 'this_week':
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        elif time_type == 'minutes_ago' and value:
            start = now - timedelta(minutes=int(value))
            end = now
        elif time_type == 'just_now':
            start = now - timedelta(minutes=5)
            end = now
        elif time_type == 'recent':
            start = now - timedelta(hours=2)
            end = now
        else:
            # Default to today
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        
        return start, end
    
    async def semantic_search(self, query: str, params: Dict) -> List[Dict]:
        """
        Search activities by semantic similarity with fallbacks.
        Parallelized for performance.
        """
        import asyncio
        unique_activities = {}

        # Stage 1: Vector Search
        try:
            results = await self.vector_store.search_by_text(query, limit=20)
            
            if results:
                activity_ids = [int(r['activity_id']) for r in results if r['activity_id'].isdigit()]
                # Parallel DB lookup
                tasks = [self.db.search_activities(query=str(aid), limit=1) for aid in activity_ids[:10]]
                db_results_list = await asyncio.gather(*tasks)
                
                for res_list in db_results_list:
                    if res_list:
                        act = res_list[0]
                        unique_activities[act['id']] = act
        except Exception as e:
            print(f"[QueryEngine] Vector search error: {e}")
        
        # Stage 2: Keyword Fallback (if few results)
        if len(unique_activities) < 5:
            keywords = [w for w in query.split() if len(w) > 3]
            # Parallel keyword search
            tasks = [self.db.search_activities(query=word, limit=10) for word in keywords]
            if tasks:
                keyword_results_list = await asyncio.gather(*tasks)
                for res_list in keyword_results_list:
                    for act in res_list:
                        unique_activities[act['id']] = act
        
        # Stage 3: Recent Context Fallback (if still no results)
        if not unique_activities:
             print("[QueryEngine] No matches found. Falling back to recent context.")
             recent_results = await self.db.get_recent_activities(limit=10)
             for act in recent_results:
                 unique_activities[act['id']] = act

        # Convert back to list and sort by time
        final_activities = list(unique_activities.values())
        final_activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return final_activities
    
    async def entity_search(self, params: Dict) -> List[Dict]:
        """
        Search activities mentioning a specific entity.
        
        Args:
            params: Entity parameters (name)
            
        Returns:
            List of activities mentioning entity
        """
        entity_name = params.get('name', '')
        
        return await self.db.search_activities(
            query=entity_name,
            limit=50
        )
    
    async def get_activity_stats(self) -> str:
        """
        Get activity statistics summary.
        
        Returns:
            Statistics as formatted string
        """
        stats = self.db.get_stats()
        
        response = f"""📊 **Activity Statistics**

• Total activities recorded: {stats['activity_count']:,}
• Total events (alerts, queries): {stats['event_count']:,}
• Earliest activity: {stats['earliest_activity'] or 'None'}
• Latest activity: {stats['latest_activity'] or 'None'}

Vector store contains {self.vector_store.get_count():,} memories for semantic search."""
        
        return response
    
    async def synthesize_response(self, query: str, activities: List[Dict]) -> str:
        """
        Generate natural language response from search results.
        
        Args:
            query: Original query
            activities: Found activities
            
        Returns:
            Natural language response
        """
        if not activities:
            return "I've checked your history, but I haven't recorded enough significant activity yet to answer that specific question. As you use your computer more, I'll build a better memory."
        
        # Build prompt for Gemini
        context_lines = []
        for i, act in enumerate(activities[:15]):
            timestamp = act.get('timestamp', 'Unknown')
            app = act.get('app_name', 'Unknown')
            analysis = act.get('analysis', {})
            desc = analysis.get('activity', 'Unknown') if isinstance(analysis, dict) else 'Unknown'
            title = act.get('window_title', '')
            
            context_lines.append(f"[{i+1}] {timestamp} | App: {app} | Title: {title} | Context: {desc}")
        
        context_block = "\n".join(context_lines)
        
        prompt = f"""You are NEXUS, an intelligent AI life OS.
User Query: "{query}"

Based on the following activity history, describe exactly what the user was doing.
If the exact answer isn't clear, summarize the user's recent actions.
Be helpful, specific, and conversational.

Activity History:
{context_block}

Answer:"""

        try:
            print(f"[QueryEngine] Synthesizing response with {len(activities)} activities")
            response = await self.gemini.chat_model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            print(f"[QueryEngine] Synthesis error: {e}")
            return self._fallback_list_response(activities)

    def _fallback_list_response(self, activities: List[Dict]) -> str:
        """Fallback to simple summary if AI fails."""
        if not activities:
            return "I couldn't find any recent activity."
            
        # Count top apps to summarize
        app_counts = {}
        for act in activities:
            app = act.get('app_name', 'Unknown')
            app_counts[app] = app_counts.get(app, 0) + 1
            
        # Sort by frequency
        sorted_apps = sorted(app_counts.items(), key=lambda x: x[1], reverse=True)
        top_app = sorted_apps[0][0]
        
        others = [a[0] for a in sorted_apps[1:3] if a[0] != top_app]
        
        response = f"I'm currently running in low-power mode (API limit), but I can see you've mostly been using **{top_app}**."
        
        if others:
            response += f" I also noticed activity in **{', '.join(others)}**."
            
        return response
