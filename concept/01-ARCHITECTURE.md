# NEXUS System Architecture

## 🏗 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                        │
│  (Electron Desktop App / Web Interface)                 │
│                                                          │
│  - Timeline Viewer                                      │
│  - Search Interface                                     │
│  - Settings & Controls                                  │
│  - Alert Notifications                                  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  NEXUS CORE ENGINE                      │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Capture    │  │   Analysis   │  │  Proactive   │ │
│  │   Manager    │──│   Engine     │──│   Agent      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Memory     │  │    Query     │  │  Knowledge   │ │
│  │   System     │──│   Engine     │──│  Synthesis   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  GEMINI 3 LAYER                         │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Gemini Live  │  │ Gemini Flash │  │  Gemini Pro  │ │
│  │     API      │  │     API      │  │     API      │ │
│  │              │  │              │  │              │ │
│  │ Real-time    │  │ Fast batch   │  │ Deep         │ │
│  │ analysis     │  │ processing   │  │ reasoning    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  DATA LAYER                             │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   SQLite     │  │   ChromaDB   │  │ Local File   │ │
│  │   Database   │  │   (Vectors)  │  │   Storage    │ │
│  │              │  │              │  │              │ │
│  │ Structured   │  │ Semantic     │  │ Screenshots  │ │
│  │ metadata     │  │ search       │  │ Audio files  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 📦 Core Components

### 1. Capture Manager

**Responsibility**: Continuously capture user activity

**Sub-components**:

#### Screen Capture Service
```python
class ScreenCaptureService:
    """Captures screenshots at regular intervals"""
    
    def __init__(self, interval=2):
        self.interval = interval  # seconds
        self.running = False
        
    async def start(self):
        """Start continuous capture"""
        
    async def capture_frame(self):
        """Capture single screenshot"""
        
    def get_active_window_info(self):
        """Get current application and window title"""
```

**Implementation Details**:
- Capture frequency: 2 seconds (configurable)
- Format: PNG for quality, JPEG for storage efficiency
- Resolution: Scaled to max 1920x1080 for API efficiency
- Metadata: timestamp, active app, window title

#### Audio Capture Service
```python
class AudioCaptureService:
    """Records system and microphone audio"""
    
    def __init__(self):
        self.sample_rate = 16000  # Hz
        self.channels = 1  # Mono
        
    async def start_recording(self):
        """Start continuous audio recording"""
        
    async def process_chunk(self, audio_data):
        """Process audio chunk for transcription"""
```

**Implementation Details**:
- Continuous recording in 30-second chunks
- Automatic silence detection (don't store silence)
- Speaker diarization (who said what)
- Background noise filtering

#### Context Capture Service
```python
class ContextCaptureService:
    """Captures additional context information"""
    
    def get_system_context(self):
        """Get CPU, memory, active processes"""
        
    def get_application_context(self):
        """Get foreground app details"""
        
    def get_clipboard_content(self):
        """Get clipboard (with privacy filters)"""
```

### 2. Analysis Engine

**Responsibility**: Process captured data with Gemini APIs

**Sub-components**:

#### Real-Time Analyzer (Gemini Live)
```python
class RealTimeAnalyzer:
    """Analyzes activity in real-time using Gemini Live API"""
    
    def __init__(self):
        self.gemini_live = GeminiLiveClient()
        self.context_window = []
        
    async def analyze_current_activity(self, screenshot, audio, context):
        """Analyze what user is doing right now"""
        
    async def detect_proactive_opportunities(self, analysis):
        """Identify when to help proactively"""
```

**Analysis Prompt Template**:
```
You are NEXUS, an AI assistant watching the user's activity.

Current Context:
- Screenshot: [image]
- Audio: [transcription]
- Active App: {app_name}
- Window Title: {window_title}
- Time: {timestamp}
- Recent Activity: {last_5_minutes}

Your Tasks:
1. Understand what the user is doing
2. Identify potential mistakes or issues
3. Detect opportunities to help
4. Flag if proactive interruption is needed

Respond in JSON:
{
  "activity": "description of what user is doing",
  "intent": "what user is trying to accomplish",
  "issues": ["potential problems detected"],
  "should_interrupt": true/false,
  "interrupt_message": "message to show user if interrupting",
  "context_tags": ["relevant tags for memory"],
  "priority": "low/medium/high"
}
```

#### Batch Analyzer (Gemini Flash)
```python
class BatchAnalyzer:
    """Process historical data in batches"""
    
    async def analyze_session(self, session_data):
        """Analyze a complete work session"""
        
    async def extract_insights(self, time_range):
        """Extract patterns and insights from time period"""
```

#### Deep Reasoner (Gemini Pro)
```python
class DeepReasoner:
    """Complex reasoning and synthesis"""
    
    async def synthesize_knowledge(self, query, context):
        """Deep analysis across multiple memories"""
        
    async def generate_insights(self, topic):
        """Generate novel insights about a topic"""
```

### 3. Memory System

**Responsibility**: Store and retrieve all captured data

**Database Schema**:

#### SQLite Schema
```sql
-- Main activity log
CREATE TABLE activities (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    activity_type TEXT,  -- 'screen', 'audio', 'event'
    app_name TEXT,
    window_title TEXT,
    screenshot_path TEXT,
    audio_path TEXT,
    transcription TEXT,
    analysis TEXT,  -- JSON from Gemini
    embedding_id TEXT,  -- Reference to ChromaDB
    tags TEXT,  -- Comma-separated tags
    priority INTEGER,
    session_id TEXT
);

-- Events (proactive alerts, user queries, etc)
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    event_type TEXT,  -- 'alert', 'query', 'reminder'
    content TEXT,
    related_activity_id INTEGER,
    user_action TEXT,  -- 'accepted', 'dismissed', 'ignored'
    FOREIGN KEY (related_activity_id) REFERENCES activities(id)
);

-- Sessions (group activities into work sessions)
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    start_time DATETIME,
    end_time DATETIME,
    session_type TEXT,  -- 'work', 'meeting', 'research'
    summary TEXT,
    productivity_score REAL
);

-- User preferences and settings
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

#### ChromaDB Collections
```python
# Vector embeddings for semantic search
collection = chromadb.Collection(
    name="nexus_memories",
    metadata={"description": "All user activities and contexts"}
)

# Document structure
{
    "id": "activity_12345",
    "embedding": [0.1, 0.2, ...],  # Generated by Gemini
    "metadata": {
        "timestamp": "2024-02-09T15:30:00",
        "app": "Chrome",
        "window": "Research Paper - arXiv",
        "activity_type": "reading",
        "tags": ["research", "AI", "transformers"]
    },
    "document": "Full text content of screen + transcription"
}
```

**Storage Strategy**:
- Screenshots: Compressed JPEG, 7-day rolling window
- Audio: MP3 format, 7-day rolling window
- Transcriptions: Full text in SQLite (permanent)
- Analysis JSON: Full JSON in SQLite (permanent)
- Embeddings: ChromaDB (permanent)

### 4. Proactive Agent

**Responsibility**: Decide when and how to help

**Decision Engine**:
```python
class ProactiveAgent:
    """Decides when to interrupt and help"""
    
    def __init__(self):
        self.rules = self.load_proactive_rules()
        self.user_preferences = self.load_user_preferences()
        
    async def evaluate_situation(self, analysis, context):
        """Decide if intervention is needed"""
        
        # Rule-based checks (fast)
        for rule in self.rules:
            if rule.matches(analysis):
                return self.create_intervention(rule, analysis)
        
        # AI-based reasoning (for complex situations)
        return await self.ai_evaluate(analysis, context)
    
    def create_intervention(self, rule, analysis):
        """Create intervention with appropriate urgency"""
```

**Proactive Rules**:
```python
PROACTIVE_RULES = [
    {
        "name": "email_no_attachment",
        "condition": lambda ctx: (
            "email" in ctx.app_name.lower() and
            "attach" in ctx.screen_text.lower() and
            not ctx.has_attachment
        ),
        "message": "⚠️ You mentioned an attachment but didn't attach anything",
        "urgency": "high",
        "action": "block_send"
    },
    {
        "name": "wrong_recipient",
        "condition": lambda ctx: (
            "email" in ctx.app_name.lower() and
            ctx.recipient_name != ctx.mentioned_name
        ),
        "message": "⚠️ Are you sure about the recipient? You mentioned {mentioned_name} but sending to {recipient_name}",
        "urgency": "critical",
        "action": "confirm_first"
    },
    {
        "name": "deadline_approaching",
        "condition": lambda ctx: (
            ctx.has_deadline_in_calendar and
            ctx.deadline_in_hours < 2 and
            not ctx.working_on_deadline_task
        ),
        "message": "⏰ Deadline '{task}' in {hours} hours - you're not working on it",
        "urgency": "medium",
        "action": "remind"
    },
    {
        "name": "duplicate_work",
        "condition": lambda ctx: (
            ctx.current_activity_similarity > 0.9 and
            ctx.similar_activity_date < 7_days_ago
        ),
        "message": "ℹ️ You did very similar work on {date}. Want to reuse it?",
        "urgency": "low",
        "action": "suggest"
    },
    {
        "name": "password_in_public",
        "condition": lambda ctx: (
            ctx.contains_password_pattern and
            not ctx.is_password_field and
            ctx.sharing_screen
        ),
        "message": "🚨 STOP! You're about to paste a password in a visible field!",
        "urgency": "critical",
        "action": "block_paste"
    }
]
```

### 5. Query Engine

**Responsibility**: Answer user questions about their history

**Query Types**:

#### 1. Temporal Queries
```python
"What was I doing on Tuesday at 3pm?"
"Show me my activity last week"
"When did I last work on project X?"
```

#### 2. Semantic Queries
```python
"Find all information about quantum computing"
"Show me research related to transformers"
"What have I learned about Python decorators?"
```

#### 3. Entity Queries
```python
"What did Sarah say about the budget?"
"Show me all emails from John"
"Find mentions of Company X"
```

#### 4. Analytical Queries
```python
"How productive was I last week?"
"What apps do I use most?"
"When am I most focused?"
```

**Query Processing Pipeline**:
```python
class QueryEngine:
    """Process natural language queries"""
    
    async def process_query(self, query: str):
        # 1. Classify query type
        query_type = await self.classify_query(query)
        
        # 2. Extract parameters
        params = await self.extract_parameters(query, query_type)
        
        # 3. Search memory
        results = await self.search_memory(query_type, params)
        
        # 4. Synthesize response
        response = await self.synthesize_response(query, results)
        
        return response
    
    async def search_memory(self, query_type, params):
        if query_type == "temporal":
            return await self.temporal_search(params)
        elif query_type == "semantic":
            return await self.semantic_search(params)
        elif query_type == "entity":
            return await self.entity_search(params)
```

### 6. Knowledge Synthesis

**Responsibility**: Connect insights across memories

```python
class KnowledgeSynthesis:
    """Generate insights from accumulated knowledge"""
    
    async def find_connections(self, topic: str):
        """Find related ideas across different activities"""
        
        # 1. Get all memories related to topic
        memories = await self.get_topic_memories(topic)
        
        # 2. Use Gemini to find non-obvious connections
        connections = await self.gemini_find_connections(memories)
        
        # 3. Generate insight summary
        insights = await self.generate_insights(connections)
        
        return insights
    
    async def gemini_find_connections(self, memories):
        prompt = f"""
        You are analyzing a person's accumulated knowledge.
        
        Here are {len(memories)} memories related to a topic:
        {self.format_memories(memories)}
        
        Find:
        1. Common patterns and themes
        2. Contradictions or tensions
        3. Novel connections between seemingly unrelated items
        4. Knowledge gaps
        5. Actionable insights
        
        Think deeply about non-obvious relationships.
        """
        
        return await self.gemini_pro.generate(prompt)
```

## 🔄 Data Flow

### Continuous Capture Flow
```
1. Screen Capture (every 2s)
   ↓
2. Audio Capture (continuous)
   ↓
3. Context Extraction (active app, window, etc)
   ↓
4. Send to Gemini Live API
   ↓
5. Receive Analysis + Embeddings
   ↓
6. Store in SQLite + ChromaDB
   ↓
7. Proactive Agent Evaluates
   ↓
8. If needed: Alert User
```

### Query Flow
```
1. User asks question
   ↓
2. Query Engine classifies query
   ↓
3. Search ChromaDB (semantic) + SQLite (structured)
   ↓
4. Retrieve relevant memories
   ↓
5. Send to Gemini for synthesis
   ↓
6. Generate response
   ↓
7. Display to user with sources
```

## 🔐 Security Architecture

### Encryption
- All data encrypted at rest (AES-256)
- Screenshots encrypted before storage
- Audio files encrypted before storage
- Database encrypted with user passkey

### Privacy Controls
```python
class PrivacyManager:
    """Manages privacy and data access"""
    
    def __init__(self):
        self.excluded_apps = set()  # Apps to never capture
        self.redaction_patterns = []  # Regex patterns to redact
        self.pause_keywords = []  # Auto-pause on these keywords
        
    def should_capture(self, context) -> bool:
        """Decide if current activity should be captured"""
        
    def redact_sensitive_data(self, content) -> str:
        """Remove passwords, credit cards, etc"""
```

### Privacy Patterns
```python
REDACTION_PATTERNS = [
    r'\b\d{16}\b',  # Credit card numbers
    r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
    r'password[:\s]*\S+',  # Passwords
    r'api[_-]?key[:\s]*\S+',  # API keys
]

AUTO_PAUSE_APPS = [
    "Incognito",
    "Private",
    "Banking",
    "Password Manager"
]
```

## ⚡ Performance Optimization

### Capture Optimization
- Adaptive capture rate: slower when idle, faster when active
- Duplicate frame detection: don't store identical screens
- Compression: JPEG quality based on content importance
- Background processing: all analysis async

### Storage Optimization
- Rolling window for binary data (7 days)
- Permanent storage for text and analysis
- Automatic cleanup of old data
- Compression for archived data

### Query Optimization
- Index on timestamps, apps, tags
- Vector search with HNSW algorithm
- Caching of frequent queries
- Lazy loading of screenshots

## 🧪 Testing Strategy

### Unit Tests
- Each component tested independently
- Mock Gemini API responses
- Test privacy filters
- Test proactive rules

### Integration Tests
- End-to-end capture → analysis → storage
- Query accuracy tests
- Proactive alert timing tests

### Performance Tests
- Load test with 1000s of activities
- Query speed benchmarks
- Memory usage monitoring
- Storage size tracking

## 📊 Monitoring & Metrics

### System Metrics
- Capture rate (frames/second)
- Analysis latency
- Storage usage
- Memory consumption
- API costs

### User Metrics
- Proactive alerts triggered
- Alerts accepted vs dismissed
- Queries per day
- Time saved (estimated)

---

This architecture provides a solid foundation for building NEXUS in 12 hours while maintaining scalability for future enhancements.
