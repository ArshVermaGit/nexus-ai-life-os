#!/bin/bash
# NEXUS - Pure Terminal Intelligence Launcher

# Check for python3
if command -v python3 &>/dev/null; then
    PYTHON=python3
else
    PYTHON=python
fi

echo "🚀 Launching NEXUS Cortex..."
$PYTHON main.py
