#!/usr/bin/env node

const fs = require('fs-extra');
const path = require('path');

console.log('🔍 Teams Transcript Harvester Validation');
console.log('========================================');

// Check Node.js version
const nodeVersion = process.version;
console.log(`📦 Node.js version: ${nodeVersion}`);

if (parseInt(nodeVersion.slice(1)) < 16) {
    console.log('⚠️  Node.js 16+ recommended for best compatibility');
}

// Check dependencies
console.log('\n📚 Checking dependencies...');
const requiredDeps = ['puppeteer', 'fs-extra', 'yaml'];

for (const dep of requiredDeps) {
    try {
        require.resolve(dep);
        console.log(`✅ ${dep} - installed`);
    } catch {
        console.log(`❌ ${dep} - missing (run: npm install)`);
    }
}

// Check configuration
console.log('\n⚙️  Checking configuration...');

if (fs.existsSync('./config.env')) {
    console.log('✅ config.env - found');
    
    const config = fs.readFileSync('./config.env', 'utf8');
    if (config.includes('OBSIDIAN_VAULT=')) {
        const vaultMatch = config.match(/OBSIDIAN_VAULT=(.+)/);
        if (vaultMatch) {
            const vaultPath = vaultMatch[1];
            console.log(`📁 Obsidian vault path: ${vaultPath}`);
            
            if (fs.existsSync(vaultPath)) {
                console.log('✅ Obsidian vault - accessible');
            } else {
                console.log('⚠️  Obsidian vault directory not found');
                console.log('   Run: mkdir -p ' + vaultPath);
            }
        }
    } else {
        console.log('⚠️  OBSIDIAN_VAULT not configured in config.env');
    }
} else {
    console.log('❌ config.env - missing');
    console.log('   Copy from config.env and edit the OBSIDIAN_VAULT path');
}

// Check harvester script
console.log('\n🤖 Checking harvester script...');

if (fs.existsSync('./harvester.js')) {
    console.log('✅ harvester.js - found');
    
    // Check if executable
    try {
        fs.accessSync('./harvester.js', fs.constants.X_OK);
        console.log('✅ harvester.js - executable');
    } catch {
        console.log('⚠️  harvester.js - not executable (run: chmod +x harvester.js)');
    }
} else {
    console.log('❌ harvester.js - missing');
}

// Check state file
if (fs.existsSync('./harvester-state.json')) {
    const state = JSON.parse(fs.readFileSync('./harvester-state.json', 'utf8'));
    console.log(`📊 State file - ${state.processedMeetings ? state.processedMeetings.length : 0} meetings processed`);
    if (state.lastRun) {
        console.log(`   Last run: ${state.lastRun}`);
    }
} else {
    console.log('📊 State file - none (will be created on first run)');
}

// Check cron job
console.log('\n⏰ Checking cron job...');

try {
    const { execSync } = require('child_process');
    const crontab = execSync('crontab -l 2>/dev/null || echo ""', { encoding: 'utf8' });
    
    if (crontab.includes('teams-harvester') || crontab.includes('harvester.js')) {
        console.log('✅ Cron job - installed');
        
        // Extract the cron line
        const cronLines = crontab.split('\n').filter(line => 
            line.includes('teams-harvester') || line.includes('harvester.js')
        );
        
        if (cronLines.length > 0) {
            console.log(`   Schedule: ${cronLines[0].split(' ').slice(0, 5).join(' ')}`);
        }
    } else {
        console.log('⚠️  Cron job - not installed');
        console.log('   Run: ./install-cron.sh');
    }
} catch (error) {
    console.log('❌ Cannot check cron jobs (crontab not available)');
}

// System requirements
console.log('\n🖥️  System requirements...');

// Check for Chrome/Chromium
const chromePaths = [
    '/usr/bin/chromium-browser',
    '/usr/bin/chromium',
    '/usr/bin/google-chrome',
    '/usr/bin/chrome',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
];

let chromeFound = false;
for (const chromePath of chromePaths) {
    if (fs.existsSync(chromePath)) {
        console.log(`✅ Chrome/Chromium - found at ${chromePath}`);
        chromeFound = true;
        break;
    }
}

if (!chromeFound) {
    console.log('⚠️  Chrome/Chromium - not found in standard locations');
    console.log('   Puppeteer will use bundled Chromium');
}

// Final recommendations
console.log('\n🎯 Recommendations:');

if (!fs.existsSync('./config.env')) {
    console.log('1. ⚠️  Create and configure config.env file');
}

if (!fs.existsSync('./harvester-state.json')) {
    console.log('2. 🧪 Run a test harvest: node harvester.js --dry-run');
}

const { execSync } = require('child_process');
try {
    const crontab = execSync('crontab -l 2>/dev/null || echo ""', { encoding: 'utf8' });
    if (!crontab.includes('teams-harvester')) {
        console.log('3. ⏰ Install cron job: ./install-cron.sh');
    }
} catch {}

console.log('\n✅ Validation complete!');
console.log('\n📖 Next steps:');
console.log('   • Test: node harvester.js --dry-run');
console.log('   • Run: node harvester.js');
console.log('   • Logs: tail -f harvest.log');
console.log('   • Help: cat README.md');