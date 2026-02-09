"""
Privacy Utilities for NEXUS

Provides functions for:
- Getting active window information (cross-platform)
- Filtering apps that should not be captured
- Redacting sensitive data from text
"""

import re
import subprocess
import platform
from typing import Dict

import sys
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])
from config import Config


def get_active_window_info() -> Dict[str, str]:
    """
    Get information about the currently active window.
    
    Returns:
        Dict with 'app_name' and 'window_title' keys
    """
    system = platform.system()
    
    try:
        if system == "Darwin":  # macOS
            return _get_active_window_macos()
        elif system == "Linux":
            return _get_active_window_linux()
        elif system == "Windows":
            return _get_active_window_windows()
        else:
            return {'app_name': 'Unknown', 'window_title': 'Unknown'}
    except Exception as e:
        print(f"[Privacy] Error getting window info: {e}")
        return {'app_name': 'Unknown', 'window_title': 'Unknown'}


def _get_active_window_macos() -> Dict[str, str]:
    """Get active window info on macOS using AppleScript"""
    script = '''
    tell application "System Events"
        set frontApp to name of first application process whose frontmost is true
        try
            set frontWindow to name of front window of application process frontApp
        on error
            set frontWindow to "No Window"
        end try
        return frontApp & "|||" & frontWindow
    end tell
    '''
    result = subprocess.check_output(['osascript', '-e', script], timeout=5)
    parts = result.decode('utf-8').strip().split('|||')
    
    if len(parts) >= 2:
        return {
            'app_name': parts[0],
            'window_title': parts[1]
        }
    return {'app_name': parts[0] if parts else 'Unknown', 'window_title': 'Unknown'}


def _get_active_window_linux() -> Dict[str, str]:
    """Get active window info on Linux using xdotool"""
    try:
        # Get window ID
        window_id = subprocess.check_output(
            ['xdotool', 'getactivewindow'], timeout=5
        ).decode('utf-8').strip()
        
        # Get window name
        window_name = subprocess.check_output(
            ['xdotool', 'getwindowname', window_id], timeout=5
        ).decode('utf-8').strip()
        
        # Get window class (app name)
        window_class = subprocess.check_output(
            ['xprop', '-id', window_id, 'WM_CLASS'], timeout=5
        ).decode('utf-8').strip()
        
        # Parse app name from WM_CLASS
        app_name = 'Unknown'
        if '=' in window_class:
            class_part = window_class.split('=')[1].strip()
            app_name = class_part.split(',')[0].strip().strip('"')
        
        return {
            'app_name': app_name,
            'window_title': window_name
        }
    except Exception:
        return {'app_name': 'Unknown', 'window_title': 'Unknown'}


def _get_active_window_windows() -> Dict[str, str]:
    """Get active window info on Windows using ctypes"""
    try:
        import ctypes
        from ctypes import wintypes
        
        user32 = ctypes.windll.user32
        
        # Get foreground window
        hwnd = user32.GetForegroundWindow()
        
        # Get window title
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        window_title = buff.value
        
        # Get process ID
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        # Get process name (simplified)
        import psutil
        try:
            process = psutil.Process(pid.value)
            app_name = process.name()
        except Exception:
            app_name = 'Unknown'
        
        return {
            'app_name': app_name,
            'window_title': window_title
        }
    except Exception:
        return {'app_name': 'Unknown', 'window_title': 'Unknown'}


def should_capture(app_name: str) -> bool:
    """
    Check if we should capture the current application.
    
    Args:
        app_name: Name of the application
        
    Returns:
        True if app should be captured, False otherwise
    """
    app_lower = app_name.lower()
    
    # Check excluded apps
    for excluded in Config.EXCLUDED_APPS:
        if excluded.lower() in app_lower:
            return False
    
    # Check for private/incognito indicators
    private_keywords = ['private', 'incognito', 'password', 'keychain', 'secure', 'vault']
    for keyword in private_keywords:
        if keyword in app_lower:
            return False
    
    return True


def redact_sensitive_data(text: str) -> str:
    """
    Remove sensitive information from text.
    
    Args:
        text: Text to redact
        
    Returns:
        Text with sensitive data replaced by [REDACTED]
    """
    if not text:
        return text
    
    redacted = text
    
    for pattern in Config.REDACT_PATTERNS:
        redacted = re.sub(pattern, '[REDACTED]', redacted, flags=re.IGNORECASE)
    
    return redacted
