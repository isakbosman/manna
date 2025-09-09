#!/usr/bin/env python3
"""Simple test script to verify account endpoints work."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_basic_imports():
    """Test that basic imports work."""
    try:
        from src.database.models import User, Account, PlaidItem, Institution
        print("✓ Database models imported successfully")
        
        from src.routers.accounts import router as accounts_router
        print("✓ Accounts router imported successfully")
        
        from src.routers.plaid import router as plaid_router  
        print("✓ Plaid router imported successfully")
        
        print("\n✅ All basic imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_account_endpoints():
    """Test account endpoint registration."""
    try:
        from src.routers.accounts import router
        
        # Count the routes
        routes = [route for route in router.routes if hasattr(route, 'methods')]
        print(f"\n✓ Account router has {len(routes)} endpoints:")
        
        for route in routes:
            methods = ', '.join(route.methods)
            print(f"  - {methods} {route.path}")
            
        return True
        
    except Exception as e:
        print(f"❌ Account endpoint error: {e}")
        return False

def test_plaid_endpoints():
    """Test plaid endpoint registration."""
    try:
        from src.routers.plaid import router
        
        # Count the routes  
        routes = [route for route in router.routes if hasattr(route, 'methods')]
        print(f"\n✓ Plaid router has {len(routes)} endpoints:")
        
        for route in routes:
            methods = ', '.join(route.methods)
            print(f"  - {methods} {route.path}")
            
        return True
        
    except Exception as e:
        print(f"❌ Plaid endpoint error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Running simple backend tests...\n")
    
    success = True
    success &= test_basic_imports()
    success &= test_account_endpoints() 
    success &= test_plaid_endpoints()
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)
