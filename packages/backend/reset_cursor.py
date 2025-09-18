#!/usr/bin/env python
"""Reset cursor for Plaid item to enable fresh sync."""

from src.database import SessionLocal
from src.database.models import PlaidItem

def reset_cursor():
    """Reset the cursor to None for the first Plaid item."""
    db = SessionLocal()

    try:
        # Get the valid plaid item
        plaid_item = db.query(PlaidItem).filter(
            PlaidItem.id == "49a6fc1f-2f24-43b6-8afe-53c733732af4"
        ).first()

        if not plaid_item:
            print("❌ Plaid item not found")
            return

        print(f"Current cursor: {plaid_item.cursor}")

        # Reset cursor to None
        plaid_item.cursor = None
        db.commit()

        print("✅ Cursor reset to None - fresh sync will now work")

    finally:
        db.close()

if __name__ == "__main__":
    reset_cursor()