# Enhanced Plaid Integration Guide

## 🎯 Overview

The enhanced Plaid integration provides complete visibility into your connected accounts with:

- **Clear account identification** - See institution name, account name, type, and masked account numbers
- **Automatic categorization** - Smart detection of business vs personal accounts
- **Balance tracking** - Real-time balance updates for all accounts
- **Institution grouping** - View accounts organized by bank/institution
- **Visual dashboard** - Beautiful account management page in the web interface

## 🚀 Getting Started

### 1. Configure Plaid Credentials

```bash
cp .env.sample .env
# Edit .env and add:
PLAID_CLIENT_ID=your_client_id_here
PLAID_SECRET=your_secret_here
PLAID_ENV=Sandbox  # or Development/Production
```

### 2. Launch the Setup Wizard

```bash
./start.sh
# Choose Option 3: Setup Plaid Accounts
```

The wizard provides these options:

1. **View Current Accounts** - See all connected accounts with full details
2. **Connect New Account** - Add accounts through Plaid Link
3. **Verify Account Mapping** - Ensure accounts are correctly categorized
4. **Test with Sandbox** - Create test accounts for development
5. **Sync Transactions** - Pull latest transactions
6. **Remove Account** - Disconnect accounts

## 📊 Account Information Displayed

### For Each Account You'll See:

```
Chase - Premium Business Checking
├── Type: Checking
├── Mask: ***1234
├── Balance: $45,678.90
├── Available: $44,178.90
├── Business: ✅
└── Connected: 2024-01-15
```

### Summary View Shows:

- **Total Assets**: Sum of all checking, savings, and investment accounts
- **Total Liabilities**: Sum of all credit card balances
- **Net Worth**: Assets minus liabilities
- **By Institution**: Grouped view of all accounts per bank
- **By Type**: Breakdown by checking, savings, credit, investment

## 🏦 Required Accounts (11 Total)

The system tracks your progress toward connecting all required accounts:

| Type              | Required | Purpose                        |
| ----------------- | -------- | ------------------------------ |
| Business Checking | 2        | Operating and payroll accounts |
| Business Credit   | 1        | Business expenses              |
| Personal Checking | 1        | Personal expenses              |
| Personal Credit   | 6-7      | Various personal cards         |
| Investment        | 1        | Investment tracking            |

## 🔄 Account Categorization

The system automatically detects business accounts by looking for:

- Keywords: "business", "corp", "company", "llc", "inc"
- Account subtypes: "commercial", "merchant"
- Institution patterns

You can always manually override categorization through:

1. The setup wizard (Option 3)
2. The dashboard Accounts page
3. Direct editing in `config/plaid_accounts.json`

## 💻 Dashboard Integration

### Accounts Page Features:

1. **Overview Tab**
   - Account summary metrics
   - Asset allocation pie chart
   - Institution breakdown bar chart
   - Full account listing with balances

2. **Business Tab**
   - All business accounts grouped by type
   - Total business assets calculation
   - Quick balance views

3. **Personal Tab**
   - Personal accounts by category
   - Credit card tracking
   - Investment account monitoring

4. **Settings Tab**
   - Toggle business/personal categorization
   - Connection status tracking
   - Add new account button

## 🧪 Sandbox Testing

For development/testing without real accounts:

```bash
# Set environment to sandbox
PLAID_ENV=Sandbox

# Run setup wizard
./start.sh → Option 3 → Option 4 (Test with Sandbox)
```

This creates test accounts with sample data from major banks.

## 📁 Data Storage

Account information is stored in:

- `config/plaid_accounts.json` - Account details and tokens
- `data/financial.db` - SQLite database for transactions

Format:

```json
{
  "accounts": {
    "account_id": {
      "institution_name": "Chase",
      "account_name": "Business Checking",
      "type": "depository",
      "mask": "1234",
      "current_balance": 45678.9,
      "is_business": true
    }
  }
}
```

## 🔒 Security

- **Access tokens** are stored locally, never transmitted
- **No cloud storage** - all data remains on your machine
- **Encrypted storage** available via ENCRYPTION_KEY in .env
- **Read-only access** by default (transactions only)

## 🛠️ Troubleshooting

### "Can't see account details"

- Ensure you're using the enhanced setup: `scripts/plaid_setup_enhanced.py`
- Check that `config/plaid_accounts.json` exists

### "Wrong categorization"

- Use wizard Option 3 to verify mappings
- Or edit directly in the dashboard Settings

### "Missing balances"

- Refresh balances from dashboard
- Check Plaid connection status

### "Sandbox not working"

- Verify PLAID_ENV=Sandbox in .env
- Ensure you have valid Plaid credentials

## 📝 API Methods

The `PlaidManager` class provides:

```python
from src.api.plaid_manager import PlaidManager

manager = PlaidManager()

# List all accounts with details
accounts = manager.list_connected_accounts()

# Get account summary
summary = manager.get_account_summary()

# Categorize accounts
categorized = manager.categorize_accounts()

# Sync transactions
transactions = manager.sync_all_transactions()

# Get specific account
account = manager.get_account_by_id("acc_123")
```

## 🎉 Benefits Over Basic Integration

| Old Integration             | Enhanced Integration                  |
| --------------------------- | ------------------------------------- |
| No visibility into accounts | Full account details displayed        |
| Manual categorization       | Auto-detection of business accounts   |
| No balance tracking         | Real-time balance updates             |
| Confusing setup             | Interactive wizard with clear options |
| No grouping                 | Organized by institution and type     |
| Text-only interface         | Rich CLI + web dashboard              |

## Next Steps

1. Connect all 11 accounts via the wizard
2. Verify categorization is correct
3. Sync initial transactions
4. Start using the dashboard for daily management

Your accounts are now fully visible and manageable!
