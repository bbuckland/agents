#!/usr/bin/env node

const { chromium } = require('playwright');
const fs = require('fs-extra');
const path = require('path');

async function openTeams() {
  console.log('🚀 Opening Teams browser...\n');

  const context = await chromium.launchPersistentContext(
    path.join(__dirname, '.browser-profile'),
    {
      headless: false,
      viewport: { width: 1920, height: 1080 },
      channel: 'chrome',
    }
  );

  const page = context.pages()[0] || await context.newPage();

  console.log('📍 Navigating to Teams...');
  await page.goto('https://teams.microsoft.com', {
    waitUntil: 'domcontentloaded',
    timeout: 60000
  });

  await page.waitForTimeout(3000);
  console.log(`✅ At: ${page.url()}`);

  console.log('\n📌 Browser is open. Navigate to:');
  console.log('   Chats → Filter "Meeting Chats" → Click meeting → Recap tab');
  console.log('\n⏳ Keeping browser open for 5 minutes...');
  console.log('   When ready, I\'ll capture the page structure.\n');

  // Keep open for 5 minutes
  await page.waitForTimeout(300000);

  await context.close();
}

openTeams().catch(err => {
  console.error('❌ Error:', err.message);
});
