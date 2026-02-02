# Oracle Expenses Form Navigation

This document describes the Oracle Expenses form structure for Playwright automation.

## Prerequisites

- Playwright server running locally: `npx playwright run-server --port 3000 --host 0.0.0.0`
- Connection via Tailscale at `ws://${EXPENSE_PLAYWRIGHT_HOST}:3000`

## Authentication Flow

1. Navigate to Oracle Expenses URL
2. Redirect to Okta SSO
3. User approves via Passkey (device-bound credential)
4. Session cookie persists for subsequent requests

**When auth is needed:** Prompt user with "Please approve Okta on your device"

## Form Structure

### Create New Expense Report

1. Navigate to: `[Oracle Expenses URL]/expenses/new`
2. Fill report header:
   - Report Title
   - Business Purpose
   - Date Range

### Add Expense Line Item

For each row in `expenses.csv`:

| CSV Field | Oracle Form Field | Notes |
|-----------|-------------------|-------|
| `date` | Expense Date | Format: MM/DD/YYYY |
| `vendor` | Merchant | Free text |
| `amount` | Amount | Decimal, no currency symbol |
| `poet` | Project/Task | May require lookup |
| `description` | Description | Free text |
| `receipt_file` | Attachment | Upload if present |

### POET Code Entry

POET format: `PROJECT.ORG.EXPENDITURE_TYPE.TASK`

Oracle may have separate fields:
- Project Number
- Organization
- Expenditure Type (dropdown)
- Task Number

Parse the POET string and fill each field.

### Submit Report

1. Review all line items
2. Click Submit
3. Confirm submission dialog
4. Capture confirmation number

## Selectors (TODO)

These selectors need to be captured from the actual Oracle interface:

```javascript
// Placeholder selectors - update after inspecting Oracle UI
const SELECTORS = {
  reportTitle: '#report-title-input',
  addExpense: '#add-expense-button',
  expenseDate: '#expense-date',
  merchant: '#merchant-name',
  amount: '#expense-amount',
  project: '#project-code',
  submit: '#submit-report',
  confirm: '#confirm-submit'
};
```

## Error Handling

| Scenario | Action |
|----------|--------|
| Okta timeout | Prompt user to re-authenticate |
| Validation error | Report which field failed |
| Session expired | Re-initiate auth flow |
| Network error | Retry with backoff |
