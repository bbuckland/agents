#!/bin/bash
# Install/update the launchd job for hourly harvesting

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_NAME="com.quant-superpowers.teams-harvester.plist"
PLIST_SRC="$SCRIPT_DIR/$PLIST_NAME"
LAUNCHD_DIR="$HOME/Library/LaunchAgents"
PLIST_DEST="$LAUNCHD_DIR/$PLIST_NAME"

echo "📅 Installing Teams Transcript Harvester schedule..."

# Unload if already loaded
if launchctl list | grep -q "com.quant-superpowers.teams-harvester"; then
    echo "Unloading existing job..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi

# Create LaunchAgents directory if needed
mkdir -p "$LAUNCHD_DIR"

# Copy plist
cp "$PLIST_SRC" "$PLIST_DEST"
echo "✅ Copied plist to $PLIST_DEST"

# Load the job
launchctl load "$PLIST_DEST"
echo "✅ Loaded launchd job"

# Verify
if launchctl list | grep -q "com.quant-superpowers.teams-harvester"; then
    echo "✅ Job is running!"
else
    echo "⚠️  Job may not be running - check: launchctl list | grep teams"
fi

echo ""
echo "Schedule: Every hour at :15 past"
echo ""
echo "Commands:"
echo "  Check status:  launchctl list | grep teams-harvester"
echo "  View logs:     tail -f ~/Library/Logs/teams-transcript-harvester.log"
echo "  Run now:       launchctl start com.quant-superpowers.teams-harvester"
echo "  Stop:          launchctl unload $PLIST_DEST"
echo "  Uninstall:     rm $PLIST_DEST && launchctl remove com.quant-superpowers.teams-harvester"
