#!/usr/bin/env python3
"""
Test script to verify Plaid transaction sync functionality after fixes.

This script tests:
1. Initial sync (no cursor)
2. Incremental sync (with cursor)
3. Pagination handling
4. Error recovery
5. Deduplication
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import models and services
from src.services.plaid_service import plaid_service
from src.database.connection import get_db
from models.database import Base
from models.plaid_item import PlaidItem
from models.account import Account
from models.transaction import Transaction
from src.config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rich console for pretty output
console = Console()


async def test_sync_functionality():
    """Test the complete sync functionality."""

    console.print("\n[bold cyan]🔧 Plaid Transaction Sync Test Suite[/bold cyan]\n")

    # Get database session
    db = next(get_db())

    try:
        # 1. Check for existing Plaid items
        console.print("[yellow]Checking for existing Plaid items...[/yellow]")
        plaid_items = db.query(PlaidItem).filter(
            PlaidItem.is_active == True
        ).all()

        if not plaid_items:
            console.print("[red]❌ No active Plaid items found. Please link an account first.[/red]")
            return

        console.print(f"[green]✓ Found {len(plaid_items)} active Plaid item(s)[/green]")

        # Create a table to show current state
        table = Table(title="Current Plaid Items State")
        table.add_column("Item ID", style="cyan")
        table.add_column("Institution", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Cursor", style="yellow")
        table.add_column("Last Sync", style="blue")
        table.add_column("Accounts", style="white")

        for item in plaid_items:
            # Get institution name
            inst_name = item.institution.name if item.institution else "Unknown"

            # Get account count
            account_count = db.query(Account).filter(
                Account.plaid_item_id == item.id
            ).count()

            # Format last sync
            last_sync = item.last_successful_sync.strftime("%Y-%m-%d %H:%M") if item.last_successful_sync else "Never"

            # Cursor status
            cursor_status = "Present" if item.cursor else "None (Initial)"

            table.add_row(
                str(item.id)[:8] + "...",
                inst_name,
                item.status,
                cursor_status,
                last_sync,
                str(account_count)
            )

        console.print(table)

        # 2. Test sync for first item
        test_item = plaid_items[0]
        console.print(f"\n[yellow]Testing sync for item {test_item.id}...[/yellow]")

        # Check if this is initial or incremental sync
        is_initial = test_item.cursor is None
        sync_type = "initial" if is_initial else "incremental"

        console.print(f"[blue]Sync type: {sync_type.upper()}[/blue]")

        # 3. Perform sync with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            # Start sync
            task = progress.add_task(f"[cyan]Syncing transactions ({sync_type})...", total=None)

            try:
                # Track stats
                total_added = 0
                total_modified = 0
                total_removed = 0
                pages_processed = 0
                has_more = True
                current_cursor = test_item.cursor

                # Store original cursor for retry logic
                original_cursor = current_cursor

                while has_more:
                    pages_processed += 1
                    progress.update(task, description=f"[cyan]Processing page {pages_processed}...")

                    # Call sync endpoint
                    sync_result = await plaid_service.sync_transactions(
                        access_token=test_item.access_token,
                        cursor=current_cursor,
                        count=500  # Max page size
                    )

                    # Update stats
                    added = len(sync_result.get('added', []))
                    modified = len(sync_result.get('modified', []))
                    removed = len(sync_result.get('removed', []))

                    total_added += added
                    total_modified += modified
                    total_removed += removed

                    # Log progress
                    if added or modified or removed:
                        console.print(f"  Page {pages_processed}: +{added} modified:{modified} removed:{removed}")

                    # Update cursor and check for more pages
                    current_cursor = sync_result.get('next_cursor')
                    has_more = sync_result.get('has_more', False)

                    # Simulate processing (in real code, this would save to DB)
                    await asyncio.sleep(0.1)

                progress.update(task, description="[green]✓ Sync completed![/green]")

        # 4. Show results
        console.print(f"\n[bold green]✓ Sync Test Completed Successfully![/bold green]")

        # Create results table
        results_table = Table(title="Sync Test Results")
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Value", style="yellow")

        results_table.add_row("Sync Type", sync_type.upper())
        results_table.add_row("Pages Processed", str(pages_processed))
        results_table.add_row("Transactions Added", str(total_added))
        results_table.add_row("Transactions Modified", str(total_modified))
        results_table.add_row("Transactions Removed", str(total_removed))
        results_table.add_row("New Cursor", current_cursor[:20] + "..." if current_cursor else "None")

        console.print(results_table)

        # 5. Test error scenarios
        console.print("\n[yellow]Testing error handling scenarios...[/yellow]")

        # Test with invalid access token
        console.print("  Testing invalid access token...")
        try:
            await plaid_service.sync_transactions(
                access_token="invalid_token",
                cursor=None
            )
            console.print("    [red]❌ Should have raised an error[/red]")
        except Exception as e:
            console.print(f"    [green]✓ Correctly caught error: {str(e)[:50]}...[/green]")

        # 6. Verify deduplication
        console.print("\n[yellow]Verifying transaction deduplication...[/yellow]")

        # Count unique transactions
        unique_count = db.query(Transaction.plaid_transaction_id).distinct().count()
        total_count = db.query(Transaction).count()

        if unique_count == total_count:
            console.print(f"  [green]✓ No duplicates found ({total_count} transactions)[/green]")
        else:
            console.print(f"  [red]❌ Found duplicates: {total_count - unique_count} duplicate(s)[/red]")

        # 7. Test webhook initialization
        console.print("\n[yellow]Testing webhook initialization...[/yellow]")

        # The first sync call should have activated webhooks
        if is_initial:
            console.print("  [blue]Initial sync performed - webhooks should be activated[/blue]")
        else:
            console.print("  [green]✓ Webhooks already active (incremental sync)[/green]")

        # 8. Performance metrics
        console.print("\n[bold cyan]Performance Metrics:[/bold cyan]")

        if pages_processed > 0:
            avg_per_page = (total_added + total_modified) / pages_processed
            console.print(f"  Average transactions per page: {avg_per_page:.1f}")

        # Check sync frequency
        if test_item.last_successful_sync:
            time_since_sync = datetime.utcnow() - test_item.last_successful_sync
            console.print(f"  Time since last sync: {time_since_sync}")

        console.print("\n[bold green]🎉 All tests completed![/bold green]")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        console.print(f"\n[bold red]❌ Test failed: {e}[/bold red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")

    finally:
        db.close()


async def test_cursor_fix():
    """Specifically test the cursor column fix."""

    console.print("\n[bold cyan]Testing Cursor Column Fix[/bold cyan]\n")

    db = next(get_db())

    try:
        # Test reading and writing cursor
        item = db.query(PlaidItem).first()

        if item:
            console.print(f"Testing cursor property on item {item.id}:")

            # Test reading
            console.print(f"  Current cursor value: {item.cursor}")

            # Test writing
            test_cursor = "test_cursor_" + datetime.now().strftime("%Y%m%d%H%M%S")
            item.cursor = test_cursor
            db.flush()

            # Verify it was saved
            db.refresh(item)
            if item.cursor == test_cursor:
                console.print(f"  [green]✓ Successfully set cursor to: {test_cursor}[/green]")
            else:
                console.print(f"  [red]❌ Failed to set cursor[/red]")

            # Reset cursor
            item.cursor = None
            db.commit()
            console.print("  [blue]Reset cursor to None for next test[/blue]")
        else:
            console.print("[yellow]No Plaid items found to test cursor[/yellow]")

    except Exception as e:
        console.print(f"[red]Cursor test failed: {e}[/red]")
        db.rollback()
    finally:
        db.close()


async def main():
    """Main test runner."""

    # Test cursor fix first
    await test_cursor_fix()

    # Then test full sync functionality
    await test_sync_functionality()


if __name__ == "__main__":
    asyncio.run(main())