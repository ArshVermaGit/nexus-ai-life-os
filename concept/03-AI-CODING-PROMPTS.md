# PROMPTS FOR AI CODING ASSISTANT

This document contains prompts you can feed to AI coding assistants (like Cursor, GitHub Copilot, Aider, or custom tools) to automatically build NEXUS.

## 📋 How to Use These Prompts

1. Start a new coding session with your AI assistant
2. Copy each prompt below **in order**
3. Review and test the code it generates
4. Move to the next prompt
5. By the end, you'll have a fully functional NEXUS

---

## PROMPT 1: Project Setup

```
I'm building NEXUS - an AI-powered personal assistant that monitors computer activity and provides proactive help.

Please create the complete project structure with all necessary files:

Project Requirements:
- Python 3.10+ application
- Captures screenshots every 2 seconds
- Integrates with Anthropic Claude API (Gemini)
- Stores data in SQLite + ChromaDB
- Simple Tkinter UI
- Proactive assistance system

Create:
1. Directory structure: nexus/ with subdirs: core/, services/, ui/, utils/, models/, data/
2. requirements.txt with dependencies: anthropic, mss, pillow, chromadb, numpy, opencv-python, pytesseract, pyaudio, python-dotenv, fastapi, uvicorn, pydantic
3. config.py with all configuration settings (API keys, intervals, directories, privacy settings)
4. .env.example template
5. main.py skeleton
6. README.md with installation instructions

Make sure:
- All necessary imports are included
- Directory creation is handled
- Configuration is centralized
- Privacy settings are included (excluded apps, redaction patterns)

Generate complete, runnable code for all files.
```

---

## PROMPT 2: Screen Capture System

```
Now implement the screen capture system for NEXUS.

Create the following files:

1. core/capture_manager.py
   - ScreenCaptureService class
   - Captures screenshots every 2 seconds using mss library
   - Resizes images to max 1920x1080
   - Saves as compressed JPEG
   - Gets active window information (app name, window title)
   - Provides callback mechanism for captured frames
   - Async implementation using asyncio

2. utils/privacy.py
   - get_active_window_info() function (works on macOS, Linux, Windows)
   - should_capture() function to check if app should be captured
   - redact_sensitive_data() function to remove passwords, credit cards, SSN, API keys
   - Uses regex patterns from Config

3. utils/compression.py
   - compress_image() function to compress PIL Image to JPEG bytes
   - Configurable quality parameter

Requirements:
- Use mss for cross-platform screen capture
- Handle errors gracefully
- Don't capture excluded apps
- Platform-specific active window detection
- Efficient async implementation

Generate complete, production-ready code with error handling and comments.
```

---

## PROMPT 3: Database Layer

```
Implement the database layer for NEXUS.

Create:

1. services/database.py
   - DatabaseService class
   - SQLite database with tables: activities, events, sessions, settings
   - Methods:
     * init_database() - creates schema
     * store_activity() - stores screen captures
     * get_recent_activities() - retrieves recent activities
     * search_activities() - search with filters (time, app, tags)
     * store_event() - stores alerts/queries
     * cleanup_old_data() - removes old files
   - Proper indexes for performance
   - JSON storage for analysis data

2. services/vector_store.py
   - VectorStore class using ChromaDB
   - Methods:
     * add_embedding() - store vector embeddings
     * semantic_search() - find similar activities
   - Persistent storage in data/db/chroma/

Database Schema:
- activities table: id, timestamp, activity_type, app_name, window_title, screenshot_path, analysis (JSON), tags, priority
- events table: id, timestamp, event_type, content, related_activity_id, user_action
- sessions table: id, start_time, end_time, session_type, summary
- settings table: key, value

Requirements:
- Thread-safe operations
- Proper error handling
- Efficient queries with indexes
- JSON serialization for complex data

Generate complete code with full CRUD operations.
```

---

## PROMPT 4: Gemini API Integration

```
Implement Gemini (Anthropic Claude) API integration for NEXUS.

Create:

1. services/gemini_client.py
   - GeminiClient class
   - Uses Anthropic Python SDK
   - Methods:
     * analyze_screen() - sends screenshot + context to Claude, gets analysis
     * generate_embedding() - creates vector embeddings (simple hash-based for hackathon)
   
   analyze_screen() should:
   - Accept image path, app name, window title, recent context
   - Send image as base64 to Claude
   - Use a structured prompt asking for:
     * Activity description
     * User intent
     * Potential issues
     * Should interrupt (true/false)
     * Interrupt message
     * Tags for categorization
     * Priority level
   - Return parsed JSON response

2. core/analysis_engine.py
   - AnalysisEngine class
   - Manages queue of captures to analyze
   - Methods:
     * start() - begins processing queue
     * queue_capture() - adds capture to queue
     * analyze_capture() - coordinates analysis
     * store_analysis() - saves to database
   - Async processing
   - Calls privacy redaction on results

Prompt Template:
"""
You are NEXUS, an AI assistant watching the user's computer activity.

Current Context:
- Active Application: {app_name}
- Window Title: {window_title}
- Time: {timestamp}

Recent Activity:
{context}

Analyze the screenshot and respond in JSON format:
{
  "activity": "what user is doing",
  "intent": "user's goal",
  "issues": ["potential problems"],
  "should_interrupt": true/false,
  "interrupt_message": "alert message",
  "tags": ["relevant", "tags"],
  "priority": "low/medium/high",
  "extracted_text": "important text from screen"
}
"""

Requirements:
- Robust error handling
- JSON parsing with fallbacks
- Rate limiting consideration
- Async operations

Generate complete, production-ready code.
```

---

## PROMPT 5: Proactive Agent System

```
Implement the proactive agent that decides when to help the user.

Create core/proactive_agent.py:

ProactiveAgent class with:
- Methods:
  * evaluate_situation() - main decision function
  * check_proactive_rules() - rule-based checks
  * check_email_no_attachment() - detects email mentions attachment but no file attached
  * check_duplicate_work() - finds similar past work
  * check_deadline_approaching() - calendar integration (simulated for hackathon)
  * trigger_alert() - fires proactive alert
  * recently_alerted() - prevents alert spam
  
- Alert Rules to Implement:
  1. Email without attachment: mentions "attach" but no attachment present
  2. Duplicate work: doing something very similar to past week
  3. Wrong recipient: mentioned name doesn't match email recipient
  4. Password in public: password pattern in non-password field
  5. Deadline approaching: task due in <2 hours, not working on it

- Features:
  * Alert cooldown (5 min between similar alerts)
  * Priority levels: low, medium, high, critical
  * Callback mechanism for UI alerts
  * Event logging to database

- Configuration:
  * PROACTIVE_ENABLED toggle
  * Customizable rules
  * Alert threshold settings

Requirements:
- Smart detection logic
- No alert spam
- Configurable rules
- Async implementation
- Database logging

Generate complete code with all proactive rules implemented.
```

---

## PROMPT 6: Query Engine

```
Implement the natural language query system for NEXUS.

Create core/query_engine.py:

QueryEngine class with:
- Methods:
  * process_query() - main query handler
  * classify_query() - determines query type (temporal/semantic/entity)
  * temporal_search() - searches by time
  * semantic_search() - searches by meaning
  * entity_search() - searches for people/companies
  * extract_time_range() - parses time from query
  * synthesize_response() - generates natural language answer

Query Types:
1. Temporal: "What was I doing Tuesday at 3pm?", "Show my activity last week"
2. Semantic: "Find information about AI", "Show research on transformers"
3. Entity: "What did Sarah say?", "Find emails from John"

Time Parsing:
- "today" -> today's activities
- "yesterday" -> yesterday's activities  
- "last week" -> past 7 days
- "last month" -> past 30 days
- Specific dates/times

Search Strategy:
- Temporal: Query SQLite by timestamp
- Semantic: Use ChromaDB vector similarity
- Entity: Regex + text search

Response Generation:
- Natural language summaries
- Top 5 most relevant results
- Timestamps and context
- Links to original activities

Requirements:
- Robust time parsing
- Efficient search
- Clear responses
- Handle edge cases

Generate complete code with comprehensive query handling.
```

---

## PROMPT 7: User Interface

```
Implement a simple but functional UI for NEXUS using Tkinter.

Create ui/app.py:

NexusUI class with:

Layout:
1. Header: "NEXUS" title
2. Status section: Running/Stopped indicator, activity count
3. Control buttons: Start Monitoring, Stop
4. Query section: Text input + Search button
5. Activity log: Scrolling text area showing all activities
6. Alert area: Prominent alert display

Features:
- Start/Stop monitoring with button state management
- Real-time activity log updates
- Query input with Enter key support
- Alert display with color coding (low=blue, medium=orange, high=red)
- Thread-safe UI updates (important for async operations)
- Activity counter
- Timestamp display

Threading:
- UI runs in main thread
- NEXUS monitoring runs in background thread
- Use root.after() for thread-safe updates

Callbacks:
- on_capture() when screen captured
- on_alert() when proactive alert triggered
- process_query() when user asks question

Visual Design:
- Clean, minimal interface
- 800x600 window
- Monospace font for logs
- Color-coded status and alerts
- Professional appearance

Requirements:
- Thread-safe operations
- Responsive UI (no freezing)
- Clear visual feedback
- Intuitive controls

Generate complete, polished UI code ready for demo.
```

---

## PROMPT 8: Main Application Integration

```
Create the main application entry point that ties everything together.

Update main.py:

Main Application:
- Check for API key
- Initialize configuration
- Create necessary directories
- Start UI
- Handle graceful shutdown
- Print startup banner

Flow:
1. Print NEXUS banner
2. Validate environment (API key, directories)
3. Initialize Config
4. Launch NexusUI
5. Handle Ctrl+C gracefully

Also create:
- .env.example with template
- Complete README.md with:
  * Project description
  * Installation instructions
  * Usage guide
  * Configuration options
  * Privacy information
  * Demo instructions
  * Technical details

Error Handling:
- Missing API key -> clear error message
- Missing dependencies -> installation hints
- Permission issues -> helpful suggestions

Documentation:
- Clear setup steps
- Feature list
- Privacy guarantees
- Troubleshooting section

Generate:
1. Complete main.py
2. Detailed README.md
3. .env.example
4. Any missing __init__.py files

Make it production-ready and demo-ready.
```

---

## PROMPT 9: Testing & Demo Preparation

```
Create testing utilities and demo preparation tools.

Generate:

1. demo_data.py
   - Script to generate sample activities for demo
   - Create 10-20 realistic activities (browsing, coding, email)
   - Insert into database
   - Various timestamps (last 2 hours)
   - Different app types

2. test_components.py
   - Unit tests for key components
   - Test capture system
   - Test database operations
   - Test privacy filters
   - Test query engine

3. demo_script.md
   - Step-by-step demo guide
   - What to show in each section
   - Expected outcomes
   - Talking points
   - Backup plans

4. run_demo.py
   - Automated demo runner
   - Triggers specific scenarios
   - Simulates proactive alerts
   - Demonstrates all features

Demo Scenarios:
1. Screen capture working
2. Proactive email alert
3. Memory query (find past activity)
4. Knowledge synthesis
5. Timeline view

Requirements:
- Realistic demo data
- Reliable tests
- Clear demo script
- Easy to execute

Generate comprehensive demo/testing suite.
```

---

## PROMPT 10: Final Polish & Optimization

```
Polish NEXUS for final submission and demo.

Improvements needed:

1. Error Handling:
   - Add try-catch blocks in all async functions
   - Graceful degradation if Gemini API fails
   - Clear error messages to user
   - Logging to file for debugging

2. Performance:
   - Optimize image compression
   - Efficient database queries
   - Background processing for analysis
   - Memory management

3. Code Quality:
   - Add comprehensive docstrings
   - Type hints for all functions
   - Consistent code style
   - Remove debug print statements

4. User Experience:
   - Loading indicators
   - Progress feedback
   - Clear status messages
   - Helpful error messages

5. Documentation:
   - Inline code comments
   - API documentation
   - Configuration guide
   - Troubleshooting section

6. Demo Readiness:
   - Pre-load demo data
   - Tested demo flow
   - Video recording script
   - Screenshot preparation

Review all files and:
- Add missing error handling
- Optimize performance bottlenecks
- Improve code documentation
- Polish UI appearance
- Ensure demo reliability

Generate:
1. Updated files with improvements
2. DEMO_CHECKLIST.md with pre-demo testing
3. VIDEO_SCRIPT.md for recording demo
4. Any bug fixes needed

Make NEXUS production-ready and demo-perfect.
```

---

## 🎯 Execution Order

Follow these prompts **in exact order**:

1. **Project Setup** → Creates structure
2. **Screen Capture** → Core functionality
3. **Database Layer** → Data storage
4. **Gemini Integration** → AI analysis
5. **Proactive Agent** → Smart assistance
6. **Query Engine** → Search capability
7. **User Interface** → Visual application
8. **Main Integration** → Ties it together
9. **Testing & Demo** → Preparation
10. **Final Polish** → Ship it!

---

## 💡 Tips for Working with AI Coding Assistants

### For Best Results:

1. **One prompt at a time**: Don't rush, let it complete each section
2. **Review the code**: Check for errors before moving on
3. **Test as you go**: Run code after each major component
4. **Ask for clarification**: If something doesn't work, ask for fixes
5. **Customize**: Feel free to modify prompts for your needs

### If Something Doesn't Work:

**Follow-up prompt:**
```
The [component name] isn't working correctly. I'm getting this error:
[paste error]

Please:
1. Identify the issue
2. Fix the bug
3. Provide updated code
4. Explain what was wrong
```

### To Add Features:

**Follow-up prompt:**
```
Add [feature name] to NEXUS. It should:
- [requirement 1]
- [requirement 2]
- [requirement 3]

Update the relevant files and ensure it integrates with existing code.
```

---

## 🚀 Quick Start Script

For the fastest build, you can use this meta-prompt:

```
I need you to build NEXUS - an AI-powered personal assistant that monitors computer activity and provides proactive help. It's for the Google Gemini Hackathon.

Here are complete requirements and all implementation details:
[paste contents of 00-PROJECT-OVERVIEW.md]
[paste contents of 01-ARCHITECTURE.md]
[paste contents of 02-IMPLEMENTATION-PART1.md]
[paste contents of 02-IMPLEMENTATION-PART2.md]
[paste contents of 02-IMPLEMENTATION-PART3.md]

Please generate all the code files needed to build this application. Generate:
1. Project structure
2. All Python files (main.py, config.py, all modules)
3. Configuration files (requirements.txt, .env.example)
4. Documentation (README.md)

Make it complete, runnable, and ready for demo. Include comprehensive error handling and documentation.
```

---

## ⚡ Speed Run (2 Hours)

If you have limited time:

```
Build a minimal viable NEXUS with these core features only:
1. Screen capture (every 5 seconds)
2. Basic Gemini analysis
3. SQLite storage
4. Simple query interface
5. One proactive alert (email without attachment)

Skip:
- ChromaDB (use SQLite only)
- Audio capture
- Complex UI (just CLI)
- Multiple proactive rules

Generate minimal but functional code in 2 hours.
```

---

**Good luck building NEXUS with AI assistance!** 🤖🚀
