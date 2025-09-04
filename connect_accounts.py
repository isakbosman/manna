#!/usr/bin/env python
"""Simple script to launch Plaid Link for connecting accounts."""

import os
import sys
import subprocess
import time
import webbrowser

def main():
    print("""
╔══════════════════════════════════════════════════════╗
║         Connect Your Bank Accounts with Plaid        ║
╚══════════════════════════════════════════════════════╝

This will launch a web browser where you can:
1. Connect your bank accounts securely through Plaid
2. Select which accounts to link
3. Categorize as business or personal
""")
    
    # Check for Flask
    try:
        import flask
    except ImportError:
        print("Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "flask", "flask-cors"], check=True)
    
    # Start the Plaid Link server
    print("\nStarting Plaid Link server...")
    server_process = subprocess.Popen(
        [sys.executable, "src/api/plaid_link_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # Wait for server to start
    time.sleep(3)
    
    # Open browser
    url = "http://127.0.0.1:8888"
    print(f"\n✨ Opening browser to: {url}")
    print("\nIn the browser:")
    print("1. Click 'Connect Account' button")
    print("2. Search and select your bank")
    print("3. Enter your credentials (handled securely by Plaid)")
    print("4. Select accounts to connect")
    print("5. Choose if it's business or personal")
    print("\nYour accounts will be automatically added to the system!")
    
    webbrowser.open(url)
    
    try:
        print("\n" + "="*50)
        print("Server is running. Press Ctrl+C to stop.")
        print("="*50 + "\n")
        
        # Stream server output
        for line in server_process.stdout:
            print(f"[Server] {line}", end='')
            
    except KeyboardInterrupt:
        print("\n\nStopping server...")
        server_process.terminate()
        server_process.wait()
        print("Server stopped. Your connected accounts have been saved!")
        
        # Show summary
        try:
            from src.api.plaid_manager import PlaidManager
            manager = PlaidManager()
            accounts = manager.list_connected_accounts()
            if accounts:
                print(f"\n✅ You have {len(accounts)} connected account(s)")
            else:
                print("\nNo accounts connected yet.")
        except:
            pass

if __name__ == "__main__":
    main()