#!/bin/bash

# NEXUS Launcher Script
# Ensures correct environment and dependencies

echo "🚀 Initializing NEXUS..."

# Check for python3
if command -v python3 &>/dev/null; then
    PYTHON=python3
else
    PYTHON=python
fi

# Check for pip
if ! command -v pip &>/dev/null && ! command -v pip3 &>/dev/null; then
    echo "❌ Error: pip not found. Please install Python."
    exit 1
fi

echo "📦 Checking dependencies..."
$PYTHON -m pip install -r requirements.txt &> /dev/null

echo "✅ Launching NEXUS..."
$PYTHON main.py
