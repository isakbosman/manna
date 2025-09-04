# Weekly Personal Finance Bookkeeping Workflow

## Overview
A streamlined 30-minute weekly process for personal finance management, leveraging ML-assisted categorization and automated reconciliation.

## 1. Step-by-Step Weekly Process (30 minutes total)

### Phase 1: Data Import & Initial Processing (5 minutes)
1. **Automated Transaction Pull**
   - Run Plaid API sync for all connected accounts
   - Import transactions from past 7 days + 3-day buffer for late-posting items
   - Store raw data in `/data/transactions/YYYY-MM-DD_weekly_import.json`

2. **Initial ML Categorization**
   - Run ML model on new transactions
   - Flag low-confidence predictions (<80% confidence) for manual review
   - Auto-categorize high-confidence transactions (≥80% confidence)

### Phase 2: Manual Review & Categorization (15 minutes)
3. **Review Flagged Transactions**
   - Process low-confidence ML predictions
   - Categorize new merchants not in training data
   - Verify large transactions (>$500) regardless of confidence level
   - Handle split transactions requiring multiple categories

4. **Pattern Recognition Review**
   - Check for duplicate transactions across accounts
   - Identify transfers between personal accounts
   - Flag unusual spending patterns or amounts

### Phase 3: Reconciliation & Quality Control (7 minutes)
5. **Account Reconciliation**
   - Compare transaction totals against bank statements
   - Verify beginning/ending balances match previous week
   - Reconcile credit card payments to checking account debits

6. **Anomaly Detection**
   - Review flagged unusual transactions
   - Verify large or uncommon purchases
   - Check for potential fraud indicators

### Phase 4: Reporting & Feedback (3 minutes)
7. **Weekly Summary Generation**
   - Generate weekly spending summary by category
   - Update running monthly totals
   - Export categorized transactions for ML model training

8. **Model Feedback Loop**
   - Submit manual categorizations to improve ML model
   - Update merchant categorization rules
   - Review and approve new auto-categorization patterns

## 2. Personal Finance Categorization Best Practices

### Core Principles
- **Consistency**: Always use the same category for similar transactions
- **Granularity**: Balance detail with simplicity (avoid over-categorizing)
- **Tax Alignment**: Structure categories to align with tax reporting needs
- **Future Planning**: Categories should support budgeting and financial planning

### Merchant Matching Rules
- Use fuzzy matching for merchant names (e.g., "AMZN*" matches all Amazon variants)
- Consider location context (same merchant name, different locations may be different categories)
- Account for seasonal variations (grocery stores vs. holiday shopping)

## 3. Standard Personal Finance Categories

### Primary Categories

#### **Housing & Utilities** (30-40% of income)
- Rent/Mortgage Payment
- Property Taxes
- Homeowners/Renters Insurance
- Electricity
- Gas/Heating
- Water/Sewer
- Trash/Recycling
- Internet/Cable
- Phone/Mobile
- Home Maintenance & Repairs
- HOA Fees

#### **Transportation** (15-20% of income)
- Car Payment
- Auto Insurance
- Gasoline
- Car Maintenance & Repairs
- Registration & Licensing
- Parking
- Tolls
- Public Transportation
- Rideshare/Taxi
- Car Rental

#### **Food & Dining** (10-15% of income)
- Groceries
- Restaurants
- Fast Food
- Coffee Shops
- Alcohol
- Work Lunches

#### **Healthcare** (5-10% of income)
- Health Insurance Premiums
- Doctor Visits
- Prescription Medications
- Dental Care
- Vision Care
- Medical Supplies
- Health & Wellness

#### **Personal Care** (2-5% of income)
- Haircuts/Salon
- Personal Care Products
- Clothing
- Dry Cleaning/Laundry
- Gym/Fitness

#### **Entertainment & Recreation** (5-10% of income)
- Streaming Services
- Movies/Theater
- Concerts/Events
- Hobbies
- Sports/Recreation
- Books/Magazines
- Gaming

#### **Financial** (10-20% of income)
- Savings Transfers
- Investment Contributions
- Retirement Contributions
- Emergency Fund
- Debt Payments
- Bank Fees
- Interest Payments
- Financial Services

#### **Shopping & Miscellaneous** (5-10% of income)
- General Merchandise
- Online Shopping
- Gifts
- Charity/Donations
- Pet Care
- Education/Training
- Professional Services
- Government/Taxes

### Subcategory Examples
```
Food & Dining
├── Groceries
│   ├── Regular Groceries
│   ├── Bulk/Warehouse Stores
│   └── Specialty Foods
├── Dining Out
│   ├── Restaurants (Sit-down)
│   ├── Fast Food
│   ├── Coffee/Cafes
│   └── Bars/Alcohol
└── Work-Related Meals
```

## 4. Split Transaction Handling Rules

### When to Split
- Mixed purchases at single merchant (groceries + pharmacy at Target)
- Business meals with personal items
- Shared expenses (splitting dinner with friends)
- Bulk purchases for multiple purposes

### Split Transaction Process
1. **Identify Split Candidates**
   - Transactions >$100 at multi-category merchants
   - Receipt-based verification when possible
   - Recurring mixed purchases

2. **Allocation Methods**
   - **Percentage-based**: 70% groceries, 30% household items
   - **Fixed amounts**: $50 business meal, $15 personal
   - **Receipt-based**: Exact amounts when receipts available

3. **Documentation Requirements**
   - Note split rationale in transaction memo
   - Maintain receipts for business-related splits
   - Track split patterns for automation

## 5. Weekly Reconciliation Checklist

### Account Balance Verification
- [ ] Check ending balance matches bank statement
- [ ] Verify beginning balance equals last week's ending balance
- [ ] Confirm no missing transactions in date range
- [ ] Cross-reference pending transactions

### Transfer Identification
- [ ] Match transfers between checking/savings accounts
- [ ] Verify credit card payments from checking account
- [ ] Confirm loan payments and automatic transfers
- [ ] Check investment account transfers

### Duplicate Detection
- [ ] Compare similar amounts across accounts on same dates
- [ ] Review merchant refunds and corresponding charges
- [ ] Identify returned purchases and original transactions
- [ ] Check for double charges from merchants

### Data Quality Checks
- [ ] Verify transaction dates fall within expected range
- [ ] Confirm no transactions with $0.00 amounts
- [ ] Check for missing merchant names or descriptions
- [ ] Validate category assignments make sense

## 6. Red Flags & Fraud Detection

### Immediate Action Required
- **Unrecognized transactions** of any amount
- **Large purchases** (>$500) not initiated by you
- **Multiple small transactions** from same unknown merchant
- **Foreign transactions** when not traveling
- **ATM withdrawals** from unfamiliar locations

### Pattern Anomalies
- **Spending spikes** >3x normal category amounts
- **New merchants** in sensitive categories (financial, healthcare)
- **Unusual timing** (transactions outside normal hours)
- **Geographic inconsistencies** (purchases in multiple distant locations same day)

### Monthly Review Flags
- **Category budget overruns** >20% of planned amounts
- **Recurring subscription changes** (amount increases, new services)
- **Cash flow concerns** (negative account balances, overdraft fees)

## 7. Weekly Metrics to Track

### Spending Analysis
- **Total weekly spending** vs. budget
- **Category breakdowns** with variance from plan
- **Discretionary spending** percentage
- **Cash flow** (income vs. expenses for week)

### Account Health
- **Account balances** (checking, savings, credit cards)
- **Credit utilization** percentage
- **Payment timeliness** (any late fees or missed payments)
- **Fee analysis** (bank fees, overdrafts, etc.)

### Goal Progress
- **Savings rate** (percentage of income saved)
- **Emergency fund** growth
- **Debt reduction** progress
- **Investment contributions** vs. targets

### Efficiency Metrics
- **Categorization accuracy** (ML model performance)
- **Manual review time** (trending down over time)
- **Uncategorized transactions** percentage
- **Data quality score** (complete, accurate transactions)

## 8. Tax Preparation Data Export Format

### Standard Export Structure
```json
{
  "export_date": "2024-12-31",
  "tax_year": 2024,
  "accounts": [
    {
      "account_id": "checking_001",
      "account_name": "Primary Checking",
      "account_type": "checking",
      "transactions": [
        {
          "date": "2024-01-15",
          "description": "WHOLE FOODS MARKET",
          "amount": -156.78,
          "category": "Groceries",
          "subcategory": "Regular Groceries",
          "tax_deductible": false,
          "business_expense": false,
          "split_transaction": false,
          "memo": "Weekly grocery shopping",
          "receipt_attached": false
        }
      ]
    }
  ],
  "tax_categories": {
    "deductible_expenses": [
      {
        "category": "Home Office",
        "total_amount": 2400.00,
        "transaction_count": 12,
        "documentation": "Monthly internet and phone bills"
      }
    ],
    "business_expenses": [...],
    "investment_contributions": [...],
    "charitable_donations": [...]
  }
}
```

### Tax-Relevant Category Mapping
- **Schedule A Deductions**: Medical expenses, state taxes, mortgage interest, charitable donations
- **Business Expenses**: Home office, professional development, business meals
- **Investment Tracking**: Capital gains/losses, dividend income, retirement contributions
- **HSA/FSA**: Healthcare expenses paid with pre-tax dollars

### Export Scheduling
- **Weekly**: Current year transactions for ongoing review
- **Monthly**: Category summaries for budget analysis
- **Quarterly**: Tax-relevant transaction reviews
- **Annually**: Complete tax preparation export with documentation

## Implementation Notes

### Technology Stack
- **Plaid API**: Transaction import and account connectivity
- **ML Model**: TensorFlow/scikit-learn for transaction categorization
- **Database**: PostgreSQL for transaction storage and historical analysis
- **Frontend**: Simple web interface for manual review and reporting

### Automation Opportunities
- **Recurring transactions**: Auto-categorize based on merchant patterns
- **Transfer detection**: Automatic identification and matching
- **Budget alerts**: Notifications when category limits approached
- **Anomaly detection**: Automated flagging of unusual transactions

### Success Metrics
- **Time efficiency**: Consistently completing weekly process in <30 minutes
- **Accuracy**: >95% correct categorization after ML training
- **Coverage**: 100% of transactions categorized within 1 week
- **Tax readiness**: Complete export available within 1 week of year-end