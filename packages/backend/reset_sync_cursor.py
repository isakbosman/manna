#!/usr/bin/env python
"""
Reset Plaid sync cursor to force a full initial sync.
"""

import sys
sys.path.insert(0, '.')

from src.database import SessionLocal
from src.database.models import PlaidItem

db = SessionLocal()

try:
    # Get the PlaidItem
    plaid_item = db.query(PlaidItem).first()

    if plaid_item:
        print(f"Current cursor: {repr(plaid_item.cursor)}")
        print(f"Last sync: {plaid_item.last_successful_sync}")

        # Reset cursor to None to force initial sync
        plaid_item.cursor = None
        plaid_item.last_successful_sync = None

        db.commit()
        print("\n✓ Cursor reset - next sync will be an initial sync")
    else:
        print("No PlaidItem found")

finally:
    db.close()