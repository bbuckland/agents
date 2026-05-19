#!/bin/bash

echo "🦌 Teams Transcript Harvester Setup"
echo "======================================"

# Check if running as root (needed for system-wide cron)
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Running as root - will install system-wide"
    INSTALL_DIR="/opt/teams-harvester"
    CRON_USER="node"
else
    echo "📁 Installing for current user"
    INSTALL_DIR="$HOME/teams-harvester"
    CRON_USER="$USER"
fi

# Create installation directory
echo "📂 Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# Copy files
cp package.json harvester.js config.env "$INSTALL_DIR/"
cd "$INSTALL_DIR"

# Install dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Make harvester executable
chmod +x harvester.js

# Set up Obsidian vault directory
echo "🗂️  Setting up Obsidian vault structure..."
OBSIDIAN_VAULT="${OBSIDIAN_VAULT:-$HOME/obsidian-vault}"
mkdir -p "$OBSIDIAN_VAULT/Meetings/Teams"

echo "📝 Created Obsidian vault structure at: $OBSIDIAN_VAULT"

# Update config with actual vault path
sed -i "s|/home/node/obsidian-vault|$OBSIDIAN_VAULT|g" config.env

# Test run (dry run)
echo "🧪 Running test harvest (dry run)..."
source config.env && node harvester.js --dry-run

# Set up cron job
echo "⏰ Setting up daily cron job..."
CRON_COMMAND="cd $INSTALL_DIR && source config.env && node harvester.js >> harvest.log 2>&1"

# Add cron job (runs daily at 8 AM)
(crontab -u $CRON_USER -l 2>/dev/null; echo "0 8 * * * $CRON_COMMAND") | crontab -u $CRON_USER -

echo "✅ Setup complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Edit $INSTALL_DIR/config.env to set your Obsidian vault path"
echo "2. Test with: cd $INSTALL_DIR && node harvester.js --dry-run"
echo "3. Run first harvest: cd $INSTALL_DIR && node harvester.js"
echo "4. Cron job will run daily at 8:00 AM"
echo ""
echo "📂 Files installed to: $INSTALL_DIR"
echo "📊 Logs will be written to: $INSTALL_DIR/harvest.log"
echo "🗂️  Meetings saved to: $OBSIDIAN_VAULT/Meetings/Teams"