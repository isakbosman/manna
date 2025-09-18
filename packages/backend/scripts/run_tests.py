#!/usr/bin/env python3
"""
Test runner script for the transaction categorization system.
Runs comprehensive tests and generates reports.
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_command(cmd: List[str], description: str) -> tuple[bool, str]:
    """Run a command and return success status and output."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")

    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        duration = time.time() - start_time

        if result.returncode == 0:
            print(f"✅ {description} - Completed in {duration:.2f}s")
            return True, result.stdout
        else:
            print(f"❌ {description} - Failed in {duration:.2f}s")
            print(f"Error: {result.stderr}")
            return False, result.stderr
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ {description} - Exception in {duration:.2f}s: {str(e)}")
        return False, str(e)

def run_unit_tests() -> bool:
    """Run unit tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "-m", "not integration and not performance"
    ]
    success, output = run_command(cmd, "Unit Tests")
    return success

def run_integration_tests() -> bool:
    """Run integration tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_categorization_flow.py",
        "tests/test_api_endpoints.py",
        "-v",
        "--tb=short"
    ]
    success, output = run_command(cmd, "Integration Tests")
    return success

def run_performance_tests() -> bool:
    """Run performance tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "-m", "performance"
    ]
    success, output = run_command(cmd, "Performance Tests")
    return success

def run_security_tests() -> bool:
    """Run security tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "-k", "security or auth"
    ]
    success, output = run_command(cmd, "Security Tests")
    return success

def run_coverage_tests() -> bool:
    """Run tests with coverage reporting."""
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "--cov=src",
        "--cov-report=html",
        "--cov-report=term",
        "--cov-fail-under=70"
    ]
    success, output = run_command(cmd, "Coverage Tests")
    return success

def run_linting() -> bool:
    """Run code linting."""
    commands = [
        (["python", "-m", "flake8", "src/", "--max-line-length=88"], "Flake8 Linting"),
        (["python", "-m", "black", "--check", "src/"], "Black Code Formatting"),
        (["python", "-m", "isort", "--check-only", "src/"], "Import Sorting"),
    ]

    all_passed = True
    for cmd, description in commands:
        success, _ = run_command(cmd, description)
        if not success:
            all_passed = False

    return all_passed

def run_type_checking() -> bool:
    """Run type checking."""
    cmd = ["python", "-m", "mypy", "src/", "--ignore-missing-imports"]
    success, output = run_command(cmd, "Type Checking")
    return success

def run_demo_script() -> bool:
    """Run the categorization demo script."""
    cmd = [
        "python", "scripts/demo_categorization.py",
        "--database-url", "sqlite:///test_demo.db"
    ]
    success, output = run_command(cmd, "Categorization Demo")
    return success

def run_seed_script() -> bool:
    """Run the seeding script."""
    cmd = [
        "python", "seeds/seed_categories.py",
        "--database-url", "sqlite:///test_seed.db"
    ]
    success, output = run_command(cmd, "Data Seeding")
    return success

def cleanup_test_files():
    """Clean up test database files."""
    test_files = [
        "test_demo.db",
        "test_seed.db",
        "demo_categorization.log",
        "seed_summary.json"
    ]

    for file in test_files:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"Cleaned up {file}")
        except Exception as e:
            print(f"Failed to clean up {file}: {e}")

def generate_test_report(results: Dict[str, bool]):
    """Generate a test report."""
    print("\n" + "="*60)
    print("TEST EXECUTION SUMMARY")
    print("="*60)

    total_tests = len(results)
    passed_tests = sum(1 for passed in results.values() if passed)

    print(f"Total test suites: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")

    print("\nDetailed Results:")
    print("-" * 40)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<25} {status}")

    if all(results.values()):
        print("\n🎉 All tests passed!")
        return True
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        return False

def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run categorization system tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--security", action="store_true", help="Run security tests only")
    parser.add_argument("--coverage", action="store_true", help="Run coverage tests")
    parser.add_argument("--lint", action="store_true", help="Run linting checks")
    parser.add_argument("--type-check", action="store_true", help="Run type checking")
    parser.add_argument("--demo", action="store_true", help="Run demo script")
    parser.add_argument("--seed", action="store_true", help="Run seeding script")
    parser.add_argument("--all", action="store_true", help="Run all tests and checks")
    parser.add_argument("--quick", action="store_true", help="Run quick test suite (unit + integration)")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test files")

    args = parser.parse_args()

    if args.cleanup:
        cleanup_test_files()
        return

    print("Transaction Categorization System - Test Runner")
    print("=" * 60)

    results = {}

    # Determine which tests to run
    if args.all:
        test_suite = {
            "Unit Tests": run_unit_tests,
            "Integration Tests": run_integration_tests,
            "Performance Tests": run_performance_tests,
            "Security Tests": run_security_tests,
            "Coverage Tests": run_coverage_tests,
            "Linting": run_linting,
            "Type Checking": run_type_checking,
            "Demo Script": run_demo_script,
            "Seed Script": run_seed_script
        }
    elif args.quick:
        test_suite = {
            "Unit Tests": run_unit_tests,
            "Integration Tests": run_integration_tests,
            "Linting": run_linting
        }
    else:
        test_suite = {}
        if args.unit:
            test_suite["Unit Tests"] = run_unit_tests
        if args.integration:
            test_suite["Integration Tests"] = run_integration_tests
        if args.performance:
            test_suite["Performance Tests"] = run_performance_tests
        if args.security:
            test_suite["Security Tests"] = run_security_tests
        if args.coverage:
            test_suite["Coverage Tests"] = run_coverage_tests
        if args.lint:
            test_suite["Linting"] = run_linting
        if args.type_check:
            test_suite["Type Checking"] = run_type_checking
        if args.demo:
            test_suite["Demo Script"] = run_demo_script
        if args.seed:
            test_suite["Seed Script"] = run_seed_script

    # If no specific tests selected, run quick suite
    if not test_suite:
        test_suite = {
            "Unit Tests": run_unit_tests,
            "Integration Tests": run_integration_tests
        }

    # Run tests
    start_time = time.time()

    for test_name, test_function in test_suite.items():
        print(f"\n{'-'*40}")
        results[test_name] = test_function()

    total_time = time.time() - start_time

    # Generate report
    print(f"\nTotal execution time: {total_time:.2f} seconds")
    success = generate_test_report(results)

    # Cleanup
    cleanup_test_files()

    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()