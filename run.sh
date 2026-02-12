echo "✅ Environment Ready."
echo ""
echo "Choose Launch Mode (Terminal Preference):"
echo "1) ⌨️  CLI Interactive Chat"
echo "2) 🌐  Web Dashboard"
echo "3) 🖥️  Desktop Window (Local)"
read -p "Selection [1-3]: " mode

case $mode in
    1)
        echo "🚀 Launching NEXUS CLI..."
        $PYTHON cli.py chat
        ;;
    2)
        echo "🚀 Launching NEXUS Web UI..."
        $PYTHON main.py
        ;;
    3)
        echo "🚀 Launching NEXUS Desktop Window..."
        $PYTHON desktop_app.py
        ;;
    *)
        echo "❌ Invalid selection. Defaulting to Web UI."
        $PYTHON main.py
        ;;
esac
