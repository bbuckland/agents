#!/usr/bin/env node

const { chromium } = require('playwright');
const fs = require('fs-extra');
const path = require('path');

// Configuration
const CONFIG = {
  obsidianVault: process.env.OBSIDIAN_VAULT || path.join(process.env.HOME, 'Documents/personal/notes'),
  meetingsFolder: 'Meetings/Teams',
  stateFile: path.join(__dirname, 'harvester-state.json'),
  userDataDir: path.join(__dirname, '.browser-profile'),
  headless: process.env.HEADLESS !== 'false',
  dryRun: process.argv.includes('--dry-run'),
  maxMeetings: parseInt(process.env.MAX_MEETINGS) || 10, // Limit per run
};

class TeamsHarvester {
  constructor() {
    this.context = null;
    this.page = null;
    this.state = this.loadState();
  }

  loadState() {
    try {
      if (fs.existsSync(CONFIG.stateFile)) {
        const data = JSON.parse(fs.readFileSync(CONFIG.stateFile, 'utf8'));
        return {
          ...data,
          processedMeetings: new Set(data.processedMeetings || [])
        };
      }
    } catch (error) {
      console.log('⚠️  Could not load state file, starting fresh');
    }
    return { processedMeetings: new Set() };
  }

  saveState() {
    try {
      const stateToSave = {
        ...this.state,
        processedMeetings: Array.from(this.state.processedMeetings),
        lastRun: new Date().toISOString()
      };
      fs.writeFileSync(CONFIG.stateFile, JSON.stringify(stateToSave, null, 2));
    } catch (error) {
      console.error('❌ Failed to save state:', error.message);
    }
  }

  async launch() {
    console.log('🚀 Launching browser...');

    this.context = await chromium.launchPersistentContext(CONFIG.userDataDir, {
      headless: CONFIG.headless,
      viewport: { width: 1920, height: 1080 },
      channel: 'chrome',
    });

    this.page = this.context.pages()[0] || await this.context.newPage();
    this.page.setDefaultTimeout(30000);
  }

  async navigateToTeams() {
    console.log('🔐 Navigating to Teams...');
    await this.page.goto('https://teams.microsoft.com', {
      waitUntil: 'domcontentloaded',
      timeout: 60000
    });

    // Wait for Teams to load
    await this.page.waitForTimeout(5000);

    const url = this.page.url();
    if (url.includes('login') || url.includes('microsoftonline')) {
      console.log('⏳ Please log in to Teams...');
      await this.page.waitForURL(
        u => u.href.includes('teams.microsoft.com') && !u.href.includes('login'),
        { timeout: 300000 }
      );
      await this.page.waitForTimeout(5000);
    }

    console.log('✅ Logged in to Teams');
  }

  async navigateToMeetingChats() {
    console.log('💬 Navigating to Meeting Chats...');

    // Click on Chat in the left sidebar
    try {
      // Try clicking Chat by aria-label or text
      const chatButton = this.page.locator('[aria-label="Chat"], [data-tid="app-bar-chat"]').first();
      if (await chatButton.isVisible({ timeout: 5000 })) {
        await chatButton.click();
        await this.page.waitForTimeout(2000);
      }
    } catch (e) {
      console.log('   Chat may already be selected');
    }

    // Click "Meeting chats" filter
    try {
      const meetingChatsFilter = this.page.locator('button:has-text("Meeting chats"), [aria-label*="Meeting chats"]').first();
      if (await meetingChatsFilter.isVisible({ timeout: 5000 })) {
        await meetingChatsFilter.click();
        await this.page.waitForTimeout(2000);
        console.log('✅ Filtered to Meeting Chats');
      } else {
        // Try alternative: look for filter pills
        const filterPill = this.page.locator('text="Meeting chats"').first();
        if (await filterPill.isVisible({ timeout: 3000 })) {
          await filterPill.click();
          await this.page.waitForTimeout(2000);
        }
      }
    } catch (e) {
      console.log('⚠️  Could not find Meeting chats filter, continuing anyway');
    }
  }

  async getMeetingsList() {
    console.log('🔍 Scanning for meetings with recordings...');

    await this.page.waitForTimeout(2000);

    // Get all meeting chat items from the left sidebar chat list
    const meetings = await this.page.evaluate(() => {
      const items = [];

      // Find all treeitems - these are the chat list items
      const allTreeItems = document.querySelectorAll('[role="treeitem"]');

      allTreeItems.forEach((item, index) => {
        const fullText = item.innerText?.trim() || '';
        const lines = fullText.split('\n').filter(l => l.trim());

        // Skip if this looks like a filter button or section header
        const skipKeywords = ['unread', 'channels', 'chats', 'meeting chats', 'more filters', 'favorites', 'pinned', 'recent'];
        const firstLine = (lines[0] || '').toLowerCase();
        if (skipKeywords.includes(firstLine) || fullText.length < 15) {
          return;
        }

        // Actual chat items have timestamps (time or date format)
        const hasTimestamp = /\d{1,2}:\d{2}\s*(AM|PM)?|\d{1,2}\/\d{1,2}/.test(fullText);
        if (!hasTimestamp) {
          return; // Skip items without timestamps - they're not chat entries
        }

        const title = lines[0] || `Meeting ${index + 1}`;
        const subtitle = lines.slice(1).join(' ').substring(0, 100);
        const hasRecording = fullText.toLowerCase().includes('recording');

        items.push({
          title: title.substring(0, 100),
          subtitle,
          hasRecording,
          index,
          fullText: fullText.substring(0, 200),
          id: `${title}`.replace(/[^a-zA-Z0-9]/g, '-').substring(0, 100)
        });
      });

      return items;
    });

    // Filter to meetings that likely have recordings
    const meetingsWithRecordings = meetings.filter(m =>
      m.hasRecording || m.subtitle.toLowerCase().includes('recording')
    );

    console.log(`📊 Found ${meetings.length} chats, ${meetingsWithRecordings.length} with recordings`);

    // Log first few for debugging
    if (meetings.length > 0) {
      console.log('   First few meetings found:');
      meetings.slice(0, 3).forEach(m => console.log(`   - "${m.title}" ${m.hasRecording ? '(has recording)' : ''}`));
    }

    // Prioritize meetings with recordings
    return meetingsWithRecordings.length > 0 ? meetingsWithRecordings : meetings.slice(0, CONFIG.maxMeetings);
  }

  async clickMeeting(meeting) {
    console.log(`📝 Opening: ${meeting.title}`);

    // Use keyboard to ensure focus is in the right place
    // Press Escape first to clear any open dialogs/menus
    await this.page.keyboard.press('Escape');
    await this.page.waitForTimeout(500);

    // Normalize the title for matching (replace special chars)
    const normalizedTitle = meeting.title
      .replace(/[–—]/g, '-')  // Normalize dashes
      .replace(/'/g, "'")      // Normalize quotes
      .substring(0, 30);

    // Try clicking by finding element containing the text
    // Use getByRole to find treeitem with matching text
    try {
      const meetingItems = this.page.getByRole('treeitem');
      const count = await meetingItems.count();

      for (let i = 0; i < count; i++) {
        const item = meetingItems.nth(i);
        if (await item.isVisible({ timeout: 500 })) {
          const text = await item.innerText();
          const normalizedText = text.replace(/[–—]/g, '-').replace(/'/g, "'");

          if (normalizedText.includes(normalizedTitle)) {
            // Found it - scroll into view and click
            await item.scrollIntoViewIfNeeded();
            await item.click({ force: true });
            await this.page.waitForTimeout(3000);
            console.log(`   ✅ Clicked meeting at index ${i}`);
            return true;
          }
        }
      }
    } catch (e) {
      console.log(`   TreeItem search failed: ${e.message.substring(0, 50)}`);
    }

    // Fallback: use keyboard navigation
    // Click on Chat nav, then use arrow keys
    try {
      await this.page.click('[aria-label="Chat"]', { timeout: 2000 });
      await this.page.waitForTimeout(1000);

      // Find and click the meeting chats filter
      await this.page.click('text="Meeting chats"', { timeout: 2000 });
      await this.page.waitForTimeout(1000);

      // Use getByText for a less strict match
      const meetingEl = this.page.getByText(normalizedTitle.substring(0, 20), { exact: false }).first();
      if (await meetingEl.isVisible({ timeout: 3000 })) {
        await meetingEl.click();
        await this.page.waitForTimeout(3000);
        console.log(`   ✅ Clicked meeting by text content`);
        return true;
      }
    } catch (e) {
      console.log(`   Fallback click failed: ${e.message.substring(0, 50)}`);
    }

    console.log(`   ⚠️  Could not click meeting "${meeting.title.substring(0, 30)}"`);
    return false;
  }

  async navigateToRecap() {
    console.log('   📋 Navigating to Recap tab...');

    // Wait for page to fully load
    await this.page.waitForTimeout(3000);

    // Look for Recap tab with multiple selectors
    const recapSelectors = [
      'text="Recap"',
      'button:has-text("Recap")',
      '[role="tab"]:has-text("Recap")',
      '[data-tid*="recap"]',
    ];

    for (const selector of recapSelectors) {
      try {
        const recapTab = this.page.locator(selector).first();
        if (await recapTab.isVisible({ timeout: 3000 })) {
          await recapTab.click();
          await this.page.waitForTimeout(3000);
          console.log('   ✅ Recap tab clicked');
          return true;
        }
      } catch (e) {
        // Try next selector
      }
    }

    // Log what tabs we can see for debugging
    const visibleTabs = await this.page.evaluate(() => {
      const tabs = document.querySelectorAll('[role="tab"], button');
      return Array.from(tabs)
        .map(t => t.innerText?.trim())
        .filter(t => t && t.length < 30)
        .slice(0, 10);
    });
    console.log(`   ⚠️  Recap not found. Visible tabs: ${visibleTabs.join(', ')}`);

    return false;
  }

  async extractAISummary() {
    console.log('   🤖 Extracting AI Summary...');

    // Click AI summary sub-tab (within Recap)
    try {
      const aiSummaryTab = this.page.locator('button:has-text("AI summary")').first();
      if (await aiSummaryTab.isVisible({ timeout: 3000 })) {
        await aiSummaryTab.click();
        await this.page.waitForTimeout(2000);
      }
    } catch (e) {
      // AI summary tab might not exist or already selected
    }

    // Extract the content - looking for the actual structure from Teams
    const summary = await this.page.evaluate(() => {
      const content = {
        meetingNotes: [],
        followUpTasks: [],
        rawText: ''
      };

      // Get all text content from the main content area
      // Teams puts the AI summary in a scrollable area after the tabs
      const mainArea = document.querySelector('[role="main"]');
      if (!mainArea) return content;

      const fullText = mainArea.innerText || '';

      // Look for "Meeting notes" section
      const meetingNotesMatch = fullText.match(/Meeting notes\s*([\s\S]*?)(?=Follow-up tasks|$)/i);
      if (meetingNotesMatch) {
        // Extract bullet points from this section
        const notesText = meetingNotesMatch[1];
        // Split by common bullet patterns or newlines with substantial content
        const bullets = notesText.split(/[▸►●•]\s*|\n(?=[A-Z])/).filter(b => b.trim().length > 20);
        bullets.forEach(b => {
          const cleaned = b.trim().replace(/\s+/g, ' ');
          if (cleaned.length > 20) {
            content.meetingNotes.push(cleaned);
          }
        });
      }

      // Look for "Follow-up tasks" section
      const tasksMatch = fullText.match(/Follow-up tasks\s*([\s\S]*?)(?=Full Transcript|$)/i);
      if (tasksMatch) {
        const tasksText = tasksMatch[1];
        const tasks = tasksText.split(/[▸►●•]\s*|\n(?=[A-Z])/).filter(t => t.trim().length > 10);
        tasks.forEach(t => {
          const cleaned = t.trim().replace(/\s+/g, ' ');
          if (cleaned.length > 10) {
            content.followUpTasks.push(cleaned);
          }
        });
      }

      // Also try: find all list items (li elements) in the content area
      if (content.meetingNotes.length === 0) {
        const listItems = mainArea.querySelectorAll('li, [role="listitem"]');
        let inTasks = false;

        listItems.forEach(li => {
          const text = li.innerText?.trim();
          if (!text || text.length < 20) return;

          // Skip if this looks like a chat message or navigation item
          if (li.closest('[data-tid="chat-list"]') || li.closest('[role="tree"]')) return;

          // Check if we've reached follow-up tasks
          const prevText = li.previousElementSibling?.innerText?.toLowerCase() || '';
          if (prevText.includes('follow-up') || prevText.includes('action')) {
            inTasks = true;
          }

          if (inTasks || text.toLowerCase().includes('(bradley)') || text.toLowerCase().includes('action:')) {
            content.followUpTasks.push(text);
          } else {
            content.meetingNotes.push(text);
          }
        });
      }

      // Store raw text for fallback
      content.rawText = fullText.substring(0, 5000);

      return content;
    });

    console.log(`   Found ${summary.meetingNotes.length} notes, ${summary.followUpTasks.length} tasks`);
    return summary;
  }

  async extractTranscript() {
    console.log('   📜 Extracting Transcript...');

    // Click Transcript tab
    const transcriptTab = this.page.locator('button:has-text("Transcript"), [aria-label*="Transcript"]').first();

    if (await transcriptTab.isVisible({ timeout: 3000 })) {
      await transcriptTab.click();
      await this.page.waitForTimeout(2000);
    } else {
      console.log('   ⚠️  Transcript tab not found');
      return null;
    }

    // Extract transcript content
    const transcript = await this.page.evaluate(() => {
      const entries = [];
      const participants = new Set();

      // Look for transcript entries
      const transcriptContainer = document.querySelector('[class*="transcript"], [data-tid*="transcript"]');

      if (transcriptContainer) {
        // Try to find individual entries
        const entryElements = transcriptContainer.querySelectorAll('[class*="entry"], [class*="line"], [role="listitem"], p, div');

        entryElements.forEach(el => {
          const text = el.innerText?.trim();
          if (!text || text.length < 5) return;

          // Try to parse speaker: text format
          const speakerMatch = text.match(/^([A-Za-z\s]+?):\s*(.+)$/s);
          if (speakerMatch) {
            const speaker = speakerMatch[1].trim();
            const content = speakerMatch[2].trim();
            participants.add(speaker);
            entries.push({ speaker, text: content, timestamp: '' });
          } else if (text.length > 20) {
            entries.push({ speaker: 'Unknown', text, timestamp: '' });
          }
        });
      }

      // Fallback: look for any substantial text in the area
      if (entries.length === 0) {
        const mainArea = document.querySelector('[role="main"], .main-content');
        if (mainArea) {
          const fullText = mainArea.innerText;
          // Split by common patterns
          const lines = fullText.split(/\n/).filter(l => l.trim().length > 10);
          lines.forEach(line => {
            const speakerMatch = line.match(/^([A-Za-z\s]+?):\s*(.+)$/);
            if (speakerMatch) {
              participants.add(speakerMatch[1].trim());
              entries.push({
                speaker: speakerMatch[1].trim(),
                text: speakerMatch[2].trim(),
                timestamp: ''
              });
            }
          });
        }
      }

      return {
        participants: Array.from(participants),
        entries
      };
    });

    return transcript;
  }

  async extractMeetingData(meeting) {
    // Click on the meeting
    if (!await this.clickMeeting(meeting)) {
      console.log(`   ❌ Could not open meeting: ${meeting.title}`);
      return null;
    }

    // Navigate to Recap
    if (!await this.navigateToRecap()) {
      return null;
    }

    // Get meeting metadata from page - need to find the correct elements
    const metadata = await this.page.evaluate(() => {
      let title = '';
      let date = '';

      // The meeting title is usually in the header area
      // Look for h2 with data-tid="chat-title" or similar
      const titleEl = document.querySelector('[data-tid="chat-title"]');
      if (titleEl) {
        title = titleEl.innerText?.trim() || '';
      }

      // Also check the page title which often has the meeting name
      const pageTitle = document.title || '';
      if (!title && pageTitle.includes('|')) {
        // Format: "Chat | Meeting Name | Microsoft Teams"
        const parts = pageTitle.split('|').map(p => p.trim());
        if (parts.length >= 2) {
          title = parts[1]; // Usually the second part
        }
      }

      // Look for date/time - Teams shows it like "Monday, February 2, 2026 3:00 PM - 3:45 PM"
      // This is typically shown below the tabs in the Recap view
      const mainArea = document.querySelector('[role="main"]');
      if (mainArea) {
        const text = mainArea.innerText || '';
        // Look for date pattern
        const dateMatch = text.match(/(\w+day,?\s+\w+\s+\d{1,2},?\s+\d{4}\s+\d{1,2}:\d{2}\s*(?:AM|PM)?(?:\s*-\s*\d{1,2}:\d{2}\s*(?:AM|PM)?)?)/i);
        if (dateMatch) {
          date = dateMatch[1];
        }
      }

      // Fallback: look for any time element
      if (!date) {
        const timeEl = document.querySelector('time');
        if (timeEl) {
          date = timeEl.innerText?.trim() || timeEl.getAttribute('datetime') || '';
        }
      }

      return { title, date };
    });

    // Use meeting.title from the list if page extraction failed
    const finalTitle = metadata.title || meeting.title;
    console.log(`   📌 Meeting: "${finalTitle}"`);
    if (metadata.date) console.log(`   📅 Date: ${metadata.date}`);

    // Extract AI Summary
    const aiSummary = await this.extractAISummary();

    // Extract Transcript
    const transcript = await this.extractTranscript();

    return {
      title: finalTitle,
      date: metadata.date,
      aiSummary,
      transcript
    };
  }

  formatMeetingNote(meeting, data) {
    const now = new Date();
    const dateStr = this.parseDate(data.date) || now.toISOString().split('T')[0];

    let content = `---
title: "${data.title}"
date: ${dateStr}
type: meeting
source: teams
extracted: ${now.toISOString()}
${data.transcript?.participants?.length ? `participants:\n${data.transcript.participants.map(p => `  - "${p}"`).join('\n')}` : ''}
---

# ${data.title}

**Date:** ${data.date || dateStr}
**Extracted:** ${now.toISOString()}
`;

    if (data.transcript?.participants?.length) {
      content += `**Participants:** ${data.transcript.participants.join(', ')}\n`;
    }

    // AI Summary section
    if (data.aiSummary) {
      content += `\n## AI Summary\n\n`;

      if (data.aiSummary.meetingNotes?.length > 0) {
        content += `### Meeting Notes\n\n`;
        data.aiSummary.meetingNotes.forEach(note => {
          content += `- ${note}\n`;
        });
        content += '\n';
      }

      if (data.aiSummary.followUpTasks?.length > 0) {
        content += `### Follow-up Tasks\n\n`;
        data.aiSummary.followUpTasks.forEach(task => {
          content += `- [ ] ${task}\n`;
        });
        content += '\n';
      }

      if (data.aiSummary.rawText && data.aiSummary.meetingNotes?.length === 0) {
        content += data.aiSummary.rawText + '\n\n';
      }
    }

    // Transcript section
    if (data.transcript?.entries?.length > 0) {
      content += `## Full Transcript\n\n`;
      data.transcript.entries.forEach(entry => {
        const timestamp = entry.timestamp ? ` (${entry.timestamp})` : '';
        content += `**${entry.speaker}**${timestamp}: ${entry.text}\n\n`;
      });
    }

    content += `---
*Auto-generated by Teams Transcript Harvester*
`;

    return content;
  }

  parseDate(dateString) {
    if (!dateString) return null;

    try {
      // Try to extract date from strings like "Monday, February 2, 2026 3:00 PM - 3:45 PM"
      const dateMatch = dateString.match(/(\w+,\s+)?(\w+\s+\d{1,2},?\s+\d{4})/);
      if (dateMatch) {
        const date = new Date(dateMatch[2]);
        if (!isNaN(date.getTime())) {
          return date.toISOString().split('T')[0];
        }
      }

      // Try direct parsing
      const date = new Date(dateString);
      if (!isNaN(date.getTime())) {
        return date.toISOString().split('T')[0];
      }
    } catch {}

    return null;
  }

  async saveMeeting(meeting, data) {
    const meetingsDir = path.join(CONFIG.obsidianVault, CONFIG.meetingsFolder);
    await fs.ensureDir(meetingsDir);

    const safeTitle = data.title.replace(/[^a-zA-Z0-9\s]/g, '').replace(/\s+/g, '-').substring(0, 50);
    const dateStr = this.parseDate(data.date) || new Date().toISOString().split('T')[0];
    const filename = `${dateStr}-${safeTitle}.md`;
    const filepath = path.join(meetingsDir, filename);

    if (await fs.pathExists(filepath)) {
      console.log(`   📄 Already exists: ${filename}`);
      return;
    }

    const content = this.formatMeetingNote(meeting, data);

    if (CONFIG.dryRun) {
      console.log(`   🧪 DRY RUN - Would save: ${filename}`);
      console.log(`   Content preview:\n${content.substring(0, 500)}...\n`);
      return;
    }

    await fs.writeFile(filepath, content, 'utf8');
    console.log(`   💾 Saved: ${filename}`);
  }

  async run() {
    try {
      console.log('🦌 Teams Transcript Harvester Starting...');
      console.log(`📁 Obsidian Vault: ${CONFIG.obsidianVault}`);
      console.log(`🗂️  Meetings Folder: ${CONFIG.meetingsFolder}`);

      if (CONFIG.dryRun) {
        console.log('🧪 DRY RUN MODE - No files will be saved\n');
      }

      await this.launch();
      await this.navigateToTeams();
      await this.navigateToMeetingChats();

      const meetings = await this.getMeetingsList();
      let processed = 0;
      let skipped = 0;

      for (const meeting of meetings.slice(0, CONFIG.maxMeetings)) {
        if (this.state.processedMeetings.has(meeting.id)) {
          console.log(`⏭️  Skipping already processed: ${meeting.title}`);
          skipped++;
          continue;
        }

        const data = await this.extractMeetingData(meeting);

        if (data) {
          await this.saveMeeting(meeting, data);
          this.state.processedMeetings.add(meeting.id);
          processed++;
        }

        // Small delay between meetings
        await this.page.waitForTimeout(1000);
      }

      console.log(`\n✅ Harvest complete!`);
      console.log(`   Processed: ${processed}`);
      console.log(`   Skipped: ${skipped}`);

    } catch (error) {
      console.error('❌ Harvest failed:', error.message);
      throw error;
    } finally {
      if (this.context) {
        await this.context.close();
      }
      this.saveState();
    }
  }
}

if (require.main === module) {
  const harvester = new TeamsHarvester();
  harvester.run().catch(error => {
    console.error(error);
    process.exit(1);
  });
}

module.exports = TeamsHarvester;
