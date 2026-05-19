#!/usr/bin/env node

const { chromium } = require('playwright');
const fs = require('fs-extra');
const path = require('path');

async function debugRecap() {
  console.log('🔍 Debug: Analyzing Recap page structure\n');

  const context = await chromium.launchPersistentContext(
    path.join(__dirname, '.browser-profile'),
    {
      headless: false,
      viewport: { width: 1920, height: 1080 },
      channel: 'chrome',
    }
  );

  const page = context.pages()[0] || await context.newPage();

  // Navigate to Teams
  console.log('📍 Navigating to Teams...');
  await page.goto('https://teams.microsoft.com', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(5000);
  console.log(`✅ At: ${page.url()}`);

  // Click Chat
  console.log('💬 Going to Chat...');
  try {
    await page.click('[aria-label="Chat"]', { timeout: 5000 });
    await page.waitForTimeout(2000);
  } catch (e) {
    console.log('   Chat may already be selected');
  }

  // Click Meeting chats filter
  console.log('🔍 Filtering to Meeting chats...');
  try {
    await page.click('text="Meeting chats"', { timeout: 5000 });
    await page.waitForTimeout(2000);
  } catch (e) {
    console.log('   Filter may already be applied');
  }

  // Click first meeting with "Recording is ready"
  console.log('📝 Looking for a meeting with recording...');
  const meetingWithRecording = page.locator('[role="treeitem"]:has-text("Recording")').first();
  if (await meetingWithRecording.isVisible({ timeout: 5000 })) {
    const meetingText = await meetingWithRecording.innerText();
    console.log(`   Found: ${meetingText.split('\n')[0]}`);
    await meetingWithRecording.click();
    await page.waitForTimeout(3000);
  } else {
    // Just click first treeitem
    console.log('   No meeting with recording visible, clicking first meeting...');
    await page.locator('[role="treeitem"]').first().click();
    await page.waitForTimeout(3000);
  }

  // Click Recap tab
  console.log('📋 Clicking Recap tab...');
  try {
    await page.click('text="Recap"', { timeout: 5000 });
    await page.waitForTimeout(3000);
  } catch (e) {
    console.log('   Recap tab not found, may already be there');
  }

  // Click AI summary tab
  console.log('🤖 Clicking AI summary tab...');
  try {
    await page.click('text="AI summary"', { timeout: 5000 });
    await page.waitForTimeout(2000);
  } catch (e) {
    console.log('   AI summary tab not found');
  }

  // Take screenshot
  const screenshotPath = path.join(__dirname, 'debug-recap-screenshot.png');
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log(`📸 Screenshot saved: ${screenshotPath}`);

  // Analyze the page structure
  console.log('\n🔬 Analyzing page structure...\n');

  const analysis = await page.evaluate(() => {
    const result = {
      pageTitle: document.title,
      url: window.location.href,

      // Find the meeting title - look in header area
      possibleTitles: [],

      // Find date/time info
      possibleDates: [],

      // Find AI summary content
      aiSummaryContent: [],

      // Find tabs
      tabs: [],

      // All text content in main area for analysis
      mainAreaText: '',

      // HTML of key areas
      recapAreaHtml: '',
    };

    // Look for meeting title in various places
    document.querySelectorAll('h1, h2, h3, [class*="title"], [data-tid*="title"]').forEach(el => {
      const text = el.innerText?.trim();
      if (text && text.length > 3 && text.length < 200) {
        result.possibleTitles.push({
          tag: el.tagName,
          class: el.className?.toString().substring(0, 50),
          dataTid: el.getAttribute('data-tid'),
          text: text.substring(0, 100)
        });
      }
    });

    // Look for date/time
    document.querySelectorAll('time, [class*="date"], [class*="time"], [data-tid*="date"]').forEach(el => {
      const text = el.innerText?.trim() || el.getAttribute('datetime');
      if (text) {
        result.possibleDates.push({
          tag: el.tagName,
          class: el.className?.toString().substring(0, 50),
          text: text.substring(0, 100)
        });
      }
    });

    // Find tabs
    document.querySelectorAll('[role="tab"], button').forEach(el => {
      const text = el.innerText?.trim();
      const ariaLabel = el.getAttribute('aria-label');
      if ((text || ariaLabel) && (text?.length < 30 || ariaLabel?.length < 30)) {
        result.tabs.push({
          text: text || ariaLabel,
          selected: el.getAttribute('aria-selected'),
          dataTid: el.getAttribute('data-tid')
        });
      }
    });

    // Get main content area text
    const mainArea = document.querySelector('[role="main"], [class*="chat-pane"], [data-tid*="message-pane"]');
    if (mainArea) {
      result.mainAreaText = mainArea.innerText?.substring(0, 3000);
    }

    // Look for bullet points (likely AI summary content)
    document.querySelectorAll('li, [role="listitem"]').forEach(el => {
      const text = el.innerText?.trim();
      if (text && text.length > 30 && text.length < 1000) {
        // Skip if it's a chat list item
        if (!el.closest('[data-tid="chat-list"]') && !el.closest('[role="tree"]')) {
          result.aiSummaryContent.push(text.substring(0, 200));
        }
      }
    });

    // Get HTML of the recap/content area
    const recapArea = document.querySelector('[class*="recap"], [class*="summary"], [data-tid*="meeting"]');
    if (recapArea) {
      result.recapAreaHtml = recapArea.outerHTML?.substring(0, 2000);
    }

    return result;
  });

  // Save full analysis
  const analysisPath = path.join(__dirname, 'debug-recap-analysis.json');
  await fs.writeJson(analysisPath, analysis, { spaces: 2 });
  console.log(`📄 Analysis saved: ${analysisPath}`);

  // Print summary
  console.log('=== POSSIBLE TITLES ===');
  analysis.possibleTitles.slice(0, 10).forEach(t => {
    console.log(`  <${t.tag}> class="${t.class}" tid="${t.dataTid}"`);
    console.log(`    "${t.text}"`);
  });

  console.log('\n=== POSSIBLE DATES ===');
  analysis.possibleDates.slice(0, 5).forEach(d => {
    console.log(`  <${d.tag}> "${d.text}"`);
  });

  console.log('\n=== TABS FOUND ===');
  analysis.tabs.filter(t => t.text).slice(0, 15).forEach(t => {
    console.log(`  "${t.text}" selected=${t.selected} tid="${t.dataTid}"`);
  });

  console.log('\n=== AI SUMMARY CONTENT (bullets) ===');
  analysis.aiSummaryContent.slice(0, 5).forEach(c => {
    console.log(`  • ${c.substring(0, 100)}...`);
  });

  console.log('\n=== MAIN AREA TEXT (first 500 chars) ===');
  console.log(analysis.mainAreaText?.substring(0, 500));

  console.log('\n✅ Done! Check debug-recap-screenshot.png and debug-recap-analysis.json');
  console.log('\n⏳ Browser stays open for manual inspection. Press Ctrl+C when done.');

  // Keep browser open
  await new Promise(() => {});
}

debugRecap().catch(err => {
  console.error('❌ Error:', err.message);
});
