"""Streamlit page for connecting Plaid accounts."""

import streamlit as st
import streamlit.components.v1 as components
import os
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.api.plaid_manager import PlaidManager
from src.utils.database import init_database, get_session, Account

def show_connect_page():
    """Display Plaid Link connection page in Streamlit."""
    st.header("🏦 Connect Bank Accounts")
    
    # Initialize Plaid Manager
    plaid_manager = PlaidManager()
    
    # Check environment
    env = os.getenv('PLAID_ENV', 'Sandbox')
    if env.lower() == 'sandbox':
        st.info("🧪 Running in Sandbox mode - you can test with fake credentials")
    
    # Connection options
    tab1, tab2, tab3 = st.tabs(["Connect via Plaid", "Manual Token", "Sandbox Accounts"])
    
    with tab1:
        st.subheader("Connect with Plaid Link")
        
        col1, col2 = st.columns(2)
        with col1:
            is_business = st.checkbox("This is a business account", value=False)
        with col2:
            if is_business:
                purpose = st.selectbox("Purpose", ["Operations", "Payroll", "Savings", "Credit"])
        
        if st.button("🔗 Launch Plaid Link", type="primary"):
            try:
                # Generate Link token
                with st.spinner("Generating secure link token..."):
                    link_token = plaid_manager.create_link_token()
                
                if link_token:
                    # Embed Plaid Link
                    plaid_html = f"""
                    <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
                    <button id="link-button" style="
                        background: #4F46E5;
                        color: white;
                        padding: 12px 24px;
                        border: none;
                        border-radius: 6px;
                        font-size: 16px;
                        cursor: pointer;
                        width: 100%;
                    ">Click to Connect Your Bank</button>
                    
                    <div id="result" style="margin-top: 20px;"></div>
                    
                    <script>
                    const linkHandler = Plaid.create({{
                        token: '{link_token}',
                        onSuccess: (public_token, metadata) => {{
                            document.getElementById('result').innerHTML = 
                                '<div style="background: #10B981; color: white; padding: 15px; border-radius: 6px;">' +
                                '<strong>Success!</strong> Copy this token and paste below:<br><br>' +
                                '<code style="background: rgba(0,0,0,0.2); padding: 10px; display: block; margin-top: 10px; word-break: break-all;">' + 
                                public_token + '</code></div>';
                        }},
                        onExit: (err, metadata) => {{
                            if (err) {{
                                document.getElementById('result').innerHTML = 
                                    '<div style="background: #EF4444; color: white; padding: 15px; border-radius: 6px;">' +
                                    'Connection cancelled or failed. Please try again.</div>';
                            }}
                        }},
                        onEvent: (eventName, metadata) => {{
                            console.log('Event:', eventName);
                        }}
                    }});
                    
                    document.getElementById('link-button').onclick = () => {{
                        linkHandler.open();
                    }};
                    
                    // Auto-click the button
                    setTimeout(() => {{
                        document.getElementById('link-button').click();
                    }}, 500);
                    </script>
                    """
                    
                    components.html(plaid_html, height=200)
                    
                    st.info("After connecting, copy the token that appears above and paste it below")
                    
            except Exception as e:
                st.error(f"Failed to create link token: {e}")
                st.info("Make sure your Plaid credentials are set in .env")
        
        # Token exchange
        st.divider()
        public_token = st.text_input("Paste your public token here:", help="This appears after connecting through Plaid Link")
        
        if public_token and st.button("Save Account"):
            try:
                metadata = {
                    'is_business': is_business,
                    'added_at': datetime.now().isoformat(),
                    'source': 'streamlit'
                }
                
                if is_business:
                    metadata['purpose'] = purpose.lower()
                
                # Exchange token
                with st.spinner("Exchanging token and fetching account details..."):
                    access_token, details = plaid_manager.exchange_public_token(public_token, metadata)
                
                st.success(f"✅ Connected {details['institution']}!")
                
                # Show account details
                for acc in details['accounts']:
                    st.write(f"• **{acc['name']}** ({acc['type']})")
                    st.write(f"  Balance: ${acc['balances']['current']:,.2f}")
                
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
                st.balloons()
                
            except Exception as e:
                st.error(f"Failed to exchange token: {e}")
    
    with tab2:
        st.subheader("Manual Token Entry")
        st.info("If you already have a public token from Plaid, enter it here")
        
        manual_token = st.text_area("Public Token", height=100)
        manual_business = st.checkbox("Business account?", key="manual_business")
        
        if manual_token and st.button("Process Token", key="manual_process"):
            # Same exchange logic as above
            st.info("Processing token...")
    
    with tab3:
        st.subheader("Create Sandbox Test Accounts")
        st.warning("Only works in Sandbox mode")
        
        if st.button("Create Test Accounts"):
            if env.lower() != 'sandbox':
                st.error("Only available in Sandbox mode. Set PLAID_ENV=Sandbox in .env")
            else:
                try:
                    with st.spinner("Creating sandbox accounts..."):
                        created = plaid_manager.create_sandbox_accounts()
                    
                    for inst_name, details in created.items():
                        st.success(f"Created {inst_name} accounts:")
                        for acc in details['accounts']:
                            st.write(f"• {acc['name']} - ${acc['balances']['current']:,.2f}")
                    
                except Exception as e:
                    st.error(f"Failed to create sandbox accounts: {e}")
        
        # Show instructions
        st.divider()
        st.markdown("""
        ### Sandbox Testing Credentials
        
        When using Plaid Link in Sandbox mode, use these test credentials:
        
        **Username:** `user_good`  
        **Password:** `pass_good`  
        **PIN (if asked):** `1234`
        
        This will create test accounts with sample transaction data.
        """)
    
    # Show current accounts
    st.divider()
    st.subheader("Currently Connected Accounts")
    
    accounts = plaid_manager.list_connected_accounts()
    if accounts:
        summary = plaid_manager.get_account_summary()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Accounts", summary['total_accounts'])
        with col2:
            st.metric("Total Assets", f"${summary['total_assets']:,.0f}")
        with col3:
            st.metric("Net Worth", f"${summary['net_worth']:,.0f}")
        
        # Account list
        for inst_name, inst_data in summary['by_institution'].items():
            with st.expander(f"{inst_name} ({inst_data['count']} accounts)"):
                for acc in inst_data['accounts']:
                    st.write(f"• {acc['name']} (***{acc['mask']}): ${acc['balance']:,.2f}")
    else:
        st.info("No accounts connected yet. Use the options above to connect your first account.")

if __name__ == "__main__":
    st.set_page_config(page_title="Connect Accounts", page_icon="🏦", layout="wide")
    init_database()
    show_connect_page()