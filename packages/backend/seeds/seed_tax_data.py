"""Seed data for tax categorization system."""

from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ..models.tax_categorization import TaxCategory, ChartOfAccount


def seed_tax_categories(session: Session) -> List[TaxCategory]:
    """Create IRS Schedule C tax categories for 2024/2025."""

    tax_categories = [
        # Schedule C - Part II: Expenses
        {
            "category_code": "SCHED_C_8",
            "category_name": "Advertising",
            "tax_form": "Schedule C",
            "tax_line": "Line 8",
            "description": "Business advertising and promotional expenses",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 535 - Business Expenses",
            "keywords": ["advertising", "marketing", "promotion", "ads", "billboard", "radio", "tv", "newspaper", "online ads"],
            "exclusions": ["personal", "entertainment"]
        },
        {
            "category_code": "SCHED_C_9",
            "category_name": "Car and truck expenses",
            "tax_form": "Schedule C",
            "tax_line": "Line 9",
            "description": "Vehicle expenses for business use",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 463 - Travel, Entertainment, Gift, and Car Expenses",
            "keywords": ["car", "truck", "vehicle", "gas", "fuel", "insurance", "repairs", "maintenance", "mileage"],
            "special_rules": {
                "mileage_rate_2024": "0.67",
                "requires_mileage_log": True,
                "business_use_percentage_required": True
            }
        },
        {
            "category_code": "SCHED_C_10",
            "category_name": "Commissions and fees",
            "tax_form": "Schedule C",
            "tax_line": "Line 10",
            "description": "Commissions and fees paid to others",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 535 - Business Expenses",
            "keywords": ["commission", "fees", "referral", "finder", "broker"],
            "special_rules": {
                "requires_1099": True,
                "threshold_amount": "600.00"
            }
        },
        {
            "category_code": "SCHED_C_11",
            "category_name": "Contract labor",
            "tax_form": "Schedule C",
            "tax_line": "Line 11",
            "description": "Payments to independent contractors",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 535 - Business Expenses",
            "keywords": ["contractor", "freelancer", "consultant", "subcontractor"],
            "special_rules": {
                "requires_1099": True,
                "threshold_amount": "600.00"
            }
        },
        {
            "category_code": "SCHED_C_12",
            "category_name": "Depletion",
            "tax_form": "Schedule C",
            "tax_line": "Line 12",
            "description": "Depletion of natural resources",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 535 - Business Expenses",
            "keywords": ["depletion", "natural resources", "oil", "gas", "mining"]
        },
        {
            "category_code": "SCHED_C_13",
            "category_name": "Depreciation",
            "tax_form": "Schedule C",
            "tax_line": "Line 13",
            "description": "Depreciation of business assets",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 946 - How to Depreciate Property",
            "keywords": ["depreciation", "equipment", "furniture", "computers", "machinery"],
            "special_rules": {
                "requires_form_4562": True,
                "section_179_limit_2024": "1160000"
            }
        },
        {
            "category_code": "SCHED_C_14",
            "category_name": "Employee benefit programs",
            "tax_form": "Schedule C",
            "tax_line": "Line 14",
            "description": "Employee benefit programs (not health insurance)",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 535 - Business Expenses",
            "keywords": ["benefits", "retirement", "401k", "pension", "life insurance"]
        },
        {
            "category_code": "SCHED_C_15",
            "category_name": "Insurance (other than health)",
            "tax_form": "Schedule C",
            "tax_line": "Line 15",
            "description": "Business insurance premiums",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 535 - Business Expenses",
            "keywords": ["insurance", "liability", "property", "business", "professional", "errors", "omissions"],
            "exclusions": ["health insurance", "life insurance"]
        },
        {
            "category_code": "SCHED_C_16A",
            "category_name": "Mortgage interest",
            "tax_form": "Schedule C",
            "tax_line": "Line 16a",
            "description": "Mortgage interest on business property",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 535 - Business Expenses",
            "keywords": ["mortgage", "interest", "loan", "business property"]
        },
        {
            "category_code": "SCHED_C_16B",
            "category_name": "Other interest",
            "tax_form": "Schedule C",
            "tax_line": "Line 16b",
            "description": "Other business interest expenses",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 535 - Business Expenses",
            "keywords": ["interest", "loan", "credit", "financing", "business loan"]
        },
        {
            "category_code": "SCHED_C_17",
            "category_name": "Legal and professional services",
            "tax_form": "Schedule C",
            "tax_line": "Line 17",
            "description": "Legal and professional service fees",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 535 - Business Expenses",
            "keywords": ["legal", "attorney", "lawyer", "accountant", "CPA", "professional", "consultant", "advisory"],
            "special_rules": {
                "requires_1099": True,
                "threshold_amount": "600.00"
            }
        },
        {
            "category_code": "SCHED_C_18",
            "category_name": "Office expense",
            "tax_form": "Schedule C",
            "tax_line": "Line 18",
            "description": "Office supplies and expenses",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 535 - Business Expenses",
            "keywords": ["office", "supplies", "paper", "pens", "printer", "ink", "postage", "shipping", "stationery"]
        },
        {
            "category_code": "SCHED_C_19",
            "category_name": "Pension and profit-sharing plans",
            "tax_form": "Schedule C",
            "tax_line": "Line 19",
            "description": "Pension and profit-sharing plan contributions",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 560 - Retirement Plans for Small Business",
            "keywords": ["pension", "401k", "retirement", "profit sharing", "SEP", "SIMPLE"]
        },
        {
            "category_code": "SCHED_C_20",
            "category_name": "Rent or lease",
            "tax_form": "Schedule C",
            "tax_line": "Line 20",
            "description": "Rent or lease of business property and equipment",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 535 - Business Expenses",
            "keywords": ["rent", "lease", "office", "equipment", "vehicle lease", "building"]
        },
        {
            "category_code": "SCHED_C_21",
            "category_name": "Repairs and maintenance",
            "tax_form": "Schedule C",
            "tax_line": "Line 21",
            "description": "Repairs and maintenance of business property",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 535 - Business Expenses",
            "keywords": ["repairs", "maintenance", "fix", "service", "upkeep"],
            "exclusions": ["improvements", "capital expenditures"]
        },
        {
            "category_code": "SCHED_C_22",
            "category_name": "Supplies",
            "tax_form": "Schedule C",
            "tax_line": "Line 22",
            "description": "Business supplies and materials",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 535 - Business Expenses",
            "keywords": ["supplies", "materials", "inventory", "raw materials", "tools"]
        },
        {
            "category_code": "SCHED_C_23",
            "category_name": "Taxes and licenses",
            "tax_form": "Schedule C",
            "tax_line": "Line 23",
            "description": "Business taxes and licenses",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 535 - Business Expenses",
            "keywords": ["taxes", "license", "permit", "registration", "fees", "property tax", "excise"],
            "exclusions": ["income tax", "self-employment tax"]
        },
        {
            "category_code": "SCHED_C_24A",
            "category_name": "Travel",
            "tax_form": "Schedule C",
            "tax_line": "Line 24a",
            "description": "Business travel expenses",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 463 - Travel, Entertainment, Gift, and Car Expenses",
            "keywords": ["travel", "airfare", "hotel", "lodging", "transportation", "taxi"],
            "documentation_required": True,
            "special_rules": {
                "requires_business_purpose": True,
                "foreign_travel_special_rules": True
            }
        },
        {
            "category_code": "SCHED_C_24B",
            "category_name": "Meals",
            "tax_form": "Schedule C",
            "tax_line": "Line 24b",
            "description": "Business meal expenses",
            "deduction_type": "ordinary",
            "percentage_limit": Decimal("50.00"),
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 463 - Travel, Entertainment, Gift, and Car Expenses",
            "keywords": ["meals", "restaurant", "food", "dining", "business lunch", "client dinner"],
            "documentation_required": True,
            "special_rules": {
                "deduction_percentage": "50",
                "requires_business_purpose": True,
                "100_percent_exceptions": ["company parties", "employee meals"]
            }
        },
        {
            "category_code": "SCHED_C_25",
            "category_name": "Utilities",
            "tax_form": "Schedule C",
            "tax_line": "Line 25",
            "description": "Business utilities",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 535 - Business Expenses",
            "keywords": ["utilities", "electricity", "gas", "water", "phone", "internet", "cable"]
        },
        {
            "category_code": "SCHED_C_26",
            "category_name": "Wages",
            "tax_form": "Schedule C",
            "tax_line": "Line 26",
            "description": "Employee wages and salaries",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 535 - Business Expenses",
            "keywords": ["wages", "salary", "payroll", "employee", "compensation"],
            "special_rules": {
                "requires_payroll_taxes": True,
                "requires_w2": True
            }
        },
        {
            "category_code": "SCHED_C_27A",
            "category_name": "Other expenses - Business",
            "tax_form": "Schedule C",
            "tax_line": "Line 27a",
            "description": "Other deductible business expenses",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 535 - Business Expenses",
            "keywords": ["other", "miscellaneous", "business expense"],
            "documentation_required": True
        },

        # Form 8829 - Home Office
        {
            "category_code": "FORM_8829",
            "category_name": "Home office expenses",
            "tax_form": "Form 8829",
            "tax_line": "Various",
            "description": "Business use of home expenses",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "effective_date": date(2024, 1, 1),
            "irs_reference": "Pub 587 - Business Use of Your Home",
            "keywords": ["home office", "home", "office", "workspace"],
            "special_rules": {
                "simplified_method_rate": "5.00",
                "simplified_method_max": "1500",
                "requires_exclusive_use": True,
                "square_footage_required": True
            }
        }
    ]

    created_categories = []
    for cat_data in tax_categories:
        # Check if category already exists
        existing = session.query(TaxCategory).filter_by(category_code=cat_data["category_code"]).first()
        if not existing:
            category = TaxCategory(**cat_data)
            session.add(category)
            created_categories.append(category)

    session.commit()
    return created_categories


def seed_chart_of_accounts(session: Session, user_id: str) -> List[ChartOfAccount]:
    """Create default chart of accounts for a user."""

    accounts = [
        # ASSETS (1000-1999)
        {
            "account_code": "1000",
            "account_name": "Cash and Cash Equivalents",
            "account_type": "asset",
            "normal_balance": "debit",
            "description": "Cash in checking and savings accounts",
            "is_system_account": True,
            "tax_category": "Not Applicable"
        },
        {
            "account_code": "1100",
            "account_name": "Checking Account",
            "account_type": "asset",
            "normal_balance": "debit",
            "description": "Business checking account",
            "parent_account_code": "1000",
            "is_system_account": True
        },
        {
            "account_code": "1200",
            "account_name": "Savings Account",
            "account_type": "asset",
            "normal_balance": "debit",
            "description": "Business savings account",
            "parent_account_code": "1000",
            "is_system_account": True
        },
        {
            "account_code": "1500",
            "account_name": "Accounts Receivable",
            "account_type": "asset",
            "normal_balance": "debit",
            "description": "Money owed by customers",
            "is_system_account": True
        },
        {
            "account_code": "1600",
            "account_name": "Inventory",
            "account_type": "asset",
            "normal_balance": "debit",
            "description": "Products held for sale",
            "is_system_account": True
        },
        {
            "account_code": "1700",
            "account_name": "Equipment",
            "account_type": "asset",
            "normal_balance": "debit",
            "description": "Business equipment and machinery",
            "is_system_account": True,
            "tax_category": "Depreciation"
        },
        {
            "account_code": "1800",
            "account_name": "Accumulated Depreciation - Equipment",
            "account_type": "contra_asset",
            "normal_balance": "credit",
            "description": "Accumulated depreciation on equipment",
            "is_system_account": True
        },

        # LIABILITIES (2000-2999)
        {
            "account_code": "2000",
            "account_name": "Accounts Payable",
            "account_type": "liability",
            "normal_balance": "credit",
            "description": "Money owed to suppliers",
            "is_system_account": True
        },
        {
            "account_code": "2100",
            "account_name": "Credit Card Payable",
            "account_type": "liability",
            "normal_balance": "credit",
            "description": "Business credit card balances",
            "is_system_account": True
        },
        {
            "account_code": "2200",
            "account_name": "Accrued Expenses",
            "account_type": "liability",
            "normal_balance": "credit",
            "description": "Expenses incurred but not yet paid",
            "is_system_account": True
        },
        {
            "account_code": "2300",
            "account_name": "Payroll Liabilities",
            "account_type": "liability",
            "normal_balance": "credit",
            "description": "Payroll taxes and withholdings",
            "is_system_account": True
        },

        # EQUITY (3000-3999)
        {
            "account_code": "3000",
            "account_name": "Owner's Equity",
            "account_type": "equity",
            "normal_balance": "credit",
            "description": "Owner's investment in the business",
            "is_system_account": True
        },
        {
            "account_code": "3100",
            "account_name": "Retained Earnings",
            "account_type": "equity",
            "normal_balance": "credit",
            "description": "Accumulated business profits",
            "is_system_account": True
        },
        {
            "account_code": "3200",
            "account_name": "Owner's Draw",
            "account_type": "equity",
            "normal_balance": "debit",
            "description": "Money withdrawn by owner",
            "is_system_account": True
        },

        # REVENUE (4000-4999)
        {
            "account_code": "4000",
            "account_name": "Service Revenue",
            "account_type": "revenue",
            "normal_balance": "credit",
            "description": "Income from services provided",
            "is_system_account": True,
            "tax_category": "Business Income"
        },
        {
            "account_code": "4100",
            "account_name": "Product Sales",
            "account_type": "revenue",
            "normal_balance": "credit",
            "description": "Income from product sales",
            "is_system_account": True,
            "tax_category": "Business Income"
        },
        {
            "account_code": "4200",
            "account_name": "Interest Income",
            "account_type": "revenue",
            "normal_balance": "credit",
            "description": "Interest earned on accounts",
            "is_system_account": True,
            "tax_category": "Other Income"
        },

        # EXPENSES (5000-8999) - Schedule C Line Items
        {
            "account_code": "5100",
            "account_name": "Advertising Expense",
            "account_type": "expense",
            "normal_balance": "debit",
            "description": "Business advertising and marketing",
            "is_system_account": True,
            "tax_category": "Advertising",
            "tax_line_mapping": "Schedule C - Line 8"
        },
        {
            "account_code": "5200",
            "account_name": "Vehicle Expense",
            "account_type": "expense",
            "normal_balance": "debit",
            "description": "Car and truck expenses",
            "is_system_account": True,
            "tax_category": "Car and truck expenses",
            "tax_line_mapping": "Schedule C - Line 9"
        },
        {
            "account_code": "5300",
            "account_name": "Professional Services",
            "account_type": "expense",
            "normal_balance": "debit",
            "description": "Legal and professional services",
            "is_system_account": True,
            "tax_category": "Legal and professional services",
            "tax_line_mapping": "Schedule C - Line 17",
            "requires_1099": True
        },
        {
            "account_code": "5400",
            "account_name": "Office Expense",
            "account_type": "expense",
            "normal_balance": "debit",
            "description": "Office supplies and expenses",
            "is_system_account": True,
            "tax_category": "Office expense",
            "tax_line_mapping": "Schedule C - Line 18"
        },
        {
            "account_code": "5500",
            "account_name": "Rent Expense",
            "account_type": "expense",
            "normal_balance": "debit",
            "description": "Rent or lease payments",
            "is_system_account": True,
            "tax_category": "Rent or lease",
            "tax_line_mapping": "Schedule C - Line 20"
        },
        {
            "account_code": "5600",
            "account_name": "Travel Expense",
            "account_type": "expense",
            "normal_balance": "debit",
            "description": "Business travel expenses",
            "is_system_account": True,
            "tax_category": "Travel",
            "tax_line_mapping": "Schedule C - Line 24a"
        },
        {
            "account_code": "5700",
            "account_name": "Meals and Entertainment",
            "account_type": "expense",
            "normal_balance": "debit",
            "description": "Business meals (50% deductible)",
            "is_system_account": True,
            "tax_category": "Meals",
            "tax_line_mapping": "Schedule C - Line 24b"
        },
        {
            "account_code": "5800",
            "account_name": "Utilities Expense",
            "account_type": "expense",
            "normal_balance": "debit",
            "description": "Business utilities",
            "is_system_account": True,
            "tax_category": "Utilities",
            "tax_line_mapping": "Schedule C - Line 25"
        },
        {
            "account_code": "5900",
            "account_name": "Insurance Expense",
            "account_type": "expense",
            "normal_balance": "debit",
            "description": "Business insurance premiums",
            "is_system_account": True,
            "tax_category": "Insurance (other than health)",
            "tax_line_mapping": "Schedule C - Line 15"
        },
        {
            "account_code": "6000",
            "account_name": "Supplies Expense",
            "account_type": "expense",
            "normal_balance": "debit",
            "description": "Business supplies and materials",
            "is_system_account": True,
            "tax_category": "Supplies",
            "tax_line_mapping": "Schedule C - Line 22"
        },
        {
            "account_code": "6100",
            "account_name": "Contract Labor",
            "account_type": "expense",
            "normal_balance": "debit",
            "description": "Independent contractor payments",
            "is_system_account": True,
            "tax_category": "Contract labor",
            "tax_line_mapping": "Schedule C - Line 11",
            "requires_1099": True
        },
        {
            "account_code": "6200",
            "account_name": "Depreciation Expense",
            "account_type": "expense",
            "normal_balance": "debit",
            "description": "Depreciation of business assets",
            "is_system_account": True,
            "tax_category": "Depreciation",
            "tax_line_mapping": "Schedule C - Line 13"
        },
        {
            "account_code": "6300",
            "account_name": "Interest Expense",
            "account_type": "expense",
            "normal_balance": "debit",
            "description": "Business loan interest",
            "is_system_account": True,
            "tax_category": "Other interest",
            "tax_line_mapping": "Schedule C - Line 16b"
        },
        {
            "account_code": "6400",
            "account_name": "Repairs and Maintenance",
            "account_type": "expense",
            "normal_balance": "debit",
            "description": "Equipment and facility repairs",
            "is_system_account": True,
            "tax_category": "Repairs and maintenance",
            "tax_line_mapping": "Schedule C - Line 21"
        },
        {
            "account_code": "8000",
            "account_name": "Home Office Expense",
            "account_type": "expense",
            "normal_balance": "debit",
            "description": "Home office deduction",
            "is_system_account": True,
            "tax_category": "Home office expenses",
            "tax_line_mapping": "Form 8829"
        },
        {
            "account_code": "8900",
            "account_name": "Other Business Expenses",
            "account_type": "expense",
            "normal_balance": "debit",
            "description": "Miscellaneous business expenses",
            "is_system_account": True,
            "tax_category": "Other expenses - Business",
            "tax_line_mapping": "Schedule C - Line 27a"
        }
    ]

    created_accounts = []
    account_map = {}  # To track accounts for parent relationships

    # First pass: create accounts without parent relationships
    for acc_data in accounts:
        account_dict = acc_data.copy()
        parent_account_code = account_dict.pop("parent_account_code", None)

        # Check if account already exists for this user
        existing = session.query(ChartOfAccount).filter_by(
            user_id=user_id,
            account_code=account_dict["account_code"]
        ).first()

        if not existing:
            account = ChartOfAccount(user_id=user_id, **account_dict)
            session.add(account)
            session.flush()  # Get the ID
            created_accounts.append(account)
            account_map[account.account_code] = account

    # Second pass: set parent relationships
    for acc_data in accounts:
        parent_account_code = acc_data.get("parent_account_code")
        if parent_account_code:
            child_account = account_map.get(acc_data["account_code"])
            parent_account = account_map.get(parent_account_code)
            if child_account and parent_account:
                child_account.parent_account_id = parent_account.id

    session.commit()
    return created_accounts


def create_default_category_mappings(session: Session, user_id: str) -> None:
    """Create default category mappings for common transactions."""
    # This would be implemented to create mappings between
    # existing categories and the new tax categories/chart of accounts
    # For now, we'll skip this as it requires the existing category data
    pass