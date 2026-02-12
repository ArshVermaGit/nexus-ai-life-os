"""
Proactive Agent for NEXUS

Provides proactive assistance by detecting potential issues
and alerting users before mistakes happen.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, List
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from services.database import DatabaseService
from services.gemini_client import GeminiClient
from services.vector_store import VectorStore
from config import Config


class ProactiveAgent:
    """
    Proactive assistance system.
    
    Watches user activity and alerts them about potential issues.
    """
    
    def __init__(self):
        """Initialize the proactive agent."""
        self.db = DatabaseService()
        self.gemini = GeminiClient()
        self.alert_history: Dict[str, datetime] = {}  # Track recent alerts
        self.running = False
        self.on_alert_callback: Optional[Callable] = None
        self.alert_count = 0
    
    def set_alert_callback(self, callback: Callable):
        """
        Set callback for when alerts are triggered.
        
        Args:
            callback: Async function receiving alert_data dict
        """
        self.on_alert_callback = callback
    
    async def evaluate_situation(self, capture_data: Dict, analysis: Dict):
        """
        Evaluate if proactive intervention is needed.
        
        Args:
            capture_data: Screen capture data
            analysis: Gemini analysis results
        """
        if not Config.PROACTIVE_ENABLED:
            return
        
        # Check if analysis suggests interruption
        if analysis.get('should_interrupt', False):
            message = analysis.get('interrupt_message', 'Attention needed')
            if message and not self.recently_alerted('ai_interrupt'):
                await self.trigger_alert(
                    message=message,
                    priority=analysis.get('priority', 'medium'),
                    capture_data=capture_data,
                    analysis=analysis,
                    alert_type='ai_interrupt'
                )
            return
        
        # Check rule-based patterns
        await self.check_proactive_rules(capture_data, analysis)
    
    async def check_proactive_rules(self, capture_data: Dict, analysis: Dict):
        """
        Check predefined proactive rules.
        
        Args:
            capture_data: Screen capture data
            analysis: Gemini analysis results
        """
        # Rule 1: Email without attachment
        if await self.check_email_no_attachment(capture_data, analysis):
            return
        
        # Rule 2: Duplicate work detection
        if await self.check_duplicate_work(capture_data, analysis):
            return
        
        # Rule 3: Password in public field
        if await self.check_password_exposed(capture_data, analysis):
            return
        
        # Rule 4: Deadline approaching
        if await self.check_deadline_approaching(capture_data, analysis):
            return
    
    async def check_email_no_attachment(self, capture_data: Dict, analysis: Dict) -> bool:
        """
        Check if user is sending email mentioning attachment but forgot to attach.
        
        Returns:
            True if alert was triggered
        """
        app_name = capture_data.get('app_name', '').lower()
        window_title = capture_data.get('window_title', '').lower()
        extracted_text = analysis.get('extracted_text', '').lower()
        activity = analysis.get('activity', '').lower()
        
        # Check if email client
        email_apps = ['mail', 'outlook', 'gmail', 'thunderbird', 'spark', 'airmail']
        is_email_app = any(email_app in app_name for email_app in email_apps)
        is_composing = any(word in window_title for word in ['compose', 'new message', 'reply', 'forward', 'draft'])
        
        if not (is_email_app or is_composing):
            return False
        
        # Check if mentions attachment
        attachment_keywords = ['attach', 'attached', 'attachment', 'attaching', 
                              'enclosed', 'enclosing', 'find the file', 'see file']
        combined_text = f"{extracted_text} {activity}"
        mentions_attachment = any(keyword in combined_text for keyword in attachment_keywords)
        
        if not mentions_attachment:
            return False
        
        # Check cooldown
        if self.recently_alerted('email_no_attachment'):
            return False
        
        await self.trigger_alert(
            message="⚠️ You mentioned an attachment but I don't see one attached. Did you forget?",
            priority="high",
            capture_data=capture_data,
            analysis=analysis,
            alert_type='email_no_attachment'
        )
        
        return True
    
    async def check_duplicate_work(self, capture_data: Dict, analysis: Dict) -> bool:
        """
        Check if user is doing work they've done before.
        
        Returns:
            True if alert was triggered
        """
        try:
            vector_store = VectorStore()
            
            # Generate embedding for current activity
            current_text = f"{analysis.get('activity', '')} {analysis.get('extracted_text', '')}"
            current_embedding = await self.gemini.generate_embedding(current_text)
            
            # Search for similar past activities
            similar = await vector_store.semantic_search(current_embedding, limit=5)
            
            # Check if very similar activity exists
            for result in similar:
                if result['distance'] < 0.1:  # Very similar (low distance)
                    if self.recently_alerted('duplicate_work'):
                        return False
                    
                    await self.trigger_alert(
                        message="ℹ️ You did very similar work recently. Want to reuse it?",
                        priority="low",
                        capture_data=capture_data,
                        analysis=analysis,
                        alert_type='duplicate_work'
                    )
                    return True
            
            return False
            
        except Exception as e:
            print(f"[ProactiveAgent] Duplicate check error: {e}")
            return False
    
    async def check_password_exposed(self, capture_data: Dict, analysis: Dict) -> bool:
        """
        Check if password might be visible in non-secure context.
        
        Returns:
            True if alert was triggered
        """
        extracted_text = analysis.get('extracted_text', '').lower()
        
        # Look for password patterns (already redacted, but check for partial exposure)
        password_indicators = ['[redacted]', 'password:', 'pwd:', 'secret:']
        
        if not any(indicator in extracted_text for indicator in password_indicators):
            return False
        
        # Check if in secure app
        app_name = capture_data.get('app_name', '').lower()
        secure_apps = ['keychain', '1password', 'lastpass', 'dashlane', 'bitwarden']
        
        if any(secure_app in app_name for secure_app in secure_apps):
            return False  # Expected in password managers
        
        # Check if screen sharing indicator
        window_title = capture_data.get('window_title', '').lower()
        sharing_indicators = ['share', 'meeting', 'call', 'zoom', 'teams', 'meet']
        is_sharing = any(indicator in window_title for indicator in sharing_indicators)
        
        if is_sharing and not self.recently_alerted('password_exposed'):
            await self.trigger_alert(
                message="🚨 Potential password visible while screen sharing!",
                priority="critical",
                capture_data=capture_data,
                analysis=analysis,
                alert_type='password_exposed'
            )
            return True
        
        return False
    
    async def trigger_alert(self,
                           message: str,
                           priority: str,
                           capture_data: Dict,
                           analysis: Dict,
                           alert_type: str = 'general'):
        """
        Trigger a proactive alert.
        
        Args:
            message: Alert message to show
            priority: low/medium/high/critical
            capture_data: Related capture data
            analysis: Related analysis
            alert_type: Type of alert for cooldown tracking
        """
        # Store alert event
        await self.db.store_event(
            event_type='proactive_alert',
            content=message
        )
        
        # Record alert time for cooldown
        self.alert_history[alert_type] = datetime.now()
        self.alert_count += 1
        
        # Build alert data
        alert_data = {
            'message': message,
            'priority': priority,
            'timestamp': datetime.now(),
            'type': alert_type,
            'capture_data': capture_data,
            'analysis': analysis
        }
        
        # Call callback if set
        if self.on_alert_callback:
            try:
                await self.on_alert_callback(alert_data)
            except Exception as e:
                print(f"[ProactiveAgent] Alert callback error: {e}")
        
        print(f"[ProactiveAgent] ALERT ({priority}): {message}")
    
    def recently_alerted(self, alert_type: str) -> bool:
        """
        Check if we recently alerted about this type.
        
        Args:
            alert_type: Type of alert
            
        Returns:
            True if cooldown is active
        """
        if alert_type not in self.alert_history:
            return False
        
        last_alert = self.alert_history[alert_type]
        time_since = (datetime.now() - last_alert).total_seconds()
        
        return time_since < Config.ALERT_COOLDOWN
    
    def clear_alert_history(self):
        """Clear alert history (reset cooldowns)."""
        self.alert_history.clear()
    
    def get_stats(self) -> Dict:
        """Get agent statistics."""
        return {
            'alert_count': self.alert_count,
            'active_cooldowns': len(self.alert_history),
            'enabled': Config.PROACTIVE_ENABLED
        }
