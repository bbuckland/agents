#!/bin/bash

echo "⏰ Setting up Teams Transcript Harvester Cron Job"
echo "=================================================="

# Get current directory (where harvester is installed)
HARVESTER_DIR="$PWD"

# Check if harvester.js exists
if [ ! -f "$HARVESTER_DIR/harvester.js" ]; then
    echo "❌ harvester.js not found in current directory"
    echo "   Please run this script from the harvester installation directory"
    exit 1
fi

# Get user input for schedule
echo "📅 Choose harvest schedule:"
echo "1. Daily at 8:00 AM (recommended)"
echo "2. Daily at 6:00 AM"
echo "3. Weekdays at 9:00 AM"
echo "4. Custom time"
echo ""
read -p "Enter choice (1-4): " schedule_choice

case $schedule_choice in
    1)
        CRON_TIME="0 8 * * *"
        SCHEDULE_DESC="Daily at 8:00 AM"
        ;;
    2)
        CRON_TIME="0 6 * * *"
        SCHEDULE_DESC="Daily at 6:00 AM"
        ;;
    3)
        CRON_TIME="0 9 * * 1-5"
        SCHEDULE_DESC="Weekdays at 9:00 AM"
        ;;
    4)
        echo "Enter cron time (format: minute hour day month weekday)"
        echo "Examples:"
        echo "  0 8 * * *     = 8:00 AM daily"
        echo "  30 9 * * 1-5  = 9:30 AM weekdays"
        echo "  0 */4 * * *   = Every 4 hours"
        read -p "Enter cron time: " CRON_TIME
        SCHEDULE_DESC="Custom: $CRON_TIME"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

# Build cron command
CRON_COMMAND="cd $HARVESTER_DIR && source config.env 2>/dev/null && node harvester.js >> harvest.log 2>&1"

# Show what will be installed
echo ""
echo "📋 Cron Job Details:"
echo "   Schedule: $SCHEDULE_DESC"
echo "   Command: $CRON_COMMAND"
echo ""

# Confirm installation
read -p "Install this cron job? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "❌ Installation cancelled"
    exit 0
fi

# Create new crontab with the job
echo "⚙️  Installing cron job..."

# Get existing crontab, add new job, install
(crontab -l 2>/dev/null | grep -v "teams-harvester"; echo "$CRON_TIME $CRON_COMMAND # teams-harvester") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ Cron job installed successfully!"
    echo ""
    echo "📊 Job Status:"
    echo "   Schedule: $SCHEDULE_DESC"
    echo "   Logs: $HARVESTER_DIR/harvest.log"
    echo ""
    echo "🔧 Management Commands:"
    echo "   View all cron jobs: crontab -l"
    echo "   Edit cron jobs: crontab -e"
    echo "   View harvest logs: tail -f $HARVESTER_DIR/harvest.log"
    echo "   Test harvest: cd $HARVESTER_DIR && node harvester.js --dry-run"
else
    echo "❌ Failed to install cron job"
    exit 1
fi

# Test that the job syntax is valid
echo ""
echo "🧪 Testing job syntax..."
if crontab -l | grep -q "teams-harvester"; then
    echo "✅ Cron job syntax valid"
else
    echo "⚠️  Cron job not found - there may have been an issue"
fi

echo ""
echo "🎉 Setup complete! Your Teams transcripts will be harvested automatically."