#!/usr/bin/env python
"""Debug script to check Plaid configuration."""

from src.config import settings

def debug_plaid_config():
    """Check the current Plaid configuration."""
    print("Plaid Configuration:")
    print(f"  Client ID: {settings.plaid_client_id}")
    print(f"  Secret: {'***' if settings.plaid_secret else None}")
    print(f"  Environment: {settings.plaid_environment}")
    print(f"  Products: {settings.plaid_products}")
    print(f"  Country Codes: {settings.plaid_country_codes}")
    print(f"  Webhook URL: {settings.plaid_webhook_url}")

    if settings.plaid_client_id is None or settings.plaid_secret is None:
        print("\n❌ PROBLEM: Plaid credentials are not configured!")
        print("   This is why sync returns 0 transactions.")
        print("   The Plaid API calls fail without proper credentials.")
        print("\n   Solutions:")
        print("   1. Set PLAID_CLIENT_ID and PLAID_SECRET environment variables")
        print("   2. Use sandbox credentials for testing")
        print("   3. Check if there are hardcoded test credentials in the codebase")
    else:
        print("\n✅ Plaid credentials are configured")

if __name__ == "__main__":
    debug_plaid_config()