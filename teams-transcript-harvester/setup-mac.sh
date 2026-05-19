#!/bin/bash

echo "🍎 Teams Transcript Harvester - Mac Setup"
echo "========================================"

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is for macOS only"
    echo "   Use setup.sh for Linux/other systems"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found"
    echo "   Install from: https://nodejs.org/"
    echo "   Or use Homebrew: brew install node"
    exit 1
fi

echo "✅ Node.js found: $(node --version)"

# Set up directories
OBSIDIAN_VAULT="$HOME/Documents/ObsidianVault"
MEETINGS_DIR="$OBSIDIAN_VAULT/Meetings/Teams"

echo "📁 Setting up Obsidian vault structure..."
mkdir -p "$MEETINGS_DIR"
echo "✅ Created: $MEETINGS_DIR"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create Mac-specific config
cat > config.env << EOF
# Teams Transcript Harvester Configuration - macOS
OBSIDIAN_VAULT=$OBSIDIAN_VAULT
HEADLESS=true
LOGIN_TIMEOUT=300
LOG_LEVEL=info

# Mac-specific Chrome path (if needed)
# PUPPETEER_EXECUTABLE_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
EOF

echo "✅ Created config.env with Mac paths"

# Make scripts executable
chmod +x harvester.js install-cron.sh validate.js

# Test run
echo "🧪 Running validation test..."
node validate.js

echo ""
echo "🎯 Next Steps:"
echo "1. Test with: node harvester.js --dry-run"
echo "2. Run harvest: node harvester.js"  
echo "3. Set up automation: ./install-cron.sh"
echo ""
echo "📂 Vault location: $OBSIDIAN_VAULT"
echo "🗂️  Meetings saved to: $MEETINGS_DIR"
echo ""
echo "💡 Tips for Mac:"
echo "   • Obsidian vaults typically in ~/Documents/"
echo "   • Use Terminal.app or iTerm2 for best results"
echo "   • Chrome will auto-launch for Teams login"

echo ""
echo "✅ Mac setup complete!"