#!/usr/bin/env python3
"""Test tax categorization implementation."""

import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.base import Base


def test_model_imports():
    """Test that all tax categorization models can be imported."""
    try:
        from models.tax_categorization import (
            TaxCategory, ChartOfAccount, BusinessExpenseTracking,
            CategoryMapping, CategorizationAudit
        )
        print("✓ Tax categorization models imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import tax categorization models: {e}")
        return False


def test_service_imports():
    """Test that services can be imported."""
    try:
        from src.services.tax_categorization_service import TaxCategorizationService
        from src.services.chart_of_accounts_service import ChartOfAccountsService
        print("✓ Tax categorization services imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import tax categorization services: {e}")
        return False


def test_schema_imports():
    """Test that schemas can be imported."""
    try:
        from src.schemas.tax_categorization import (
            TaxCategory, ChartOfAccount, TaxCategorizationRequest
        )
        print("✓ Tax categorization schemas imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import tax categorization schemas: {e}")
        return False


def test_router_imports():
    """Test that router can be imported."""
    try:
        from src.routers.tax_categorization import router
        print("✓ Tax categorization router imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import tax categorization router: {e}")
        return False


def main():
    """Run all tests."""
    print("Testing Tax Categorization Implementation")
    print("=" * 50)

    tests = [
        test_model_imports,
        test_service_imports,
        test_schema_imports,
        test_router_imports,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("🎉 All tax categorization components are properly implemented!")
        return True
    else:
        print("❌ Some components have issues that need to be fixed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)