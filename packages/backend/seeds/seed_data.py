"""Seed data for development environment."""

from decimal import Decimal
from datetime import datetime, timedelta
import uuid
from sqlalchemy.orm import Session

from src.database.models import (
    User, Institution, Category, Account, Transaction,
    CategorizationRule, Budget, BudgetItem
)


def create_seed_data(session: Session) -> None:
    """Create seed data for development."""
    
    # Create test user
    user = User(
        email="test@manna.com",
        password_hash="$2b$12$sample_hash_for_testing",
        first_name="Test",
        last_name="User",
        is_active=True,
        is_verified=True,
        business_name="Manna Financial LLC",
        business_type="llc",
        timezone="America/Los_Angeles"
    )
    session.add(user)
    session.flush()  # Get the ID
    
    # Create sample institutions
    chase = Institution(
        plaid_institution_id="ins_109508",
        name="Chase Bank",
        country_codes=["US"],
        products=["transactions", "auth", "identity"],
        logo="https://example.com/chase-logo.png",
        primary_color="#0066b2",
        url="https://chase.com"
    )
    
    wells_fargo = Institution(
        plaid_institution_id="ins_109511",
        name="Wells Fargo",
        country_codes=["US"],
        products=["transactions", "auth", "identity"],
        logo="https://example.com/wells-fargo-logo.png",
        primary_color="#d52b1e",
        url="https://wellsfargo.com"
    )
    
    session.add_all([chase, wells_fargo])
    session.flush()
    
    # Create system categories
    categories = [
        # Income categories
        Category(
            name="Business Income",
            category_type="income",
            is_business_category=True,
            is_system_category=True,
            icon="money",
            color="#22c55e"
        ),
        Category(
            name="Investment Income",
            category_type="income",
            is_system_category=True,
            icon="trending-up",
            color="#10b981"
        ),
        
        # Expense categories
        Category(
            name="Office Expenses",
            category_type="expense",
            is_business_category=True,
            is_tax_deductible=True,
            is_system_category=True,
            icon="building",
            color="#f59e0b"
        ),
        Category(
            name="Food & Dining",
            category_type="expense",
            is_system_category=True,
            icon="utensils",
            color="#ef4444"
        ),
        Category(
            name="Transportation",
            category_type="expense",
            is_system_category=True,
            icon="car",
            color="#8b5cf6"
        ),
        Category(
            name="Utilities",
            category_type="expense",
            is_system_category=True,
            icon="zap",
            color="#06b6d4"
        ),
    ]
    
    # Add subcategories
    office_expenses = categories[2]  # Office Expenses
    subcategories = [
        Category(
            parent=office_expenses,
            name="Software & SaaS",
            category_type="expense",
            is_business_category=True,
            is_tax_deductible=True,
            is_system_category=True
        ),
        Category(
            parent=office_expenses,
            name="Office Supplies",
            category_type="expense",
            is_business_category=True,
            is_tax_deductible=True,
            is_system_category=True
        ),
    ]
    
    categories.extend(subcategories)
    session.add_all(categories)
    session.flush()
    
    # Create sample accounts
    checking = Account(
        user_id=user.id,
        institution_id=chase.id,
        plaid_account_id="sample_checking_id",
        name="Chase Business Checking",
        account_type="checking",
        account_subtype="checking",
        is_business=True,
        current_balance=Decimal("15432.50"),
        available_balance=Decimal("15432.50")
    )
    
    savings = Account(
        user_id=user.id,
        institution_id=chase.id,
        plaid_account_id="sample_savings_id",
        name="Chase Business Savings",
        account_type="savings",
        account_subtype="savings",
        is_business=True,
        current_balance=Decimal("75000.00"),
        available_balance=Decimal("75000.00")
    )
    
    credit = Account(
        user_id=user.id,
        institution_id=wells_fargo.id,
        plaid_account_id="sample_credit_id",
        name="Wells Fargo Business Credit",
        account_type="credit",
        account_subtype="credit_card",
        is_business=True,
        current_balance=Decimal("2150.75"),
        available_balance=Decimal("7849.25"),
        credit_limit=Decimal("10000.00")
    )
    
    session.add_all([checking, savings, credit])
    session.flush()
    
    # Create sample transactions
    transactions = []
    base_date = datetime.utcnow() - timedelta(days=30)
    
    # Business income
    transactions.append(Transaction(
        account_id=checking.id,
        plaid_transaction_id="txn_income_1",
        amount=Decimal("5000.00"),
        transaction_type="credit",
        date=base_date + timedelta(days=1),
        name="Client Payment - ABC Corp",
        merchant_name="ABC Corp",
        category_id=categories[0].id,  # Business Income
        is_business=True,
        payment_method="ach"
    ))
    
    # Office expenses
    transactions.append(Transaction(
        account_id=credit.id,
        plaid_transaction_id="txn_office_1",
        amount=Decimal("49.99"),
        transaction_type="debit",
        date=base_date + timedelta(days=5),
        name="Slack Premium Subscription",
        merchant_name="Slack Technologies",
        category_id=subcategories[0].id,  # Software & SaaS
        is_business=True,
        is_tax_deductible=True,
        payment_method="online"
    ))
    
    # Office supplies
    transactions.append(Transaction(
        account_id=credit.id,
        plaid_transaction_id="txn_office_2",
        amount=Decimal("127.45"),
        transaction_type="debit",
        date=base_date + timedelta(days=10),
        name="Office Depot Purchase",
        merchant_name="Office Depot",
        category_id=subcategories[1].id,  # Office Supplies
        is_business=True,
        is_tax_deductible=True,
        payment_method="in_store"
    ))
    
    # Personal dining
    transactions.append(Transaction(
        account_id=credit.id,
        plaid_transaction_id="txn_dining_1",
        amount=Decimal("45.67"),
        transaction_type="debit",
        date=base_date + timedelta(days=15),
        name="Chipotle Mexican Grill",
        merchant_name="Chipotle",
        category_id=categories[3].id,  # Food & Dining
        is_business=False,
        payment_method="in_store"
    ))
    
    session.add_all(transactions)
    
    # Create categorization rules
    rules = [
        CategorizationRule(
            user_id=user.id,
            category_id=subcategories[0].id,  # Software & SaaS
            name="Software Subscriptions",
            rule_type="merchant",
            pattern="Slack|Microsoft|Adobe|Google|AWS|DigitalOcean",
            pattern_type="regex",
            match_fields=["merchant_name", "name"],
            priority=10,
            set_business=True,
            set_tax_deductible=True
        ),
        CategorizationRule(
            user_id=user.id,
            category_id=categories[3].id,  # Food & Dining
            name="Restaurants",
            rule_type="merchant",
            pattern="Chipotle|Starbucks|McDonald|Subway|Pizza",
            pattern_type="regex",
            match_fields=["merchant_name"],
            priority=20,
            set_business=False
        ),
    ]
    
    session.add_all(rules)
    
    # Create sample budget
    budget = Budget(
        user_id=user.id,
        name="Q4 2024 Business Budget",
        description="Fourth quarter business budget",
        budget_type="quarterly",
        period_start=datetime(2024, 10, 1),
        period_end=datetime(2024, 12, 31),
        is_business_budget=True,
        total_income_target=Decimal("45000.00"),
        total_expense_target=Decimal("35000.00"),
        savings_target=Decimal("10000.00"),
        status="active"
    )
    session.add(budget)
    session.flush()
    
    # Create budget items
    budget_items = [
        BudgetItem(
            budget_id=budget.id,
            category_id=categories[0].id,  # Business Income
            name="Client Services",
            budgeted_amount=Decimal("45000.00"),
            item_type="income",
            is_fixed=False,
            is_essential=True
        ),
        BudgetItem(
            budget_id=budget.id,
            category_id=categories[2].id,  # Office Expenses
            name="Office Operations",
            budgeted_amount=Decimal("5000.00"),
            item_type="expense",
            is_fixed=False,
            is_essential=True
        ),
        BudgetItem(
            budget_id=budget.id,
            category_id=subcategories[0].id,  # Software & SaaS
            name="Software Subscriptions",
            budgeted_amount=Decimal("1200.00"),
            item_type="expense",
            is_fixed=True,
            is_essential=True
        ),
    ]
    
    session.add_all(budget_items)
    
    # Commit all changes
    session.commit()
    print("Seed data created successfully!")


def clear_seed_data(session: Session) -> None:
    """Clear all seed data."""
    
    # Delete in reverse dependency order
    session.query(BudgetItem).delete()
    session.query(Budget).delete()
    session.query(CategorizationRule).delete()
    session.query(Transaction).delete()
    session.query(Account).delete()
    session.query(Category).delete()
    session.query(Institution).delete()
    session.query(User).delete()
    
    session.commit()
    print("Seed data cleared successfully!")