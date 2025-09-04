#!/bin/bash

# Financial Management System Launcher with manna environment

PYTHON_ENV="$HOME/anaconda3/envs/manna/bin/python"
STREAMLIT_ENV="$HOME/anaconda3/envs/manna/bin/streamlit"

echo "======================================"
echo "Financial Management System"
echo "======================================"
echo ""
echo "Select an option:"
echo "1) Run Dashboard (Recommended)"
echo "2) Connect Bank Accounts (Easy)"
echo "3) Advanced Plaid Setup"
echo "4) Run Full Automation"
echo "5) Generate CPA Reports"
echo "6) Test System"
echo "7) Backup Database"
echo "8) Exit"
echo ""
read -p "Enter your choice (1-8): " choice

case $choice in
    1)
        echo "Starting dashboard..."
        $STREAMLIT_ENV run src/dashboard/app.py --server.port 8502
        ;;
    2)
        echo "Launching Plaid Link to connect accounts..."
        $PYTHON_ENV connect_accounts.py
        ;;
    3)
        echo "Starting advanced Plaid setup..."
        $PYTHON_ENV scripts/plaid_setup_enhanced.py
        ;;
    4)
        echo "Starting automation system..."
        $PYTHON_ENV main.py
        ;;
    5)
        echo "Generating CPA reports..."
        $PYTHON_ENV -c "from src.reports.generator import ReportGenerator; from src.utils.database import get_session; from datetime import datetime; rg = ReportGenerator(get_session()); rg.generate_cpa_package(datetime.now().year); print('Reports generated in reports/cpa/')"
        ;;
    6)
        echo "Running system tests..."
        $PYTHON_ENV test_setup.py
        ;;
    7)
        echo "Creating database backup..."
        mkdir -p backups
        timestamp=$(date +%Y%m%d_%H%M%S)
        cp data/financial.db backups/financial_backup_$timestamp.db 2>/dev/null || echo "No database to backup yet"
        echo "Backup saved to backups/financial_backup_$timestamp.db"
        ;;
    8)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo "Invalid option. Please try again."
        ;;
esac