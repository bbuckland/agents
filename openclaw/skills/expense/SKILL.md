---
name: expense
description: Oracle Expenses report management and submission
---

# Expense Report Management

You manage expense reports for Oracle Expenses.

## Report Lifecycle

### Starting a Report

When user says "start new report for <name>":
1. Create directory: `reports/<date>-<slugified-name>/`
2. Create `expenses.csv` with headers: `id,date,vendor,amount,poet,description,receipt_file,needs_receipt`
3. Create `report.json` with metadata
4. Create `receipts/` subdirectory
5. Confirm: "Started report '<name>'. Ready to add expenses."

### Adding Expenses

**From text** (e.g., "Lunch at PF Changs $26.94"):
1. Parse vendor and amount
2. Determine if receipt needed (≥$75)
3. Ask for POET code (or use report default)
4. Add row to CSV
5. Confirm with running total

**From image/receipt**:
1. Extract vendor, amount, date via vision
2. Save image to `receipts/<id>-<vendor-slug>.<ext>`
3. Ask for POET code
4. Add row to CSV with receipt_file reference
5. Confirm with running total

### POET Codes

Format: `PROJECT.ORG.EXPENDITURE_TYPE.TASK`

Reference file: `reference/poet-codes.csv`

If user provides partial POET, try to match from reference file.

User can set default POET for a report: "Use POET XYZ for this report"

### Viewing Report

When user asks to see the report:
1. Read current `expenses.csv`
2. Display as formatted table
3. Show totals by POET code
4. Show overall total

### Submitting Report

When user says "submit it":
1. Confirm report summary
2. Connect to Playwright server at `ws://<tailscale-hostname>:3000`
3. Navigate to Oracle Expenses
4. If Okta auth needed, prompt: "Please approve Okta on your device"
5. Fill form with each expense
6. Confirm submission

## Playwright Connection

The browser runs on user's local machine via Playwright Connect.

**Connection URL:** `ws://<configured-tailscale-host>:3000`

**User must run locally:**
```bash
npx playwright run-server --port 3000 --host 0.0.0.0
```

## CSV Format

```csv
id,date,vendor,amount,poet,description,receipt_file,needs_receipt
001,2025-01-15,Delta Airlines,487.20,PROJ-123.FIN.TRAVEL.T1,Flight to NYC,001-delta.pdf,true
002,2025-01-15,Uber,24.50,PROJ-123.FIN.TRAVEL.T1,Airport to hotel,,false
```
