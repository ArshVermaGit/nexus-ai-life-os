#!/bin/bash
# NEXUS Global Installer for macOS/Linux

echo "🚀 Installing NEXUS Terminal Intelligence..."

# Get absolute path of this directory
INSTALL_DIR=$(pwd)
PYTHON_CMD="python3"

# Check for python3
if ! command -v python3 &>/dev/null; then
    if command -v python &>/dev/null; then
        PYTHON_CMD="python"
    else
        echo "❌ Error: Python not found. Please install Python 3."
        exit 1
    fi
fi

# Install requirements
echo "📦 Installing dependencies..."
$PYTHON_CMD -m pip install -r requirements.txt

# Create symlink
BIN_DIR="/usr/local/bin"
TARGET="$BIN_DIR/nexus"

echo "🔗 Creating global command 'nexus'..."

# Create the wrapper script
sudo bash -c "cat > $TARGET <<EOF
#!/bin/bash
cd $INSTALL_DIR
$PYTHON_CMD cli.py \\\$@
EOF"

sudo chmod +x $TARGET

echo ""
echo "✅ NEXUS installed successfully!"
echo "You can now run 'nexus chat' or 'nexus start' from any terminal."
echo ""
