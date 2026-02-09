#!/usr/bin/env python3
"""
Demo Data Generator for NEXUS

Generates sample activity data for demo purposes.
"""

import asyncio
import random
from datetime import datetime, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from services.database import DatabaseService
from services.vector_store import VectorStore
from services.gemini_client import GeminiClient


# Sample activities for demo
SAMPLE_ACTIVITIES = [
    {
        "app_name": "VS Code",
        "window_title": "nexus/main.py - NEXUS",
        "analysis": {
            "activity": "Writing Python code for NEXUS main application",
            "intent": "Building the main entry point for the AI assistant",
            "issues": [],
            "should_interrupt": False,
            "tags": ["coding", "python", "development"],
            "priority": "medium"
        }
    },
    {
        "app_name": "Chrome",
        "window_title": "Claude API Documentation - Anthropic",
        "analysis": {
            "activity": "Reading Claude API documentation",
            "intent": "Learning how to integrate Claude vision API",
            "issues": [],
            "should_interrupt": False,
            "tags": ["research", "api", "documentation"],
            "priority": "low"
        }
    },
    {
        "app_name": "Mail",
        "window_title": "Re: Project Update - Compose",
        "analysis": {
            "activity": "Composing email reply about project update",
            "intent": "Sending status report to team",
            "issues": ["User mentioned 'attached' but no attachment visible"],
            "should_interrupt": True,
            "interrupt_message": "⚠️ You mentioned an attachment but didn't attach anything!",
            "tags": ["email", "communication", "work"],
            "priority": "high"
        }
    },
    {
        "app_name": "Slack",
        "window_title": "#general - Slack",
        "analysis": {
            "activity": "Chatting in team Slack channel",
            "intent": "Team communication and updates",
            "issues": [],
            "should_interrupt": False,
            "tags": ["communication", "team", "slack"],
            "priority": "low"
        }
    },
    {
        "app_name": "Chrome",
        "window_title": "GitHub - ArshVerma/NEXUS",
        "analysis": {
            "activity": "Reviewing GitHub repository for NEXUS project",
            "intent": "Checking code commits and pull requests",
            "issues": [],
            "should_interrupt": False,
            "tags": ["github", "code-review", "development"],
            "priority": "medium"
        }
    },
    {
        "app_name": "Notes",
        "window_title": "Meeting Notes - Product Planning",
        "analysis": {
            "activity": "Taking notes during product planning meeting",
            "intent": "Documenting decisions and action items",
            "issues": [],
            "should_interrupt": False,
            "tags": ["notes", "meeting", "planning"],
            "priority": "medium"
        }
    },
    {
        "app_name": "Terminal",
        "window_title": "zsh - nexus",
        "analysis": {
            "activity": "Running commands in terminal",
            "intent": "Testing and debugging application",
            "issues": [],
            "should_interrupt": False,
            "tags": ["terminal", "development", "testing"],
            "priority": "low"
        }
    },
    {
        "app_name": "Figma",
        "window_title": "NEXUS UI Design - Figma",
        "analysis": {
            "activity": "Designing UI mockups for NEXUS interface",
            "intent": "Creating visual design for the application",
            "issues": [],
            "should_interrupt": False,
            "tags": ["design", "ui", "figma"],
            "priority": "medium"
        }
    },
    {
        "app_name": "Calendar",
        "window_title": "February 2026 - Calendar",
        "analysis": {
            "activity": "Checking calendar for upcoming meetings",
            "intent": "Planning schedule for the day",
            "issues": ["Meeting in 15 minutes with John"],
            "should_interrupt": True,
            "interrupt_message": "📅 Reminder: Meeting with John in 15 minutes!",
            "tags": ["calendar", "meetings", "scheduling"],
            "priority": "high"
        }
    },
    {
        "app_name": "Chrome",
        "window_title": "Stack Overflow - How to use asyncio in Python",
        "analysis": {
            "activity": "Researching async programming in Python",
            "intent": "Learning asyncio patterns for better code",
            "issues": [],
            "should_interrupt": False,
            "tags": ["research", "python", "stackoverflow"],
            "priority": "low"
        }
    }
]


async def generate_demo_data(num_activities: int = 20):
    """
    Generate demo activity data.
    
    Args:
        num_activities: Number of activities to generate
    """
    print(f"Generating {num_activities} demo activities...")
    
    db = DatabaseService()
    gemini = GeminiClient()
    
    base_time = datetime.now()
    
    for i in range(num_activities):
        # Pick a random sample activity
        sample = random.choice(SAMPLE_ACTIVITIES)
        
        # Create timestamp (spread over last 2 hours)
        offset_minutes = random.randint(0, 120)
        timestamp = base_time - timedelta(minutes=offset_minutes)
        
        # Slightly vary the analysis
        analysis = sample["analysis"].copy()
        analysis["timestamp"] = timestamp.isoformat()
        
        # Generate embedding
        search_text = f"{analysis.get('activity', '')} {sample['window_title']}"
        embedding = await gemini.generate_embedding(search_text)
        
        # Store in database
        activity_id = await db.store_activity(
            timestamp=timestamp,
            activity_type="screen",
            app_name=sample["app_name"],
            window_title=sample["window_title"],
            screenshot_path=None,  # No actual screenshots for demo
            analysis=analysis,
            embedding=embedding
        )
        
        print(f"  [{i+1}/{num_activities}] Created activity: {sample['app_name']} - {analysis.get('activity', '')[:40]}...")
    
    # Print summary
    stats = db.get_stats()
    print(f"\n✓ Demo data generated!")
    print(f"  Total activities: {stats['activity_count']}")
    print(f"  Time range: {stats['earliest_activity']} to {stats['latest_activity']}")


def main():
    """Main entry point."""
    print("=" * 50)
    print("  NEXUS Demo Data Generator")
    print("=" * 50)
    print()
    
    # Ensure directories exist
    Config.ensure_directories()
    
    # Generate data
    asyncio.run(generate_demo_data(20))
    
    print("\nDemo data is ready! Run 'python main.py' to start NEXUS.")


if __name__ == "__main__":
    main()
