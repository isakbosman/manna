"""seed initial data

Revision ID: seed_001
Revises: 003
Create Date: 2025-09-18 04:30:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime, timezone
import bcrypt
import uuid

# revision identifiers, used by Alembic.
revision: str = "seed_001"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def generate_password_hash(password: str) -> str:
    """Generate a bcrypt password hash."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def upgrade() -> None:
    """Add initial seed data."""

    # Create a connection for executing raw SQL
    conn = op.get_bind()

    # Generate UUIDs for initial data
    demo_user_id = str(uuid.uuid4())

    # Insert initial demo user
    conn.execute(
        sa.text(
            """
        INSERT INTO users (
            id, email, username, hashed_password, is_active, is_superuser, is_verified,
            full_name, created_at, updated_at
        ) VALUES (
            :id, :email, :username, :hashed_password, :is_active, :is_superuser, :is_verified,
            :full_name, :created_at, :updated_at
        )
        ON CONFLICT (email) DO NOTHING
        """
        ),
        {
            "id": demo_user_id,
            "email": "isak@avidware.ai",
            "username": "isak",
            "hashed_password": generate_password_hash("Demo123!"),
            "is_active": True,
            "is_superuser": False,
            "is_verified": True,
            "full_name": "Isak Demo User",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
    )

    # Insert initial categories (income categories)
    income_categories = [
        ("Sales Revenue", "Revenue from product sales", "Income"),
        ("Service Revenue", "Revenue from services", "Income"),
        ("Consulting Revenue", "Revenue from consulting", "Income"),
        ("Investment Income", "Income from investments", "Income"),
        ("Interest Income", "Interest earned", "Income"),
        ("Other Income", "Miscellaneous income", "Income"),
    ]

    for name, description, parent_category in income_categories:
        category_id = str(uuid.uuid4())
        conn.execute(
            sa.text(
                """
            INSERT INTO categories (
                id, user_id, name, description, parent_category,
                is_system, is_active, created_at, updated_at
            ) VALUES (
                :id, :user_id, :name, :description, :parent_category,
                true, true, :created_at, :updated_at
            )
            """
            ),
            {
                "id": category_id,
                "user_id": None,  # System categories don't belong to a specific user
                "name": name,
                "description": description,
                "parent_category": parent_category,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            },
        )

    # Insert expense categories
    expense_categories = [
        # Business expenses
        ("Office Supplies", "Office supplies and materials", "Expense"),
        ("Software & Subscriptions", "Software licenses and subscriptions", "Expense"),
        ("Professional Services", "Legal, accounting, consulting", "Expense"),
        ("Marketing & Advertising", "Marketing and advertising costs", "Expense"),
        ("Travel - Business", "Business travel expenses", "Expense"),
        ("Meals & Entertainment", "Business meals and entertainment", "Expense"),
        ("Equipment", "Business equipment and tools", "Expense"),
        ("Insurance", "Business insurance premiums", "Expense"),
        ("Rent & Utilities", "Office rent and utilities", "Expense"),
        ("Payroll", "Employee salaries and wages", "Expense"),
        ("Contractor Payments", "Payments to contractors", "Expense"),
        ("Bank Fees", "Banking and financial fees", "Expense"),
        # Personal expenses
        ("Food & Dining", "Personal meals and restaurants", "Expense"),
        ("Transportation", "Personal transportation costs", "Expense"),
        ("Shopping", "Personal shopping and retail", "Expense"),
        ("Entertainment", "Personal entertainment", "Expense"),
        ("Healthcare", "Medical and health expenses", "Expense"),
        ("Housing", "Personal rent/mortgage", "Expense"),
        ("Personal Care", "Personal care and grooming", "Expense"),
        ("Education", "Education and learning", "Expense"),
    ]

    for name, description, parent_category in expense_categories:
        category_id = str(uuid.uuid4())
        conn.execute(
            sa.text(
                """
            INSERT INTO categories (
                id, user_id, name, description, parent_category,
                is_system, is_active, created_at, updated_at
            ) VALUES (
                :id, :user_id, :name, :description, :parent_category,
                true, true, :created_at, :updated_at
            )
            """
            ),
            {
                "id": category_id,
                "user_id": None,
                "name": name,
                "description": description,
                "parent_category": parent_category,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            },
        )

    # Insert transfer/other categories
    other_categories = [
        ("Transfer In", "Money transferred in", "Transfer"),
        ("Transfer Out", "Money transferred out", "Transfer"),
        ("Credit Card Payment", "Credit card payments", "Transfer"),
        ("Loan Payment", "Loan payments", "Other"),
        ("Owner Draw", "Owner withdrawals", "Other"),
        ("Owner Investment", "Owner capital contributions", "Other"),
        ("Uncategorized", "Uncategorized transactions", "Other"),
    ]

    for name, description, parent_category in other_categories:
        category_id = str(uuid.uuid4())
        conn.execute(
            sa.text(
                """
            INSERT INTO categories (
                id, user_id, name, description, parent_category,
                is_system, is_active, created_at, updated_at
            ) VALUES (
                :id, :user_id, :name, :description, :parent_category,
                true, true, :created_at, :updated_at
            )
            """
            ),
            {
                "id": category_id,
                "user_id": None,
                "name": name,
                "description": description,
                "parent_category": parent_category,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            },
        )

    print("✅ Initial seed data added successfully!")
    print("   - Demo user: isak@avidware.ai (password: Demo123!)")
    print(f"   - {len(income_categories)} income categories")
    print(f"   - {len(expense_categories)} expense categories")
    print(f"   - {len(other_categories)} other categories")


def downgrade() -> None:
    """Remove seed data."""
    conn = op.get_bind()

    # Delete seeded categories (only system categories)
    conn.execute(sa.text("DELETE FROM categories WHERE is_system = true"))

    # Delete demo user
    conn.execute(sa.text("DELETE FROM users WHERE email = 'isak@avidware.ai'"))

    print("✅ Seed data removed successfully!")
