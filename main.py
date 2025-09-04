"""Main orchestrator for the financial management system."""

import os
import schedule
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

from src.api.plaid_client import PlaidClient
from src.ml.categorizer import TransactionCategorizer
from src.utils.database import init_database, get_session, Transaction, Account
from src.reports.generator import ReportGenerator

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/financial_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FinancialOrchestrator:
    """Main orchestrator for all financial operations."""
    
    def __init__(self):
        self.plaid_client = PlaidClient()
        self.categorizer = TransactionCategorizer()
        self.session = get_session()
        self.report_generator = ReportGenerator(self.session)
        logger.info("Financial Orchestrator initialized")
    
    def daily_sync(self):
        """Daily sync of all transactions from Plaid."""
        logger.info("Starting daily transaction sync...")
        
        try:
            # Fetch transactions from all accounts
            all_transactions = self.plaid_client.fetch_all_accounts_transactions(days_back=7)
            
            total_new = 0
            for account_name, transactions in all_transactions.items():
                new_count = self._process_transactions(account_name, transactions)
                total_new += new_count
                logger.info(f"Processed {new_count} new transactions from {account_name}")
            
            # Run ML categorization on new transactions
            self._categorize_new_transactions()
            
            # Check for anomalies
            self._detect_anomalies()
            
            # Backup database
            self._backup_database()
            
            logger.info(f"Daily sync completed. {total_new} new transactions processed.")
            
        except Exception as e:
            logger.error(f"Error in daily sync: {e}")
    
    def _process_transactions(self, account_name: str, transactions: list) -> int:
        """Process and store transactions in database."""
        # Get or create account
        account = self.session.query(Account).filter(
            Account.account_name == account_name
        ).first()
        
        if not account:
            # Create new account
            account = Account(
                id=f"acc_{account_name}",
                account_name=account_name,
                account_type='checking',  # Would be determined from Plaid
                is_business=account_name.startswith('business')
            )
            self.session.add(account)
            self.session.commit()
        
        new_count = 0
        for txn_data in transactions:
            # Check if transaction already exists
            existing = self.session.query(Transaction).filter(
                Transaction.plaid_transaction_id == txn_data['id']
            ).first()
            
            if not existing:
                # Create new transaction
                transaction = Transaction(
                    id=f"txn_{txn_data['id']}",
                    plaid_transaction_id=txn_data['id'],
                    account_id=account.id,
                    amount=txn_data['amount'],
                    date=txn_data['date'],
                    merchant_name=txn_data.get('merchant_name'),
                    name=txn_data['name'],
                    pending=txn_data['pending'],
                    category=txn_data.get('category'),
                    subcategory=txn_data.get('subcategory'),
                    location_city=txn_data['location'].get('city'),
                    location_state=txn_data['location'].get('state'),
                    payment_method=txn_data.get('payment_channel'),
                    is_business=account.is_business
                )
                self.session.add(transaction)
                new_count += 1
        
        self.session.commit()
        return new_count
    
    def _categorize_new_transactions(self):
        """Run ML categorization on uncategorized transactions."""
        # Get uncategorized transactions
        uncategorized = self.session.query(Transaction).filter(
            Transaction.ml_category == None
        ).all()
        
        if not uncategorized:
            return
        
        logger.info(f"Categorizing {len(uncategorized)} transactions...")
        
        # Prepare data for ML model
        import pandas as pd
        txn_df = pd.DataFrame([{
            'merchant_name': t.merchant_name or '',
            'name': t.name,
            'amount': t.amount,
            'date': t.date,
            'is_business': t.is_business
        } for t in uncategorized])
        
        # Get predictions
        predictions = self.categorizer.predict(txn_df)
        
        # Update transactions with predictions
        for txn, pred_row in zip(uncategorized, predictions.itertuples()):
            txn.ml_category = pred_row.predicted_category
            txn.ml_confidence = pred_row.confidence
            
            # Auto-apply high confidence predictions
            if pred_row.confidence > 0.9:
                txn.category = pred_row.predicted_category
            
            # Detect tax deductible expenses
            if txn.is_business and txn.ml_category in self.categorizer.BUSINESS_CATEGORIES:
                txn.is_tax_deductible = True
        
        self.session.commit()
        logger.info("Categorization completed")
    
    def _detect_anomalies(self):
        """Detect unusual transactions or patterns."""
        # Check for large transactions
        large_threshold = 5000
        large_txns = self.session.query(Transaction).filter(
            Transaction.amount > large_threshold,
            Transaction.date >= datetime.now() - timedelta(days=1)
        ).all()
        
        if large_txns:
            logger.warning(f"Found {len(large_txns)} large transactions (>${large_threshold})")
        
        # Check for duplicate transactions
        from sqlalchemy import func
        duplicates = self.session.query(
            Transaction.merchant_name,
            Transaction.amount,
            func.count(Transaction.id).label('count')
        ).filter(
            Transaction.date >= datetime.now() - timedelta(days=7)
        ).group_by(
            Transaction.merchant_name,
            Transaction.amount
        ).having(func.count(Transaction.id) > 1).all()
        
        if duplicates:
            logger.warning(f"Found potential duplicate transactions: {duplicates}")
    
    def _backup_database(self):
        """Create daily backup of database."""
        import shutil
        
        db_path = os.getenv('DATABASE_PATH', 'data/financial.db')
        backup_path = f"backups/financial_{datetime.now().strftime('%Y%m%d')}.db"
        
        os.makedirs('backups', exist_ok=True)
        shutil.copy2(db_path, backup_path)
        logger.info(f"Database backed up to {backup_path}")
        
        # Keep only last 30 days of backups
        self._cleanup_old_backups()
    
    def _cleanup_old_backups(self):
        """Remove backups older than 30 days."""
        import glob
        
        cutoff_date = datetime.now() - timedelta(days=30)
        
        for backup_file in glob.glob('backups/financial_*.db'):
            # Extract date from filename
            date_str = backup_file.split('_')[1].split('.')[0]
            file_date = datetime.strptime(date_str, '%Y%m%d')
            
            if file_date < cutoff_date:
                os.remove(backup_file)
                logger.info(f"Removed old backup: {backup_file}")
    
    def weekly_bookkeeping(self):
        """Weekly bookkeeping review process."""
        logger.info("Starting weekly bookkeeping review...")
        
        # Get transactions needing review
        needs_review = self.session.query(Transaction).filter(
            Transaction.ml_confidence < 0.8,
            Transaction.user_category == None,
            Transaction.date >= datetime.now() - timedelta(days=7)
        ).all()
        
        logger.info(f"{len(needs_review)} transactions need manual review")
        
        # This would trigger a notification to review in the dashboard
        # In production, could send email or Slack notification
    
    def monthly_close(self):
        """Monthly financial close process."""
        logger.info("Starting monthly close process...")
        
        # Generate monthly reports
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # Generate CPA package
        package = self.report_generator.generate_cpa_package(current_year)
        
        logger.info("Monthly close completed. Reports generated.")
    
    def quarterly_tax_estimates(self):
        """Calculate and save quarterly tax estimates."""
        logger.info("Calculating quarterly tax estimates...")
        
        from src.utils.database import TaxEstimate
        from sqlalchemy import func
        
        current_year = datetime.now().year
        current_quarter = (datetime.now().month - 1) // 3 + 1
        
        # Calculate YTD income and expenses
        ytd_start = datetime(current_year, 1, 1)
        ytd_end = datetime.now()
        
        business_income = self.session.query(func.sum(Transaction.amount)).filter(
            Transaction.is_business == True,
            Transaction.amount > 0,
            Transaction.date >= ytd_start,
            Transaction.date <= ytd_end
        ).scalar() or 0
        
        business_expenses = abs(self.session.query(func.sum(Transaction.amount)).filter(
            Transaction.is_business == True,
            Transaction.amount < 0,
            Transaction.date >= ytd_start,
            Transaction.date <= ytd_end
        ).scalar() or 0)
        
        net_income = business_income - business_expenses
        
        # Calculate estimated taxes (simplified)
        federal_tax = net_income * 0.22
        state_tax = net_income * 0.093  # California
        se_tax = net_income * 0.9235 * 0.153
        
        quarterly_federal = federal_tax / 4
        quarterly_state = state_tax / 4
        
        # Save estimate
        estimate = TaxEstimate(
            tax_year=current_year,
            quarter=current_quarter,
            business_income=business_income,
            business_expenses=business_expenses,
            estimated_quarterly_tax=quarterly_federal + quarterly_state,
            federal_amount=quarterly_federal,
            state_amount=quarterly_state,
            effective_rate=(federal_tax + state_tax) / net_income if net_income > 0 else 0
        )
        
        self.session.add(estimate)
        self.session.commit()
        
        logger.info(f"Q{current_quarter} tax estimate: Federal ${quarterly_federal:.2f}, State ${quarterly_state:.2f}")
    
    def run_scheduler(self):
        """Run the scheduling system."""
        # Schedule daily sync at 6 AM
        schedule.every().day.at("06:00").do(self.daily_sync)
        
        # Schedule weekly bookkeeping on Sundays
        schedule.every().sunday.at("10:00").do(self.weekly_bookkeeping)
        
        # Schedule monthly close on the 1st
        schedule.every().month.do(self.monthly_close)
        
        # Schedule quarterly tax estimates
        schedule.every(3).months.do(self.quarterly_tax_estimates)
        
        logger.info("Scheduler started. Press Ctrl+C to stop.")
        
        # Run initial sync
        self.daily_sync()
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def main():
    """Main entry point."""
    # Initialize database
    engine = init_database()
    logger.info("Database initialized")
    
    # Create orchestrator
    orchestrator = FinancialOrchestrator()
    
    # Run scheduler
    try:
        orchestrator.run_scheduler()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")

if __name__ == "__main__":
    main()