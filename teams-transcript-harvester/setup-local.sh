#!/bin/bash
# Setup Teams Transcript Harvester for local Mac execution
# Uses Playwright with persistent browser profile for login sessions

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VAULT_DIR="$HOME/Documents/personal/notes"

echo "🍎 Teams Transcript Harvester - Local Mac Setup"
echo "================================================"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Install via: brew install node"
    exit 1
fi
echo "✅ Node.js: $(node --version)"

# Check pnpm
if ! command -v pnpm &> /dev/null; then
    echo "❌ pnpm not found. Install via: brew install pnpm"
    exit 1
fi
echo "✅ pnpm: $(pnpm --version)"

# Ensure Teams meetings folder exists in vault
echo ""
echo "📁 Ensuring meetings folder exists..."
mkdir -p "$VAULT_DIR/Meetings/Teams"
echo "✅ Meetings folder ready: $VAULT_DIR/Meetings/Teams"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
cd "$SCRIPT_DIR"
pnpm install

# Install Playwright browsers (uses system Chrome by default, but install as backup)
echo ""
echo "🌐 Setting up Playwright..."
pnpm exec playwright install chromium

# Create log directory
mkdir -p "$HOME/Library/Logs"

# Make scripts executable
chmod +x "$SCRIPT_DIR/install-launchd.sh"

echo ""
echo "================================================"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo ""
echo "1. First run (visible browser for Teams login):"
echo "   cd $SCRIPT_DIR"
echo "   HEADLESS=false node harvester.js --dry-run"
echo ""
echo "2. Once logged in, test headless mode:"
echo "   node harvester.js --dry-run"
echo ""
echo "3. Install hourly schedule:"
echo "   ./install-launchd.sh"
echo ""
echo "4. Teams transcripts will be saved to:"
echo "   $VAULT_DIR/Meetings/Teams"
echo ""
echo "📂 Vault:    $VAULT_DIR/Meetings/Teams"
echo "🔐 Profile:  $SCRIPT_DIR/.browser-profile"
echo "📝 Logs:     ~/Library/Logs/teams-transcript-harvester.log"
