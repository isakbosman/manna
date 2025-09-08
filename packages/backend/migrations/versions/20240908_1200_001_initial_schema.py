"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2024-09-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply initial database schema."""
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('email_verified_at', sa.DateTime(timezone=True)),
        sa.Column('first_name', sa.String(length=100)),
        sa.Column('last_name', sa.String(length=100)),
        sa.Column('phone', sa.String(length=20)),
        sa.Column('timezone', sa.String(length=50), default='UTC'),
        sa.Column('business_name', sa.String(length=255)),
        sa.Column('business_type', sa.String(length=100)),
        sa.Column('tax_id', sa.String(length=20)),
        sa.Column('business_address', postgresql.JSONB()),
        sa.Column('preferences', postgresql.JSONB(), default={}),
        sa.Column('notification_settings', postgresql.JSONB(), default={}),
        sa.Column('last_login', sa.DateTime(timezone=True)),
        sa.Column('failed_login_attempts', sa.String(length=10), default='0'),
        sa.Column('account_locked_until', sa.DateTime(timezone=True)),
        sa.Column('password_reset_token', sa.String(length=255)),
        sa.Column('password_reset_expires', sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_users_email_active', 'users', ['email', 'is_active'])
    op.create_index('idx_users_last_login', 'users', ['last_login'])
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create institutions table
    op.create_table('institutions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('plaid_institution_id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('country_codes', postgresql.JSONB(), default=[]),
        sa.Column('products', postgresql.JSONB(), default=[]),
        sa.Column('routing_numbers', postgresql.JSONB(), default=[]),
        sa.Column('logo', sa.String(length=500)),
        sa.Column('primary_color', sa.String(length=7)),
        sa.Column('url', sa.String(length=500)),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('oauth_required', sa.Boolean(), default=False),
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_institutions_active', 'institutions', ['is_active'])
    op.create_index('idx_institutions_name', 'institutions', ['name'])
    op.create_index(op.f('ix_institutions_plaid_institution_id'), 'institutions', ['plaid_institution_id'], unique=True)
    
    # Create categories table
    op.create_table('categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True)),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('category_type', sa.String(length=20), default='expense'),
        sa.Column('is_business_category', sa.Boolean(), default=False),
        sa.Column('is_tax_deductible', sa.Boolean(), default=False),
        sa.Column('is_system_category', sa.Boolean(), default=False),
        sa.Column('icon', sa.String(length=50)),
        sa.Column('color', sa.String(length=7)),
        sa.Column('sort_order', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_budgetable', sa.Boolean(), default=True),
        sa.Column('default_budget_percentage', sa.Integer()),
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.CheckConstraint("category_type IN ('income', 'expense', 'transfer')", name='ck_category_type'),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'parent_id', 'name', name='uq_category_hierarchy')
    )
    op.create_index('idx_categories_parent', 'categories', ['parent_id'])
    op.create_index('idx_categories_system', 'categories', ['is_system_category', 'is_active'])
    op.create_index('idx_categories_type', 'categories', ['category_type', 'is_active'])
    op.create_index('idx_categories_user_active', 'categories', ['user_id', 'is_active'])
    
    # Create plaid_items table
    op.create_table('plaid_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('institution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plaid_item_id', sa.String(length=255), nullable=False),
        sa.Column('plaid_access_token', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, default='active'),
        sa.Column('error_code', sa.String(length=50)),
        sa.Column('error_message', sa.Text()),
        sa.Column('available_products', postgresql.JSONB(), default=[]),
        sa.Column('billed_products', postgresql.JSONB(), default=[]),
        sa.Column('webhook_url', sa.String(length=500)),
        sa.Column('consent_expiration_time', sa.DateTime(timezone=True)),
        sa.Column('last_successful_sync', sa.DateTime(timezone=True)),
        sa.Column('last_sync_attempt', sa.DateTime(timezone=True)),
        sa.Column('sync_cursor', sa.String(length=255)),
        sa.Column('max_days_back', sa.Integer(), default=730),
        sa.Column('sync_frequency_hours', sa.Integer(), default=6),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('requires_reauth', sa.Boolean(), default=False),
        sa.Column('has_mfa', sa.Boolean(), default=False),
        sa.Column('update_type', sa.String(length=20)),
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.CheckConstraint("max_days_back > 0 AND max_days_back <= 730", name='ck_max_days_back'),
        sa.CheckConstraint("status IN ('active', 'error', 'expired', 'revoked', 'pending')", name='ck_plaid_item_status'),
        sa.CheckConstraint("sync_frequency_hours >= 1 AND sync_frequency_hours <= 168", name='ck_sync_frequency'),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_plaid_items_institution', 'plaid_items', ['institution_id'])
    op.create_index('idx_plaid_items_reauth', 'plaid_items', ['requires_reauth', 'is_active'])
    op.create_index('idx_plaid_items_status', 'plaid_items', ['status', 'last_sync_attempt'])
    op.create_index('idx_plaid_items_user', 'plaid_items', ['user_id', 'is_active'])
    op.create_index(op.f('ix_plaid_items_plaid_item_id'), 'plaid_items', ['plaid_item_id'], unique=True)
    
    # Create accounts table
    op.create_table('accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('institution_id', postgresql.UUID(as_uuid=True)),
        sa.Column('plaid_item_id', postgresql.UUID(as_uuid=True)),
        sa.Column('plaid_account_id', sa.String(length=255)),
        sa.Column('plaid_persistent_id', sa.String(length=255)),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('official_name', sa.String(length=255)),
        sa.Column('account_type', sa.String(length=50), nullable=False),
        sa.Column('account_subtype', sa.String(length=50)),
        sa.Column('is_business', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_manual', sa.Boolean(), nullable=False, default=False),
        sa.Column('current_balance', sa.Numeric(precision=15, scale=2)),
        sa.Column('available_balance', sa.Numeric(precision=15, scale=2)),
        sa.Column('credit_limit', sa.Numeric(precision=15, scale=2)),
        sa.Column('minimum_balance', sa.Numeric(precision=15, scale=2)),
        sa.Column('account_number_masked', sa.String(length=20)),
        sa.Column('routing_number', sa.String(length=20)),
        sa.Column('last_sync', sa.DateTime(timezone=True)),
        sa.Column('sync_status', sa.String(length=20), default='active'),
        sa.Column('error_code', sa.String(length=50)),
        sa.Column('error_message', sa.Text()),
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.CheckConstraint("account_type IN ('checking', 'savings', 'credit', 'investment', 'loan', 'other')", name='ck_account_type'),
        sa.CheckConstraint("sync_status IN ('active', 'error', 'disconnected', 'pending')", name='ck_sync_status'),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id']),
        sa.ForeignKeyConstraint(['plaid_item_id'], ['plaid_items.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_account_name')
    )
    op.create_index('idx_accounts_business', 'accounts', ['is_business', 'is_active'])
    op.create_index('idx_accounts_sync_status', 'accounts', ['sync_status', 'last_sync'])
    op.create_index('idx_accounts_user_type', 'accounts', ['user_id', 'account_type'])
    op.create_index(op.f('ix_accounts_plaid_account_id'), 'accounts', ['plaid_account_id'], unique=True)
    op.create_index(op.f('ix_accounts_plaid_persistent_id'), 'accounts', ['plaid_persistent_id'], unique=True)
    op.create_index(op.f('ix_accounts_user_id'), 'accounts', ['user_id'])
    
    # Create user_sessions table
    op.create_table('user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_token', sa.String(length=255), nullable=False),
        sa.Column('refresh_token', sa.String(length=255)),
        sa.Column('device_info', postgresql.JSONB(), default={}),
        sa.Column('user_agent', sa.String(length=500)),
        sa.Column('ip_address', postgresql.INET()),
        sa.Column('location_info', postgresql.JSONB()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=False),
        sa.Column('login_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('logout_time', sa.DateTime(timezone=True)),
        sa.Column('logout_reason', sa.String(length=50)),
        sa.Column('is_suspicious', sa.Boolean(), default=False),
        sa.Column('risk_score', sa.Integer(), default=0),
        sa.Column('requires_mfa', sa.Boolean(), default=False),
        sa.Column('mfa_verified', sa.Boolean(), default=False),
        sa.Column('session_type', sa.String(length=20), default='web'),
        sa.Column('login_method', sa.String(length=50)),
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.CheckConstraint("expires_at > created_at", name='ck_valid_expiry'),
        sa.CheckConstraint("logout_reason IN ('user_logout', 'timeout', 'security', 'admin', 'expired')", name='ck_logout_reason'),
        sa.CheckConstraint("risk_score >= 0 AND risk_score <= 100", name='ck_risk_score_range'),
        sa.CheckConstraint("session_type IN ('web', 'mobile', 'api', 'background')", name='ck_session_type'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sessions_activity', 'user_sessions', ['last_activity', 'is_active'])
    op.create_index('idx_sessions_expires', 'user_sessions', ['expires_at', 'is_active'])
    op.create_index('idx_sessions_ip', 'user_sessions', ['ip_address'])
    op.create_index('idx_sessions_mfa', 'user_sessions', ['requires_mfa', 'mfa_verified'])
    op.create_index('idx_sessions_suspicious', 'user_sessions', ['is_suspicious', 'risk_score'])
    op.create_index('idx_sessions_type', 'user_sessions', ['session_type', 'login_method'])
    op.create_index('idx_sessions_user_active', 'user_sessions', ['user_id', 'is_active'])
    op.create_index(op.f('ix_user_sessions_refresh_token'), 'user_sessions', ['refresh_token'], unique=True)
    op.create_index(op.f('ix_user_sessions_session_token'), 'user_sessions', ['session_token'], unique=True)


def downgrade() -> None:
    """Revert initial database schema."""
    
    op.drop_table('user_sessions')
    op.drop_table('accounts')
    op.drop_table('plaid_items')
    op.drop_table('categories')
    op.drop_table('institutions')
    op.drop_table('users')