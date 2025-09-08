"""Add transaction and ML tables

Revision ID: 002
Revises: 001
Create Date: 2024-09-08 12:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add transaction and ML-related tables."""
    
    # Create transactions table
    op.create_table('transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plaid_transaction_id', sa.String(length=255)),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('transaction_type', sa.String(length=10), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('posted_date', sa.DateTime(timezone=True)),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('merchant_name', sa.String(length=255)),
        sa.Column('description', sa.Text()),
        sa.Column('is_pending', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_recurring', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_transfer', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_fee', sa.Boolean(), nullable=False, default=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True)),
        sa.Column('subcategory', sa.String(length=100)),
        sa.Column('user_category_override', sa.String(length=100)),
        sa.Column('is_business', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_tax_deductible', sa.Boolean(), nullable=False, default=False),
        sa.Column('tax_year', sa.Integer()),
        sa.Column('location_address', sa.String(length=500)),
        sa.Column('location_city', sa.String(length=100)),
        sa.Column('location_region', sa.String(length=100)),
        sa.Column('location_postal_code', sa.String(length=20)),
        sa.Column('location_country', sa.String(length=3), default='US'),
        sa.Column('location_coordinates', postgresql.JSONB()),
        sa.Column('payment_method', sa.String(length=50)),
        sa.Column('payment_channel', sa.String(length=50)),
        sa.Column('account_number_masked', sa.String(length=20)),
        sa.Column('contra_transaction_id', postgresql.UUID(as_uuid=True)),
        sa.Column('journal_entry_id', postgresql.UUID(as_uuid=True)),
        sa.Column('is_reconciled', sa.Boolean(), nullable=False, default=False),
        sa.Column('reconciled_date', sa.DateTime(timezone=True)),
        sa.Column('reconciled_by', sa.String(length=255)),
        sa.Column('notes', sa.Text()),
        sa.Column('tags', postgresql.JSONB(), default=[]),
        sa.Column('attachments', postgresql.JSONB(), default=[]),
        sa.Column('plaid_metadata', postgresql.JSONB(), default={}),
        sa.Column('processing_status', sa.String(length=20), default='processed'),
        sa.Column('error_details', sa.Text()),
        sa.CheckConstraint("amount > 0", name='ck_amount_positive'),
        sa.CheckConstraint("processing_status IN ('processed', 'pending', 'error', 'manual_review')", name='ck_processing_status'),
        sa.CheckConstraint("transaction_type IN ('debit', 'credit')", name='ck_transaction_type'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id']),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
        sa.ForeignKeyConstraint(['contra_transaction_id'], ['transactions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_transactions_account_date', 'transactions', ['account_id', 'date'])
    op.create_index('idx_transactions_amount', 'transactions', ['amount'])
    op.create_index('idx_transactions_business_date', 'transactions', ['is_business', 'date'])
    op.create_index('idx_transactions_category_date', 'transactions', ['category_id', 'date'])
    op.create_index('idx_transactions_journal', 'transactions', ['journal_entry_id'])
    op.create_index('idx_transactions_merchant', 'transactions', ['merchant_name'])
    op.create_index('idx_transactions_pending', 'transactions', ['is_pending', 'date'])
    op.create_index('idx_transactions_reconciled', 'transactions', ['is_reconciled'])
    op.create_index('idx_transactions_tax_year', 'transactions', ['tax_year', 'is_tax_deductible'])
    op.create_index(op.f('ix_transactions_account_id'), 'transactions', ['account_id'])
    op.create_index(op.f('ix_transactions_date'), 'transactions', ['date'])
    op.create_index(op.f('ix_transactions_is_business'), 'transactions', ['is_business'])
    op.create_index(op.f('ix_transactions_plaid_transaction_id'), 'transactions', ['plaid_transaction_id'], unique=True)
    
    # Create ml_predictions table
    op.create_table('ml_predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('probability', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('alternative_predictions', postgresql.JSONB(), default=[]),
        sa.Column('features_used', postgresql.JSONB(), default={}),
        sa.Column('feature_importance', postgresql.JSONB(), default={}),
        sa.Column('prediction_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processing_time_ms', sa.Integer()),
        sa.Column('is_accepted', sa.Boolean()),
        sa.Column('user_feedback', sa.String(length=20)),
        sa.Column('feedback_date', sa.DateTime(timezone=True)),
        sa.Column('is_outlier', sa.Boolean(), default=False),
        sa.Column('requires_review', sa.Boolean(), default=False),
        sa.Column('review_reason', sa.String(length=100)),
        sa.CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name='ck_confidence_range'),
        sa.CheckConstraint("probability >= 0.0 AND probability <= 1.0", name='ck_probability_range'),
        sa.CheckConstraint("user_feedback IN ('correct', 'incorrect', 'partial', 'unsure')", name='ck_user_feedback'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ml_predictions_confidence', 'ml_predictions', ['confidence'])
    op.create_index('idx_ml_predictions_date', 'ml_predictions', ['prediction_date'])
    op.create_index('idx_ml_predictions_feedback', 'ml_predictions', ['user_feedback', 'is_accepted'])
    op.create_index('idx_ml_predictions_model', 'ml_predictions', ['model_version', 'model_type'])
    op.create_index('idx_ml_predictions_review', 'ml_predictions', ['requires_review', 'is_outlier'])
    op.create_index('idx_ml_predictions_transaction', 'ml_predictions', ['transaction_id'])
    
    # Create categorization_rules table
    op.create_table('categorization_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('rule_type', sa.String(length=50), nullable=False),
        sa.Column('pattern', sa.String(length=1000), nullable=False),
        sa.Column('pattern_type', sa.String(length=20), default='contains'),
        sa.Column('case_sensitive', sa.Boolean(), default=False),
        sa.Column('match_fields', postgresql.JSONB(), default=[]),
        sa.Column('conditions', postgresql.JSONB(), default={}),
        sa.Column('priority', sa.Integer(), nullable=False, default=100),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_system_rule', sa.Boolean(), default=False),
        sa.Column('auto_apply', sa.Boolean(), default=True),
        sa.Column('requires_approval', sa.Boolean(), default=False),
        sa.Column('set_business', sa.Boolean()),
        sa.Column('set_tax_deductible', sa.Boolean()),
        sa.Column('match_count', sa.Integer(), default=0),
        sa.Column('last_matched', sa.DateTime(timezone=True)),
        sa.Column('accuracy_score', sa.Integer(), default=0),
        sa.Column('tags', postgresql.JSONB(), default=[]),
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.CheckConstraint("accuracy_score >= -100 AND accuracy_score <= 100", name='ck_accuracy_range'),
        sa.CheckConstraint("pattern_type IN ('contains', 'exact', 'regex', 'starts_with', 'ends_with', 'fuzzy')", name='ck_pattern_type'),
        sa.CheckConstraint("priority >= 0 AND priority <= 1000", name='ck_priority_range'),
        sa.CheckConstraint("rule_type IN ('merchant', 'keyword', 'amount', 'regex', 'compound', 'ml_assisted')", name='ck_rule_type'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_rules_category', 'categorization_rules', ['category_id'])
    op.create_index('idx_rules_pattern', 'categorization_rules', ['pattern'])
    op.create_index('idx_rules_priority', 'categorization_rules', ['priority', 'is_active'])
    op.create_index('idx_rules_system', 'categorization_rules', ['is_system_rule', 'is_active'])
    op.create_index('idx_rules_type', 'categorization_rules', ['rule_type', 'is_active'])
    op.create_index('idx_rules_user_active', 'categorization_rules', ['user_id', 'is_active'])


def downgrade() -> None:
    """Remove transaction and ML tables."""
    
    op.drop_table('categorization_rules')
    op.drop_table('ml_predictions')
    op.drop_table('transactions')