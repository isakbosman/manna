"""Performance optimization indexes for the Manna database schema."""

from sqlalchemy import text, Index
from sqlalchemy.orm import Session
from .database import engine


class DatabaseOptimizer:
    """Database performance optimization utilities."""
    
    # Custom indexes beyond what's defined in models
    CUSTOM_INDEXES = [
        # Transaction analysis indexes
        {
            "name": "idx_transactions_amount_date_business",
            "table": "transactions",
            "columns": ["amount", "date", "is_business"],
            "description": "Optimize large transaction queries by business type"
        },
        {
            "name": "idx_transactions_merchant_amount",
            "table": "transactions", 
            "columns": ["merchant_name", "amount"],
            "description": "Fast merchant spending analysis"
        },
        {
            "name": "idx_transactions_category_amount_date",
            "table": "transactions",
            "columns": ["category_id", "amount", "date"],
            "description": "Category spending reports with amounts"
        },
        
        # ML prediction optimization
        {
            "name": "idx_ml_predictions_model_confidence_date",
            "table": "ml_predictions",
            "columns": ["model_version", "confidence", "prediction_date"],
            "description": "Model performance analysis"
        },
        {
            "name": "idx_ml_predictions_feedback_confidence",
            "table": "ml_predictions",
            "columns": ["user_feedback", "confidence", "is_accepted"],
            "description": "ML feedback analysis for model improvement"
        },
        
        # Account balance tracking
        {
            "name": "idx_accounts_balance_sync",
            "table": "accounts",
            "columns": ["current_balance", "last_sync", "is_active"],
            "description": "Account balance monitoring and sync status"
        },
        
        # Audit log performance
        {
            "name": "idx_audit_logs_timestamp_user_action",
            "table": "audit_logs",
            "columns": ["event_timestamp", "user_id", "action"],
            "description": "User activity timeline queries"
        },
        {
            "name": "idx_audit_logs_compliance_financial",
            "table": "audit_logs", 
            "columns": ["compliance_relevant", "financial_impact", "event_timestamp"],
            "description": "Compliance and financial audit queries"
        },
        
        # Budget performance
        {
            "name": "idx_budget_items_utilization",
            "table": "budget_items",
            "columns": ["budget_id", "actual_amount", "budgeted_amount"],
            "description": "Budget utilization analysis"
        },
        
        # Webhook processing
        {
            "name": "idx_webhooks_processing_priority",
            "table": "plaid_webhooks",
            "columns": ["processing_status", "retry_count", "received_at"],
            "description": "Webhook processing queue optimization"
        },
        
        # Session security
        {
            "name": "idx_sessions_risk_active",
            "table": "user_sessions",
            "columns": ["risk_score", "is_suspicious", "is_active"],
            "description": "Security monitoring of active sessions"
        }
    ]
    
    # Partial indexes for better performance on filtered queries
    PARTIAL_INDEXES = [
        {
            "name": "idx_transactions_pending_recent",
            "sql": """
                CREATE INDEX CONCURRENTLY idx_transactions_pending_recent 
                ON transactions (account_id, date) 
                WHERE is_pending = true AND date >= NOW() - INTERVAL '7 days'
            """,
            "description": "Recent pending transactions only"
        },
        {
            "name": "idx_transactions_business_deductible",
            "sql": """
                CREATE INDEX CONCURRENTLY idx_transactions_business_deductible
                ON transactions (category_id, amount, date)
                WHERE is_business = true AND is_tax_deductible = true
            """,
            "description": "Business tax-deductible transactions for reporting"
        },
        {
            "name": "idx_ml_predictions_low_confidence", 
            "sql": """
                CREATE INDEX CONCURRENTLY idx_ml_predictions_low_confidence
                ON ml_predictions (transaction_id, confidence, prediction_date)
                WHERE confidence < 0.8 AND requires_review = true
            """,
            "description": "Low confidence predictions needing review"
        },
        {
            "name": "idx_plaid_items_needs_attention",
            "sql": """
                CREATE INDEX CONCURRENTLY idx_plaid_items_needs_attention
                ON plaid_items (user_id, status, last_sync_attempt)
                WHERE requires_reauth = true OR status IN ('error', 'expired')
            """,
            "description": "Plaid items requiring user attention"
        }
    ]
    
    # JSONB indexes for metadata queries
    JSONB_INDEXES = [
        {
            "name": "idx_transactions_location_gin",
            "sql": """
                CREATE INDEX CONCURRENTLY idx_transactions_location_gin
                ON transactions USING gin (location_coordinates)
            """,
            "description": "Geographic transaction analysis"
        },
        {
            "name": "idx_transactions_tags_gin",
            "sql": """
                CREATE INDEX CONCURRENTLY idx_transactions_tags_gin
                ON transactions USING gin (tags)
            """,
            "description": "Transaction tag-based filtering"
        },
        {
            "name": "idx_users_preferences_gin",
            "sql": """
                CREATE INDEX CONCURRENTLY idx_users_preferences_gin
                ON users USING gin (preferences)
            """,
            "description": "User preference queries"
        },
        {
            "name": "idx_ml_predictions_features_gin",
            "sql": """
                CREATE INDEX CONCURRENTLY idx_ml_predictions_features_gin
                ON ml_predictions USING gin (features_used)
            """,
            "description": "ML feature analysis"
        }
    ]
    
    @classmethod
    def create_performance_indexes(cls, session: Session) -> None:
        """Create all performance optimization indexes."""
        
        print("Creating custom performance indexes...")
        
        # Create composite indexes
        for idx_config in cls.CUSTOM_INDEXES:
            try:
                columns_str = ", ".join(idx_config["columns"])
                sql = f"""
                    CREATE INDEX CONCURRENTLY {idx_config["name"]}
                    ON {idx_config["table"]} ({columns_str})
                """
                session.execute(text(sql))
                print(f"✓ Created index: {idx_config['name']}")
            except Exception as e:
                print(f"✗ Failed to create {idx_config['name']}: {e}")
        
        # Create partial indexes
        for idx_config in cls.PARTIAL_INDEXES:
            try:
                session.execute(text(idx_config["sql"]))
                print(f"✓ Created partial index: {idx_config['name']}")
            except Exception as e:
                print(f"✗ Failed to create {idx_config['name']}: {e}")
        
        # Create JSONB indexes
        for idx_config in cls.JSONB_INDEXES:
            try:
                session.execute(text(idx_config["sql"]))
                print(f"✓ Created JSONB index: {idx_config['name']}")
            except Exception as e:
                print(f"✗ Failed to create {idx_config['name']}: {e}")
        
        session.commit()
        print("Performance index creation completed!")
    
    @classmethod
    def analyze_query_performance(cls, session: Session) -> dict:
        """Analyze database performance metrics."""
        
        metrics = {}
        
        # Table sizes
        table_sizes_query = """
            SELECT 
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation,
                most_common_vals,
                most_common_freqs
            FROM pg_stats 
            WHERE schemaname = 'public'
            ORDER BY tablename, attname
        """
        
        try:
            result = session.execute(text(table_sizes_query))
            metrics["table_stats"] = [dict(row) for row in result]
        except Exception as e:
            metrics["table_stats_error"] = str(e)
        
        # Index usage
        index_usage_query = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_tup_read,
                idx_tup_fetch,
                idx_scan
            FROM pg_stat_user_indexes
            ORDER BY idx_scan DESC
        """
        
        try:
            result = session.execute(text(index_usage_query))
            metrics["index_usage"] = [dict(row) for row in result]
        except Exception as e:
            metrics["index_usage_error"] = str(e)
        
        # Slow queries (if pg_stat_statements is enabled)
        slow_queries_query = """
            SELECT 
                query,
                calls,
                total_time,
                mean_time,
                rows
            FROM pg_stat_statements
            WHERE query NOT LIKE '%pg_stat_statements%'
            ORDER BY mean_time DESC
            LIMIT 10
        """
        
        try:
            result = session.execute(text(slow_queries_query))
            metrics["slow_queries"] = [dict(row) for row in result]
        except Exception as e:
            metrics["slow_queries_error"] = "pg_stat_statements not available"
        
        return metrics
    
    @classmethod
    def optimize_database(cls, session: Session) -> None:
        """Run database optimization tasks."""
        
        print("Running database optimization...")
        
        # Update table statistics
        try:
            session.execute(text("ANALYZE"))
            print("✓ Updated table statistics")
        except Exception as e:
            print(f"✗ Failed to analyze tables: {e}")
        
        # Vacuum (if not in transaction)
        try:
            session.commit()  # End current transaction
            session.execute(text("VACUUM (ANALYZE)"))
            print("✓ Completed vacuum analyze")
        except Exception as e:
            print(f"✗ Failed to vacuum: {e}")
        
        print("Database optimization completed!")
    
    @classmethod
    def drop_performance_indexes(cls, session: Session) -> None:
        """Drop all custom performance indexes."""
        
        print("Dropping custom performance indexes...")
        
        all_indexes = (
            [idx["name"] for idx in cls.CUSTOM_INDEXES] +
            [idx["name"] for idx in cls.PARTIAL_INDEXES] + 
            [idx["name"] for idx in cls.JSONB_INDEXES]
        )
        
        for idx_name in all_indexes:
            try:
                session.execute(text(f"DROP INDEX CONCURRENTLY IF EXISTS {idx_name}"))
                print(f"✓ Dropped index: {idx_name}")
            except Exception as e:
                print(f"✗ Failed to drop {idx_name}: {e}")
        
        session.commit()
        print("Performance index cleanup completed!")


def create_indexes():
    """CLI function to create performance indexes."""
    from .database import SessionLocal
    
    with SessionLocal() as session:
        DatabaseOptimizer.create_performance_indexes(session)


def analyze_performance():
    """CLI function to analyze performance."""
    from .database import SessionLocal
    
    with SessionLocal() as session:
        metrics = DatabaseOptimizer.analyze_query_performance(session)
        
        print("\n=== DATABASE PERFORMANCE ANALYSIS ===\n")
        
        # Print table statistics
        if "table_stats" in metrics:
            print("Table Statistics:")
            for stat in metrics["table_stats"][:10]:  # Top 10
                print(f"  {stat['tablename']}.{stat['attname']}: {stat['n_distinct']} distinct values")
        
        # Print index usage
        if "index_usage" in metrics:
            print(f"\nIndex Usage (Top 10):")
            for idx in metrics["index_usage"][:10]:
                print(f"  {idx['indexname']}: {idx['idx_scan']} scans")
        
        # Print slow queries
        if "slow_queries" in metrics:
            print(f"\nSlow Queries (Top 5):")
            for query in metrics["slow_queries"][:5]:
                print(f"  {query['mean_time']:.2f}ms avg: {query['query'][:100]}...")


if __name__ == "__main__":
    create_indexes()