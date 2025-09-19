"""Add tax categorization system tables

Revision ID: 004
Revises: 20250918_0600_upgrade_to_aes256_gcm
Create Date: 2025-09-18 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '20250918_0600_upgrade_to_aes256_gcm'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add tax categorization system tables."""

    # Create chart_of_accounts table
    op.create_table('chart_of_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_code', sa.String(length=20), nullable=False),
        sa.Column('account_name', sa.String(length=255), nullable=False),
        sa.Column('account_type', sa.String(length=50), nullable=False),
        sa.Column('parent_account_id', postgresql.UUID(as_uuid=True)),
        sa.Column('description', sa.Text()),
        sa.Column('normal_balance', sa.String(length=10), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_system_account', sa.Boolean(), nullable=False, default=False),
        sa.Column('current_balance', sa.Numeric(precision=15, scale=2), default=0.00),
        sa.Column('tax_category', sa.String(length=100)),
        sa.Column('tax_line_mapping', sa.String(length=100)),
        sa.Column('requires_1099', sa.Boolean(), default=False),
        sa.Column('account_metadata', postgresql.JSONB(), default={}),
        sa.CheckConstraint("account_type IN ('asset', 'liability', 'equity', 'revenue', 'expense', 'contra_asset', 'contra_liability', 'contra_equity')", name='ck_account_type'),
        sa.CheckConstraint("normal_balance IN ('debit', 'credit')", name='ck_normal_balance'),
        sa.ForeignKeyConstraint(['parent_account_id'], ['chart_of_accounts.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'account_code', name='uq_user_account_code')
    )
    op.create_index('idx_chart_of_accounts_code', 'chart_of_accounts', ['account_code'])
    op.create_index('idx_chart_of_accounts_type', 'chart_of_accounts', ['account_type', 'is_active'])
    op.create_index('idx_chart_of_accounts_user', 'chart_of_accounts', ['user_id', 'is_active'])
    op.create_index('idx_chart_of_accounts_parent', 'chart_of_accounts', ['parent_account_id'])

    # Create tax_categories table
    op.create_table('tax_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('category_code', sa.String(length=20), nullable=False),
        sa.Column('category_name', sa.String(length=255), nullable=False),
        sa.Column('tax_form', sa.String(length=50), nullable=False),
        sa.Column('tax_line', sa.String(length=100)),
        sa.Column('description', sa.Text()),
        sa.Column('deduction_type', sa.String(length=50)),
        sa.Column('percentage_limit', sa.Numeric(precision=5, scale=2)),
        sa.Column('dollar_limit', sa.Numeric(precision=15, scale=2)),
        sa.Column('carryover_allowed', sa.Boolean(), default=False),
        sa.Column('documentation_required', sa.Boolean(), default=False),
        sa.Column('is_business_expense', sa.Boolean(), default=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('expiration_date', sa.Date()),
        sa.Column('irs_reference', sa.String(length=100)),
        sa.Column('keywords', postgresql.JSONB(), default=[]),
        sa.Column('exclusions', postgresql.JSONB(), default=[]),
        sa.Column('special_rules', postgresql.JSONB(), default={}),
        sa.CheckConstraint("deduction_type IN ('ordinary', 'capital', 'itemized', 'above_line', 'business')", name='ck_deduction_type'),
        sa.CheckConstraint("tax_form IN ('Schedule C', 'Schedule E', 'Form 8829', 'Form 4562', 'Schedule A')", name='ck_tax_form'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('category_code', name='uq_tax_category_code')
    )
    op.create_index('idx_tax_categories_code', 'tax_categories', ['category_code'])
    op.create_index('idx_tax_categories_form', 'tax_categories', ['tax_form', 'is_active'])
    op.create_index('idx_tax_categories_business', 'tax_categories', ['is_business_expense', 'is_active'])
    op.create_index('idx_tax_categories_effective', 'tax_categories', ['effective_date', 'expiration_date'])

    # Create business_expense_tracking table
    op.create_table('business_expense_tracking',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_purpose', sa.Text()),
        sa.Column('business_percentage', sa.Numeric(precision=5, scale=2), default=100.00),
        sa.Column('receipt_required', sa.Boolean(), default=False),
        sa.Column('receipt_attached', sa.Boolean(), default=False),
        sa.Column('receipt_url', sa.String(length=500)),
        sa.Column('mileage_start_location', sa.String(length=255)),
        sa.Column('mileage_end_location', sa.String(length=255)),
        sa.Column('miles_driven', sa.Numeric(precision=8, scale=2)),
        sa.Column('vehicle_info', postgresql.JSONB(), default={}),
        sa.Column('depreciation_method', sa.String(length=50)),
        sa.Column('depreciation_years', sa.Integer()),
        sa.Column('section_179_eligible', sa.Boolean(), default=False),
        sa.Column('substantiation_notes', sa.Text()),
        sa.Column('audit_trail', postgresql.JSONB(), default=[]),
        sa.CheckConstraint("business_percentage >= 0 AND business_percentage <= 100", name='ck_business_percentage'),
        sa.CheckConstraint("miles_driven >= 0", name='ck_miles_positive'),
        sa.CheckConstraint("depreciation_years > 0", name='ck_depreciation_years_positive'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_id', name='uq_transaction_business_expense')
    )
    op.create_index('idx_business_expense_transaction', 'business_expense_tracking', ['transaction_id'])
    op.create_index('idx_business_expense_user', 'business_expense_tracking', ['user_id'])
    op.create_index('idx_business_expense_receipt', 'business_expense_tracking', ['receipt_required', 'receipt_attached'])

    # Create category_mappings table
    op.create_table('category_mappings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_category_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chart_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tax_category_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=4), default=1.0000),
        sa.Column('is_user_defined', sa.Boolean(), default=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('expiration_date', sa.Date()),
        sa.Column('business_percentage_default', sa.Numeric(precision=5, scale=2), default=100.00),
        sa.Column('always_require_receipt', sa.Boolean(), default=False),
        sa.Column('auto_substantiation_rules', postgresql.JSONB(), default={}),
        sa.Column('mapping_notes', sa.Text()),
        sa.CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name='ck_confidence_score'),
        sa.CheckConstraint("business_percentage_default >= 0 AND business_percentage_default <= 100", name='ck_default_business_percentage'),
        sa.ForeignKeyConstraint(['chart_account_id'], ['chart_of_accounts.id']),
        sa.ForeignKeyConstraint(['source_category_id'], ['categories.id']),
        sa.ForeignKeyConstraint(['tax_category_id'], ['tax_categories.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'source_category_id', 'effective_date', name='uq_user_category_mapping')
    )
    op.create_index('idx_category_mappings_source', 'category_mappings', ['source_category_id', 'is_active'])
    op.create_index('idx_category_mappings_user', 'category_mappings', ['user_id', 'is_active'])
    op.create_index('idx_category_mappings_tax', 'category_mappings', ['tax_category_id'])
    op.create_index('idx_category_mappings_effective', 'category_mappings', ['effective_date', 'expiration_date'])

    # Create categorization_audit table
    op.create_table('categorization_audit',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('old_category_id', postgresql.UUID(as_uuid=True)),
        sa.Column('new_category_id', postgresql.UUID(as_uuid=True)),
        sa.Column('old_tax_category_id', postgresql.UUID(as_uuid=True)),
        sa.Column('new_tax_category_id', postgresql.UUID(as_uuid=True)),
        sa.Column('old_chart_account_id', postgresql.UUID(as_uuid=True)),
        sa.Column('new_chart_account_id', postgresql.UUID(as_uuid=True)),
        sa.Column('reason', sa.String(length=255)),
        sa.Column('confidence_before', sa.Numeric(precision=5, scale=4)),
        sa.Column('confidence_after', sa.Numeric(precision=5, scale=4)),
        sa.Column('automated', sa.Boolean(), default=False),
        sa.Column('ml_model_version', sa.String(length=50)),
        sa.Column('processing_time_ms', sa.Integer()),
        sa.Column('audit_metadata', postgresql.JSONB(), default={}),
        sa.CheckConstraint("action_type IN ('categorize', 'recategorize', 'tax_categorize', 'chart_assign', 'bulk_update')", name='ck_action_type'),
        sa.ForeignKeyConstraint(['chart_account_id'], ['chart_of_accounts.id']),
        sa.ForeignKeyConstraint(['new_category_id'], ['categories.id']),
        sa.ForeignKeyConstraint(['new_chart_account_id'], ['chart_of_accounts.id']),
        sa.ForeignKeyConstraint(['new_tax_category_id'], ['tax_categories.id']),
        sa.ForeignKeyConstraint(['old_category_id'], ['categories.id']),
        sa.ForeignKeyConstraint(['old_chart_account_id'], ['chart_of_accounts.id']),
        sa.ForeignKeyConstraint(['old_tax_category_id'], ['tax_categories.id']),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_categorization_audit_transaction', 'categorization_audit', ['transaction_id'])
    op.create_index('idx_categorization_audit_user', 'categorization_audit', ['user_id', 'created_at'])
    op.create_index('idx_categorization_audit_action', 'categorization_audit', ['action_type', 'created_at'])
    op.create_index('idx_categorization_audit_automated', 'categorization_audit', ['automated', 'created_at'])

    # Add new columns to transactions table
    op.add_column('transactions', sa.Column('chart_account_id', postgresql.UUID(as_uuid=True)))
    op.add_column('transactions', sa.Column('tax_category_id', postgresql.UUID(as_uuid=True)))
    op.add_column('transactions', sa.Column('schedule_c_line', sa.String(length=50)))
    op.add_column('transactions', sa.Column('business_use_percentage', sa.Numeric(precision=5, scale=2), default=0.00))
    op.add_column('transactions', sa.Column('deductible_amount', sa.Numeric(precision=15, scale=2)))
    op.add_column('transactions', sa.Column('requires_substantiation', sa.Boolean(), default=False))
    op.add_column('transactions', sa.Column('substantiation_complete', sa.Boolean(), default=False))
    op.add_column('transactions', sa.Column('tax_notes', sa.Text()))

    # Add foreign key constraints for new columns
    op.create_foreign_key('fk_transactions_chart_account', 'transactions', 'chart_of_accounts', ['chart_account_id'], ['id'])
    op.create_foreign_key('fk_transactions_tax_category', 'transactions', 'tax_categories', ['tax_category_id'], ['id'])

    # Add indexes for new columns
    op.create_index('idx_transactions_chart_account', 'transactions', ['chart_account_id'])
    op.create_index('idx_transactions_tax_category', 'transactions', ['tax_category_id'])
    op.create_index('idx_transactions_schedule_c', 'transactions', ['schedule_c_line'])
    op.create_index('idx_transactions_substantiation', 'transactions', ['requires_substantiation', 'substantiation_complete'])
    op.create_index('idx_transactions_deductible', 'transactions', ['is_tax_deductible', 'tax_year', 'deductible_amount'])

    # Add check constraints for new columns
    op.create_check_constraint(
        'ck_business_use_percentage',
        'transactions',
        'business_use_percentage >= 0 AND business_use_percentage <= 100'
    )


def downgrade() -> None:
    """Remove tax categorization system tables and columns."""

    # Drop indexes first
    op.drop_index('idx_transactions_deductible', 'transactions')
    op.drop_index('idx_transactions_substantiation', 'transactions')
    op.drop_index('idx_transactions_schedule_c', 'transactions')
    op.drop_index('idx_transactions_tax_category', 'transactions')
    op.drop_index('idx_transactions_chart_account', 'transactions')

    # Drop foreign key constraints
    op.drop_constraint('fk_transactions_tax_category', 'transactions', type_='foreignkey')
    op.drop_constraint('fk_transactions_chart_account', 'transactions', type_='foreignkey')

    # Drop check constraints
    op.drop_constraint('ck_business_use_percentage', 'transactions', type_='check')

    # Drop new columns from transactions table
    op.drop_column('transactions', 'tax_notes')
    op.drop_column('transactions', 'substantiation_complete')
    op.drop_column('transactions', 'requires_substantiation')
    op.drop_column('transactions', 'deductible_amount')
    op.drop_column('transactions', 'business_use_percentage')
    op.drop_column('transactions', 'schedule_c_line')
    op.drop_column('transactions', 'tax_category_id')
    op.drop_column('transactions', 'chart_account_id')

    # Drop tables in reverse order
    op.drop_table('categorization_audit')
    op.drop_table('category_mappings')
    op.drop_table('business_expense_tracking')
    op.drop_table('tax_categories')
    op.drop_table('chart_of_accounts')