"""CLI utilities for database management."""

import click
from sqlalchemy.orm import Session
from .models.database import SessionLocal, create_tables, drop_tables, DatabaseManager
from .models.performance_indexes import DatabaseOptimizer
from .seeds import create_seed_data, clear_seed_data


@click.group()
def cli():
    """Manna Financial Platform Database CLI."""
    pass


@cli.command()
def init_db():
    """Initialize database with all tables."""
    click.echo("Initializing database...")
    try:
        create_tables()
        click.echo("✓ Database tables created successfully!")
    except Exception as e:
        click.echo(f"✗ Error creating tables: {e}")


@cli.command()
@click.confirmation_option(prompt="Are you sure you want to drop all tables?")
def drop_db():
    """Drop all database tables."""
    click.echo("Dropping database tables...")
    try:
        drop_tables()
        click.echo("✓ Database tables dropped successfully!")
    except Exception as e:
        click.echo(f"✗ Error dropping tables: {e}")


@cli.command()
def reset_db():
    """Reset database (drop and recreate)."""
    click.echo("Resetting database...")
    try:
        drop_tables()
        create_tables()
        click.echo("✓ Database reset successfully!")
    except Exception as e:
        click.echo(f"✗ Error resetting database: {e}")


@cli.command()
def seed_db():
    """Create seed data for development."""
    click.echo("Creating seed data...")
    try:
        with SessionLocal() as session:
            create_seed_data(session)
        click.echo("✓ Seed data created successfully!")
    except Exception as e:
        click.echo(f"✗ Error creating seed data: {e}")


@cli.command()
def clear_seeds():
    """Clear seed data."""
    click.echo("Clearing seed data...")
    try:
        with SessionLocal() as session:
            clear_seed_data(session)
        click.echo("✓ Seed data cleared successfully!")
    except Exception as e:
        click.echo(f"✗ Error clearing seed data: {e}")


@cli.command()
def health_check():
    """Check database health."""
    click.echo("Checking database health...")
    
    if DatabaseManager.health_check():
        click.echo("✓ Database connection healthy!")
        
        # Show table counts
        counts = DatabaseManager.get_table_counts()
        if "error" not in counts:
            click.echo("\nTable record counts:")
            for table, count in counts.items():
                click.echo(f"  {table}: {count:,} records")
        else:
            click.echo(f"✗ Error getting table counts: {counts['error']}")
    else:
        click.echo("✗ Database connection failed!")


@cli.command()
def create_indexes():
    """Create performance optimization indexes."""
    click.echo("Creating performance indexes...")
    try:
        with SessionLocal() as session:
            DatabaseOptimizer.create_performance_indexes(session)
        click.echo("✓ Performance indexes created successfully!")
    except Exception as e:
        click.echo(f"✗ Error creating indexes: {e}")


@cli.command()
def analyze_performance():
    """Analyze database performance."""
    click.echo("Analyzing database performance...")
    try:
        with SessionLocal() as session:
            metrics = DatabaseOptimizer.analyze_query_performance(session)
        
        click.echo("\n=== DATABASE PERFORMANCE ANALYSIS ===")
        
        # Show table statistics
        if "table_stats" in metrics:
            click.echo(f"\nTable Statistics (showing first 10):")
            for stat in metrics["table_stats"][:10]:
                click.echo(f"  {stat['tablename']}.{stat['attname']}: {stat['n_distinct']} distinct values")
        
        # Show index usage
        if "index_usage" in metrics:
            click.echo(f"\nMost Used Indexes:")
            for idx in metrics["index_usage"][:10]:
                click.echo(f"  {idx['indexname']}: {idx['idx_scan']} scans")
        
        # Show slow queries if available
        if "slow_queries" in metrics and len(metrics["slow_queries"]) > 0:
            click.echo(f"\nSlowest Queries:")
            for query in metrics["slow_queries"][:5]:
                truncated_query = query['query'][:80] + "..." if len(query['query']) > 80 else query['query']
                click.echo(f"  {query['mean_time']:.2f}ms: {truncated_query}")
        elif "slow_queries_error" in metrics:
            click.echo(f"\nSlow queries: {metrics['slow_queries_error']}")
            
    except Exception as e:
        click.echo(f"✗ Error analyzing performance: {e}")


@cli.command()
def optimize_db():
    """Run database optimization (VACUUM ANALYZE)."""
    click.echo("Optimizing database...")
    try:
        with SessionLocal() as session:
            DatabaseOptimizer.optimize_database(session)
        click.echo("✓ Database optimization completed!")
    except Exception as e:
        click.echo(f"✗ Error optimizing database: {e}")


@cli.command()
@click.confirmation_option(prompt="Are you sure you want to drop performance indexes?")
def drop_indexes():
    """Drop custom performance indexes."""
    click.echo("Dropping performance indexes...")
    try:
        with SessionLocal() as session:
            DatabaseOptimizer.drop_performance_indexes(session)
        click.echo("✓ Performance indexes dropped successfully!")
    except Exception as e:
        click.echo(f"✗ Error dropping indexes: {e}")


@cli.command()
@click.option('--include-data', is_flag=True, help='Include sample data')
def setup_dev():
    """Complete development environment setup."""
    click.echo("Setting up development environment...")
    
    try:
        # Initialize database
        click.echo("1. Creating database tables...")
        create_tables()
        
        # Create performance indexes
        click.echo("2. Creating performance indexes...")
        with SessionLocal() as session:
            DatabaseOptimizer.create_performance_indexes(session)
        
        # Add seed data if requested
        if include_data:
            click.echo("3. Creating seed data...")
            with SessionLocal() as session:
                create_seed_data(session)
        
        click.echo("✓ Development environment setup completed!")
        
        # Show status
        click.echo("\nEnvironment Status:")
        if DatabaseManager.health_check():
            counts = DatabaseManager.get_table_counts()
            if "error" not in counts:
                total_records = sum(counts.values())
                click.echo(f"  Database: Connected ({total_records:,} total records)")
                if include_data:
                    click.echo(f"  Seed data: Loaded")
            else:
                click.echo("  Database: Connected (error getting counts)")
        else:
            click.echo("  Database: Connection failed")
            
    except Exception as e:
        click.echo(f"✗ Error setting up environment: {e}")


@cli.command()
def show_schema():
    """Display database schema information."""
    click.echo("=== MANNA DATABASE SCHEMA ===\n")
    
    schema_info = {
        "users": "User accounts and authentication",
        "institutions": "Financial institutions from Plaid", 
        "accounts": "Linked bank/credit accounts",
        "transactions": "Financial transactions with double-entry support",
        "categories": "Hierarchical transaction categories",
        "ml_predictions": "ML categorization results and feedback",
        "categorization_rules": "Automated categorization rules",
        "reports": "Generated financial reports",
        "budgets": "Budget plans and tracking", 
        "budget_items": "Individual budget line items",
        "plaid_items": "Plaid connection management",
        "plaid_webhooks": "Real-time webhook events",
        "audit_logs": "Complete audit trail",
        "user_sessions": "Active user sessions and security"
    }
    
    for table, description in schema_info.items():
        click.echo(f"{table:20} - {description}")
    
    click.echo(f"\nTotal tables: {len(schema_info)}")
    
    # Show current record counts if possible
    if DatabaseManager.health_check():
        click.echo("\nCurrent record counts:")
        counts = DatabaseManager.get_table_counts()
        if "error" not in counts:
            for table in schema_info.keys():
                count = counts.get(table, 0)
                click.echo(f"  {table:20}: {count:,}")


if __name__ == '__main__':
    cli()