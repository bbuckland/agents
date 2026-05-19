#!/usr/bin/env node

const { chromium } = require('playwright');
const fs = require('fs-extra');
const path = require('path');

async function capture() {
  console.log('📸 Capturing Teams page structure...\n');

  const context = await chromium.launchPersistentContext(
    path.join(__dirname, '.browser-profile'),
    {
      headless: false,
      viewport: { width: 1920, height: 1080 },
      channel: 'chrome',
    }
  );

  const page = context.pages()[0] || await context.newPage();

  // Give user time to be on the right page
  console.log('⏳ Waiting 5 seconds (make sure you\'re on the Recap/AI Summary page)...');
  await page.waitForTimeout(5000);

  console.log(`\n📍 Current URL: ${page.url()}`);

  // Take screenshot
  const screenshotPath = path.join(__dirname, 'debug-screenshot.png');
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log(`📸 Screenshot saved: ${screenshotPath}`);

  // Analyze page structure
  const analysis = await page.evaluate(() => {
    const result = {
      url: window.location.href,
      title: document.title,

      // All data-tid attributes (Teams uses these extensively)
      dataTids: [],

      // Elements that might be transcript content
      transcriptElements: [],

      // Elements that might be AI summary
      summaryElements: [],

      // All text content in main area
      mainTextContent: [],

      // Clickable elements
      buttons: [],
    };

    // Collect all data-tid values
    document.querySelectorAll('[data-tid]').forEach(el => {
      const tid = el.getAttribute('data-tid');
      if (tid && !result.dataTids.includes(tid)) {
        result.dataTids.push(tid);
      }
    });

    // Look for transcript/summary related elements
    const keywords = ['transcript', 'summary', 'recap', 'ai', 'speaker', 'participant'];

    document.querySelectorAll('*').forEach(el => {
      const text = el.innerText?.trim() || '';
      const className = (el.className || '').toString().toLowerCase();
      const dataTid = el.getAttribute('data-tid') || '';
      const ariaLabel = el.getAttribute('aria-label') || '';

      // Check if element relates to transcript/summary
      const isRelevant = keywords.some(k =>
        className.includes(k) ||
        dataTid.toLowerCase().includes(k) ||
        ariaLabel.toLowerCase().includes(k)
      );

      if (isRelevant && text.length > 0 && text.length < 500) {
        result.transcriptElements.push({
          tag: el.tagName,
          className: className.substring(0, 100),
          dataTid,
          ariaLabel,
          text: text.substring(0, 200),
        });
      }
    });

    // Look for any substantial text blocks (potential transcript content)
    document.querySelectorAll('div, p, span').forEach(el => {
      const text = el.innerText?.trim() || '';
      // Look for speaker patterns like "Name:" or timestamps
      if (text.length > 50 && text.length < 2000) {
        const hasTimestamp = /\d{1,2}:\d{2}/.test(text);
        const hasSpeaker = /^[A-Z][a-z]+ [A-Z][a-z]+:/.test(text) || text.includes('said');

        if (hasTimestamp || hasSpeaker || text.toLowerCase().includes('summary')) {
          result.mainTextContent.push({
            tag: el.tagName,
            className: (el.className || '').toString().substring(0, 50),
            dataTid: el.getAttribute('data-tid'),
            textPreview: text.substring(0, 300),
            fullLength: text.length,
          });
        }
      }
    });

    // Find buttons/tabs (for navigation)
    document.querySelectorAll('button, [role="tab"], [role="button"]').forEach(el => {
      const text = el.innerText?.trim() || el.getAttribute('aria-label') || '';
      if (text) {
        result.buttons.push({
          tag: el.tagName,
          text: text.substring(0, 50),
          dataTid: el.getAttribute('data-tid'),
          ariaSelected: el.getAttribute('aria-selected'),
        });
      }
    });

    return result;
  });

  // Save full analysis
  const analysisPath = path.join(__dirname, 'debug-analysis.json');
  await fs.writeJson(analysisPath, analysis, { spaces: 2 });
  console.log(`📄 Full analysis saved: ${analysisPath}`);

  // Print summary
  console.log(`\n📊 Analysis Summary:`);
  console.log(`   Data-tid attributes: ${analysis.dataTids.length}`);
  console.log(`   Transcript-related elements: ${analysis.transcriptElements.length}`);
  console.log(`   Text content blocks: ${analysis.mainTextContent.length}`);
  console.log(`   Buttons/tabs: ${analysis.buttons.length}`);

  if (analysis.transcriptElements.length > 0) {
    console.log(`\n🎯 Transcript-related elements:`);
    analysis.transcriptElements.slice(0, 10).forEach(el => {
      console.log(`   <${el.tag}> tid="${el.dataTid}" aria="${el.ariaLabel}"`);
      console.log(`      text: "${el.text.substring(0, 80)}..."`);
    });
  }

  if (analysis.mainTextContent.length > 0) {
    console.log(`\n📝 Text content blocks:`);
    analysis.mainTextContent.slice(0, 5).forEach(el => {
      console.log(`   <${el.tag}> tid="${el.dataTid}" (${el.fullLength} chars)`);
      console.log(`      "${el.textPreview.substring(0, 100)}..."`);
    });
  }

  if (analysis.buttons.length > 0) {
    console.log(`\n🔘 Buttons/tabs found:`);
    analysis.buttons.slice(0, 15).forEach(b => {
      console.log(`   "${b.text}" tid="${b.dataTid}" selected=${b.ariaSelected}`);
    });
  }

  console.log(`\n✅ Done! Check debug-screenshot.png and debug-analysis.json`);

  await context.close();
}

capture().catch(err => {
  console.error('❌ Error:', err.message);
  process.exit(1);
});
