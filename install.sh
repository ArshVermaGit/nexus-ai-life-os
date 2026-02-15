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
echo "📦 Installing terminal-optimized dependencies..."
$PYTHON_CMD -m pip install -r requirements.txt

# Create symlink
BIN_DIR="/usr/local/bin"
if [ ! -d "$BIN_DIR" ]; then
    BIN_DIR="/usr/bin"
fi
TARGET="$BIN_DIR/nexus"

echo "🔗 Creating global command 'nexus' in $BIN_DIR..."

# Create the wrapper script
cat <<EOF | sudo tee $TARGET > /dev/null
#!/bin/bash
cd $INSTALL_DIR
$PYTHON_CMD main.py "\$@"
EOF

sudo chmod +x $TARGET

echo ""
echo "✅ NEXUS installed successfully!"
echo "You can now run 'nexus chat', 'nexus search', or 'nexus check' from any terminal."
echo ""
