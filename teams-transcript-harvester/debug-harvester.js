#!/usr/bin/env node

const { chromium } = require('playwright');
const fs = require('fs-extra');
const path = require('path');

const CONFIG = {
  userDataDir: path.join(__dirname, '.browser-profile'),
};

async function debug() {
  console.log('🔍 DEBUG: Teams Harvester Investigation');
  console.log('========================================\n');

  const context = await chromium.launchPersistentContext(CONFIG.userDataDir, {
    headless: false,
    viewport: { width: 1920, height: 1080 },
    channel: 'chrome',
  });

  const page = context.pages()[0] || await context.newPage();

  try {
    // Step 1: Navigate to Teams (use domcontentloaded, not networkidle)
    console.log('📍 Step 1: Navigating to Teams...');
    await page.goto('https://teams.microsoft.com', {
      waitUntil: 'domcontentloaded',
      timeout: 60000
    });

    // Give it time to render
    await page.waitForTimeout(5000);
    console.log(`   Current URL: ${page.url()}`);

    // Check login status
    const url = page.url();
    if (url.includes('login') || url.includes('microsoftonline')) {
      console.log('⏳ Please log in to Teams...');
      await page.waitForURL(
        u => u.href.includes('teams.microsoft.com') && !u.href.includes('login'),
        { timeout: 300000 }
      );
      await page.waitForTimeout(5000);
    }
    console.log('✅ Logged in\n');

    // Step 2: Navigate to calendar (where recordings typically are)
    console.log('📍 Step 2: Looking for recordings...');
    console.log('   Please navigate to where your meeting recordings are.');
    console.log('   (Calendar → past meeting → Recap tab, or OneDrive recordings)');
    console.log('   Press Enter in this terminal when you\'re on the recordings page...\n');

    // Wait for user input
    await new Promise(resolve => {
      process.stdin.once('data', resolve);
    });

    // Step 3: Analyze the page
    console.log('📍 Step 3: Analyzing current page...\n');
    console.log(`   URL: ${page.url()}`);

    // Take screenshot
    const screenshotPath = path.join(__dirname, 'debug-screenshot.png');
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`   Screenshot saved: ${screenshotPath}`);

    // Analyze page structure
    const pageAnalysis = await page.evaluate(() => {
      const analysis = {
        title: document.title,
        url: window.location.href,
        dataTids: [],
        clickableElements: [],
        textContent: [],
      };

      // Find all data-tid attributes
      document.querySelectorAll('[data-tid]').forEach(el => {
        const tid = el.getAttribute('data-tid');
        if (tid && !analysis.dataTids.includes(tid)) {
          analysis.dataTids.push(tid);
        }
      });

      // Find clickable elements with text
      document.querySelectorAll('button, a, [role="button"], [role="listitem"], [role="row"]').forEach(el => {
        const text = el.innerText?.trim().substring(0, 100);
        const dataTid = el.getAttribute('data-tid');
        const ariaLabel = el.getAttribute('aria-label');
        if (text || dataTid || ariaLabel) {
          analysis.clickableElements.push({
            tag: el.tagName,
            text: text || '',
            dataTid: dataTid || '',
            ariaLabel: ariaLabel || '',
            className: (el.className || '').substring(0, 50),
          });
        }
      });

      // Find any transcript-related text
      const keywords = ['transcript', 'recording', 'recap', 'video', 'meeting'];
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) {
        const text = walker.currentNode.textContent?.trim().toLowerCase();
        if (text && keywords.some(k => text.includes(k))) {
          const parent = walker.currentNode.parentElement;
          analysis.textContent.push({
            text: walker.currentNode.textContent.trim().substring(0, 100),
            parentTag: parent?.tagName,
            parentTid: parent?.getAttribute('data-tid'),
          });
        }
      }

      return analysis;
    });

    // Save analysis
    const analysisPath = path.join(__dirname, 'debug-analysis.json');
    await fs.writeJson(analysisPath, pageAnalysis, { spaces: 2 });
    console.log(`   Analysis saved: ${analysisPath}`);

    console.log(`\n   Found ${pageAnalysis.dataTids.length} data-tid attributes`);
    console.log(`   Found ${pageAnalysis.clickableElements.length} clickable elements`);
    console.log(`   Found ${pageAnalysis.textContent.length} transcript-related text nodes`);

    // Show relevant elements
    if (pageAnalysis.textContent.length > 0) {
      console.log('\n   Transcript-related text found:');
      pageAnalysis.textContent.slice(0, 15).forEach(t => {
        console.log(`     - "${t.text}" (parent: ${t.parentTag}, tid: ${t.parentTid})`);
      });
    }

    console.log('\n📍 Step 4: Browser stays open. Press Ctrl+C when done.\n');
    await new Promise(() => {});

  } catch (error) {
    console.error('❌ Error:', error.message);
    console.log('\n   Browser stays open for manual inspection. Press Ctrl+C when done.');
    await new Promise(() => {});
  }
}

debug().catch(console.error);
