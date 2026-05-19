# Start My Day — Phase 1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Claude Code skill (`/start-my-day`) that generates a styled HTML morning briefing from local data sources.

**Architecture:** A personal Claude Code skill at `~/.personalclaude/skills/start-my-day/` containing a SKILL.md (instructions for Claude), quotes.md (200+ curated quotes), and an HTML template. When invoked, Claude gathers data from 5 local sources, assembles the HTML, saves it, and opens it in the browser.

**Tech Stack:** Claude Code skill (markdown), HTML/CSS (single-file template with inline styles + Google Fonts), icalBuddy (calendar), ESV/Bible API (verse), Bash (osascript for notification).

**Design doc:** `docs/plans/2026-02-06-start-my-day-design.md`

---

### Task 1: Install Prerequisites

**Files:**
- None (system setup)

**Step 1: Install icalBuddy**

Run: `brew install ical-buddy`

**Step 2: Verify icalBuddy works**

Run: `icalBuddy eventsToday`
Expected: List of today's calendar events (or empty output if no events). Should NOT error.

**Step 3: Create directory structure**

Run:
```bash
mkdir -p ~/.startmyday/logs
```

**Step 4: Commit**

No commit — system setup only.

---

### Task 2: Create the Leadership Quotes File

**Files:**
- Create: `~/.personalclaude/skills/start-my-day/quotes.md`

**Step 1: Create the skill directory**

Run: `mkdir -p ~/.personalclaude/skills/start-my-day`

**Step 2: Write quotes.md with 200+ curated quotes**

Create `~/.personalclaude/skills/start-my-day/quotes.md` with the following structure:

```markdown
# Leadership Quotes

One quote per line. Format: "Quote text" — Author

## Faith & Purpose

"Trust in the Lord with all your heart and lean not on your own understanding; in all your ways submit to him, and he will make your paths straight." — Proverbs 3:5-6
"The place God calls you to is the place where your deep gladness and the world's deep hunger meet." — Frederick Buechner
"You are never too old to set another goal or to dream a new dream." — C.S. Lewis
...

## Leadership & Influence

"A leader is one who knows the way, goes the way, and shows the way." — John Maxwell
...

## Growth & Habits

"Every action you take is a vote for the type of person you wish to become." — James Clear
...

## Courage & Character

"The ultimate measure of a man is not where he stands in moments of comfort, but where he stands at times of challenge." — Martin Luther King Jr.
...

## Service & Humility

"The best leader is the one who has sense enough to pick good men to do what he wants done, and self-restraint enough to keep from meddling with them while they do it." — Theodore Roosevelt
...
```

**Quote sources to include (minimum counts):**

- James Clear — 15+ quotes (Atomic Habits, newsletter)
- John Maxwell — 15+ quotes (21 Irrefutable Laws, Developing the Leader Within You)
- John Piper — 10+ quotes (Desiring God, Don't Waste Your Life)
- Louie Giglio — 10+ quotes (Not Forsaken, Goliath Must Fall)
- C.S. Lewis — 10+ quotes (Mere Christianity, Screwtape Letters)
- Tim Keller — 10+ quotes (Every Good Endeavor, The Reason for God)
- Andy Stanley — 10+ quotes (Next Generation Leader, Better Decisions)
- Craig Groeschel — 8+ quotes (Leadership Podcast, Winning the War in Your Mind)
- Bob Goff — 8+ quotes (Love Does, Dream Big)
- Dietrich Bonhoeffer — 5+ quotes (The Cost of Discipleship, Life Together)
- Martin Luther King Jr. — 8+ quotes
- Brene Brown — 8+ quotes (Dare to Lead, Rising Strong)
- Simon Sinek — 8+ quotes (Start With Why, Leaders Eat Last)
- Jim Collins — 5+ quotes (Good to Great)
- Patrick Lencioni — 5+ quotes (Five Dysfunctions of a Team)
- Theodore Roosevelt — 5+ quotes
- Abraham Lincoln — 5+ quotes
- Mother Teresa — 5+ quotes
- Nelson Mandela — 5+ quotes
- Henri Nouwen — 5+ quotes
- Dallas Willard — 5+ quotes
- A.W. Tozer — 5+ quotes
- Oswald Chambers — 5+ quotes
- Additional leaders, pastors, authors — fill to 200+

**Guiding principle:** Every quote should resonate with a Christian leader — it doesn't have to be explicitly Christian, but it should align with values of servant leadership, faith, humility, courage, growth, and purpose.

**Step 3: Verify quote count**

Run: `grep -c '^"' ~/.personalclaude/skills/start-my-day/quotes.md`
Expected: 200 or more

**Step 4: Commit**

```bash
cd ~/personal/code/agents
git add ~/.personalclaude/skills/start-my-day/quotes.md
git commit -m "feat: add 200+ curated leadership quotes for start-my-day skill"
```

Note: This file is outside the repo. No git commit needed unless we symlink or copy it in.

---

### Task 3: Create the HTML Template

**Files:**
- Create: `~/.personalclaude/skills/start-my-day/template.html`

**Step 1: Write the HTML template**

Create `~/.personalclaude/skills/start-my-day/template.html` — a complete, self-contained HTML file with inline CSS. Claude will read this template and replace the placeholder sections with real data.

**Template requirements:**

1. **Google Fonts loaded via `<link>`:** `Dancing Script` (greeting/footer), `Cormorant Garamond` (verse), `Inter` (body)

2. **Color palette (from design doc):**
   - Background: `#1a1a2e` with gradient to `#16213e`
   - Gold accent: `#f5c542`
   - Pink accent: `#ff6b9d`
   - Body text: `#f5f0e8`
   - Muted text: `#a0a0c0`
   - Card bg: `rgba(255,255,255,0.05)`
   - Card border: `rgba(255,255,255,0.1)`

3. **Sections with placeholder markers:**
   - `{{GREETING}}` — "Good Morning, Bradley"
   - `{{DATE}}` — "Friday, February 6, 2026"
   - `{{VERSE_TEXT}}` — The verse text
   - `{{VERSE_REFERENCE}}` — e.g., "Proverbs 3:5 (ESV)"
   - `{{QUOTE_TEXT}}` — The quote
   - `{{QUOTE_AUTHOR}}` — The author
   - `{{SCHEDULE_ITEMS}}` — HTML list of calendar events (each as `<div class="event"><span class="time">9:00 AM</span><span class="title">1:1 with Ben</span></div>`)
   - `{{ACTION_ITEMS}}` — HTML grouped by Kanban lane
   - `{{RECENT_ACTIVITY}}` — HTML list of summaries
   - `{{TRANSCRIPT_HIGHLIGHTS}}` — HTML list of highlights (or "No recent transcripts" message)

4. **CSS animations:**
   - `@keyframes shimmer` on greeting text
   - `@keyframes fadeUp` on cards (staggered via `animation-delay`)

5. **Layout:** Centered, `max-width: 700px`, responsive
6. **Cards:** `border-radius: 16px`, frosted-glass effect
7. **Time pills:** Gold bg (`#f5c542`), dark text (`#1a1a2e`), `border-radius: 20px`, `padding: 4px 12px`
8. **Footer:** "Go lead well today." in `Dancing Script`, muted

**Step 2: Open in browser to visually verify**

Run: `open ~/.personalclaude/skills/start-my-day/template.html`

Verify:
- Dark navy background with warm gold gradient at top
- Greeting in flowing script with shimmer
- Cards have frosted-glass look
- Typography hierarchy is clear
- Gold/pink/cream colors are balanced
- Animations are subtle and smooth
- Looks good on a normal browser window

**Step 3: Iterate on design if needed**

If the design doesn't look right, adjust the CSS and re-open. Repeat until it matches the Pointless + Valor vibe described in the design doc.

---

### Task 4: Create the SKILL.md

**Files:**
- Create: `~/.personalclaude/skills/start-my-day/SKILL.md`

**Step 1: Write SKILL.md**

The SKILL.md is the core of the skill. It tells Claude exactly what to do when `/start-my-day` is invoked. Structure:

```markdown
---
name: start-my-day
description: Generate a personalized morning leadership briefing with scripture, quotes, calendar, action items, and recent activity — delivered as a styled HTML page
---

# Start My Day — Morning Leadership Briefing

## Overview

Generate a morning briefing for Bradley. Gather data from local sources, assemble into a styled HTML page, save it, notify, and open in browser.

## Step 1: Gather Data

### 1a. Bible Verse (ESV or CSB)

Use WebFetch to get a verse from the ESV API:
- URL: `https://api.esv.org/v3/passage/text/?q=verse-of-the-day`
- If the ESV API requires a key or fails, use WebFetch against `https://bible-api.com/john+3:16?translation=web` (change verse as needed)
- Fallback: Pick a well-known verse from memory

Preferred translations: ESV first, then CSB.

### 1b. Leadership Quote

Read `quotes.md` (in this skill's directory).
Pick ONE quote at random from the file.
To avoid repeats, check `~/.startmyday/.last-quote` for the last used quote and pick a different one. After selecting, write the chosen quote to `.last-quote`.

### 1c. Calendar Events

Run via Bash: `icalBuddy -f -nc eventsToday`
Parse the output to extract event times and titles.
If icalBuddy is not installed or errors, show "Calendar unavailable — install icalBuddy via brew install ical-buddy"

### 1d. Action Items (Obsidian Kanban)

Read file: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/action-items-registry-kanban.md`

This is an Obsidian Kanban board. Format:
- `## Lane Name` headers define lanes
- Items are listed as `- [ ] item text` or `- item text` under each lane
- Lanes to show: **Today**, **This Week**, **Pending Response** (skip Backlog, Done, Icebox)
- Present items grouped by lane

### 1e. Recent Notes

Use Glob to find `.md` files modified in the last 48 hours in these directories:
- `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/Direct Reports/`
- `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/Manager/`
- `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/Meetings/`
- `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/Peers/`

Use Bash with `find` to identify recently modified files:
`find "<directory>" -name "*.md" -mtime -2 -type f`

Read each file and write a 1-2 line summary of what's notable (decisions, topics, follow-ups). Skip files that are just template/boilerplate.

### 1f. Meeting Transcript Highlights

Check if `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/notes/Meetings/_transcripts/` exists.
If it does, find transcripts from yesterday using `find` with `-mtime -1`.
Read each and summarize key discussion points, decisions, action items.
If the folder doesn't exist or has no recent transcripts, show "No recent transcripts available."

## Step 2: Generate HTML

Read the template file: `template.html` (in this skill's directory).

Replace each placeholder with the gathered data:
- `{{GREETING}}` → "Good Morning, Bradley" (or afternoon/evening based on time)
- `{{DATE}}` → Current date formatted as "Friday, February 6, 2026"
- `{{VERSE_TEXT}}` → The fetched verse text
- `{{VERSE_REFERENCE}}` → Book Chapter:Verse (Translation)
- `{{QUOTE_TEXT}}` → The selected quote
- `{{QUOTE_AUTHOR}}` → The author name
- `{{SCHEDULE_ITEMS}}` → Calendar events as HTML. Each event: `<div class="event"><span class="time-pill">TIME</span> <span class="event-title">TITLE</span></div>`. If no events: `<p class="muted">No events scheduled today.</p>`
- `{{ACTION_ITEMS}}` → Kanban items grouped by lane as HTML. Each lane: `<h4 class="lane-title">LANE</h4>` followed by `<div class="action-item"><span class="checkbox">☐</span> ITEM</div>`. If no items: `<p class="muted">All clear!</p>`
- `{{RECENT_ACTIVITY}}` → Recent notes as HTML. Each: `<div class="activity-item"><span class="activity-source">SOURCE</span><p>SUMMARY</p></div>`. If none: `<p class="muted">No recent notes.</p>`
- `{{TRANSCRIPT_HIGHLIGHTS}}` → Transcript summaries as HTML. Each: `<div class="transcript-item"><span class="transcript-meeting">MEETING NAME</span><p>KEY POINTS</p></div>`. If none: `<p class="muted">No recent transcripts.</p>`

## Step 3: Save and Open

1. Write the completed HTML to `~/.startmyday/briefing-YYYY-MM-DD.html` (using today's date)
2. Run via Bash: `osascript -e 'display notification "Your morning briefing is ready" with title "Good Morning ☀️" sound name "Glass"'`
3. Run via Bash: `open ~/.startmyday/briefing-YYYY-MM-DD.html`

## Important Notes

- Do NOT ask the user any questions. Just gather, generate, and open.
- If any data source fails, include a graceful fallback message in that section — never let one failure block the whole briefing.
- Keep summaries concise — this is a morning scan, not a deep read.
- The greeting should adapt: "Good Morning" before noon, "Good Afternoon" 12-5pm, "Good Evening" after 5pm.
```

**Step 2: Verify skill is discoverable**

Run: `ls ~/.personalclaude/skills/start-my-day/`
Expected: `SKILL.md  quotes.md  template.html`

---

### Task 5: End-to-End Test

**Step 1: Invoke the skill manually**

In a Claude Code session, run: `/start-my-day`

**Step 2: Verify all sections populated**

Check that the opened HTML page has:
- [ ] Greeting with correct name and date
- [ ] Bible verse with reference
- [ ] Leadership quote with author
- [ ] Calendar events (or graceful "no events" message)
- [ ] Action items from Kanban (or "all clear")
- [ ] Recent activity summaries (or "no recent notes")
- [ ] Transcript section (expect "no recent transcripts" until Phase 2)
- [ ] Footer tagline "Go lead well today."
- [ ] Correct visual styling matching the design

**Step 3: Verify HTML file was saved**

Run: `ls ~/.startmyday/briefing-$(date +%Y-%m-%d).html`
Expected: File exists

**Step 4: Verify notification appeared**

Expected: macOS notification with "Your morning briefing is ready" title

**Step 5: Iterate**

If any section looks wrong, fix the relevant file (SKILL.md, template.html, or quotes.md) and re-run `/start-my-day`.
