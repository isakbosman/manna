#!/usr/bin/env python3
"""
Weekly Personal Finance Bookkeeping Processor

This script implements the core weekly bookkeeping workflow for personal finance management.
It handles transaction import, ML-assisted categorization, reconciliation, and reporting.

Usage:
    python sample_weekly_processor.py --week-of 2024-01-15
    python sample_weekly_processor.py --dry-run  # Test mode without database changes
"""

import json
import logging
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Transaction:
    """Represents a financial transaction"""
    account_id: str
    date: datetime
    amount: float
    description: str
    merchant_name: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    confidence: Optional[float] = None
    needs_review: bool = False
    is_transfer: bool = False
    is_split: bool = False
    transaction_id: str = ""

class WeeklyBookkeepingProcessor:
    """Main processor for weekly bookkeeping workflow"""
    
    def __init__(self, config_path: str = "categorization_config.json"):
        """Initialize the processor with configuration"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.ml_model = None
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.transactions = []
        self.flagged_transactions = []
        
        logger.info("Initialized Weekly Bookkeeping Processor")
    
    def run_weekly_process(self, week_date: datetime, dry_run: bool = False) -> Dict:
        """Execute the complete weekly bookkeeping process"""
        start_time = datetime.now()
        logger.info(f"Starting weekly process for week of {week_date.strftime('%Y-%m-%d')}")
        
        try:
            # Phase 1: Data Import & Initial Processing (5 minutes target)
            logger.info("Phase 1: Data Import & Initial Processing")
            self.import_transactions(week_date)
            self.run_ml_categorization()
            
            # Phase 2: Manual Review & Categorization (15 minutes target)
            logger.info("Phase 2: Manual Review & Categorization")
            review_items = self.identify_review_items()
            manual_changes = self.process_manual_review(review_items, dry_run)
            
            # Phase 3: Reconciliation & Quality Control (7 minutes target)
            logger.info("Phase 3: Reconciliation & Quality Control")
            reconciliation_status = self.run_reconciliation()
            anomalies = self.detect_anomalies()
            
            # Phase 4: Reporting & Feedback (3 minutes target)
            logger.info("Phase 4: Reporting & Feedback")
            weekly_summary = self.generate_weekly_summary()
            self.update_ml_model(manual_changes)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds() / 60
            
            results = {
                "processing_time_minutes": processing_time,
                "transactions_processed": len(self.transactions),
                "flagged_for_review": len(self.flagged_transactions),
                "manual_changes_made": len(manual_changes),
                "reconciliation_status": reconciliation_status,
                "anomalies_detected": len(anomalies),
                "weekly_summary": weekly_summary,
                "target_time_met": processing_time <= 30
            }
            
            logger.info(f"Weekly process completed in {processing_time:.1f} minutes")
            return results
            
        except Exception as e:
            logger.error(f"Error in weekly process: {str(e)}")
            raise
    
    def import_transactions(self, week_date: datetime) -> None:
        """Import transactions from Plaid API for the specified week"""
        # Calculate date range (week + 3-day buffer for late posting)
        start_date = week_date - timedelta(days=3)
        end_date = week_date + timedelta(days=7)
        
        logger.info(f"Importing transactions from {start_date} to {end_date}")
        
        # TODO: Implement actual Plaid API integration
        # This is a placeholder for the actual implementation
        sample_transactions = self._generate_sample_transactions(start_date, end_date)
        
        self.transactions = sample_transactions
        logger.info(f"Imported {len(self.transactions)} transactions")
    
    def run_ml_categorization(self) -> None:
        """Apply ML model to categorize transactions"""
        if not self.ml_model:
            self._load_or_train_model()
        
        logger.info("Running ML categorization")
        
        for transaction in self.transactions:
            if transaction.category is None:  # Only categorize uncategorized transactions
                features = self._extract_features(transaction)
                prediction = self.ml_model.predict_proba([features])[0]
                
                # Get the category with highest probability
                category_idx = np.argmax(prediction)
                confidence = prediction[category_idx]
                category = self.ml_model.classes_[category_idx]
                
                transaction.category = category
                transaction.confidence = confidence
                
                # Flag for manual review if confidence is low
                if confidence < self.config["ml_model_config"]["confidence_threshold"]:
                    transaction.needs_review = True
                    self.flagged_transactions.append(transaction)
                
                # Also flag large transactions regardless of confidence
                if abs(transaction.amount) > self.config["ml_model_config"]["large_transaction_threshold"]:
                    transaction.needs_review = True
                    if transaction not in self.flagged_transactions:
                        self.flagged_transactions.append(transaction)
        
        logger.info(f"ML categorization complete. {len(self.flagged_transactions)} transactions flagged for review")
    
    def identify_review_items(self) -> List[Transaction]:
        """Identify transactions that need manual review"""
        review_items = []
        
        # Start with flagged transactions
        review_items.extend(self.flagged_transactions)
        
        # Add potential duplicate transactions
        duplicates = self._detect_duplicates()
        review_items.extend(duplicates)
        
        # Add potential split transactions
        split_candidates = self._identify_split_candidates()
        review_items.extend(split_candidates)
        
        # Remove duplicates and sort by amount (largest first)
        review_items = list(set(review_items))
        review_items.sort(key=lambda x: abs(x.amount), reverse=True)
        
        return review_items
    
    def process_manual_review(self, review_items: List[Transaction], dry_run: bool) -> List[Dict]:
        """Process manual review items (simulation for demo)"""
        manual_changes = []
        
        logger.info(f"Processing {len(review_items)} items for manual review")
        
        for transaction in review_items:
            # In a real implementation, this would present items to user for review
            # For demo purposes, we'll simulate some manual decisions
            
            change_made = self._simulate_manual_decision(transaction)
            if change_made:
                manual_changes.append({
                    "transaction_id": transaction.transaction_id,
                    "old_category": change_made.get("old_category"),
                    "new_category": change_made.get("new_category"),
                    "reason": change_made.get("reason"),
                    "timestamp": datetime.now().isoformat()
                })
                
                if not dry_run:
                    # Apply the change to the transaction
                    transaction.category = change_made["new_category"]
                    transaction.needs_review = False
        
        logger.info(f"Manual review complete. {len(manual_changes)} changes made")
        return manual_changes
    
    def run_reconciliation(self) -> Dict:
        """Run account reconciliation checks"""
        logger.info("Running reconciliation checks")
        
        reconciliation_results = {
            "accounts_reconciled": [],
            "balance_discrepancies": [],
            "missing_transactions": [],
            "duplicate_transactions": [],
            "transfer_matches": []
        }
        
        # Group transactions by account
        account_groups = {}
        for transaction in self.transactions:
            if transaction.account_id not in account_groups:
                account_groups[transaction.account_id] = []
            account_groups[transaction.account_id].append(transaction)
        
        # Check each account
        for account_id, transactions in account_groups.items():
            account_result = self._reconcile_account(account_id, transactions)
            reconciliation_results["accounts_reconciled"].append(account_result)
        
        # Detect transfers between accounts
        transfers = self._detect_transfers(account_groups)
        reconciliation_results["transfer_matches"] = transfers
        
        logger.info(f"Reconciliation complete. {len(reconciliation_results['accounts_reconciled'])} accounts processed")
        return reconciliation_results
    
    def detect_anomalies(self) -> List[Dict]:
        """Detect anomalies and potential fraud"""
        logger.info("Running anomaly detection")
        
        anomalies = []
        fraud_rules = self.config["fraud_detection_rules"]
        
        for transaction in self.transactions:
            # Check amount thresholds
            if abs(transaction.amount) > fraud_rules["amount_thresholds"]["immediate_alert"]:
                anomalies.append({
                    "type": "large_transaction",
                    "transaction": transaction,
                    "severity": "high",
                    "reason": f"Transaction amount ${abs(transaction.amount):.2f} exceeds alert threshold"
                })
            
            # Check for unusual merchant patterns
            if self._is_new_merchant(transaction.merchant_name):
                anomalies.append({
                    "type": "new_merchant",
                    "transaction": transaction,
                    "severity": "medium",
                    "reason": f"New merchant: {transaction.merchant_name}"
                })
            
            # Check timing patterns
            if self._is_unusual_timing(transaction.date):
                anomalies.append({
                    "type": "unusual_timing",
                    "transaction": transaction,
                    "severity": "low",
                    "reason": f"Transaction at unusual time: {transaction.date}"
                })
        
        logger.info(f"Anomaly detection complete. {len(anomalies)} anomalies detected")
        return anomalies
    
    def generate_weekly_summary(self) -> Dict:
        """Generate weekly summary report"""
        logger.info("Generating weekly summary")
        
        # Calculate spending by category
        category_spending = {}
        total_spending = 0
        
        for transaction in self.transactions:
            if transaction.amount < 0:  # Spending (negative amounts)
                category = transaction.category or "Uncategorized"
                if category not in category_spending:
                    category_spending[category] = 0
                category_spending[category] += abs(transaction.amount)
                total_spending += abs(transaction.amount)
        
        # Calculate account balances (simulated)
        account_balances = self._calculate_account_balances()
        
        # Generate insights
        top_categories = sorted(category_spending.items(), key=lambda x: x[1], reverse=True)[:5]
        
        summary = {
            "week_ending": datetime.now().strftime('%Y-%m-%d'),
            "total_spending": total_spending,
            "transaction_count": len(self.transactions),
            "category_breakdown": category_spending,
            "top_spending_categories": top_categories,
            "account_balances": account_balances,
            "categorization_stats": {
                "auto_categorized": len([t for t in self.transactions if not t.needs_review]),
                "manual_review": len([t for t in self.transactions if t.needs_review]),
                "uncategorized": len([t for t in self.transactions if t.category is None])
            }
        }
        
        logger.info("Weekly summary generated")
        return summary
    
    def update_ml_model(self, manual_changes: List[Dict]) -> None:
        """Update ML model with manual categorization feedback"""
        if not manual_changes:
            logger.info("No manual changes to incorporate into model")
            return
        
        logger.info(f"Updating ML model with {len(manual_changes)} manual corrections")
        
        # TODO: Implement actual model retraining
        # This would involve:
        # 1. Adding manual corrections to training data
        # 2. Retraining the model with updated data
        # 3. Validating improved performance
        # 4. Saving updated model
        
        logger.info("ML model updated (simulated)")
    
    # Helper methods (implementation details)
    
    def _generate_sample_transactions(self, start_date: datetime, end_date: datetime) -> List[Transaction]:
        """Generate sample transactions for demonstration"""
        import random
        
        sample_merchants = [
            ("WHOLE FOODS MARKET", "Groceries"),
            ("SHELL OIL", "Transportation"),
            ("STARBUCKS", "Restaurants"),
            ("AMAZON.COM", "Shopping"),
            ("NETFLIX.COM", "Entertainment"),
            ("COMCAST", "Utilities"),
            ("TARGET", "Shopping"),
            ("UBER", "Transportation"),
            ("CVS PHARMACY", "Healthcare")
        ]
        
        transactions = []
        current_date = start_date
        
        while current_date <= end_date:
            # Generate 0-5 transactions per day
            daily_count = random.randint(0, 5)
            
            for i in range(daily_count):
                merchant, category = random.choice(sample_merchants)
                amount = round(random.uniform(5.0, 200.0), 2)
                
                transaction = Transaction(
                    account_id=f"account_{random.randint(1, 3)}",
                    date=current_date,
                    amount=-amount,  # Spending is negative
                    description=f"{merchant} Purchase",
                    merchant_name=merchant,
                    transaction_id=f"txn_{len(transactions) + 1}"
                )
                
                transactions.append(transaction)
            
            current_date += timedelta(days=1)
        
        return transactions
    
    def _load_or_train_model(self) -> None:
        """Load existing ML model or train a new one"""
        # For demo purposes, create a simple random forest model
        # In practice, this would load a pre-trained model or train on historical data
        
        self.ml_model = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # Create some sample training data
        sample_features = np.random.rand(100, 10)  # 10 features
        sample_labels = np.random.choice(['Groceries', 'Transportation', 'Restaurants', 'Shopping'], 100)
        
        self.ml_model.fit(sample_features, sample_labels)
        logger.info("ML model loaded/trained")
    
    def _extract_features(self, transaction: Transaction) -> List[float]:
        """Extract features from transaction for ML model"""
        # In a real implementation, this would extract meaningful features
        # For demo, return random features
        return np.random.rand(10).tolist()
    
    def _detect_duplicates(self) -> List[Transaction]:
        """Detect potential duplicate transactions"""
        duplicates = []
        
        # Simple duplicate detection based on amount, date, and merchant
        seen = {}
        
        for transaction in self.transactions:
            key = (transaction.date.date(), abs(transaction.amount), transaction.merchant_name)
            
            if key in seen:
                duplicates.extend([seen[key], transaction])
            else:
                seen[key] = transaction
        
        return duplicates
    
    def _identify_split_candidates(self) -> List[Transaction]:
        """Identify transactions that might need to be split"""
        candidates = []
        
        split_merchants = self.config["split_transaction_rules"]["target_stores"]["merchants"]
        min_amount = self.config["split_transaction_rules"]["minimum_amount"]
        
        for transaction in self.transactions:
            # Check if merchant is in split candidate list and amount is above threshold
            for pattern in split_merchants:
                if pattern.replace("*", "") in transaction.merchant_name and abs(transaction.amount) > min_amount:
                    transaction.is_split = True
                    candidates.append(transaction)
                    break
        
        return candidates
    
    def _simulate_manual_decision(self, transaction: Transaction) -> Optional[Dict]:
        """Simulate manual categorization decision"""
        import random
        
        # Randomly decide whether to make a change (simulate human decision)
        if random.random() < 0.3:  # 30% chance of manual change
            old_category = transaction.category
            new_categories = ["Groceries", "Transportation", "Restaurants", "Shopping", "Entertainment"]
            new_category = random.choice(new_categories)
            
            return {
                "old_category": old_category,
                "new_category": new_category,
                "reason": "Manual correction during review"
            }
        
        return None
    
    def _reconcile_account(self, account_id: str, transactions: List[Transaction]) -> Dict:
        """Reconcile a specific account"""
        total_amount = sum(t.amount for t in transactions)
        
        return {
            "account_id": account_id,
            "transaction_count": len(transactions),
            "net_amount": total_amount,
            "reconciled": True,  # Simplified for demo
            "discrepancies": []
        }
    
    def _detect_transfers(self, account_groups: Dict) -> List[Dict]:
        """Detect transfers between accounts"""
        transfers = []
        
        # Simplified transfer detection
        # In practice, this would be more sophisticated
        
        return transfers
    
    def _is_new_merchant(self, merchant_name: str) -> bool:
        """Check if merchant is new/unknown"""
        # For demo, randomly return True for some merchants
        import random
        return random.random() < 0.1  # 10% chance of being "new"
    
    def _is_unusual_timing(self, transaction_date: datetime) -> bool:
        """Check if transaction timing is unusual"""
        # Check if transaction is in unusual hours (2 AM - 5 AM)
        hour = transaction_date.hour
        return 2 <= hour <= 5
    
    def _calculate_account_balances(self) -> Dict:
        """Calculate current account balances"""
        # Simplified balance calculation
        balances = {}
        
        for transaction in self.transactions:
            if transaction.account_id not in balances:
                balances[transaction.account_id] = 5000.0  # Starting balance
            
            balances[transaction.account_id] += transaction.amount
        
        return balances

def main():
    """Main entry point for the weekly processor"""
    parser = argparse.ArgumentParser(description='Weekly Personal Finance Bookkeeping Processor')
    parser.add_argument('--week-of', type=str, help='Week date (YYYY-MM-DD format)')
    parser.add_argument('--dry-run', action='store_true', help='Run without making database changes')
    parser.add_argument('--config', type=str, default='categorization_config.json', help='Configuration file path')
    
    args = parser.parse_args()
    
    # Parse week date
    if args.week_of:
        try:
            week_date = datetime.strptime(args.week_of, '%Y-%m-%d')
        except ValueError:
            logger.error("Invalid date format. Use YYYY-MM-DD")
            return
    else:
        # Default to current week
        week_date = datetime.now() - timedelta(days=datetime.now().weekday())
    
    try:
        # Initialize processor
        processor = WeeklyBookkeepingProcessor(args.config)
        
        # Run weekly process
        results = processor.run_weekly_process(week_date, args.dry_run)
        
        # Display results
        print("\n" + "="*50)
        print("WEEKLY BOOKKEEPING RESULTS")
        print("="*50)
        print(f"Processing Time: {results['processing_time_minutes']:.1f} minutes")
        print(f"Target Time Met: {'Yes' if results['target_time_met'] else 'No'}")
        print(f"Transactions Processed: {results['transactions_processed']}")
        print(f"Flagged for Review: {results['flagged_for_review']}")
        print(f"Manual Changes Made: {results['manual_changes_made']}")
        print(f"Anomalies Detected: {results['anomalies_detected']}")
        
        print("\nWeekly Summary:")
        summary = results['weekly_summary']
        print(f"Total Spending: ${summary['total_spending']:.2f}")
        print("Top Categories:")
        for category, amount in summary['top_spending_categories']:
            print(f"  {category}: ${amount:.2f}")
        
    except Exception as e:
        logger.error(f"Error running weekly process: {str(e)}")
        raise

if __name__ == "__main__":
    main()