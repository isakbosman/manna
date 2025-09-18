#!/usr/bin/env python
"""Force initial sync by manually processing transactions."""

import asyncio
import json
from src.database import SessionLocal
from src.database.models import User, PlaidItem, Account, Transaction
from src.services.plaid_service import plaid_service
from datetime import datetime, timedelta

async def force_initial_sync():
    """Force initial sync of transactions."""
    db = SessionLocal()

    try:
        # Disable the invalid second item
        invalid_item = db.query(PlaidItem).filter(
            PlaidItem.id == "703f900a-c9e5-4432-a959-0efe7c786670"
        ).first()
        if invalid_item:
            invalid_item.is_active = False
            print("✅ Disabled invalid Plaid item")

        # Get the valid plaid item
        plaid_item = db.query(PlaidItem).filter(
            PlaidItem.id == "49a6fc1f-2f24-43b6-8afe-53c733732af4"
        ).first()

        if not plaid_item:
            print("❌ Valid Plaid item not found")
            return

        print(f"✅ Using Plaid item: {plaid_item.id}")

        # Use get_transactions to force fetch (not sync which might be empty)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)  # Last 90 days

        result = await plaid_service.get_transactions(
            access_token=plaid_item.access_token,
            start_date=start_date,
            end_date=end_date,
            count=500,
            offset=0
        )

        print(f"✅ Fetched {len(result['transactions'])} transactions")

        # Manually save each transaction
        saved_count = 0
        for txn_data in result['transactions']:
            # Get account
            account = db.query(Account).filter(
                Account.plaid_account_id == txn_data["account_id"]
            ).first()

            if account:
                # Check if transaction exists
                existing = db.query(Transaction).filter(
                    Transaction.plaid_transaction_id == txn_data["transaction_id"]
                ).first()

                if not existing:
                    transaction = Transaction(
                        account_id=account.id,
                        plaid_transaction_id=txn_data["transaction_id"],
                        amount_cents=int(txn_data["amount"] * 100),
                        iso_currency_code=txn_data.get("iso_currency_code", "USD"),
                        date=datetime.strptime(txn_data["date"], "%Y-%m-%d").date() if isinstance(txn_data["date"], str) else txn_data["date"],
                        name=txn_data["name"],
                        merchant_name=txn_data.get("merchant_name"),
                        category=txn_data.get("category", []),
                        category_id=txn_data.get("category_id"),
                        primary_category=txn_data.get("category", [""])[0] if txn_data.get("category") else None,
                        detailed_category=txn_data.get("category", ["", ""])[-1] if txn_data.get("category") and len(txn_data.get("category")) > 1 else None,
                        pending=txn_data["pending"],
                        pending_transaction_id=txn_data.get("pending_transaction_id"),
                        payment_channel=txn_data.get("payment_channel"),
                        location=txn_data.get("location"),
                        account_owner=txn_data.get("account_owner"),
                        authorized_date=datetime.strptime(txn_data["authorized_date"], "%Y-%m-%d").date() if txn_data.get("authorized_date") and isinstance(txn_data["authorized_date"], str) else txn_data.get("authorized_date")
                    )
                    db.add(transaction)
                    saved_count += 1

        db.commit()
        print(f"✅ Saved {saved_count} new transactions to database")

        # Check final count
        total = db.query(Transaction).count()
        print(f"📊 Total transactions in database: {total}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(force_initial_sync())