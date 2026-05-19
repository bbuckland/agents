# Teams Transcript Harvester - Known Issues

## Launchd Setup Issues

### 1. Wrong paths in plist
**File:** `com.quant-superpowers.teams-harvester.plist`

Current (incorrect):
```
/Users/bradley.buckland/Documents/personal/code/quant-superpowers/teams-transcript-harvester
```

Should be:
```
/Users/bradley.buckland/Documents/personal/code/agents/teams-transcript-harvester
```

### 2. Wrong node path
**File:** `com.quant-superpowers.teams-harvester.plist`

Current (incorrect):
```
/usr/local/bin/node
```

Actual node location (via mise):
```
/Users/bradley.buckland/.local/share/mise/installs/node/24.12.0/bin/node
```

**Fix options:**
- Use the mise path directly (may break on node version updates)
- Use `/usr/bin/env node` (requires PATH to include mise)
- Symlink node to `/usr/local/bin/node`

### 3. Obsidian vault directory doesn't exist
**Path:** `/Users/bradley.buckland/Documents/ObsidianVaults/TeamsTranscripts`

Run: `mkdir -p /Users/bradley.buckland/Documents/ObsidianVaults/TeamsTranscripts`

---

## Code Issues

### 4. validate.js is outdated
Checks for `puppeteer` and `yaml` but project uses `playwright` and doesn't need `yaml`.

### 5. Meeting discovery finds 0 meetings
The DOM selectors in `extractMeetings()` may not match the current Teams UI:
- Recording page URL may have changed
- Element selectors may be outdated
- Need to inspect actual Teams DOM structure

---

## Status

- [x] Core harvester works (browser launch, login, navigation)
- [ ] Fix meeting discovery selectors
- [ ] Fix launchd plist paths
- [ ] Fix node path for launchd
- [ ] Create Obsidian vault directory
- [ ] Update validate.js for playwright
