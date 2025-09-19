#!/usr/bin/env python3
"""
Diagnose schema issues by examining current model definitions vs database state
"""

import sys
import os
sys.path.insert(0, '.')

from models.plaid_item import PlaidItem
from sqlalchemy import inspect, MetaData, Table
from sqlalchemy.dialects import postgresql
import logging

def diagnose_plaid_item_schema():
    """Diagnose PlaidItem model schema."""
    print("=== PlaidItem Schema Diagnosis ===\n")

    # Get model table definition
    plaid_items_table = PlaidItem.__table__

    print("1. Model expects these columns:")
    for column in plaid_items_table.columns:
        print(f"   {column.name}: {column.type} {'NOT NULL' if not column.nullable else 'NULL'}")

    print("\n2. Model indexes:")
    for index in plaid_items_table.indexes:
        columns = [col.name for col in index.columns]
        print(f"   {index.name}: {columns}")

    print("\n3. Model constraints:")
    for constraint in plaid_items_table.constraints:
        constraint_type = type(constraint).__name__
        if hasattr(constraint, 'columns'):
            columns = [col.name for col in constraint.columns]
            print(f"   {constraint.name} ({constraint_type}): {columns}")
        else:
            print(f"   {constraint.name} ({constraint_type})")

    print("\n4. Critical fields analysis:")
    print(f"   - sync_cursor maps to column: {'cursor' if hasattr(PlaidItem, 'sync_cursor') else 'NOT FOUND'}")
    print(f"   - last_sync_attempt exists: {hasattr(PlaidItem, 'last_sync_attempt')}")
    print(f"   - access_token field: {hasattr(PlaidItem, 'plaid_access_token')}")

    # Check for encrypted field
    if hasattr(PlaidItem, 'plaid_access_token'):
        access_token_column = plaid_items_table.columns.get('plaid_access_token')
        if access_token_column:
            print(f"   - access_token type: {access_token_column.type}")

    print("\n5. Sync-related methods:")
    methods = [method for method in dir(PlaidItem) if 'sync' in method.lower() or 'cursor' in method.lower()]
    for method in methods:
        if not method.startswith('_'):
            print(f"   - {method}")

if __name__ == "__main__":
    diagnose_plaid_item_schema()