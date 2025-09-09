"""
Machine Learning categorization service for automatic transaction classification.
"""

import pickle
import json
import re
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime, timedelta
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
from pathlib import Path
import logging

from ..database.models import Transaction, Category
from ..schemas.transaction import TransactionCategorization

logger = logging.getLogger(__name__)


class MLCategorizationService:
    """
    Machine learning service for transaction categorization.
    Uses a hybrid approach with ML models and rule-based fallbacks.
    """
    
    def __init__(self, model_path: Optional[Path] = None):
        """Initialize the ML categorization service."""
        self.model_path = model_path or Path("/tmp/manna_ml_models")
        self.model_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize models
        self.text_vectorizer: Optional[TfidfVectorizer] = None
        self.text_classifier: Optional[MultinomialNB] = None
        self.amount_classifier: Optional[RandomForestClassifier] = None
        self.category_mapping: Dict[str, str] = {}
        self.confidence_threshold = 0.6
        
        # Load existing models if available
        self.load_models()
        
        # Rule-based patterns for common transactions
        self.rule_patterns = self._initialize_rule_patterns()
    
    def _initialize_rule_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize rule-based patterns for common transaction types."""
        return {
            "Food & Dining": [
                {"pattern": r"(?i)(restaurant|cafe|coffee|starbucks|mcdonald|subway|pizza|food|dining|eat)",
                 "confidence": 0.9},
                {"pattern": r"(?i)(uber.*eats|doordash|grubhub|postmates|delivery)",
                 "confidence": 0.85},
            ],
            "Transportation": [
                {"pattern": r"(?i)(uber|lyft|taxi|transit|metro|bus|train|parking|gas|shell|exxon|chevron)",
                 "confidence": 0.9},
                {"pattern": r"(?i)(airline|flight|airport|car rental)",
                 "confidence": 0.95},
            ],
            "Shopping": [
                {"pattern": r"(?i)(amazon|walmart|target|best buy|home depot|costco|ebay|etsy)",
                 "confidence": 0.9},
                {"pattern": r"(?i)(store|shop|mall|retail|market)",
                 "confidence": 0.7},
            ],
            "Bills & Utilities": [
                {"pattern": r"(?i)(electric|gas|water|internet|cable|phone|verizon|at&t|comcast|utility)",
                 "confidence": 0.95},
                {"pattern": r"(?i)(insurance|mortgage|rent)",
                 "confidence": 0.9},
            ],
            "Entertainment": [
                {"pattern": r"(?i)(netflix|spotify|hulu|disney|movie|theater|cinema|concert|game|steam)",
                 "confidence": 0.9},
                {"pattern": r"(?i)(bar|club|nightlife|entertainment)",
                 "confidence": 0.8},
            ],
            "Healthcare": [
                {"pattern": r"(?i)(hospital|clinic|doctor|medical|pharmacy|cvs|walgreens|dental|health)",
                 "confidence": 0.9},
                {"pattern": r"(?i)(insurance.*health|medicare|medicaid)",
                 "confidence": 0.95},
            ],
            "Income": [
                {"pattern": r"(?i)(salary|payroll|deposit|direct deposit|income|payment from|reimbursement)",
                 "confidence": 0.95},
                {"pattern": r"(?i)(transfer from.*savings|interest earned|dividend)",
                 "confidence": 0.9},
            ],
            "Transfer": [
                {"pattern": r"(?i)(transfer|zelle|venmo|paypal|cash app|wire)",
                 "confidence": 0.85},
            ],
            "Fees & Charges": [
                {"pattern": r"(?i)(fee|charge|penalty|overdraft|interest charged|finance charge)",
                 "confidence": 0.95},
            ],
        }
    
    def categorize_transaction(
        self,
        transaction: Transaction,
        use_ml: bool = True,
        use_rules: bool = True
    ) -> TransactionCategorization:
        """
        Categorize a single transaction using ML and/or rules.
        
        Args:
            transaction: Transaction to categorize
            use_ml: Whether to use ML model
            use_rules: Whether to use rule-based categorization
        
        Returns:
            TransactionCategorization with category and confidence
        """
        category = None
        confidence = 0.0
        alternatives = []
        rules_applied = []
        
        # Try rule-based categorization first (usually more accurate for known patterns)
        if use_rules:
            rule_category, rule_confidence = self._apply_rules(transaction)
            if rule_category and rule_confidence >= self.confidence_threshold:
                category = rule_category
                confidence = rule_confidence
                rules_applied.append(f"Pattern match: {rule_category}")
        
        # Try ML categorization if rules didn't give high confidence
        if use_ml and self.text_classifier and (not category or confidence < 0.8):
            ml_category, ml_confidence, ml_alternatives = self._apply_ml(transaction)
            if ml_confidence > confidence:
                category = ml_category
                confidence = ml_confidence
                alternatives = ml_alternatives
                if not rules_applied:
                    rules_applied.append("ML classification")
        
        # Default fallback
        if not category:
            category = self._get_fallback_category(transaction)
            confidence = 0.3
            rules_applied.append("Fallback classification")
        
        return TransactionCategorization(
            transaction_id=transaction.id,
            suggested_category=category,
            confidence=confidence,
            alternative_categories=alternatives[:3] if alternatives else None,
            rules_applied=rules_applied if rules_applied else None
        )
    
    def _apply_rules(self, transaction: Transaction) -> Tuple[Optional[str], float]:
        """Apply rule-based categorization."""
        text_to_match = f"{transaction.name} {transaction.merchant_name or ''} {transaction.original_description or ''}"
        
        best_category = None
        best_confidence = 0.0
        
        for category, patterns in self.rule_patterns.items():
            for pattern_dict in patterns:
                pattern = pattern_dict["pattern"]
                pattern_confidence = pattern_dict["confidence"]
                
                if re.search(pattern, text_to_match):
                    if pattern_confidence > best_confidence:
                        best_category = category
                        best_confidence = pattern_confidence
        
        # Check amount-based rules
        if transaction.amount > 0:
            # Likely income
            if best_confidence < 0.8:
                if transaction.amount > 1000:
                    best_category = "Income"
                    best_confidence = max(best_confidence, 0.7)
        
        return best_category, best_confidence
    
    def _apply_ml(self, transaction: Transaction) -> Tuple[Optional[str], float, List[Dict[str, float]]]:
        """Apply ML model for categorization."""
        try:
            # Prepare features
            text_features = f"{transaction.name} {transaction.merchant_name or ''}"
            
            # Vectorize text
            X_text = self.text_vectorizer.transform([text_features])
            
            # Get predictions with probabilities
            probabilities = self.text_classifier.predict_proba(X_text)[0]
            classes = self.text_classifier.classes_
            
            # Get top predictions
            top_indices = np.argsort(probabilities)[-3:][::-1]
            
            best_category = classes[top_indices[0]]
            best_confidence = probabilities[top_indices[0]]
            
            alternatives = [
                {"category": classes[idx], "confidence": float(probabilities[idx])}
                for idx in top_indices[1:] if probabilities[idx] > 0.1
            ]
            
            return best_category, float(best_confidence), alternatives
            
        except Exception as e:
            logger.error(f"ML categorization failed: {e}")
            return None, 0.0, []
    
    def _get_fallback_category(self, transaction: Transaction) -> str:
        """Get fallback category based on simple heuristics."""
        if transaction.amount > 0:
            return "Income"
        elif transaction.amount < -500:
            return "Bills & Utilities"
        elif "transfer" in transaction.name.lower():
            return "Transfer"
        else:
            return "Other"
    
    def train_model(
        self,
        transactions: List[Transaction],
        test_size: float = 0.2,
        min_samples: int = 100
    ) -> Dict[str, Any]:
        """
        Train the ML model on historical transactions.
        
        Args:
            transactions: List of labeled transactions for training
            test_size: Proportion of data to use for testing
            min_samples: Minimum samples required for training
        
        Returns:
            Training metrics and results
        """
        # Filter transactions with categories
        labeled_transactions = [
            t for t in transactions
            if t.user_category or t.primary_category
        ]
        
        if len(labeled_transactions) < min_samples:
            return {
                "success": False,
                "error": f"Insufficient training data. Need at least {min_samples} labeled transactions, got {len(labeled_transactions)}"
            }
        
        # Prepare training data
        X_text = []
        y = []
        
        for txn in labeled_transactions:
            text_features = f"{txn.name} {txn.merchant_name or ''} {txn.original_description or ''}"
            X_text.append(text_features)
            y.append(txn.user_category or txn.primary_category)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_text, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Train text vectorizer
        self.text_vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            stop_words='english',
            lowercase=True
        )
        X_train_vectorized = self.text_vectorizer.fit_transform(X_train)
        X_test_vectorized = self.text_vectorizer.transform(X_test)
        
        # Train classifier
        self.text_classifier = MultinomialNB(alpha=0.1)
        self.text_classifier.fit(X_train_vectorized, y_train)
        
        # Evaluate
        y_pred = self.text_classifier.predict(X_test_vectorized)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Save models
        self.save_models()
        
        # Get detailed metrics
        report = classification_report(y_test, y_pred, output_dict=True)
        
        return {
            "success": True,
            "accuracy": accuracy,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "categories": list(set(y)),
            "classification_report": report,
            "model_saved": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def update_from_feedback(
        self,
        transaction_id: str,
        correct_category: str,
        was_correct: bool
    ) -> Dict[str, Any]:
        """
        Update model based on user feedback.
        
        Args:
            transaction_id: ID of the transaction
            correct_category: The correct category
            was_correct: Whether the prediction was correct
        
        Returns:
            Feedback processing result
        """
        # Store feedback for batch retraining
        feedback_file = self.model_path / "feedback.jsonl"
        
        feedback_entry = {
            "transaction_id": transaction_id,
            "correct_category": correct_category,
            "was_correct": was_correct,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        with open(feedback_file, "a") as f:
            f.write(json.dumps(feedback_entry) + "\n")
        
        # Check if we should trigger retraining
        feedback_count = sum(1 for _ in open(feedback_file))
        
        retrain_triggered = False
        if feedback_count >= 100:  # Retrain every 100 feedback items
            retrain_triggered = True
            # In production, this would trigger an async retraining job
        
        return {
            "success": True,
            "feedback_recorded": True,
            "total_feedback": feedback_count,
            "retrain_triggered": retrain_triggered
        }
    
    def batch_categorize(
        self,
        transactions: List[Transaction],
        parallel: bool = False
    ) -> List[TransactionCategorization]:
        """
        Categorize multiple transactions efficiently.
        
        Args:
            transactions: List of transactions to categorize
            parallel: Whether to use parallel processing
        
        Returns:
            List of categorization results
        """
        results = []
        
        for transaction in transactions:
            result = self.categorize_transaction(transaction)
            results.append(result)
        
        return results
    
    def get_model_metrics(self) -> Dict[str, Any]:
        """Get current model performance metrics."""
        metrics = {
            "model_loaded": self.text_classifier is not None,
            "vectorizer_loaded": self.text_vectorizer is not None,
            "confidence_threshold": self.confidence_threshold,
            "rule_categories": list(self.rule_patterns.keys()),
            "model_path": str(self.model_path)
        }
        
        # Load training metrics if available
        metrics_file = self.model_path / "metrics.json"
        if metrics_file.exists():
            with open(metrics_file) as f:
                training_metrics = json.load(f)
                metrics.update(training_metrics)
        
        return metrics
    
    def save_models(self):
        """Save trained models to disk."""
        if self.text_vectorizer:
            joblib.dump(self.text_vectorizer, self.model_path / "text_vectorizer.pkl")
        
        if self.text_classifier:
            joblib.dump(self.text_classifier, self.model_path / "text_classifier.pkl")
        
        # Save metadata
        metadata = {
            "saved_at": datetime.utcnow().isoformat(),
            "confidence_threshold": self.confidence_threshold,
            "categories": list(self.text_classifier.classes_) if self.text_classifier else []
        }
        
        with open(self.model_path / "metadata.json", "w") as f:
            json.dump(metadata, f)
    
    def load_models(self):
        """Load trained models from disk."""
        try:
            vectorizer_path = self.model_path / "text_vectorizer.pkl"
            classifier_path = self.model_path / "text_classifier.pkl"
            
            if vectorizer_path.exists():
                self.text_vectorizer = joblib.load(vectorizer_path)
                logger.info("Loaded text vectorizer")
            
            if classifier_path.exists():
                self.text_classifier = joblib.load(classifier_path)
                logger.info("Loaded text classifier")
            
            # Load metadata
            metadata_path = self.model_path / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path) as f:
                    metadata = json.load(f)
                    self.confidence_threshold = metadata.get("confidence_threshold", 0.6)
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
    
    def export_training_data(
        self,
        transactions: List[Transaction],
        output_path: Path
    ) -> Dict[str, Any]:
        """Export training data for external analysis."""
        data = []
        
        for txn in transactions:
            data.append({
                "id": str(txn.id),
                "name": txn.name,
                "merchant": txn.merchant_name,
                "amount": float(txn.amount),
                "date": txn.date.isoformat(),
                "category": txn.user_category or txn.primary_category,
                "user_category": txn.user_category,
                "ml_category": txn.primary_category,
                "confidence": txn.confidence_level
            })
        
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        
        return {
            "success": True,
            "exported_transactions": len(data),
            "output_path": str(output_path)
        }


# Singleton instance
ml_service = MLCategorizationService()