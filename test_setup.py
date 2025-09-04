#!/usr/bin/env python
"""Test setup to verify the system works."""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    
    try:
        # Test database
        from src.utils.database import init_database, get_session, Account, Transaction
        print("✅ Database imports successful")
        
        # Test Plaid client
        from src.api.plaid_client import PlaidClient, ACCOUNT_CONFIG
        print("✅ Plaid client imports successful")
        
        # Test ML categorizer
        from src.ml.categorizer import TransactionCategorizer
        print("✅ ML categorizer imports successful")
        
        # Test report generator
        from src.reports.generator import ReportGenerator
        print("✅ Report generator imports successful")
        
        # Test main orchestrator
        from main import FinancialOrchestrator
        print("✅ Main orchestrator imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_database():
    """Test database initialization."""
    print("\nTesting database...")
    
    try:
        from src.utils.database import init_database, get_session
        
        # Initialize database
        engine = init_database()
        print("✅ Database initialized")
        
        # Get session
        session = get_session()
        print("✅ Database session created")
        
        # Test query
        from src.utils.database import Account
        accounts = session.query(Account).all()
        print(f"✅ Database query successful ({len(accounts)} accounts found)")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_ml_model():
    """Test ML model initialization."""
    print("\nTesting ML model...")
    
    try:
        from src.ml.categorizer import TransactionCategorizer
        import pandas as pd
        
        # Initialize categorizer
        categorizer = TransactionCategorizer()
        print("✅ ML categorizer initialized")
        
        # Test feature extraction
        test_data = pd.DataFrame({
            'merchant_name': ['Starbucks', 'AWS', 'Whole Foods'],
            'name': ['Coffee', 'Cloud Services', 'Groceries'],
            'amount': [5.50, 150.00, 75.25],
            'date': pd.date_range('2024-01-01', periods=3)
        })
        
        features = categorizer.extract_features(test_data)
        print(f"✅ Feature extraction successful ({len(features.columns)} features)")
        
        # Test category suggestions
        suggestions = categorizer.get_category_suggestions('starbucks', 5.50, False)
        print(f"✅ Category suggestions working: {suggestions}")
        
        return True
        
    except Exception as e:
        print(f"❌ ML model test failed: {e}")
        return False

def test_dashboard_imports():
    """Test dashboard imports."""
    print("\nTesting dashboard imports...")
    
    try:
        import streamlit as st
        print("✅ Streamlit imported")
        
        import plotly.express as px
        print("✅ Plotly imported")
        
        from src.dashboard.app import FinancialDashboard
        print("✅ Dashboard app imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard import failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("FINANCIAL SYSTEM TEST SUITE")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Database", test_database()))
    results.append(("ML Model", test_ml_model()))
    results.append(("Dashboard", test_dashboard_imports()))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Copy .env.sample to .env and add your Plaid credentials")
        print("2. Run: ~/anaconda3/envs/manna/bin/python scripts/setup_plaid.py")
        print("3. Launch dashboard: ~/anaconda3/envs/manna/bin/streamlit run src/dashboard/app.py")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)