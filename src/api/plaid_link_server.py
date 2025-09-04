"""Simple Flask server to handle Plaid Link integration."""

import os
import json
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.api.plaid_manager import PlaidManager
from src.utils.database import init_database, get_session, Account

app = Flask(__name__)
CORS(app)

# Initialize Plaid Manager
plaid_manager = PlaidManager()

# HTML template for Plaid Link
PLAID_LINK_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Connect Your Bank Account</title>
    <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        p {
            color: #666;
            line-height: 1.6;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 30px;
            font-size: 16px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s;
        }
        button:hover {
            background: #5a67d8;
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .success {
            background: #10b981;
            color: white;
            padding: 15px;
            border-radius: 6px;
            margin-top: 20px;
            display: none;
        }
        .error {
            background: #ef4444;
            color: white;
            padding: 15px;
            border-radius: 6px;
            margin-top: 20px;
            display: none;
        }
        .accounts {
            margin-top: 20px;
            padding: 20px;
            background: #f9fafb;
            border-radius: 6px;
            display: none;
        }
        .account-item {
            padding: 10px;
            margin: 5px 0;
            background: white;
            border-radius: 4px;
            border-left: 4px solid #667eea;
        }
        .loading {
            display: none;
            color: #667eea;
            margin-top: 10px;
        }
        .category-selector {
            margin: 20px 0;
            padding: 20px;
            background: #f3f4f6;
            border-radius: 6px;
            display: none;
        }
        .category-selector label {
            display: block;
            margin: 10px 0;
            cursor: pointer;
        }
        .category-selector input[type="radio"] {
            margin-right: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏦 Connect Your Bank Account</h1>
        <p>Click the button below to securely connect your bank account using Plaid.</p>
        <p style="font-size: 14px; color: #999;">Your credentials are never stored - Plaid handles the connection securely.</p>
        
        <button id="link-button">Connect Account</button>
        <div class="loading" id="loading">Connecting to your bank...</div>
        
        <div class="category-selector" id="category-selector">
            <h3>Account Category</h3>
            <label>
                <input type="radio" name="category" value="business" id="business-radio">
                Business Account
            </label>
            <label>
                <input type="radio" name="category" value="personal" id="personal-radio" checked>
                Personal Account
            </label>
        </div>
        
        <div class="success" id="success-message">
            <strong>Success!</strong> Your account has been connected.
            <div id="account-details"></div>
        </div>
        
        <div class="error" id="error-message"></div>
        
        <div class="accounts" id="accounts-list">
            <h3>Connected Accounts</h3>
            <div id="accounts-container"></div>
        </div>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
            <p style="font-size: 14px; color: #999;">
                Need help? Check the terminal for detailed logs or refresh this page to try again.
            </p>
        </div>
    </div>

    <script>
    let linkHandler = null;
    let publicToken = null;
    
    async function initializeLink() {
        const linkButton = document.getElementById('link-button');
        linkButton.disabled = true;
        linkButton.textContent = 'Initializing...';
        
        try {
            // Get link token from server
            const response = await fetch('/api/create_link_token', {
                method: 'POST',
            });
            const data = await response.json();
            
            if (!data.link_token) {
                throw new Error('Failed to get link token');
            }
            
            // Initialize Plaid Link
            linkHandler = Plaid.create({
                token: data.link_token,
                onSuccess: async (public_token, metadata) => {
                    console.log('Success!', public_token, metadata);
                    publicToken = public_token;
                    
                    // Show category selector
                    document.getElementById('category-selector').style.display = 'block';
                    document.getElementById('loading').style.display = 'block';
                    document.getElementById('loading').textContent = 'Exchanging token...';
                    
                    // Get selected category
                    const isBusinessElement = document.getElementById('business-radio');
                    const isPersonalElement = document.getElementById('personal-radio');
                    
                    // Wait a moment for user to select category if needed
                    setTimeout(async () => {
                        const isBusiness = document.getElementById('business-radio').checked;
                        
                        // Exchange token
                        try {
                            const exchangeResponse = await fetch('/api/exchange_public_token', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    public_token: public_token,
                                    metadata: metadata,
                                    is_business: isBusiness
                                }),
                            });
                            
                            const exchangeData = await exchangeResponse.json();
                            
                            if (exchangeData.success) {
                                document.getElementById('loading').style.display = 'none';
                                document.getElementById('success-message').style.display = 'block';
                                document.getElementById('account-details').innerHTML = 
                                    `<p>Institution: ${exchangeData.institution}</p>
                                     <p>Accounts added: ${exchangeData.accounts_count}</p>
                                     <p>Category: ${isBusiness ? 'Business' : 'Personal'}</p>`;
                                
                                // Refresh accounts list
                                await loadAccounts();
                                
                                linkButton.textContent = 'Connect Another Account';
                                linkButton.disabled = false;
                            } else {
                                throw new Error(exchangeData.error || 'Exchange failed');
                            }
                        } catch (error) {
                            console.error('Exchange error:', error);
                            document.getElementById('loading').style.display = 'none';
                            document.getElementById('error-message').style.display = 'block';
                            document.getElementById('error-message').innerHTML = 
                                `<strong>Error:</strong> ${error.message}`;
                        }
                    }, 1000);
                },
                onLoad: () => {
                    console.log('Plaid Link loaded');
                    linkButton.disabled = false;
                    linkButton.textContent = 'Connect Account';
                },
                onExit: (err, metadata) => {
                    console.log('Exit:', err, metadata);
                    if (err) {
                        document.getElementById('error-message').style.display = 'block';
                        document.getElementById('error-message').innerHTML = 
                            `<strong>Connection cancelled or failed:</strong> ${err.error_message || 'Please try again'}`;
                    }
                    document.getElementById('loading').style.display = 'none';
                },
                onEvent: (eventName, metadata) => {
                    console.log('Event:', eventName, metadata);
                }
            });
            
        } catch (error) {
            console.error('Initialization error:', error);
            document.getElementById('error-message').style.display = 'block';
            document.getElementById('error-message').innerHTML = 
                `<strong>Error:</strong> Failed to initialize. Check your Plaid credentials.`;
            linkButton.textContent = 'Retry';
            linkButton.disabled = false;
        }
    }
    
    async function loadAccounts() {
        try {
            const response = await fetch('/api/accounts');
            const data = await response.json();
            
            if (data.accounts && data.accounts.length > 0) {
                document.getElementById('accounts-list').style.display = 'block';
                const container = document.getElementById('accounts-container');
                container.innerHTML = '';
                
                data.accounts.forEach(account => {
                    const div = document.createElement('div');
                    div.className = 'account-item';
                    div.innerHTML = `
                        <strong>${account.institution_name}</strong> - ${account.account_name}
                        <br>Type: ${account.type} | Mask: ***${account.mask || 'N/A'}
                        <br>Balance: $${(account.current_balance || 0).toLocaleString()}
                        ${account.is_business ? ' (Business)' : ' (Personal)'}
                    `;
                    container.appendChild(div);
                });
            }
        } catch (error) {
            console.error('Failed to load accounts:', error);
        }
    }
    
    // Initialize on page load
    window.onload = async () => {
        await initializeLink();
        await loadAccounts();
    };
    
    // Handle button click
    document.getElementById('link-button').onclick = () => {
        if (linkHandler) {
            document.getElementById('loading').style.display = 'block';
            linkHandler.open();
        }
    };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the Plaid Link interface."""
    return render_template_string(PLAID_LINK_HTML)

@app.route('/api/create_link_token', methods=['POST'])
def create_link_token():
    """Create a Link token for Plaid Link initialization."""
    try:
        link_token = plaid_manager.create_link_token()
        return jsonify({'link_token': link_token})
    except Exception as e:
        print(f"Error creating link token: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/exchange_public_token', methods=['POST'])
def exchange_public_token():
    """Exchange public token for access token and store account info."""
    try:
        data = request.json
        public_token = data['public_token']
        metadata = data.get('metadata', {})
        is_business = data.get('is_business', False)
        
        # Add business flag to metadata
        metadata['is_business'] = is_business
        metadata['added_via'] = 'web_interface'
        metadata['added_at'] = datetime.now().isoformat()
        
        # Exchange token
        access_token, details = plaid_manager.exchange_public_token(public_token, metadata)
        
        # Save to database
        session = get_session()
        for acc in details['accounts']:
            existing = session.query(Account).filter(
                Account.plaid_account_id == acc['account_id']
            ).first()
            
            if not existing:
                db_account = Account(
                    id=f"acc_{acc['account_id'][-8:]}",
                    plaid_account_id=acc['account_id'],
                    institution_name=details['institution'],
                    account_name=acc['name'],
                    account_type=acc['type'],
                    account_subtype=acc.get('subtype'),
                    is_business=is_business,
                    current_balance=acc['balances']['current'],
                    available_balance=acc['balances'].get('available')
                )
                session.add(db_account)
        
        session.commit()
        
        return jsonify({
            'success': True,
            'institution': details['institution'],
            'accounts_count': len(details['accounts']),
            'accounts': details['accounts']
        })
        
    except Exception as e:
        print(f"Error exchanging token: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/accounts')
def get_accounts():
    """Get all connected accounts."""
    try:
        accounts = plaid_manager.list_connected_accounts()
        return jsonify({'accounts': accounts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/summary')
def get_summary():
    """Get account summary."""
    try:
        summary = plaid_manager.get_account_summary()
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def run_server(port=8888):
    """Run the Flask server."""
    print(f"""
    ╔══════════════════════════════════════════════════════╗
    ║           Plaid Link Server Starting                 ║
    ╠══════════════════════════════════════════════════════╣
    ║                                                      ║
    ║  Open your browser to:                              ║
    ║  → http://127.0.0.1:{port}                              ║
    ║                                                      ║
    ║  This will launch Plaid Link to connect accounts    ║
    ║                                                      ║
    ║  Press Ctrl+C to stop the server                    ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    # Initialize database
    init_database()
    
    # Run server on localhost only for security
    app.run(host='127.0.0.1', port=port, debug=False, threaded=True)

if __name__ == '__main__':
    run_server()