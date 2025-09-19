"""Seed tax categories and chart of accounts

Revision ID: 005
Revises: 004
Create Date: 2025-01-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy.dialects import postgresql
from datetime import date, datetime, timezone
import uuid

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Seed IRS tax categories, chart of accounts, and category mappings."""

    # Define table references for bulk insert
    tax_categories = table('tax_categories',
        column('id', postgresql.UUID),
        column('created_at', sa.DateTime(timezone=True)),
        column('updated_at', sa.DateTime(timezone=True)),
        column('category_code', sa.String),
        column('category_name', sa.String),
        column('tax_form', sa.String),
        column('tax_line', sa.String),
        column('description', sa.Text),
        column('deduction_type', sa.String),
        column('percentage_limit', sa.Numeric),
        column('is_business_expense', sa.Boolean),
        column('is_active', sa.Boolean),
        column('effective_date', sa.Date),
        column('irs_reference', sa.String),
        column('keywords', postgresql.JSONB),
        column('exclusions', postgresql.JSONB),
        column('special_rules', postgresql.JSONB),
        column('documentation_required', sa.Boolean)
    )

    chart_of_accounts = table('chart_of_accounts',
        column('id', postgresql.UUID),
        column('created_at', sa.DateTime(timezone=True)),
        column('updated_at', sa.DateTime(timezone=True)),
        column('user_id', postgresql.UUID),
        column('account_code', sa.String),
        column('account_name', sa.String),
        column('account_type', sa.String),
        column('parent_account_id', postgresql.UUID),
        column('description', sa.Text),
        column('normal_balance', sa.String),
        column('is_active', sa.Boolean),
        column('is_system_account', sa.Boolean),
        column('tax_category', sa.String),
        column('tax_line_mapping', sa.String),
        column('requires_1099', sa.Boolean)
    )

    category_mappings = table('category_mappings',
        column('id', postgresql.UUID),
        column('created_at', sa.DateTime(timezone=True)),
        column('updated_at', sa.DateTime(timezone=True)),
        column('user_id', postgresql.UUID),
        column('source_category_id', postgresql.UUID),
        column('chart_account_id', postgresql.UUID),
        column('tax_category_id', postgresql.UUID),
        column('confidence_score', sa.Numeric),
        column('is_user_defined', sa.Boolean),
        column('is_active', sa.Boolean),
        column('effective_date', sa.Date),
        column('business_percentage_default', sa.Numeric)
    )

    # Check if tax categories already exist
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT COUNT(*) FROM tax_categories"))
    existing_count = result.scalar()

    if existing_count == 0:
        print(f"Seeding tax categories...")

        # Generate timestamp
        now = datetime.now(timezone.utc)

        # IRS Schedule C Tax Categories (2024/2025)
        tax_categories_data = [
            # Schedule C - Line 8
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'SCHED_C_8',
                'category_name': 'Advertising',
                'tax_form': 'Schedule C',
                'tax_line': 'Line 8',
                'description': 'Business advertising and promotional expenses',
                'deduction_type': 'business',
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 535',
                'keywords': ['advertising', 'marketing', 'promotion', 'ads', 'social media ads', 'google ads', 'facebook ads'],
                'exclusions': ['personal', 'entertainment'],
                'special_rules': {},
                'documentation_required': False
            },
            # Schedule C - Line 9
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'SCHED_C_9',
                'category_name': 'Car and truck expenses',
                'tax_form': 'Schedule C',
                'tax_line': 'Line 9',
                'description': 'Vehicle expenses for business use',
                'deduction_type': 'business',
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 463',
                'keywords': ['car', 'truck', 'vehicle', 'gas', 'fuel', 'auto insurance', 'repairs', 'maintenance', 'mileage'],
                'exclusions': [],
                'special_rules': {
                    'mileage_rate_2024': '0.67',
                    'mileage_rate_2025': '0.70',
                    'requires_mileage_log': True,
                    'business_use_percentage_required': True
                },
                'documentation_required': True
            },
            # Schedule C - Line 10
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'SCHED_C_10',
                'category_name': 'Commissions and fees',
                'tax_form': 'Schedule C',
                'tax_line': 'Line 10',
                'description': 'Commissions and fees paid to non-employees',
                'deduction_type': 'business',
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 535',
                'keywords': ['commission', 'fees', 'referral', 'finder', 'broker', 'affiliate'],
                'exclusions': [],
                'special_rules': {
                    'requires_1099': True,
                    'threshold_amount': '600.00'
                },
                'documentation_required': True
            },
            # Schedule C - Line 11
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'SCHED_C_11',
                'category_name': 'Contract labor',
                'tax_form': 'Schedule C',
                'tax_line': 'Line 11',
                'description': 'Payments to independent contractors',
                'deduction_type': 'business',
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 535',
                'keywords': ['contractor', 'freelancer', 'consultant', 'subcontractor', '1099'],
                'exclusions': [],
                'special_rules': {
                    'requires_1099': True,
                    'threshold_amount': '600.00'
                },
                'documentation_required': True
            },
            # Schedule C - Line 13
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'SCHED_C_13',
                'category_name': 'Depreciation and section 179',
                'tax_form': 'Schedule C',
                'tax_line': 'Line 13',
                'description': 'Depreciation of business property and Section 179 deduction',
                'deduction_type': 'business',
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 946',
                'keywords': ['depreciation', 'equipment', 'furniture', 'computers', 'machinery', 'section 179'],
                'exclusions': [],
                'special_rules': {
                    'form_4562_required': True,
                    'section_179_limit_2024': '1220000'
                },
                'documentation_required': True
            },
            # Schedule C - Line 15
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'SCHED_C_15',
                'category_name': 'Insurance',
                'tax_form': 'Schedule C',
                'tax_line': 'Line 15',
                'description': 'Business insurance premiums (other than health)',
                'deduction_type': 'business',
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 535',
                'keywords': ['insurance', 'liability insurance', 'property insurance', 'business insurance', 'errors omissions'],
                'exclusions': ['health insurance', 'life insurance'],
                'special_rules': {},
                'documentation_required': False
            },
            # Schedule C - Line 16a
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'SCHED_C_16A',
                'category_name': 'Interest - Mortgage',
                'tax_form': 'Schedule C',
                'tax_line': 'Line 16a',
                'description': 'Mortgage interest on business property',
                'deduction_type': 'business',
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 535',
                'keywords': ['mortgage interest', 'loan interest', 'business mortgage'],
                'exclusions': [],
                'special_rules': {
                    'form_1098_required': True
                },
                'documentation_required': True
            },
            # Schedule C - Line 16b
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'SCHED_C_16B',
                'category_name': 'Interest - Other',
                'tax_form': 'Schedule C',
                'tax_line': 'Line 16b',
                'description': 'Other business interest expenses',
                'deduction_type': 'business',
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 535',
                'keywords': ['interest', 'credit card interest', 'loan interest', 'line of credit'],
                'exclusions': [],
                'special_rules': {},
                'documentation_required': True
            },
            # Schedule C - Line 17
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'SCHED_C_17',
                'category_name': 'Legal and professional services',
                'tax_form': 'Schedule C',
                'tax_line': 'Line 17',
                'description': 'Legal, accounting, and other professional fees',
                'deduction_type': 'business',
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 535',
                'keywords': ['legal', 'attorney', 'lawyer', 'accountant', 'cpa', 'bookkeeper', 'professional services'],
                'exclusions': [],
                'special_rules': {
                    'requires_1099': True,
                    'threshold_amount': '600.00'
                },
                'documentation_required': True
            },
            # Schedule C - Line 18
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'SCHED_C_18',
                'category_name': 'Office expense',
                'tax_form': 'Schedule C',
                'tax_line': 'Line 18',
                'description': 'General office supplies and expenses',
                'deduction_type': 'business',
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 535',
                'keywords': ['office supplies', 'paper', 'pens', 'printer ink', 'toner', 'staples', 'folders'],
                'exclusions': ['furniture', 'equipment'],
                'special_rules': {},
                'documentation_required': False
            },
            # Schedule C - Line 20a
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'SCHED_C_20A',
                'category_name': 'Rent or lease - Vehicles',
                'tax_form': 'Schedule C',
                'tax_line': 'Line 20a',
                'description': 'Vehicle lease payments for business',
                'deduction_type': 'business',
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 463',
                'keywords': ['vehicle lease', 'car lease', 'truck lease'],
                'exclusions': [],
                'special_rules': {
                    'inclusion_amount_applies': True
                },
                'documentation_required': True
            },
            # Schedule C - Line 20b
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'SCHED_C_20B',
                'category_name': 'Rent or lease - Other',
                'tax_form': 'Schedule C',
                'tax_line': 'Line 20b',
                'description': 'Office, equipment, and other business property rent',
                'deduction_type': 'business',
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 535',
                'keywords': ['rent', 'lease', 'office rent', 'equipment lease', 'property lease'],
                'exclusions': [],
                'special_rules': {},
                'documentation_required': True
            },
            # Schedule C - Line 21
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'SCHED_C_21',
                'category_name': 'Repairs and maintenance',
                'tax_form': 'Schedule C',
                'tax_line': 'Line 21',
                'description': 'Repairs and maintenance of business property',
                'deduction_type': 'business',
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 535',
                'keywords': ['repairs', 'maintenance', 'fixing', 'upkeep', 'service'],
                'exclusions': ['improvements', 'capital expenses'],
                'special_rules': {},
                'documentation_required': False
            },
            # Schedule C - Line 22
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'SCHED_C_22',
                'category_name': 'Supplies',
                'tax_form': 'Schedule C',
                'tax_line': 'Line 22',
                'description': 'Supplies consumed in business operations',
                'deduction_type': 'business',
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 535',
                'keywords': ['supplies', 'materials', 'consumables', 'inventory supplies'],
                'exclusions': ['office supplies'],
                'special_rules': {},
                'documentation_required': False
            },
            # Schedule C - Line 23
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'SCHED_C_23',
                'category_name': 'Taxes and licenses',
                'tax_form': 'Schedule C',
                'tax_line': 'Line 23',
                'description': 'Business taxes and license fees',
                'deduction_type': 'business',
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 535',
                'keywords': ['taxes', 'licenses', 'permits', 'business license', 'property tax', 'sales tax'],
                'exclusions': ['income tax', 'self-employment tax'],
                'special_rules': {},
                'documentation_required': True
            },
            # Schedule C - Line 24a
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'SCHED_C_24A',
                'category_name': 'Travel',
                'tax_form': 'Schedule C',
                'tax_line': 'Line 24a',
                'description': 'Business travel expenses',
                'deduction_type': 'business',
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 463',
                'keywords': ['travel', 'airfare', 'hotel', 'lodging', 'taxi', 'uber', 'lyft', 'train'],
                'exclusions': ['commuting', 'personal travel'],
                'special_rules': {
                    'business_purpose_required': True
                },
                'documentation_required': True
            },
            # Schedule C - Line 24b
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'SCHED_C_24B',
                'category_name': 'Meals',
                'tax_form': 'Schedule C',
                'tax_line': 'Line 24b',
                'description': 'Business meals',
                'deduction_type': 'business',
                'percentage_limit': 50.00,
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 463',
                'keywords': ['meals', 'dining', 'restaurant', 'food', 'business meal', 'client meal'],
                'exclusions': ['entertainment', 'personal meals'],
                'special_rules': {
                    'deduction_percentage': '50',
                    'temporary_100_percent_expired': '2022-12-31'
                },
                'documentation_required': True
            },
            # Schedule C - Line 25
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'SCHED_C_25',
                'category_name': 'Utilities',
                'tax_form': 'Schedule C',
                'tax_line': 'Line 25',
                'description': 'Business utilities',
                'deduction_type': 'business',
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 535',
                'keywords': ['utilities', 'electricity', 'gas', 'water', 'phone', 'internet', 'cell phone'],
                'exclusions': [],
                'special_rules': {},
                'documentation_required': False
            },
            # Schedule C - Line 26
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'SCHED_C_26',
                'category_name': 'Wages',
                'tax_form': 'Schedule C',
                'tax_line': 'Line 26',
                'description': 'Wages paid to employees (W-2 wages)',
                'deduction_type': 'business',
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 535',
                'keywords': ['wages', 'salary', 'payroll', 'employee', 'W-2'],
                'exclusions': ['contractor payments', '1099 payments'],
                'special_rules': {
                    'requires_w2': True,
                    'payroll_tax_required': True
                },
                'documentation_required': True
            },
            # Schedule C - Line 27a
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'SCHED_C_27A',
                'category_name': 'Other expenses',
                'tax_form': 'Schedule C',
                'tax_line': 'Line 27a',
                'description': 'Other ordinary and necessary business expenses',
                'deduction_type': 'business',
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 535',
                'keywords': ['other', 'miscellaneous', 'bank fees', 'software', 'subscriptions', 'education', 'training'],
                'exclusions': [],
                'special_rules': {
                    'requires_itemization': True
                },
                'documentation_required': True
            },
            # Form 8829 - Home Office
            {
                'id': str(uuid.uuid4()),
                'created_at': now,
                'updated_at': now,
                'category_code': 'FORM_8829',
                'category_name': 'Business use of home',
                'tax_form': 'Form 8829',
                'tax_line': 'Line 30',
                'description': 'Home office deduction',
                'deduction_type': 'business',
                'is_business_expense': True,
                'is_active': True,
                'effective_date': date(2024, 1, 1),
                'irs_reference': 'Pub 587',
                'keywords': ['home office', 'business use of home', 'home expenses'],
                'exclusions': [],
                'special_rules': {
                    'exclusive_use_required': True,
                    'principal_place_required': True,
                    'simplified_method_available': True,
                    'simplified_rate_2024': '5.00',
                    'simplified_max_sqft': '300'
                },
                'documentation_required': True
            }
        ]

        # Insert tax categories
        op.bulk_insert(tax_categories, tax_categories_data)
        print(f"✓ Inserted {len(tax_categories_data)} tax categories")

        # Now seed Chart of Accounts for existing users
        result = conn.execute(sa.text("SELECT id, email FROM users WHERE is_active = true"))
        users = result.fetchall()

        if users:
            print(f"Creating chart of accounts for {len(users)} users...")

            for user in users:
                user_id = user[0]
                email = user[1]

                # Generate standard chart of accounts for this user
                chart_data = []

                # Assets (1000-1999)
                assets = [
                    ('1000', 'Cash and Cash Equivalents', 'asset', 'Operating cash accounts', 'debit'),
                    ('1010', 'Business Checking', 'asset', 'Primary business checking account', 'debit'),
                    ('1020', 'Business Savings', 'asset', 'Business savings account', 'debit'),
                    ('1100', 'Accounts Receivable', 'asset', 'Money owed by customers', 'debit'),
                    ('1200', 'Inventory', 'asset', 'Products held for sale', 'debit'),
                    ('1500', 'Equipment', 'asset', 'Business equipment and machinery', 'debit'),
                    ('1510', 'Computer Equipment', 'asset', 'Computers and related equipment', 'debit'),
                    ('1520', 'Office Furniture', 'asset', 'Office furniture and fixtures', 'debit'),
                    ('1600', 'Accumulated Depreciation', 'contra_asset', 'Accumulated depreciation on assets', 'credit'),
                    ('1900', 'Other Assets', 'asset', 'Other business assets', 'debit'),
                ]

                # Liabilities (2000-2999)
                liabilities = [
                    ('2000', 'Accounts Payable', 'liability', 'Money owed to vendors', 'credit'),
                    ('2100', 'Credit Cards', 'liability', 'Business credit card balances', 'credit'),
                    ('2200', 'Short-term Loans', 'liability', 'Loans due within one year', 'credit'),
                    ('2300', 'Long-term Loans', 'liability', 'Loans due after one year', 'credit'),
                    ('2400', 'Sales Tax Payable', 'liability', 'Sales tax collected', 'credit'),
                    ('2500', 'Payroll Liabilities', 'liability', 'Payroll taxes and withholdings', 'credit'),
                    ('2600', 'Income Tax Payable', 'liability', 'Income tax owed', 'credit'),
                ]

                # Equity (3000-3999)
                equity = [
                    ('3000', "Owner's Equity", 'equity', 'Owner investment in business', 'credit'),
                    ('3100', "Owner's Draw", 'equity', 'Owner withdrawals from business', 'debit'),
                    ('3200', 'Retained Earnings', 'equity', 'Accumulated profits', 'credit'),
                ]

                # Revenue (4000-4999)
                revenue = [
                    ('4000', 'Service Revenue', 'revenue', 'Income from services', 'credit'),
                    ('4100', 'Product Sales', 'revenue', 'Income from product sales', 'credit'),
                    ('4200', 'Interest Income', 'revenue', 'Interest earned', 'credit'),
                    ('4900', 'Other Income', 'revenue', 'Miscellaneous income', 'credit'),
                ]

                # Expenses (5000-8999) - Mapped to Schedule C lines
                expenses = [
                    ('5000', 'Advertising', 'expense', 'Marketing and advertising costs', 'debit', 'SCHED_C_8'),
                    ('5100', 'Vehicle Expenses', 'expense', 'Car and truck expenses', 'debit', 'SCHED_C_9'),
                    ('5200', 'Commissions and Fees', 'expense', 'Commissions paid', 'debit', 'SCHED_C_10'),
                    ('5300', 'Contract Labor', 'expense', 'Independent contractor payments', 'debit', 'SCHED_C_11'),
                    ('5400', 'Depreciation', 'expense', 'Asset depreciation', 'debit', 'SCHED_C_13'),
                    ('5500', 'Insurance', 'expense', 'Business insurance premiums', 'debit', 'SCHED_C_15'),
                    ('5600', 'Interest Expense', 'expense', 'Loan and credit interest', 'debit', 'SCHED_C_16B'),
                    ('5700', 'Legal and Professional', 'expense', 'Legal and professional fees', 'debit', 'SCHED_C_17'),
                    ('5800', 'Office Expenses', 'expense', 'Office supplies and expenses', 'debit', 'SCHED_C_18'),
                    ('5900', 'Rent', 'expense', 'Rent and lease payments', 'debit', 'SCHED_C_20B'),
                    ('6000', 'Repairs and Maintenance', 'expense', 'Repair and maintenance costs', 'debit', 'SCHED_C_21'),
                    ('6100', 'Supplies', 'expense', 'Business supplies', 'debit', 'SCHED_C_22'),
                    ('6200', 'Taxes and Licenses', 'expense', 'Business taxes and licenses', 'debit', 'SCHED_C_23'),
                    ('6300', 'Travel', 'expense', 'Business travel expenses', 'debit', 'SCHED_C_24A'),
                    ('6400', 'Meals', 'expense', 'Business meals (50% deductible)', 'debit', 'SCHED_C_24B'),
                    ('6500', 'Utilities', 'expense', 'Business utilities', 'debit', 'SCHED_C_25'),
                    ('6600', 'Wages', 'expense', 'Employee wages', 'debit', 'SCHED_C_26'),
                    ('6700', 'Bank Fees', 'expense', 'Bank service charges', 'debit', 'SCHED_C_27A'),
                    ('6800', 'Software Subscriptions', 'expense', 'Software and SaaS subscriptions', 'debit', 'SCHED_C_27A'),
                    ('6900', 'Education and Training', 'expense', 'Professional development', 'debit', 'SCHED_C_27A'),
                    ('7000', 'Home Office', 'expense', 'Home office expenses', 'debit', 'FORM_8829'),
                    ('8900', 'Other Expenses', 'expense', 'Other business expenses', 'debit', 'SCHED_C_27A'),
                ]

                # Combine all account categories
                all_accounts = []
                for code, name, acc_type, desc, balance, *tax in assets + liabilities + equity + revenue:
                    all_accounts.append({
                        'id': str(uuid.uuid4()),
                        'created_at': now,
                        'updated_at': now,
                        'user_id': user_id,
                        'account_code': code,
                        'account_name': name,
                        'account_type': acc_type,
                        'description': desc,
                        'normal_balance': balance,
                        'is_active': True,
                        'is_system_account': True,
                        'tax_category': None,
                        'tax_line_mapping': None,
                        'requires_1099': False
                    })

                for code, name, acc_type, desc, balance, tax_cat in expenses:
                    all_accounts.append({
                        'id': str(uuid.uuid4()),
                        'created_at': now,
                        'updated_at': now,
                        'user_id': user_id,
                        'account_code': code,
                        'account_name': name,
                        'account_type': acc_type,
                        'description': desc,
                        'normal_balance': balance,
                        'is_active': True,
                        'is_system_account': True,
                        'tax_category': tax_cat,
                        'tax_line_mapping': tax_cat,
                        'requires_1099': tax_cat in ['SCHED_C_10', 'SCHED_C_11', 'SCHED_C_17']
                    })

                # Insert accounts for this user
                if all_accounts:
                    op.bulk_insert(chart_of_accounts, all_accounts)
                    print(f"✓ Created {len(all_accounts)} accounts for user {email}")

        # Create category mappings - map existing transaction categories to tax categories
        result = conn.execute(sa.text("""
            SELECT c.id, c.name, c.parent_category, u.id as user_id
            FROM categories c
            LEFT JOIN users u ON c.user_id = u.id OR (c.user_id IS NULL AND u.is_active = true)
            WHERE c.is_active = true
        """))
        categories = result.fetchall()

        if categories:
            print(f"Creating category mappings for {len(categories)} categories...")

            # Mapping of category names to tax category codes
            category_tax_map = {
                'Marketing & Advertising': 'SCHED_C_8',
                'Transportation': 'SCHED_C_9',
                'Contractor Payments': 'SCHED_C_11',
                'Equipment': 'SCHED_C_13',
                'Insurance': 'SCHED_C_15',
                'Professional Services': 'SCHED_C_17',
                'Office Supplies': 'SCHED_C_18',
                'Rent & Utilities': 'SCHED_C_20B',
                'Software & Subscriptions': 'SCHED_C_27A',
                'Travel - Business': 'SCHED_C_24A',
                'Meals & Entertainment': 'SCHED_C_24B',
                'Payroll': 'SCHED_C_26',
                'Bank Fees': 'SCHED_C_27A',
                'Education': 'SCHED_C_27A',
            }

            # Get tax category IDs
            tax_cat_ids = {}
            result = conn.execute(sa.text("SELECT id, category_code FROM tax_categories"))
            for row in result:
                tax_cat_ids[row[1]] = row[0]

            # Get chart account IDs for each user
            chart_account_ids = {}
            result = conn.execute(sa.text("""
                SELECT user_id, account_code, id
                FROM chart_of_accounts
                WHERE is_active = true
            """))
            for row in result:
                if row[0] not in chart_account_ids:
                    chart_account_ids[row[0]] = {}
                chart_account_ids[row[0]][row[1]] = row[2]

            # Account code mapping based on tax category
            tax_to_account = {
                'SCHED_C_8': '5000',   # Advertising
                'SCHED_C_9': '5100',   # Vehicle
                'SCHED_C_10': '5200',  # Commissions
                'SCHED_C_11': '5300',  # Contract Labor
                'SCHED_C_13': '5400',  # Depreciation
                'SCHED_C_15': '5500',  # Insurance
                'SCHED_C_17': '5700',  # Legal/Professional
                'SCHED_C_18': '5800',  # Office
                'SCHED_C_20B': '5900', # Rent
                'SCHED_C_24A': '6300', # Travel
                'SCHED_C_24B': '6400', # Meals
                'SCHED_C_25': '6500',  # Utilities
                'SCHED_C_26': '6600',  # Wages
                'SCHED_C_27A': '8900', # Other
            }

            mappings = []
            for cat_id, cat_name, parent_cat, user_id in categories:
                if cat_name in category_tax_map and user_id:
                    tax_code = category_tax_map[cat_name]
                    tax_id = tax_cat_ids.get(tax_code)

                    # Get appropriate chart account
                    if user_id in chart_account_ids:
                        account_code = tax_to_account.get(tax_code, '8900')
                        chart_id = chart_account_ids[user_id].get(account_code)

                        if tax_id and chart_id:
                            mappings.append({
                                'id': str(uuid.uuid4()),
                                'created_at': now,
                                'updated_at': now,
                                'user_id': user_id,
                                'source_category_id': cat_id,
                                'chart_account_id': chart_id,
                                'tax_category_id': tax_id,
                                'confidence_score': 0.95,
                                'is_user_defined': False,
                                'is_active': True,
                                'effective_date': date(2024, 1, 1),
                                'business_percentage_default': 100.00 if cat_name != 'Meals & Entertainment' else 50.00
                            })

            if mappings:
                op.bulk_insert(category_mappings, mappings)
                print(f"✓ Created {len(mappings)} category mappings")

    else:
        print(f"Tax categories already seeded ({existing_count} found), skipping...")


def downgrade() -> None:
    """Remove seeded data."""

    # Delete in reverse order due to foreign key constraints
    op.execute("DELETE FROM category_mappings WHERE is_user_defined = false")
    op.execute("DELETE FROM chart_of_accounts WHERE is_system_account = true")
    op.execute("DELETE FROM tax_categories WHERE category_code LIKE 'SCHED_C_%' OR category_code = 'FORM_8829'")

    print("✓ Removed seeded tax categorization data")