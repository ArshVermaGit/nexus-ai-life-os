"""
NEXUS Build Script

Packages the application into a standalone executable using PyInstaller.
"""

import sys
import os
import subprocess
from pathlib import Path

def build_app():
    """Run PyInstaller to build the app."""
    print("🛠️ Starting NEXUS Build Process...")
    
    # Get platform
    platform = sys.platform
    
    # Base command
    cmd = [
        'pyinstaller',
        '--name=NEXUS',
        '--onefile',
        '--windowed',
        '--clean',
        # Include data files
        '--add-data=ui/templates:ui/templates',
        '--add-data=ui/static:ui/static',
        '--add-data=concept:concept',
        '--add-data=config.py:.',
        '--add-data=requirements.txt:.',
        'desktop_app.py'
    ]
    
    # platform specific adjustments
    if platform == 'darwin':
        # cmd.extend(['--icon=ui/static/icon.icns']) # If icon exists
        pass
    elif platform == 'win32':
        # cmd.extend(['--icon=ui/static/icon.ico']) # If icon exists
        pass

    print(f"🚀 Running build command for {platform}...")
    
    try:
        subprocess.check_call(cmd)
        print("\n✅ Build Successful!")
        print(f"📂 Output located in 'dist/NEXUS{'.app' if platform=='darwin' else '.exe'}'")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build Failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    build_app()
