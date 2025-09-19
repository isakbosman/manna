"""Add bookkeeping tables

Revision ID: 008
Revises: 007
Create Date: 2025-01-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    # Create accounting_periods table
    op.create_table('accounting_periods',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('period_name', sa.String(100), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False),  # month, quarter, year
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('is_closed', sa.Boolean(), default=False),
        sa.Column('closing_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closing_journal_entry_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_accounting_periods_user_id'), 'accounting_periods', ['user_id'], unique=False)
    op.create_index(op.f('ix_accounting_periods_start_date'), 'accounting_periods', ['start_date'], unique=False)
    op.create_index(op.f('ix_accounting_periods_end_date'), 'accounting_periods', ['end_date'], unique=False)

    # Create bookkeeping_rules table
    op.create_table('bookkeeping_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rule_name', sa.String(255), nullable=False),
        sa.Column('rule_type', sa.String(50), nullable=False),  # categorization, journal_entry, accrual
        sa.Column('trigger_conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('journal_template', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('priority', sa.Integer(), default=100),
        sa.Column('last_executed', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bookkeeping_rules_user_id'), 'bookkeeping_rules', ['user_id'], unique=False)
    op.create_index(op.f('ix_bookkeeping_rules_is_active'), 'bookkeeping_rules', ['is_active'], unique=False)

    # Create journal_entries table
    op.create_table('journal_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entry_number', sa.String(50), nullable=False),
        sa.Column('entry_date', sa.Date(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('reference', sa.String(100), nullable=True),
        sa.Column('journal_type', sa.String(20), nullable=True),  # general, sales, purchase, etc.
        sa.Column('total_debits', sa.Numeric(15, 2), nullable=False),
        sa.Column('total_credits', sa.Numeric(15, 2), nullable=False),
        sa.Column('is_balanced', sa.Boolean(), default=True),
        sa.Column('is_posted', sa.Boolean(), default=False),
        sa.Column('posting_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_type', sa.String(50), nullable=True),  # plaid_sync, manual, recurring
        sa.Column('automation_rule_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['period_id'], ['accounting_periods.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['automation_rule_id'], ['bookkeeping_rules.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('entry_number')
    )
    op.create_index(op.f('ix_journal_entries_user_id'), 'journal_entries', ['user_id'], unique=False)
    op.create_index(op.f('ix_journal_entries_entry_date'), 'journal_entries', ['entry_date'], unique=False)
    op.create_index(op.f('ix_journal_entries_period_id'), 'journal_entries', ['period_id'], unique=False)
    op.create_index(op.f('ix_journal_entries_is_posted'), 'journal_entries', ['is_posted'], unique=False)

    # Create journal_entry_lines table
    op.create_table('journal_entry_lines',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('journal_entry_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chart_account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('debit_amount', sa.Numeric(15, 2), default=0.00),
        sa.Column('credit_amount', sa.Numeric(15, 2), default=0.00),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('tax_category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['journal_entry_id'], ['journal_entries.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chart_account_id'], ['chart_of_accounts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tax_category_id'], ['tax_categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_journal_entry_lines_journal_entry_id'), 'journal_entry_lines', ['journal_entry_id'], unique=False)
    op.create_index(op.f('ix_journal_entry_lines_transaction_id'), 'journal_entry_lines', ['transaction_id'], unique=False)

    # Create reconciliation_records table
    op.create_table('reconciliation_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reconciliation_date', sa.Date(), nullable=False),
        sa.Column('statement_balance', sa.Numeric(15, 2), nullable=True),
        sa.Column('book_balance', sa.Numeric(15, 2), nullable=True),
        sa.Column('adjusted_balance', sa.Numeric(15, 2), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),  # pending, reconciled, discrepancy
        sa.Column('reconciled_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('discrepancy_amount', sa.Numeric(15, 2), default=0.00),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reconciled_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reconciliation_records_account_id'), 'reconciliation_records', ['account_id'], unique=False)
    op.create_index(op.f('ix_reconciliation_records_reconciliation_date'), 'reconciliation_records', ['reconciliation_date'], unique=False)
    op.create_index(op.f('ix_reconciliation_records_status'), 'reconciliation_records', ['status'], unique=False)

    # Create reconciliation_items table for matching transactions
    op.create_table('reconciliation_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('reconciliation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('statement_date', sa.Date(), nullable=False),
        sa.Column('statement_description', sa.String(255), nullable=True),
        sa.Column('statement_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('is_matched', sa.Boolean(), default=False),
        sa.Column('match_confidence', sa.Numeric(5, 4), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['reconciliation_id'], ['reconciliation_records.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reconciliation_items_reconciliation_id'), 'reconciliation_items', ['reconciliation_id'], unique=False)
    op.create_index(op.f('ix_reconciliation_items_is_matched'), 'reconciliation_items', ['is_matched'], unique=False)

    # Create transaction_patterns table for ML pattern recognition
    op.create_table('transaction_patterns',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pattern_type', sa.String(50), nullable=False),  # recurring, seasonal, anomaly
        sa.Column('pattern_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('confidence_score', sa.Numeric(5, 4), nullable=False),
        sa.Column('last_occurrence', sa.Date(), nullable=True),
        sa.Column('next_expected', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transaction_patterns_user_id'), 'transaction_patterns', ['user_id'], unique=False)
    op.create_index(op.f('ix_transaction_patterns_pattern_type'), 'transaction_patterns', ['pattern_type'], unique=False)


def downgrade():
    # Drop tables in reverse order of dependencies
    op.drop_table('transaction_patterns')
    op.drop_table('reconciliation_items')
    op.drop_table('reconciliation_records')
    op.drop_table('journal_entry_lines')
    op.drop_table('journal_entries')
    op.drop_table('bookkeeping_rules')
    op.drop_table('accounting_periods')