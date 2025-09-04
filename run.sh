#!/bin/bash

# Financial Management System Launcher

echo "======================================"
echo "Financial Management System"
echo "======================================"
echo ""
echo "Select an option:"
echo "1) Run Dashboard (Recommended)"
echo "2) Run Full Automation"
echo "3) Setup Plaid Accounts"
echo "4) Generate CPA Reports"
echo "5) Backup Database"
echo "6) Exit"
echo ""
read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        echo "Starting dashboard..."
        streamlit run src/dashboard/app.py
        ;;
    2)
        echo "Starting automation system..."
        python main.py
        ;;
    3)
        echo "Setting up Plaid accounts..."
        python scripts/setup_plaid.py
        ;;
    4)
        echo "Generating CPA reports..."
        python -c "from src.reports.generator import ReportGenerator; from src.utils.database import get_session; from datetime import datetime; rg = ReportGenerator(get_session()); rg.generate_cpa_package(datetime.now().year); print('Reports generated in reports/cpa/')"
        ;;
    5)
        echo "Creating database backup..."
        timestamp=$(date +%Y%m%d_%H%M%S)
        cp data/financial.db backups/financial_backup_$timestamp.db
        echo "Backup saved to backups/financial_backup_$timestamp.db"
        ;;
    6)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo "Invalid option. Please try again."
        ;;
esac