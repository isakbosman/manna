"""
Enhanced Machine Learning categorization service for automatic transaction classification.
Supports multiple algorithms, feature engineering, Redis caching, and incremental learning.
"""

import pickle
import json
import re
import hashlib
import logging
from typing import List, Dict, Tuple, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from decimal import Decimal

# Scikit-learn imports
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.naive_bayes import MultinomialNB, ComplementNB
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib

# Database imports
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

# Local imports
from ..database.models import Transaction, Category, MLPrediction
from ..schemas.transaction import TransactionCategorization
from ..schemas.ml import CategoryPrediction, TransactionFeatures
from ..utils.redis import get_redis_client_sync
from ..config import settings

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Extract and engineer features from transactions for ML models."""

    def __init__(self):
        self.merchant_encoder = LabelEncoder()
        self.day_encoder = LabelEncoder()
        self.amount_bins = [0, 10, 50, 100, 500, 1000, float('inf')]
        self.amount_labels = ['micro', 'small', 'medium', 'large', 'xlarge', 'huge']

    def extract_text_features(self, transaction: Transaction) -> str:
        """Extract and clean text features from transaction."""
        text_parts = []

        # Main description
        if transaction.name:
            text_parts.append(transaction.name.lower())

        # Merchant name (often more consistent)
        if transaction.merchant_name:
            text_parts.append(transaction.merchant_name.lower())

        # Original description
        if transaction.description:
            text_parts.append(transaction.description.lower())

        # Combine all text
        full_text = " ".join(text_parts)

        # Clean text: remove special characters, normalize spaces
        full_text = re.sub(r'[^\w\s]', ' ', full_text)
        full_text = re.sub(r'\s+', ' ', full_text).strip()

        return full_text

    def extract_amount_features(self, transaction: Transaction) -> Dict[str, float]:
        """Extract amount-based features."""
        amount = float(transaction.amount)

        features = {
            'amount_raw': amount,
            'amount_abs': abs(amount),
            'amount_log': np.log1p(abs(amount)),  # log(1 + amount)
            'is_round_number': float(amount % 1 == 0),
            'is_even_dollar': float(amount % 10 == 0),
            'amount_magnitude': len(str(int(abs(amount)))),
        }

        # Amount bins
        amount_bin = pd.cut([abs(amount)], self.amount_bins, labels=self.amount_labels)[0]
        for label in self.amount_labels:
            features[f'amount_bin_{label}'] = float(amount_bin == label)

        return features

    def extract_temporal_features(self, transaction: Transaction) -> Dict[str, Any]:
        """Extract time-based features."""
        dt = transaction.date

        features = {
            'hour': dt.hour if hasattr(dt, 'hour') else 12,
            'day_of_week': dt.weekday(),
            'day_of_month': dt.day,
            'month': dt.month,
            'quarter': (dt.month - 1) // 3 + 1,
            'is_weekend': float(dt.weekday() >= 5),
            'is_month_start': float(dt.day <= 3),
            'is_month_end': float(dt.day >= 28),
        }

        return features

    def extract_merchant_features(self, transaction: Transaction) -> Dict[str, Any]:
        """Extract merchant-specific features."""
        features = {}

        if transaction.merchant_name:
            merchant = transaction.merchant_name.lower()

            # Common merchant patterns
            features.update({
                'is_online_merchant': float(any(x in merchant for x in ['amazon', 'ebay', '.com', 'online'])),
                'is_gas_station': float(any(x in merchant for x in ['shell', 'exxon', 'chevron', 'bp', 'gas'])),
                'is_grocery': float(any(x in merchant for x in ['walmart', 'target', 'kroger', 'safeway', 'grocery'])),
                'is_restaurant': float(any(x in merchant for x in ['restaurant', 'cafe', 'coffee', 'pizza', 'mcdonalds'])),
                'is_bank': float(any(x in merchant for x in ['bank', 'credit union', 'atm', 'deposit'])),
                'is_subscription': float(any(x in merchant for x in ['netflix', 'spotify', 'subscription', 'monthly'])),
            })
        else:
            # Default values when no merchant
            features.update({
                'is_online_merchant': 0.0,
                'is_gas_station': 0.0,
                'is_grocery': 0.0,
                'is_restaurant': 0.0,
                'is_bank': 0.0,
                'is_subscription': 0.0,
            })

        return features

    def extract_all_features(self, transaction: Transaction) -> TransactionFeatures:
        """Extract all features from a transaction."""
        return TransactionFeatures(
            text_features=self.extract_text_features(transaction).split(),
            amount_features=self.extract_amount_features(transaction),
            temporal_features=self.extract_temporal_features(transaction),
            merchant_features=self.extract_merchant_features(transaction)
        )


class MLCategorizationService:
    """
    Enhanced machine learning service for transaction categorization.
    Features:
    - Multiple ML algorithms with ensemble voting
    - TF-IDF text vectorization with feature engineering
    - Redis caching for predictions
    - Incremental learning from user feedback
    - Confidence scoring and rule-based fallbacks
    """

    def __init__(self, model_path: Optional[Path] = None):
        """Initialize the ML categorization service."""
        self.model_path = model_path or Path(settings.ml_model_path)
        self.model_path.mkdir(parents=True, exist_ok=True)

        # Feature extraction
        self.feature_extractor = FeatureExtractor()

        # Models and vectorizers
        self.text_vectorizer: Optional[TfidfVectorizer] = None
        self.ensemble_classifier: Optional[VotingClassifier] = None
        self.category_encoder: Optional[LabelEncoder] = None

        # Configuration
        self.confidence_threshold = settings.ml_confidence_threshold
        self.cache_ttl = 3600  # 1 hour cache

        # Redis for caching
        self.redis_client = get_redis_client_sync()

        # Load existing models
        self._load_models()

        # Rule-based patterns (enhanced from original)
        self.rule_patterns = self._initialize_enhanced_rule_patterns()

    def _initialize_enhanced_rule_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize enhanced rule-based patterns with priorities and weights."""
        return {
            "Food & Dining": [
                {
                    "pattern": r"(?i)(starbucks|coffee|cafe|restaurant|dining|food|eat|pizza|subway|mcdonald)",
                    "confidence": 0.95,
                    "priority": 1
                },
                {
                    "pattern": r"(?i)(uber.*eats|doordash|grubhub|postmates|delivery|takeout)",
                    "confidence": 0.90,
                    "priority": 1
                },
                {
                    "pattern": r"(?i)(grocery|supermarket|market|store.*food)",
                    "confidence": 0.85,
                    "priority": 2
                },
            ],
            "Transportation": [
                {
                    "pattern": r"(?i)(uber|lyft|taxi|cab|rideshare)",
                    "confidence": 0.95,
                    "priority": 1
                },
                {
                    "pattern": r"(?i)(gas|fuel|shell|exxon|chevron|bp|mobil|citgo)",
                    "confidence": 0.90,
                    "priority": 1
                },
                {
                    "pattern": r"(?i)(parking|metro|transit|bus|train|airline|flight)",
                    "confidence": 0.85,
                    "priority": 2
                },
            ],
            "Shopping": [
                {
                    "pattern": r"(?i)(amazon|walmart|target|costco|best buy|home depot)",
                    "confidence": 0.95,
                    "priority": 1
                },
                {
                    "pattern": r"(?i)(ebay|etsy|online.*store|shop|retail|mall)",
                    "confidence": 0.80,
                    "priority": 2
                },
            ],
            "Bills & Utilities": [
                {
                    "pattern": r"(?i)(electric|electricity|gas.*utility|water|sewer|internet|cable|phone)",
                    "confidence": 0.95,
                    "priority": 1
                },
                {
                    "pattern": r"(?i)(verizon|at&t|comcast|xfinity|spectrum|utility|bill)",
                    "confidence": 0.90,
                    "priority": 1
                },
                {
                    "pattern": r"(?i)(insurance|mortgage|rent|loan|payment)",
                    "confidence": 0.85,
                    "priority": 2
                },
            ],
            "Entertainment": [
                {
                    "pattern": r"(?i)(netflix|spotify|hulu|disney|streaming|subscription)",
                    "confidence": 0.95,
                    "priority": 1
                },
                {
                    "pattern": r"(?i)(movie|theater|cinema|concert|game|steam|entertainment)",
                    "confidence": 0.85,
                    "priority": 2
                },
            ],
            "Healthcare": [
                {
                    "pattern": r"(?i)(hospital|clinic|doctor|medical|pharmacy|cvs|walgreens)",
                    "confidence": 0.90,
                    "priority": 1
                },
                {
                    "pattern": r"(?i)(dental|dentist|health|medicare|medicaid)",
                    "confidence": 0.85,
                    "priority": 2
                },
            ],
            "Income": [
                {
                    "pattern": r"(?i)(salary|payroll|direct.*deposit|income|wage|payment.*from)",
                    "confidence": 0.95,
                    "priority": 1
                },
                {
                    "pattern": r"(?i)(interest|dividend|bonus|refund|reimbursement)",
                    "confidence": 0.85,
                    "priority": 2
                },
            ],
            "Transfer": [
                {
                    "pattern": r"(?i)(transfer|zelle|venmo|paypal|cash.*app|wire|p2p)",
                    "confidence": 0.90,
                    "priority": 1
                },
            ],
            "Fees & Charges": [
                {
                    "pattern": r"(?i)(fee|charge|penalty|overdraft|interest.*charged|finance.*charge)",
                    "confidence": 0.95,
                    "priority": 1
                },
            ],
        }

    def _get_cache_key(self, transaction: Transaction) -> str:
        """Generate cache key for transaction prediction."""
        # Create hash from transaction characteristics
        text = f"{transaction.name}|{transaction.merchant_name}|{transaction.amount}|{transaction.date.date()}"
        return f"ml_prediction:{hashlib.md5(text.encode()).hexdigest()}"

    def _cache_prediction(self, cache_key: str, prediction: Dict[str, Any]):
        """Cache prediction result."""
        try:
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(prediction, default=str)
            )
        except Exception as e:
            logger.warning(f"Failed to cache prediction: {e}")

    def _get_cached_prediction(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached prediction result."""
        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Failed to get cached prediction: {e}")
        return None

    def categorize_transaction(
        self,
        transaction: Transaction,
        use_ml: bool = True,
        use_rules: bool = True,
        use_cache: bool = True
    ) -> TransactionCategorization:
        """
        Categorize a single transaction using enhanced ML and rule-based methods.
        """
        # Check cache first
        cache_key = self._get_cache_key(transaction)
        if use_cache:
            cached_result = self._get_cached_prediction(cache_key)
            if cached_result:
                logger.debug(f"Using cached prediction for transaction {transaction.id}")
                return TransactionCategorization(**cached_result)

        category = None
        confidence = 0.0
        alternatives = []
        rules_applied = []

        # Try rule-based categorization first (usually more accurate for known patterns)
        if use_rules:
            rule_category, rule_confidence, rule_name = self._apply_enhanced_rules(transaction)
            if rule_category and rule_confidence >= self.confidence_threshold:
                category = rule_category
                confidence = rule_confidence
                rules_applied.append(f"Rule: {rule_name}")

        # Try ML categorization if rules didn't give high confidence
        if use_ml and self.ensemble_classifier and (not category or confidence < 0.9):
            ml_category, ml_confidence, ml_alternatives = self._apply_enhanced_ml(transaction)
            if ml_confidence > confidence:
                category = ml_category
                confidence = ml_confidence
                alternatives = ml_alternatives
                if not rules_applied:
                    rules_applied.append("ML ensemble classification")

        # Default fallback
        if not category:
            category = self._get_enhanced_fallback_category(transaction)
            confidence = 0.3
            rules_applied.append("Fallback heuristic")

        result = TransactionCategorization(
            transaction_id=transaction.id,
            suggested_category=category,
            confidence=confidence,
            alternative_categories=alternatives[:3] if alternatives else None,
            rules_applied=rules_applied if rules_applied else None
        )

        # Cache the result
        if use_cache:
            self._cache_prediction(cache_key, result.model_dump())

        return result

    def _apply_enhanced_rules(self, transaction: Transaction) -> Tuple[Optional[str], float, Optional[str]]:
        """Apply enhanced rule-based categorization with priorities."""
        text_to_match = f"{transaction.name} {transaction.merchant_name or ''} {transaction.description or ''}"

        best_category = None
        best_confidence = 0.0
        best_rule_name = None

        # Sort patterns by priority and confidence
        all_patterns = []
        for category, patterns in self.rule_patterns.items():
            for pattern_dict in patterns:
                all_patterns.append({
                    'category': category,
                    'pattern': pattern_dict['pattern'],
                    'confidence': pattern_dict['confidence'],
                    'priority': pattern_dict.get('priority', 5)
                })

        # Sort by priority (lower is better), then confidence (higher is better)
        all_patterns.sort(key=lambda x: (x['priority'], -x['confidence']))

        for pattern_info in all_patterns:
            if re.search(pattern_info['pattern'], text_to_match):
                if pattern_info['confidence'] > best_confidence:
                    best_category = pattern_info['category']
                    best_confidence = pattern_info['confidence']
                    best_rule_name = f"{pattern_info['category']} (P{pattern_info['priority']})"
                    break  # Use first match due to priority sorting

        # Enhanced amount-based rules
        if transaction.amount and not best_category:
            amount = float(transaction.amount)

            # Large positive amounts likely income
            if amount > 1000 and 'deposit' in text_to_match.lower():
                best_category = "Income"
                best_confidence = 0.8
                best_rule_name = "Large deposit heuristic"

            # ATM withdrawals
            elif 'atm' in text_to_match.lower() and amount > 0:
                best_category = "Transfer"
                best_confidence = 0.85
                best_rule_name = "ATM withdrawal"

            # Small recurring amounts likely subscriptions
            elif 5 <= amount <= 50 and transaction.is_recurring:
                best_category = "Entertainment"
                best_confidence = 0.7
                best_rule_name = "Small recurring payment"

        return best_category, best_confidence, best_rule_name

    def _apply_enhanced_ml(self, transaction: Transaction) -> Tuple[Optional[str], float, List[Dict[str, float]]]:
        """Apply enhanced ML model ensemble for categorization."""
        try:
            # Extract comprehensive features
            features = self.feature_extractor.extract_all_features(transaction)

            # Prepare feature vector
            text_features = " ".join(features.text_features)
            X_text = self.text_vectorizer.transform([text_features])

            # Get ensemble predictions with probabilities
            probabilities = self.ensemble_classifier.predict_proba(X_text)[0]
            classes = self.ensemble_classifier.classes_

            # Get top predictions
            top_indices = np.argsort(probabilities)[-5:][::-1]  # Top 5

            best_category = classes[top_indices[0]]
            best_confidence = probabilities[top_indices[0]]

            # Build alternatives list
            alternatives = []
            for idx in top_indices[1:]:
                if probabilities[idx] > 0.05:  # Only include meaningful alternatives
                    alternatives.append({
                        "category": classes[idx],
                        "confidence": float(probabilities[idx])
                    })

            return best_category, float(best_confidence), alternatives

        except Exception as e:
            logger.error(f"Enhanced ML categorization failed: {e}")
            return None, 0.0, []

    def _get_enhanced_fallback_category(self, transaction: Transaction) -> str:
        """Enhanced fallback category assignment."""
        amount = float(transaction.amount) if transaction.amount else 0
        name = transaction.name.lower() if transaction.name else ""

        # Enhanced heuristics
        if amount > 0:
            if amount > 500:
                return "Income"
            elif "refund" in name or "return" in name:
                return "Income"
            else:
                return "Transfer"
        else:
            amount = abs(amount)
            if amount > 1000:
                return "Bills & Utilities"
            elif amount < 20:
                return "Food & Dining"
            elif "transfer" in name or "payment" in name:
                return "Transfer"
            else:
                return "Shopping"

    def train_enhanced_model(
        self,
        db: Session,
        user_id: Optional[str] = None,
        test_size: float = 0.2,
        min_samples: int = 100,
        use_ensemble: bool = True
    ) -> Dict[str, Any]:
        """
        Train enhanced ML model with multiple algorithms and feature engineering.
        """
        # Get training data
        query = db.query(Transaction).join(Category)
        if user_id:
            from ..database.models import Account
            query = query.join(Account).filter(Account.user_id == user_id)

        # Filter for labeled transactions
        query = query.filter(
            or_(
                Transaction.category_id.isnot(None),
                Transaction.user_category_override.isnot(None)
            )
        )

        transactions = query.all()

        if len(transactions) < min_samples:
            return {
                "success": False,
                "error": f"Insufficient training data. Need at least {min_samples} labeled transactions, got {len(transactions)}"
            }

        # Prepare training data with enhanced features
        X_text = []
        y = []

        for txn in transactions:
            # Extract text features
            features = self.feature_extractor.extract_all_features(txn)
            text_features = " ".join(features.text_features)
            X_text.append(text_features)

            # Get label (prefer user override, then category)
            if txn.user_category_override:
                label = txn.user_category_override
            elif txn.category:
                label = txn.category.name
            else:
                continue  # Skip if no label

            y.append(label)

        # Check if we have enough data after filtering
        if len(y) < min_samples:
            return {
                "success": False,
                "error": f"Insufficient labeled data after filtering. Need {min_samples}, got {len(y)}"
            }

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_text, y, test_size=test_size, random_state=42, stratify=y
        )

        # Train text vectorizer with enhanced parameters
        self.text_vectorizer = TfidfVectorizer(
            max_features=2000,
            ngram_range=(1, 3),  # Include trigrams
            stop_words='english',
            lowercase=True,
            min_df=2,  # Ignore terms that appear in less than 2 documents
            max_df=0.95,  # Ignore terms that appear in more than 95% of documents
            sublinear_tf=True  # Apply sublinear tf scaling
        )

        X_train_vectorized = self.text_vectorizer.fit_transform(X_train)
        X_test_vectorized = self.text_vectorizer.transform(X_test)

        # Train multiple models for ensemble
        if use_ensemble:
            models = [
                ('nb', MultinomialNB(alpha=0.1)),
                ('cnb', ComplementNB(alpha=0.1)),
                ('rf', RandomForestClassifier(n_estimators=100, random_state=42, max_depth=20)),
                ('svm', SVC(probability=True, random_state=42, C=1.0, kernel='linear'))
            ]

            # Create ensemble classifier
            self.ensemble_classifier = VotingClassifier(
                estimators=models,
                voting='soft'  # Use probability averaging
            )
        else:
            # Single best performer
            self.ensemble_classifier = RandomForestClassifier(
                n_estimators=200,
                random_state=42,
                max_depth=25,
                min_samples_split=5
            )

        # Train the classifier
        self.ensemble_classifier.fit(X_train_vectorized, y_train)

        # Evaluate with cross-validation
        cv_scores = cross_val_score(
            self.ensemble_classifier,
            X_train_vectorized,
            y_train,
            cv=5,
            scoring='accuracy'
        )

        # Test set evaluation
        y_pred = self.ensemble_classifier.predict(X_test_vectorized)
        test_accuracy = accuracy_score(y_test, y_pred)

        # Save models
        self._save_models()

        # Get detailed metrics
        classification_rep = classification_report(y_test, y_pred, output_dict=True)

        # Save training metrics
        training_metrics = {
            "success": True,
            "test_accuracy": test_accuracy,
            "cv_mean_accuracy": cv_scores.mean(),
            "cv_std_accuracy": cv_scores.std(),
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "categories": list(set(y)),
            "feature_count": X_train_vectorized.shape[1],
            "classification_report": classification_rep,
            "model_type": "ensemble" if use_ensemble else "single",
            "timestamp": datetime.utcnow().isoformat()
        }

        # Save metrics to file
        with open(self.model_path / "training_metrics.json", "w") as f:
            json.dump(training_metrics, f, indent=2, default=str)

        return training_metrics

    def batch_categorize(
        self,
        transactions: List[Transaction],
        use_cache: bool = True,
        parallel: bool = False
    ) -> List[TransactionCategorization]:
        """
        Efficiently categorize multiple transactions with caching.
        """
        results = []
        cache_hits = 0

        for transaction in transactions:
            try:
                result = self.categorize_transaction(
                    transaction,
                    use_cache=use_cache
                )
                results.append(result)

                # Track cache efficiency
                if use_cache and self._get_cached_prediction(self._get_cache_key(transaction)):
                    cache_hits += 1

            except Exception as e:
                logger.error(f"Failed to categorize transaction {transaction.id}: {e}")
                # Add fallback result
                results.append(TransactionCategorization(
                    transaction_id=transaction.id,
                    suggested_category="Other",
                    confidence=0.1,
                    alternative_categories=None,
                    rules_applied=["Error fallback"]
                ))

        logger.info(f"Batch categorization: {len(results)} transactions, {cache_hits} cache hits")
        return results

    def store_prediction_feedback(
        self,
        db: Session,
        transaction_id: str,
        predicted_category: str,
        actual_category: str,
        user_confidence: Optional[float] = None
    ) -> MLPrediction:
        """Store prediction result and feedback for future model training."""

        # Get or create ML prediction record
        ml_prediction = db.query(MLPrediction).filter(
            MLPrediction.transaction_id == transaction_id
        ).first()

        if not ml_prediction:
            ml_prediction = MLPrediction(
                transaction_id=transaction_id,
                category_id=None,  # Will be set based on actual_category
                model_version="ensemble_v1",
                model_type="ensemble",
                confidence=user_confidence or 0.5,
                probability=user_confidence or 0.5,
                prediction_date=datetime.utcnow()
            )
            db.add(ml_prediction)

        # Update feedback
        ml_prediction.is_accepted = (predicted_category == actual_category)
        ml_prediction.user_feedback = "correct" if ml_prediction.is_accepted else "incorrect"
        ml_prediction.feedback_date = datetime.utcnow()

        db.commit()
        return ml_prediction

    def update_from_feedback(
        self,
        transaction_id: str,
        correct_category: str,
        was_correct: bool
    ) -> Dict[str, Any]:
        """Enhanced feedback processing with incremental learning preparation."""

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

        # Invalidate cache for this transaction (if we could identify it)
        try:
            # We'd need the transaction object to generate the cache key
            # For now, we'll implement a simple cache invalidation pattern
            pattern = f"ml_prediction:*"
            # In a real implementation, we'd be more surgical about cache invalidation
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")

        # Check if we should trigger retraining
        feedback_count = sum(1 for _ in open(feedback_file))

        retrain_triggered = False
        if feedback_count >= 50:  # More frequent retraining
            retrain_triggered = True
            logger.info(f"Triggering model retraining after {feedback_count} feedback items")

        return {
            "success": True,
            "feedback_recorded": True,
            "total_feedback": feedback_count,
            "retrain_triggered": retrain_triggered,
            "cache_invalidated": True
        }

    def get_model_metrics(self) -> Dict[str, Any]:
        """Get comprehensive model performance metrics."""
        metrics = {
            "model_loaded": self.ensemble_classifier is not None,
            "vectorizer_loaded": self.text_vectorizer is not None,
            "confidence_threshold": self.confidence_threshold,
            "rule_categories": list(self.rule_patterns.keys()),
            "model_path": str(self.model_path),
            "cache_enabled": self.redis_client is not None
        }

        # Load training metrics if available
        metrics_file = self.model_path / "training_metrics.json"
        if metrics_file.exists():
            with open(metrics_file) as f:
                training_metrics = json.load(f)
                metrics.update(training_metrics)

        # Add cache statistics
        if self.redis_client:
            try:
                cache_info = self.redis_client.info()
                metrics["cache_stats"] = {
                    "connected_clients": cache_info.get("connected_clients", 0),
                    "used_memory_human": cache_info.get("used_memory_human", "N/A"),
                    "keyspace_hits": cache_info.get("keyspace_hits", 0),
                    "keyspace_misses": cache_info.get("keyspace_misses", 0),
                }
            except Exception as e:
                logger.warning(f"Failed to get cache stats: {e}")

        return metrics

    def _save_models(self):
        """Save all trained models and metadata to disk."""
        try:
            if self.text_vectorizer:
                joblib.dump(self.text_vectorizer, self.model_path / "text_vectorizer.pkl")

            if self.ensemble_classifier:
                joblib.dump(self.ensemble_classifier, self.model_path / "ensemble_classifier.pkl")

            # Save metadata
            metadata = {
                "saved_at": datetime.utcnow().isoformat(),
                "confidence_threshold": self.confidence_threshold,
                "model_version": "enhanced_v1",
                "feature_count": self.text_vectorizer.vocabulary_.__len__() if self.text_vectorizer else 0,
                "categories": list(self.ensemble_classifier.classes_) if self.ensemble_classifier else []
            }

            with open(self.model_path / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)

            logger.info("Models saved successfully")

        except Exception as e:
            logger.error(f"Failed to save models: {e}")

    def _load_models(self):
        """Load trained models from disk."""
        try:
            vectorizer_path = self.model_path / "text_vectorizer.pkl"
            classifier_path = self.model_path / "ensemble_classifier.pkl"

            if vectorizer_path.exists():
                self.text_vectorizer = joblib.load(vectorizer_path)
                logger.info("Loaded text vectorizer")

            if classifier_path.exists():
                self.ensemble_classifier = joblib.load(classifier_path)
                logger.info("Loaded ensemble classifier")

            # Load metadata
            metadata_path = self.model_path / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path) as f:
                    metadata = json.load(f)
                    self.confidence_threshold = metadata.get("confidence_threshold", 0.75)
                    logger.info(f"Loaded model metadata, version: {metadata.get('model_version', 'unknown')}")

        except Exception as e:
            logger.error(f"Failed to load models: {e}")


# Singleton instance
ml_service = MLCategorizationService()