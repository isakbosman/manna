#!/usr/bin/env python3
"""Test runner for tax categorization system tests.

This script can be used to run the tax categorization tests in various modes:
- Individual test files
- All tests together
- Specific test classes
- With coverage reporting

Usage:
    python run_tax_categorization_tests.py --help
    python run_tax_categorization_tests.py --all
    python run_tax_categorization_tests.py --unit-only
    python run_tax_categorization_tests.py --api-only
    python run_tax_categorization_tests.py --database-only
    python run_tax_categorization_tests.py --e2e-only
    python run_tax_categorization_tests.py --coverage
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_command(cmd, description=""):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def check_imports():
    """Check if all required imports are available."""
    print("\nChecking imports...")

    try:
        import pytest
        print(f"✅ pytest version: {pytest.__version__}")
    except ImportError as e:
        print(f"❌ pytest not available: {e}")
        return False

    try:
        from sqlalchemy.orm import Session
        print("✅ SQLAlchemy available")
    except ImportError as e:
        print(f"❌ SQLAlchemy not available: {e}")
        return False

    try:
        from fastapi.testclient import TestClient
        print("✅ FastAPI TestClient available")
    except ImportError as e:
        print(f"❌ FastAPI TestClient not available: {e}")
        return False

    # Check if our models can be imported
    try:
        from models.tax_categorization import TaxCategory, ChartOfAccount
        print("✅ Tax categorization models available")
    except ImportError as e:
        print(f"❌ Tax categorization models not available: {e}")
        print("Note: This might be expected if database migrations haven't been run")

    try:
        from src.services.tax_categorization_service import TaxCategorizationService
        print("✅ Tax categorization service available")
    except ImportError as e:
        print(f"❌ Tax categorization service not available: {e}")
        return False

    return True

def get_test_files():
    """Get all tax categorization test files."""
    test_dir = Path(__file__).parent
    return {
        'comprehensive': test_dir / 'test_tax_categorization_comprehensive.py',
        'api': test_dir / 'test_tax_categorization_api.py',
        'database': test_dir / 'test_tax_categorization_database.py',
        'e2e': test_dir / 'test_tax_categorization_e2e.py',
        'legacy': test_dir / 'test_tax_categorization.py'
    }

def run_unit_tests():
    """Run unit tests (comprehensive test file)."""
    test_files = get_test_files()
    cmd = ['python', '-m', 'pytest', str(test_files['comprehensive']), '-v']
    return run_command(cmd, "Unit Tests (Comprehensive)")

def run_api_tests():
    """Run API integration tests."""
    test_files = get_test_files()
    cmd = ['python', '-m', 'pytest', str(test_files['api']), '-v']
    return run_command(cmd, "API Integration Tests")

def run_database_tests():
    """Run database and transaction tests."""
    test_files = get_test_files()
    cmd = ['python', '-m', 'pytest', str(test_files['database']), '-v']
    return run_command(cmd, "Database Transaction Tests")

def run_e2e_tests():
    """Run end-to-end workflow tests."""
    test_files = get_test_files()
    cmd = ['python', '-m', 'pytest', str(test_files['e2e']), '-v']
    return run_command(cmd, "End-to-End Workflow Tests")

def run_all_tests():
    """Run all tax categorization tests."""
    test_files = get_test_files()
    test_patterns = [
        str(test_files['comprehensive']),
        str(test_files['api']),
        str(test_files['database']),
        str(test_files['e2e'])
    ]
    cmd = ['python', '-m', 'pytest'] + test_patterns + ['-v']
    return run_command(cmd, "All Tax Categorization Tests")

def run_with_coverage():
    """Run tests with coverage reporting."""
    test_files = get_test_files()
    test_patterns = [
        str(test_files['comprehensive']),
        str(test_files['api']),
        str(test_files['database']),
        str(test_files['e2e'])
    ]

    # Check if pytest-cov is available
    try:
        import pytest_cov
        coverage_args = [
            '--cov=src.services.tax_categorization_service',
            '--cov=src.services.chart_of_accounts_service',
            '--cov=models.tax_categorization',
            '--cov=src.routers.tax_categorization',
            '--cov-report=html',
            '--cov-report=term-missing'
        ]
    except ImportError:
        print("⚠️  pytest-cov not available, running without coverage")
        coverage_args = []

    cmd = ['python', '-m', 'pytest'] + test_patterns + coverage_args + ['-v']
    return run_command(cmd, "Tests with Coverage")

def run_dry_run():
    """Run a dry run to check test discovery."""
    test_files = get_test_files()
    test_patterns = [
        str(test_files['comprehensive']),
        str(test_files['api']),
        str(test_files['database']),
        str(test_files['e2e'])
    ]
    cmd = ['python', '-m', 'pytest'] + test_patterns + ['--collect-only']
    return run_command(cmd, "Test Discovery (Dry Run)")

def validate_test_files():
    """Validate that all test files exist and are readable."""
    print("\nValidating test files...")
    test_files = get_test_files()

    all_valid = True
    for name, path in test_files.items():
        if path.exists():
            size = path.stat().st_size
            print(f"✅ {name}: {path.name} ({size} bytes)")
        else:
            print(f"❌ {name}: {path.name} - FILE NOT FOUND")
            all_valid = False

    return all_valid

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run tax categorization system tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('--all', action='store_true',
                      help='Run all tax categorization tests')
    parser.add_argument('--unit-only', action='store_true',
                      help='Run only unit tests')
    parser.add_argument('--api-only', action='store_true',
                      help='Run only API integration tests')
    parser.add_argument('--database-only', action='store_true',
                      help='Run only database tests')
    parser.add_argument('--e2e-only', action='store_true',
                      help='Run only end-to-end tests')
    parser.add_argument('--coverage', action='store_true',
                      help='Run tests with coverage reporting')
    parser.add_argument('--dry-run', action='store_true',
                      help='Show what tests would be run without executing')
    parser.add_argument('--check-imports', action='store_true',
                      help='Check if all required imports are available')
    parser.add_argument('--validate', action='store_true',
                      help='Validate test files exist')

    args = parser.parse_args()

    # Default to showing help if no arguments
    if not any(vars(args).values()):
        parser.print_help()
        return

    print("🧪 Tax Categorization System Test Runner")
    print("=" * 50)

    # Always validate test files first
    if not validate_test_files():
        print("\n❌ Some test files are missing. Please check your setup.")
        return

    if args.check_imports:
        if not check_imports():
            print("\n❌ Some required imports are not available.")
            print("Please ensure you have activated the correct conda environment (mana).")
            return
        else:
            print("\n✅ All imports are available!")

    if args.validate:
        print("\n✅ All test files validated!")
        return

    if args.dry_run:
        run_dry_run()
        return

    # Run the appropriate tests
    success = True

    if args.unit_only:
        success = run_unit_tests()
    elif args.api_only:
        success = run_api_tests()
    elif args.database_only:
        success = run_database_tests()
    elif args.e2e_only:
        success = run_e2e_tests()
    elif args.coverage:
        success = run_with_coverage()
    elif args.all:
        success = run_all_tests()

    # Print final result
    print("\n" + "=" * 60)
    if success:
        print("✅ Tests completed successfully!")
    else:
        print("❌ Some tests failed or encountered errors.")
        print("Note: This might be expected if the database is not set up.")
    print("=" * 60)

if __name__ == '__main__':
    main()