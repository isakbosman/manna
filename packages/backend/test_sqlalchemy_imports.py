"""
Test script to check correct SQLAlchemy 2.x imports for StaleDataError.
"""

import sqlalchemy
print(f"SQLAlchemy version: {sqlalchemy.__version__}")

# Check what's available in sqlalchemy.exc
try:
    from sqlalchemy.exc import StaleDataError
    print("✓ StaleDataError imported successfully from sqlalchemy.exc")
except ImportError as e:
    print(f"✗ Cannot import StaleDataError from sqlalchemy.exc: {e}")

# Check what's available in sqlalchemy.orm.exc
try:
    from sqlalchemy.orm.exc import StaleDataError
    print("✓ StaleDataError imported successfully from sqlalchemy.orm.exc")
except ImportError as e:
    print(f"✗ Cannot import StaleDataError from sqlalchemy.orm.exc: {e}")

# Check what's available in sqlalchemy.exc module
print("\n=== Available exceptions in sqlalchemy.exc ===")
import sqlalchemy.exc
exc_names = [name for name in dir(sqlalchemy.exc) if not name.startswith('_')]
for name in sorted(exc_names):
    if 'stale' in name.lower() or 'data' in name.lower() or 'version' in name.lower() or 'optimistic' in name.lower():
        print(f"  {name}")

# Check sqlalchemy.orm.exc if available
try:
    import sqlalchemy.orm.exc
    print("\n=== Available exceptions in sqlalchemy.orm.exc ===")
    orm_exc_names = [name for name in dir(sqlalchemy.orm.exc) if not name.startswith('_')]
    for name in sorted(orm_exc_names):
        if 'stale' in name.lower() or 'data' in name.lower() or 'version' in name.lower() or 'optimistic' in name.lower():
            print(f"  {name}")
except ImportError:
    print("\nsqlalchemy.orm.exc not available")

# Look for any exception with "stale" in the name across all modules
print("\n=== Searching for stale-related exceptions ===")
all_exceptions = []

# Check sqlalchemy.exc
for name in dir(sqlalchemy.exc):
    obj = getattr(sqlalchemy.exc, name)
    if isinstance(obj, type) and issubclass(obj, Exception):
        all_exceptions.append(f"sqlalchemy.exc.{name}")

# Check sqlalchemy.orm.exc
try:
    import sqlalchemy.orm.exc
    for name in dir(sqlalchemy.orm.exc):
        obj = getattr(sqlalchemy.orm.exc, name)
        if isinstance(obj, type) and issubclass(obj, Exception):
            all_exceptions.append(f"sqlalchemy.orm.exc.{name}")
except ImportError:
    pass

# Filter for relevant names
relevant_exceptions = [exc for exc in all_exceptions if
                      'stale' in exc.lower() or
                      'version' in exc.lower() or
                      'optimistic' in exc.lower()]

if relevant_exceptions:
    print("Found relevant exceptions:")
    for exc in relevant_exceptions:
        print(f"  {exc}")
else:
    print("No obviously relevant exceptions found")

print(f"\nTotal exceptions found: {len(all_exceptions)}")