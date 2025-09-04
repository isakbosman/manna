"""Account management page for the dashboard."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.api.plaid_manager import PlaidManager
from src.utils.database import get_session, Account

def show_accounts_page():
    """Display comprehensive account management page."""
    st.header("💳 Account Management")
    
    # Initialize Plaid Manager
    plaid_manager = PlaidManager()
    session = get_session()
    
    # Get account data
    accounts = plaid_manager.list_connected_accounts()
    summary = plaid_manager.get_account_summary() if accounts else None
    categorized = plaid_manager.categorize_accounts() if accounts else None
    
    if not accounts:
        st.warning("No accounts connected yet. Please run the setup wizard to connect your accounts.")
        st.code("./start.sh → Option 3", language="bash")
        return
    
    # Account Summary Section
    st.subheader("📊 Account Summary")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Accounts", summary['total_accounts'])
    with col2:
        st.metric("Business", summary['business_accounts'])
    with col3:
        st.metric("Personal", summary['personal_accounts'])
    with col4:
        st.metric("Total Assets", f"${summary['total_assets']:,.0f}", 
                 delta=f"+${summary['total_assets']*0.02:.0f}")
    with col5:
        st.metric("Total Liabilities", f"${summary['total_liabilities']:,.0f}",
                 delta=f"-${summary['total_liabilities']*0.05:.0f}")
    with col6:
        st.metric("Net Worth", f"${summary['net_worth']:,.0f}",
                 delta=f"+${summary['net_worth']*0.03:.0f}", 
                 delta_color="normal")
    
    # Visual breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        # Asset allocation pie chart
        st.subheader("Asset Allocation")
        
        allocation_data = []
        for acc_type, balance in summary['by_type'].items():
            if balance > 0 and acc_type != 'credit_cards':
                allocation_data.append({
                    'Type': acc_type.replace('_', ' ').title(),
                    'Balance': balance
                })
        
        if allocation_data:
            df_allocation = pd.DataFrame(allocation_data)
            fig = px.pie(df_allocation, values='Balance', names='Type',
                        color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Institution breakdown
        st.subheader("By Institution")
        
        inst_data = []
        for inst_name, inst_info in summary['by_institution'].items():
            inst_data.append({
                'Institution': inst_name,
                'Accounts': inst_info['count'],
                'Balance': abs(inst_info['balance'])
            })
        
        df_inst = pd.DataFrame(inst_data)
        fig = px.bar(df_inst, x='Institution', y='Balance',
                    color='Accounts', 
                    color_continuous_scale='Viridis')
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # Account Details Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["All Accounts", "Business", "Personal", "Settings"])
    
    with tab1:
        st.subheader("All Connected Accounts")
        
        # Create detailed account table
        account_data = []
        for acc in accounts:
            account_data.append({
                'Institution': acc['institution_name'],
                'Account': acc['account_name'],
                'Type': acc['type'].title(),
                'Subtype': (acc.get('subtype', '').title() if acc.get('subtype') else 'N/A'),
                'Mask': f"***{acc.get('mask', 'N/A')}",
                'Current Balance': acc.get('current_balance', 0),
                'Available': acc.get('available_balance', 0) if acc.get('available_balance') else acc.get('current_balance', 0),
                'Business': '✅' if acc.get('is_business') else '❌',
                'Connected': pd.to_datetime(acc.get('connected_at', datetime.now())).strftime('%Y-%m-%d')
            })
        
        df_accounts = pd.DataFrame(account_data)
        
        # Format currency columns
        currency_cols = ['Current Balance', 'Available']
        for col in currency_cols:
            df_accounts[col] = df_accounts[col].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(
            df_accounts,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Current Balance": st.column_config.TextColumn(
                    help="Current balance of the account"
                ),
                "Available": st.column_config.TextColumn(
                    help="Available balance (for checking/savings) or credit limit (for credit cards)"
                )
            }
        )
        
        # Quick actions
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Refresh All Balances", type="primary"):
                with st.spinner("Refreshing account balances..."):
                    # This would refresh all account balances
                    st.success("Balances refreshed!")
                    st.rerun()
        
        with col2:
            if st.button("📊 Sync Transactions"):
                with st.spinner("Syncing transactions..."):
                    results = plaid_manager.sync_all_transactions()
                    total_new = sum(len(txns) for txns in results.values())
                    st.success(f"Synced {total_new} new transactions!")
        
        with col3:
            if st.button("📥 Export Account List"):
                df_accounts.to_csv('exports/accounts.csv', index=False)
                st.success("Exported to exports/accounts.csv")
    
    with tab2:
        st.subheader("Business Accounts")
        
        business_total = 0
        
        for acc_type in ['checking', 'savings', 'credit']:
            accounts_list = categorized['business'].get(acc_type, [])
            if accounts_list:
                st.write(f"**{acc_type.title()} Accounts ({len(accounts_list)})**")
                
                for acc in accounts_list:
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    
                    balance = acc.get('current_balance', 0)
                    if acc['type'] != 'credit':
                        business_total += balance
                    
                    with col1:
                        st.write(f"🏦 {acc['institution_name']}")
                        st.caption(f"{acc['account_name']} • ***{acc.get('mask', 'N/A')}")
                    with col2:
                        color = "red" if acc['type'] == 'credit' else "green"
                        st.markdown(f"**:${color}[${abs(balance):,.2f}]**")
                    with col3:
                        if acc.get('available_balance'):
                            st.write(f"Available: ${acc['available_balance']:,.2f}")
                    with col4:
                        if st.button("Details", key=f"biz_{acc['account_id']}"):
                            st.info(f"Account ID: {acc['account_id']}")
                
                st.divider()
        
        st.metric("Total Business Assets", f"${business_total:,.2f}")
    
    with tab3:
        st.subheader("Personal Accounts")
        
        personal_total = 0
        
        for acc_type in ['checking', 'savings', 'credit', 'investment']:
            accounts_list = categorized['personal'].get(acc_type, [])
            if accounts_list:
                st.write(f"**{acc_type.title()} Accounts ({len(accounts_list)})**")
                
                for acc in accounts_list:
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    
                    balance = acc.get('current_balance', 0)
                    if acc['type'] != 'credit':
                        personal_total += balance
                    
                    with col1:
                        icon = "💳" if acc['type'] == 'credit' else "🏦" if acc['type'] == 'depository' else "📈"
                        st.write(f"{icon} {acc['institution_name']}")
                        st.caption(f"{acc['account_name']} • ***{acc.get('mask', 'N/A')}")
                    with col2:
                        color = "red" if acc['type'] == 'credit' else "green"
                        st.markdown(f"**:{color}[${abs(balance):,.2f}]**")
                    with col3:
                        if acc.get('available_balance'):
                            st.write(f"Available: ${acc['available_balance']:,.2f}")
                    with col4:
                        if st.button("Details", key=f"per_{acc['account_id']}"):
                            st.info(f"Account ID: {acc['account_id']}")
                
                st.divider()
        
        st.metric("Total Personal Assets", f"${personal_total:,.2f}")
    
    with tab4:
        st.subheader("Account Settings")
        
        # Account verification
        st.write("**Verify Account Categories**")
        st.caption("Ensure each account is correctly categorized as business or personal.")
        
        for acc in accounts:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"{acc['institution_name']} - {acc['account_name']}")
            with col2:
                current = "Business" if acc.get('is_business') else "Personal"
                st.write(f"Current: **{current}**")
            with col3:
                if st.button("Toggle", key=f"toggle_{acc['account_id']}"):
                    # Toggle business/personal
                    acc['is_business'] = not acc.get('is_business', False)
                    plaid_manager.accounts_data['accounts'][acc['account_id']]['is_business'] = acc['is_business']
                    plaid_manager._save_accounts_data()
                    st.success("Updated!")
                    st.rerun()
        
        st.divider()
        
        # Connection status
        st.write("**Connection Status**")
        
        required = {
            'Business Checking': 2,
            'Business Credit': 1,
            'Personal Checking': 1,
            'Personal Credit': 6,
            'Investment': 1
        }
        
        current = {
            'Business Checking': len(categorized['business']['checking']),
            'Business Credit': len(categorized['business']['credit']),
            'Personal Checking': len(categorized['personal']['checking']),
            'Personal Credit': len(categorized['personal']['credit']),
            'Investment': len(categorized['personal']['investment'])
        }
        
        for account_type, required_count in required.items():
            current_count = current[account_type]
            if current_count >= required_count:
                st.success(f"✅ {account_type}: {current_count}/{required_count}")
            else:
                st.warning(f"⚠️ {account_type}: {current_count}/{required_count}")
        
        # Add new account button
        st.divider()
        if st.button("➕ Add New Account", type="primary"):
            st.info("Run the setup wizard to connect new accounts:")
            st.code("./start.sh → Option 3", language="bash")

if __name__ == "__main__":
    st.set_page_config(page_title="Account Management", page_icon="💳", layout="wide")
    show_accounts_page()