# Start My Day — Leadership Morning Briefing

**Date:** 2026-02-06
**Status:** Design
**Author:** Bradley Buckland + Claude

## Overview

A Claude Code skill (`/start-my-day`) that generates a personalized morning leadership briefing. Runs locally on macOS, reads from local data sources, and outputs a beautifully styled HTML page delivered via macOS notification on login/wake.

The briefing opens each day with scripture and an inspiring leadership quote, then gives a clear picture of the day ahead: calendar, action items, recent activity, and meeting transcript highlights.

## Data Sources

### 1. Bible Verse (CSB or ESV)

- **Primary:** ESV API (`api.esv.org`) — free tier, 500 requests/day
- **Fallback:** Bible API (`bible-api.com`) for CSB translation
- **Selection:** Verse of the day or curated rotation
- **Offline fallback:** Curated list embedded in skill file

### 2. Leadership Quotes

- Curated `quotes.md` file with 200+ quotes
- Sources: James Clear, John Maxwell, John Piper, Louie Giglio, C.S. Lewis, Martin Luther King Jr., Brene Brown, Andy Stanley, Tim Keller, Simon Sinek, Jim Collins, Patrick Lencioni, Craig Groeschel, Bob Goff, Dietrich Bonhoeffer, Abraham Lincoln, Theodore Roosevelt, Mother Teresa, Nelson Mandela, and more
- Aligned with Christian faith — quotes don't have to be from Christians but should resonate with a faith-driven leader
- Claude picks one randomly, avoiding recent repeats

### 3. Action Items (Obsidian Kanban)

- **Source:** `action-items-registry-kanban.md` in Obsidian vault
- **Vault path:** `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/`
- **Behavior:** Parse Kanban board format, extract active/in-progress items, present grouped by lane

### 4. Recent Notes (Obsidian)

- **Scan directories:** `Direct Reports/`, `Manager/`, `Meetings/`, `Peers/`
- **Time window:** Files modified in the last 48 hours
- **Behavior:** Claude reads each file and synthesizes a 1-2 line summary of what's notable (decisions made, topics discussed, follow-ups mentioned)

### 5. macOS Calendar

- **Tool:** `icalBuddy` CLI (`brew install ical-buddy`)
- **Command:** `icalBuddy -f eventsFrom:today to:today`
- **Behavior:** Parse today's events, format with times and titles

### 6. Teams Meeting Transcripts

- **Source:** `Meetings/_transcripts/` folder in the main Obsidian vault
- **Time window:** Transcripts from yesterday
- **Behavior:** Claude reads transcripts and extracts key discussion points, decisions, and action items
- **Prerequisite:** Fix and install the Teams transcript harvester (see Phase 2)

## Skill Structure

```
~/.personalclaude/skills/start-my-day/
├── SKILL.md          # Skill definition + Claude instructions
└── quotes.md         # 200+ curated leadership quotes
```

### SKILL.md Responsibilities

The skill instructs Claude to:

1. Greet the user with the current date
2. Fetch a Bible verse (CSB/ESV) via API, fall back to curated list
3. Select a leadership quote from `quotes.md`
4. Run `icalBuddy` to get today's calendar events
5. Read `action-items-registry-kanban.md` and extract open items
6. Glob for recently modified `.md` files in key Obsidian directories, read and summarize
7. Read yesterday's transcripts from `Meetings/_transcripts/`, summarize highlights
8. Generate a styled HTML file with all sections
9. Save to `~/.startmyday/briefing-YYYY-MM-DD.html`
10. Send macOS notification and open in browser

## HTML Design

### Design Inspiration

Blending two visual references:
- **Pointless Cards** (`pointless.cards`) — dark, cozy, playful, retro-pop energy
- **Valor Coffee** (`valor.coffee`) — warm, artisanal, handcrafted, golden warmth

The fusion: dark cozy night sky meets warm golden morning light. Like sunrise breaking through.

### Color Palette

| Role | Color | Hex |
|------|-------|-----|
| Background | Deep navy | `#1a1a2e` |
| Background gradient | Darker navy | `#16213e` |
| Sunrise gradient (top) | Warm gold glow | `#f5c542` at 5% opacity |
| Primary accent | Warm gold | `#f5c542` |
| Secondary accent | Valor navy blue | `#3E51A1` |
| Tertiary accent | Soft pink/coral | `#ff6b9d` |
| Body text | Warm cream | `#f5f0e8` |
| Muted text | Lavender-gray | `#a0a0c0` |
| Emphasis text | Bright cream | `#e8e8f0` |
| Card background | Semi-transparent | `rgba(255,255,255,0.05)` |
| Card border | Subtle light | `rgba(255,255,255,0.1)` |

### Typography

| Element | Font | Style |
|---------|------|-------|
| Greeting ("Good Morning, Bradley") | `Dancing Script` or `Cormorant Garamond` italic | Flowing cursive, large, gold with shimmer animation |
| Date | Sans-serif (Inter / system) | Small, muted lavender-gray |
| Verse text | `Cormorant Garamond` or elegant serif | Larger, gold, generous padding |
| Verse reference | Serif italic | Muted, smaller |
| Quote text | Sans-serif italic | Warm cream |
| Quote attribution | Sans-serif | Pink gradient |
| Section headers | Sans-serif bold | Gold with emoji prefix |
| Body / list items | Sans-serif (Inter / system) | Warm cream, 1.6 line-height |
| Footer tagline | Cursive (same as greeting) | Muted, smaller |

### Layout

- Centered single column, `max-width: 700px`
- Generous whitespace between sections (2-3rem)
- Each section in a frosted-glass card: `border-radius: 16px`, subtle border, soft background
- Subtle warm gradient overlay at the very top of the page (gold fading to transparent)
- Mobile-friendly (responsive, works on any screen)

### Section Visual Hierarchy

```
╭──────────────────────────────────────────╮
│  Warm gold-to-transparent gradient top   │
│                                          │
│  "Good Morning, Bradley"                 │
│   (flowing script, gold, shimmer)        │
│  Friday, February 6, 2026               │
╰──────────────────────────────────────────╯

╭──────────────────────────────────────────╮
│  VERSE OF THE DAY                        │
│  Large gold serif text, extra padding    │
│  — Reference in muted italic             │
│                                          │
│  LEADERSHIP QUOTE                        │
│  Cream italic text                       │
│  — Author in pink gradient               │
╰──────────────────────────────────────────╯

╭──────────────────────────────────────────╮
│  TODAY'S SCHEDULE                         │
│  Time pills: gold bg, dark text,         │
│  rounded corners. Event name in cream.   │
╰──────────────────────────────────────────╯

╭──────────────────────────────────────────╮
│  ACTION ITEMS                            │
│  Custom-styled checkboxes                │
│  Grouped by Kanban lane                  │
╰──────────────────────────────────────────╯

╭──────────────────────────────────────────╮
│  RECENT ACTIVITY                         │
│  1-2 line AI summaries per note          │
│  File context in muted text              │
╰──────────────────────────────────────────╯

╭──────────────────────────────────────────╮
│  MEETING HIGHLIGHTS                      │
│  Key points from yesterday's transcripts │
│  Decisions and action items called out   │
╰──────────────────────────────────────────╯

       "Go lead well today."
         (flowing script, muted)
```

### Animations

- **Greeting:** Subtle CSS shimmer/glow animation on the script text
- **Cards:** Fade-up entrance animation on page load (staggered, 100ms delay between cards)
- **Time pills:** Gentle pulse on hover
- **Overall:** Understated — enhances warmth without distraction

## Automation

### Delivery Mechanism

1. **Launchd plist** at `~/Library/LaunchAgents/com.startmyday.briefing.plist`
2. Configured with `RunAtLoad: true` — fires on login or wake from sleep
3. State file at `~/.startmyday/.last-run` prevents running more than once per day

### Wrapper Script (`~/.startmyday/run.sh`)

```bash
#!/bin/bash
STATE_FILE="$HOME/.startmyday/.last-run"
TODAY=$(date +%Y-%m-%d)

# Only run once per day
if [ -f "$STATE_FILE" ] && [ "$(cat $STATE_FILE)" = "$TODAY" ]; then
    exit 0
fi

# Generate briefing
claude -p "/start-my-day" 2>/dev/null

# Record that we ran today
echo "$TODAY" > "$STATE_FILE"

# Notify
osascript -e 'display notification "Your morning briefing is ready" with title "Good Morning" sound name "Glass"'

# Open in browser
open "$HOME/.startmyday/briefing-$TODAY.html"
```

### Launchd Plist

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.startmyday.briefing</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>~/.startmyday/run.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>~/.startmyday/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>~/.startmyday/logs/stderr.log</string>
</dict>
</plist>
```

## Implementation Phases

### Phase 1 — Build the Skill

Create the Claude Code skill with all data source integrations:

- `~/.personalclaude/skills/start-my-day/SKILL.md` — full skill definition
- `~/.personalclaude/skills/start-my-day/quotes.md` — 200+ curated quotes
- HTML template generation with the designed visual style
- All 6 data source integrations
- Manual invocation via `/start-my-day` for iteration

**Prerequisites:**
- Install `icalBuddy`: `brew install ical-buddy`
- ESV API key: register at `api.esv.org` (free)

### Phase 2 — Fix the Teams Transcript Harvester

- Update `teams-transcript-harvester/config.env`:
  - Fix repo path references (currently points to old `quant-superpowers`)
  - Set `OBSIDIAN_VAULT` output to main vault's `Meetings/_transcripts/`
- Create `Meetings/_transcripts/` directory in Obsidian vault
- Fix launchd plist paths in `com.quant-superpowers.teams-harvester.plist`
- Rename plist to `com.teams-harvester.plist`
- Install launchd job and verify it runs

### Phase 3 — Automate the Briefing

- Create `~/.startmyday/` directory structure
- Write `run.sh` wrapper script
- Create and install launchd plist
- Test end-to-end: login → generate → notify → open HTML

### Phase 4 — Graduate to OpenClaw (Future)

- Port skill to `openclaw/skills/start-my-day/`
- BuckBot delivers briefing via Telegram
- Add Jira integration (via API)
- Add GitHub integration (via `gh` CLI or API)
- Server-side scheduling (works even when laptop is closed)

## Dependencies

| Dependency | Purpose | Install |
|------------|---------|---------|
| `icalBuddy` | macOS calendar access | `brew install ical-buddy` |
| ESV API key | Bible verse (ESV translation) | Register at `api.esv.org` |
| Google Fonts | `Dancing Script`, `Cormorant Garamond` | Loaded via CSS `@import` in HTML |
| Teams harvester (Phase 2) | Meeting transcripts | Fix existing `teams-transcript-harvester/` |

## Open Questions

1. **ESV API key** — need to register. Free tier is 500 req/day (more than enough)
2. **icalBuddy** — need to verify it's installed or install it
3. **Kanban format** — need to read `action-items-registry-kanban.md` to understand the exact Obsidian Kanban plugin format for parsing
4. **Transcript folder** — `Meetings/_transcripts/` doesn't exist yet, needs creation
