# MASTER BUILD PROMPT - NEXUS

**Copy this entire document and paste it into your AI coding assistant (Cursor, Aider, Claude, etc.) to build the complete NEXUS application in one go.**

---

# BUILD NEXUS: AI Life Operating System

I need you to build NEXUS - a complete AI-powered personal assistant application for the Google Gemini Hackathon. This is a production-ready system that monitors computer activity and provides proactive assistance.

## PROJECT OVERVIEW

**Name**: NEXUS - Your AI Life Operating System

**Core Concept**: An AI that watches everything you do on your computer, maintains perfect memory, and proactively helps you before mistakes happen.

**Key Features**:
1. **Perfect Memory**: Captures screen every 2 seconds, never forgets anything
2. **Proactive Alerts**: Prevents mistakes (email without attachment, wrong recipient, etc.)
3. **Semantic Search**: Find anything using natural language queries
4. **Knowledge Synthesis**: Connects insights across all activities
5. **Privacy First**: All data local, encrypted, user-controlled

**Target**: Win Google Gemini Hackathon ($100K prize)

**Time Constraint**: Must be buildable and demo-ready

---

## COMPLETE TECHNICAL SPECIFICATION

### Technology Stack
- **Language**: Python 3.10+
- **AI**: Anthropic Claude API (as Gemini)
- **Databases**: SQLite (structured) + ChromaDB (vectors)
- **Screen Capture**: mss library
- **UI**: Tkinter (desktop app)
- **Async**: asyncio for concurrent operations

### System Architecture

```
┌─────────────────────────────────────┐
│         USER INTERFACE              │
│  (Tkinter Desktop App)              │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│      NEXUS CORE ENGINE              │
│                                     │
│  ┌──────────┐  ┌──────────────┐   │
│  │ Capture  │→ │  Analysis    │   │
│  │ Manager  │  │  Engine      │   │
│  └──────────┘  └──────────────┘   │
│                      ↓              │
│  ┌──────────┐  ┌──────────────┐   │
│  │ Memory   │← │  Proactive   │   │
│  │ System   │  │  Agent       │   │
│  └──────────┘  └──────────────┘   │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│      GEMINI AI LAYER                │
│  (Claude API for Analysis)          │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│      DATA LAYER                     │
│  SQLite + ChromaDB + Files          │
└─────────────────────────────────────┘
```

---

## COMPLETE FILE STRUCTURE

Generate this exact structure:

```
nexus/
├── main.py                    # Entry point
├── config.py                  # Configuration
├── requirements.txt           # Dependencies
├── .env.example              # Environment template
├── README.md                 # Documentation
│
├── core/
│   ├── __init__.py
│   ├── capture_manager.py    # Screen capture
│   ├── analysis_engine.py    # AI analysis coordinator
│   ├── proactive_agent.py    # Proactive assistance
│   ├── query_engine.py       # Natural language queries
│   └── knowledge_synthesis.py # Insight generation
│
├── services/
│   ├── __init__.py
│   ├── gemini_client.py      # Claude API wrapper
│   ├── database.py           # SQLite operations
│   └── vector_store.py       # ChromaDB operations
│
├── models/
│   ├── __init__.py
│   ├── activity.py           # Data models
│   └── schemas.py            # Database schemas
│
├── ui/
│   ├── __init__.py
│   └── app.py               # Tkinter UI
│
├── utils/
│   ├── __init__.py
│   ├── privacy.py           # Privacy filters
│   ├── compression.py       # Image compression
│   └── helpers.py           # Utilities
│
└── data/                    # Created at runtime
    ├── screenshots/
    ├── audio/
    └── db/
        ├── nexus.db
        └── chroma/
```

---

## IMPLEMENTATION REQUIREMENTS

### 1. Project Configuration (config.py)

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
    SCREEN_CAPTURE_QUALITY = 85  # JPEG quality
    MAX_SCREENSHOT_WIDTH = 1920
    MAX_SCREENSHOT_HEIGHT = 1080
    
    # Storage Settings
    DATA_DIR = Path("data")
    SCREENSHOTS_DIR = DATA_DIR / "screenshots"
    AUDIO_DIR = DATA_DIR / "audio"
    DB_PATH = DATA_DIR / "db" / "nexus.db"
    CHROMA_DIR = DATA_DIR / "db" / "chroma"
    
    # Memory Settings
    SCREENSHOT_RETENTION_DAYS = 7
    
    # Proactive Settings
    PROACTIVE_ENABLED = True
    ALERT_COOLDOWN = 300  # seconds
    
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
        cls.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
```

### 2. Screen Capture System (core/capture_manager.py)

Requirements:
- Capture screenshot every 2 seconds using `mss` library
- Get active window info (app name, window title)
- Resize images to max 1920x1080
- Compress to JPEG format
- Check privacy filters before capturing
- Async implementation
- Callback mechanism for new captures

Key methods:
- `start()` - begin continuous capture
- `capture_frame()` - capture single screenshot
- `set_callback()` - register callback for new captures

### 3. Privacy System (utils/privacy.py)

Requirements:
- `get_active_window_info()` - detect active app/window (cross-platform)
- `should_capture()` - check if app should be captured
- `redact_sensitive_data()` - remove passwords, credit cards, SSNs, API keys
- Use regex patterns from Config

### 4. Database Layer (services/database.py)

Schema:
```sql
CREATE TABLE activities (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    activity_type TEXT,
    app_name TEXT,
    window_title TEXT,
    screenshot_path TEXT,
    analysis TEXT,  -- JSON
    tags TEXT,
    priority TEXT
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    event_type TEXT,
    content TEXT,
    related_activity_id INTEGER
);
```

Methods:
- `init_database()` - create schema
- `store_activity()` - save capture + analysis
- `get_recent_activities()` - fetch recent items
- `search_activities()` - search with filters
- `store_event()` - log alerts/queries
- `cleanup_old_data()` - remove old screenshots

### 5. Vector Store (services/vector_store.py)

Requirements:
- Use ChromaDB for semantic search
- `add_embedding()` - store vector + metadata
- `semantic_search()` - find similar activities
- Persistent storage in data/db/chroma/

### 6. Gemini Client (services/gemini_client.py)

Requirements:
- Use Anthropic Python SDK
- `analyze_screen()` - send screenshot to Claude, get analysis
- Send image as base64
- Structured prompt requesting JSON response with:
  * activity: what user is doing
  * intent: user's goal
  * issues: potential problems
  * should_interrupt: true/false
  * interrupt_message: alert text
  * tags: categorization tags
  * priority: low/medium/high
  * extracted_text: important text from screen
- `generate_embedding()` - create vector (simple hash-based for hackathon)
- Robust error handling
- Parse JSON from response

Prompt template:
```
You are NEXUS, an AI assistant watching the user's computer activity.

Current Context:
- Active Application: {app_name}
- Window Title: {window_title}
- Time: {timestamp}

Recent Activity:
{recent_context}

Analyze the screenshot and respond in JSON format ONLY:
{
  "activity": "description",
  "intent": "user's goal",
  "issues": ["list of issues"],
  "should_interrupt": true/false,
  "interrupt_message": "alert message",
  "tags": ["tag1", "tag2"],
  "priority": "low/medium/high",
  "extracted_text": "text from screen"
}
```

### 7. Analysis Engine (core/analysis_engine.py)

Requirements:
- Async queue processing
- `start()` - begin processing captures
- `queue_capture()` - add capture to queue
- `analyze_capture()` - coordinate Gemini analysis
- `store_analysis()` - save to database
- Get recent context for each analysis
- Apply privacy redaction to results

### 8. Proactive Agent (core/proactive_agent.py)

Requirements:
- `evaluate_situation()` - main decision function
- `check_proactive_rules()` - apply rules
- Implement these specific rules:
  1. **Email without attachment**: Detects "attach" keyword but no file
  2. **Duplicate work**: Finds very similar past activity
  3. **Wrong recipient**: Name mismatch in email
  4. **Password in public**: Password pattern in non-password field
- `trigger_alert()` - fire proactive alert
- `recently_alerted()` - prevent spam (5 min cooldown)
- Callback mechanism for UI
- Priority levels: low, medium, high, critical

### 9. Query Engine (core/query_engine.py)

Requirements:
- `process_query()` - handle natural language queries
- `classify_query()` - determine type (temporal/semantic/entity)
- `temporal_search()` - search by time
  * Parse: "today", "yesterday", "last week", "Tuesday at 3pm"
- `semantic_search()` - search by meaning using vectors
- `entity_search()` - find mentions of people/companies
- `synthesize_response()` - generate natural language answer

Query examples:
- "What was I doing last Tuesday at 3pm?"
- "Find all information about AI"
- "Show me what Sarah said about the budget"

### 10. User Interface (ui/app.py)

Requirements:
- Tkinter-based desktop app
- 800x600 window
- Components:
  * Header with "NEXUS" title
  * Status indicator (Running/Stopped)
  * Activity counter
  * Start/Stop buttons
  * Query input with Enter key support
  * Scrolling activity log
  * Alert display (color-coded by priority)
- Thread-safe UI updates (use `root.after()`)
- Background thread for NEXUS monitoring
- Callbacks:
  * `on_capture()` - when screen captured
  * `on_alert()` - when proactive alert triggered
  * `process_query()` - when user asks question

### 11. Main Application (main.py)

Requirements:
- Entry point
- Check for API key
- Initialize Config
- Print startup banner
- Launch UI
- Handle graceful shutdown

---

## DEPENDENCIES (requirements.txt)

```
anthropic>=0.40.0
mss>=9.0.1
pillow>=10.0.0
chromadb>=0.4.0
numpy>=1.24.0
opencv-python>=4.8.0
pytesseract>=0.3.10
pyaudio>=0.2.13
python-dotenv>=1.0.0
pydantic>=2.5.0
```

---

## CRITICAL IMPLEMENTATION DETAILS

### Privacy & Security
- All data stored locally (never sent to cloud except API calls)
- Passwords/credit cards automatically redacted
- User can pause/exclude apps
- 7-day rolling deletion of old screenshots
- Encrypted database (nice-to-have)

### Performance
- Async capture and analysis (non-blocking)
- Queue-based processing
- Efficient image compression
- Indexed database queries
- Lazy loading of results

### Error Handling
- Graceful API failures
- Try-catch in all async functions
- Clear error messages to user
- Logging for debugging
- Fallback behaviors

### Code Quality
- Type hints on all functions
- Comprehensive docstrings
- Consistent style (PEP 8)
- Comments on complex logic
- No hardcoded values (use Config)

---

## DEMO PREPARATION

Also generate:

### demo_data.py
Script to insert 10-20 realistic sample activities for demo purposes:
- Various timestamps (last 2 hours)
- Different apps (Chrome, VSCode, Mail, Zoom)
- Realistic activity descriptions
- Tags and priorities

### README.md
Complete documentation including:
- Project description
- Installation instructions (step-by-step)
- Usage guide
- Configuration options
- Privacy information
- Demo instructions
- Technical architecture
- Troubleshooting

### .env.example
```
ANTHROPIC_API_KEY=your-api-key-here
SCREEN_CAPTURE_INTERVAL=2
PROACTIVE_ENABLED=true
```

---

## SUCCESS CRITERIA

The generated code must:

1. ✅ **Run without errors** on fresh Python 3.10+ install
2. ✅ **Capture screenshots** every 2 seconds
3. ✅ **Send to Claude API** for analysis
4. ✅ **Store in database** (SQLite + ChromaDB)
5. ✅ **Display in UI** with activity log
6. ✅ **Trigger at least one proactive alert** (email without attachment)
7. ✅ **Answer natural language queries** ("what was I doing this morning?")
8. ✅ **Be demo-ready** with clean UI and no crashes

---

## ADDITIONAL REQUIREMENTS

### Code Organization
- All imports at top of file
- Consistent naming (snake_case for functions/vars, PascalCase for classes)
- Clear separation of concerns
- Each file has single responsibility
- No circular imports

### Documentation
- Every class has docstring
- Every public method has docstring
- Complex logic has inline comments
- README has complete setup guide

### Testing
- Code must actually work
- No placeholder/TODO functions
- All features implemented
- Error cases handled

---

## WHAT TO GENERATE

Please generate:

1. **All Python files** with complete, working code
2. **Configuration files** (requirements.txt, .env.example)
3. **Documentation** (README.md with full instructions)
4. **Demo utilities** (demo_data.py)
5. **All necessary __init__.py files**

Make it:
- ✅ **Production-ready**: Clean, documented, robust
- ✅ **Demo-ready**: Works reliably, looks polished
- ✅ **Hackathon-winning**: Impressive, innovative, complete

---

## PRIORITY ORDER

If time is limited, implement in this order:
1. Screen capture + basic storage
2. Gemini analysis integration
3. Database + query system
4. UI
5. Proactive agent
6. Polish + demo prep

---

## OUTPUT FORMAT

For each file, provide:
```python
# filepath: nexus/path/to/file.py

"""
Module docstring describing purpose
"""

# Complete working code here
```

---

**Generate everything now. Make it complete, working, and amazing. This needs to win the $100K hackathon prize. Let's build NEXUS!** 🚀
