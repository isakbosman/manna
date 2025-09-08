"""Add reporting and webhook tables

Revision ID: 003
Revises: 002
Create Date: 2024-09-08 12:02:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add reporting, budget, and webhook tables."""
    
    # Create reports table
    op.create_table('reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('report_type', sa.String(length=50), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fiscal_year', sa.Integer()),
        sa.Column('fiscal_quarter', sa.Integer()),
        sa.Column('is_business_report', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_tax_report', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_preliminary', sa.Boolean(), nullable=False, default=True),
        sa.Column('generation_status', sa.String(length=20), default='pending'),
        sa.Column('generated_at', sa.DateTime(timezone=True)),
        sa.Column('generation_duration_ms', sa.Integer()),
        sa.Column('report_data', postgresql.JSONB(), nullable=False),
        sa.Column('summary_metrics', postgresql.JSONB(), default={}),
        sa.Column('chart_data', postgresql.JSONB(), default={}),
        sa.Column('file_path', sa.String(length=500)),
        sa.Column('file_format', sa.String(length=20), default='json'),
        sa.Column('file_size_bytes', sa.Integer()),
        sa.Column('template_id', sa.String(length=100)),
        sa.Column('filters', postgresql.JSONB(), default={}),
        sa.Column('groupings', postgresql.JSONB(), default=[]),
        sa.Column('is_shared', sa.Boolean(), default=False),
        sa.Column('share_token', sa.String(length=255)),
        sa.Column('share_expires_at', sa.DateTime(timezone=True)),
        sa.Column('access_level', sa.String(length=20), default='private'),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('parent_report_id', postgresql.UUID(as_uuid=True)),
        sa.Column('is_archived', sa.Boolean(), default=False),
        sa.Column('error_code', sa.String(length=50)),
        sa.Column('error_message', sa.Text()),
        sa.Column('tags', postgresql.JSONB(), default=[]),
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.CheckConstraint("access_level IN ('private', 'shared', 'public')", name='ck_access_level'),
        sa.CheckConstraint("file_format IN ('json', 'pdf', 'excel', 'csv', 'html')", name='ck_file_format'),
        sa.CheckConstraint("fiscal_quarter >= 1 AND fiscal_quarter <= 4", name='ck_fiscal_quarter'),
        sa.CheckConstraint("generation_status IN ('pending', 'generating', 'completed', 'failed', 'cancelled')", name='ck_generation_status'),
        sa.CheckConstraint("period_end >= period_start", name='ck_valid_period'),
        sa.CheckConstraint("report_type IN ('profit_loss', 'balance_sheet', 'cash_flow', 'owner_package', 'tax_summary', 'budget_vs_actual', 'expense_analysis', 'income_analysis', 'custom')", name='ck_report_type'),
        sa.CheckConstraint("version > 0", name='ck_positive_version'),
        sa.ForeignKeyConstraint(['parent_report_id'], ['reports.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_reports_business', 'reports', ['is_business_report', 'user_id'])
    op.create_index('idx_reports_fiscal', 'reports', ['fiscal_year', 'fiscal_quarter'])
    op.create_index('idx_reports_period', 'reports', ['period_start', 'period_end'])
    op.create_index('idx_reports_shared', 'reports', ['is_shared', 'share_expires_at'])
    op.create_index('idx_reports_status', 'reports', ['generation_status', 'generated_at'])
    op.create_index('idx_reports_user_type', 'reports', ['user_id', 'report_type'])
    op.create_index('idx_reports_version', 'reports', ['parent_report_id', 'version'])
    op.create_index(op.f('ix_reports_fiscal_year'), 'reports', ['fiscal_year'])
    op.create_index(op.f('ix_reports_share_token'), 'reports', ['share_token'], unique=True)
    op.create_index(op.f('ix_reports_user_id'), 'reports', ['user_id'])
    
    # Create budgets table
    op.create_table('budgets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('budget_type', sa.String(length=20), default='monthly'),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_business_budget', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_template', sa.Boolean(), default=False),
        sa.Column('total_income_target', sa.Numeric(precision=15, scale=2), default=0),
        sa.Column('total_expense_target', sa.Numeric(precision=15, scale=2), default=0),
        sa.Column('savings_target', sa.Numeric(precision=15, scale=2), default=0),
        sa.Column('status', sa.String(length=20), default='draft'),
        sa.Column('last_reviewed', sa.DateTime(timezone=True)),
        sa.Column('alert_threshold', sa.Numeric(precision=3, scale=2), default=0.8),
        sa.Column('enable_alerts', sa.Boolean(), default=True),
        sa.Column('tags', postgresql.JSONB(), default=[]),
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.CheckConstraint("alert_threshold > 0 AND alert_threshold <= 1", name='ck_alert_threshold_range'),
        sa.CheckConstraint("budget_type IN ('monthly', 'quarterly', 'annual', 'custom')", name='ck_budget_type'),
        sa.CheckConstraint("period_end > period_start", name='ck_valid_budget_period'),
        sa.CheckConstraint("status IN ('draft', 'active', 'completed', 'archived')", name='ck_budget_status'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', 'period_start', name='uq_user_budget_period')
    )
    op.create_index('idx_budgets_business', 'budgets', ['is_business_budget', 'user_id'])
    op.create_index('idx_budgets_period', 'budgets', ['period_start', 'period_end'])
    op.create_index('idx_budgets_status', 'budgets', ['status', 'is_active'])
    op.create_index('idx_budgets_type', 'budgets', ['budget_type', 'is_active'])
    op.create_index('idx_budgets_user_active', 'budgets', ['user_id', 'is_active'])
    
    # Create budget_items table
    op.create_table('budget_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('budget_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('budgeted_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('actual_amount', sa.Numeric(precision=15, scale=2), default=0),
        sa.Column('item_type', sa.String(length=20), default='expense'),
        sa.Column('is_fixed', sa.Boolean(), default=False),
        sa.Column('is_essential', sa.Boolean(), default=True),
        sa.Column('alert_threshold', sa.Numeric(precision=3, scale=2)),
        sa.Column('last_updated', sa.DateTime(timezone=True)),
        sa.Column('allow_rollover', sa.Boolean(), default=False),
        sa.Column('rollover_amount', sa.Numeric(precision=15, scale=2), default=0),
        sa.Column('notes', sa.Text()),
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.CheckConstraint("alert_threshold IS NULL OR (alert_threshold > 0 AND alert_threshold <= 1)", name='ck_item_alert_threshold_range'),
        sa.CheckConstraint("budgeted_amount >= 0", name='ck_budgeted_amount_positive'),
        sa.CheckConstraint("item_type IN ('income', 'expense', 'savings', 'transfer')", name='ck_budget_item_type'),
        sa.ForeignKeyConstraint(['budget_id'], ['budgets.id']),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('budget_id', 'category_id', name='uq_budget_category')
    )
    op.create_index('idx_budget_items_budget', 'budget_items', ['budget_id'])
    op.create_index('idx_budget_items_category', 'budget_items', ['category_id'])
    op.create_index('idx_budget_items_essential', 'budget_items', ['is_essential'])
    op.create_index('idx_budget_items_type', 'budget_items', ['item_type', 'is_fixed'])
    
    # Create plaid_webhooks table
    op.create_table('plaid_webhooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('plaid_item_id', postgresql.UUID(as_uuid=True)),
        sa.Column('webhook_type', sa.String(length=50), nullable=False),
        sa.Column('webhook_code', sa.String(length=50), nullable=False),
        sa.Column('plaid_item_id_raw', sa.String(length=255)),
        sa.Column('plaid_environment', sa.String(length=20), default='production'),
        sa.Column('event_data', postgresql.JSONB(), nullable=False),
        sa.Column('new_transactions', sa.Integer(), default=0),
        sa.Column('modified_transactions', sa.Integer(), default=0),
        sa.Column('removed_transactions', sa.Integer(), default=0),
        sa.Column('processing_status', sa.String(length=20), default='pending'),
        sa.Column('processed_at', sa.DateTime(timezone=True)),
        sa.Column('processing_duration_ms', sa.Integer()),
        sa.Column('error_code', sa.String(length=50)),
        sa.Column('error_message', sa.Text()),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('max_retries', sa.Integer(), default=3),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_agent', sa.String(length=500)),
        sa.Column('source_ip', sa.String(length=45)),
        sa.Column('webhook_hash', sa.String(length=64)),
        sa.Column('is_duplicate', sa.Boolean(), default=False),
        sa.Column('original_webhook_id', postgresql.UUID(as_uuid=True)),
        sa.CheckConstraint("plaid_environment IN ('sandbox', 'development', 'production')", name='ck_plaid_environment'),
        sa.CheckConstraint("processing_status IN ('pending', 'processing', 'completed', 'failed', 'ignored')", name='ck_processing_status'),
        sa.CheckConstraint("retry_count >= 0 AND retry_count <= max_retries", name='ck_retry_count'),
        sa.CheckConstraint("webhook_type IN ('TRANSACTIONS', 'AUTH', 'IDENTITY', 'ASSETS', 'HOLDINGS', 'ITEM', 'INCOME', 'LIABILITIES')", name='ck_webhook_type'),
        sa.ForeignKeyConstraint(['original_webhook_id'], ['plaid_webhooks.id']),
        sa.ForeignKeyConstraint(['plaid_item_id'], ['plaid_items.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_webhooks_duplicate', 'plaid_webhooks', ['is_duplicate', 'webhook_hash'])
    op.create_index('idx_webhooks_environment', 'plaid_webhooks', ['plaid_environment'])
    op.create_index('idx_webhooks_item', 'plaid_webhooks', ['plaid_item_id', 'received_at'])
    op.create_index('idx_webhooks_retry', 'plaid_webhooks', ['retry_count', 'processing_status'])
    op.create_index('idx_webhooks_status', 'plaid_webhooks', ['processing_status', 'received_at'])
    op.create_index('idx_webhooks_type_code', 'plaid_webhooks', ['webhook_type', 'webhook_code'])
    op.create_index(op.f('ix_plaid_webhooks_plaid_item_id_raw'), 'plaid_webhooks', ['plaid_item_id_raw'])
    op.create_index(op.f('ix_plaid_webhooks_webhook_hash'), 'plaid_webhooks', ['webhook_hash'], unique=True)
    
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('session_id', postgresql.UUID(as_uuid=True)),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=100)),
        sa.Column('old_values', postgresql.JSONB()),
        sa.Column('new_values', postgresql.JSONB()),
        sa.Column('changes_summary', sa.Text()),
        sa.Column('event_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source', sa.String(length=50), default='web_app'),
        sa.Column('user_agent', sa.String(length=500)),
        sa.Column('ip_address', postgresql.INET()),
        sa.Column('request_id', sa.String(length=100)),
        sa.Column('endpoint', sa.String(length=200)),
        sa.Column('http_method', sa.String(length=10)),
        sa.Column('status_code', sa.Integer()),
        sa.Column('business_impact', sa.String(length=20), default='low'),
        sa.Column('compliance_relevant', sa.Boolean(), default=False),
        sa.Column('financial_impact', sa.Boolean(), default=False),
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.Column('tags', postgresql.JSONB(), default=[]),
        sa.Column('error_code', sa.String(length=50)),
        sa.Column('error_message', sa.Text()),
        sa.ForeignKeyConstraint(['session_id'], ['user_sessions.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_logs_action_resource', 'audit_logs', ['action', 'resource_type'])
    op.create_index('idx_audit_logs_business_impact', 'audit_logs', ['business_impact', 'event_timestamp'])
    op.create_index('idx_audit_logs_compliance', 'audit_logs', ['compliance_relevant', 'event_timestamp'])
    op.create_index('idx_audit_logs_financial', 'audit_logs', ['financial_impact', 'event_timestamp'])
    op.create_index('idx_audit_logs_ip', 'audit_logs', ['ip_address'])
    op.create_index('idx_audit_logs_request', 'audit_logs', ['request_id'])
    op.create_index('idx_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_logs_source_time', 'audit_logs', ['source', 'event_timestamp'])
    op.create_index('idx_audit_logs_user_time', 'audit_logs', ['user_id', 'event_timestamp'])
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'])
    op.create_index(op.f('ix_audit_logs_event_timestamp'), 'audit_logs', ['event_timestamp'])
    op.create_index(op.f('ix_audit_logs_resource_type'), 'audit_logs', ['resource_type'])
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'])


def downgrade() -> None:
    """Remove reporting and webhook tables."""
    
    op.drop_table('audit_logs')
    op.drop_table('plaid_webhooks')
    op.drop_table('budget_items')
    op.drop_table('budgets')
    op.drop_table('reports')