#!/usr/bin/env python
"""Check transactions in the database."""

from src.database import SessionLocal
from src.database.models import Transaction
from datetime import datetime

def check_transactions():
    """Check and display transaction counts."""
    db = SessionLocal()

    try:
        # Get total count
        total = db.query(Transaction).count()
        print(f"Total transactions in database: {total}")

        if total > 0:
            print("\nLatest 5 transactions:")
            transactions = db.query(Transaction).order_by(Transaction.created_at.desc()).limit(5).all()
            for t in transactions:
                amount = t.amount_cents / 100 if t.amount_cents else 0
                print(f"  - {t.name}: ${amount:.2f} on {t.date}")
                print(f"    Category: {t.primary_category or 'Uncategorized'}")
                print(f"    Merchant: {t.merchant_name or 'N/A'}")
        else:
            print("\nNo transactions found in database.")
            print("Please sync transactions from the frontend.")

    finally:
        db.close()

if __name__ == "__main__":
    check_transactions()