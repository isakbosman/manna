"""
Optimized Machine Learning categorization service with performance enhancements.

Key optimizations:
- Redis caching for repeated categorizations
- Batch processing with vectorized operations
- Model loading optimization with lazy loading
- Memory-efficient processing for large datasets
- Confidence-based early stopping
- Feature extraction caching
"""

import pickle
import json
import re
from typing import List, Dict, Tuple, Optional, Any, Set
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
from pathlib import Path
import logging
import hashlib
import time
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import redis
from threading import Lock

from ..database.models import Transaction, Category
from ..schemas.transaction import TransactionCategorization

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis-based cache manager for ML predictions."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        try:
            self.redis_client = redis_client or redis.Redis(
                host='localhost', 
                port=6379, 
                db=1,  # Use separate DB for ML cache
                decode_responses=True,
                socket_connect_timeout=1
            )
            # Test connection
            self.redis_client.ping()
            self.cache_enabled = True
        except (redis.ConnectionError, redis.TimeoutError):
            logger.warning("Redis not available, caching disabled")
            self.redis_client = None
            self.cache_enabled = False
    
    def get_cache_key(self, transaction_features: Dict[str, Any]) -> str:
        """Generate cache key from transaction features."""
        # Create deterministic hash from key features
        key_data = {
            "name": transaction_features.get("name", "").lower(),
            "merchant": transaction_features.get("merchant_name", "").lower(),
            "amount_range": self._get_amount_range(transaction_features.get("amount", 0))
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return f"ml_cat:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def _get_amount_range(self, amount: float) -> str:
        """Categorize amount into ranges for caching."""
        abs_amount = abs(amount)
        if abs_amount < 10:
            return "micro"
        elif abs_amount < 50:
            return "small"
        elif abs_amount < 200:
            return "medium"
        elif abs_amount < 1000:
            return "large"
        else:
            return "xlarge"
    
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached prediction."""
        if not self.cache_enabled:
            return None
        
        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.debug(f"Cache get failed: {e}")
        return None
    
    def set(self, cache_key: str, prediction: Dict[str, Any], ttl: int = 3600):
        """Cache prediction with TTL."""
        if not self.cache_enabled:
            return
        
        try:
            self.redis_client.setex(
                cache_key, 
                ttl, 
                json.dumps(prediction, default=str)
            )
        except Exception as e:
            logger.debug(f"Cache set failed: {e}")


class OptimizedMLCategorizationService:
    """
    Optimized ML categorization service with performance enhancements.
    """
    
    def __init__(self, model_path: Optional[Path] = None, enable_cache: bool = True):
        """Initialize the optimized ML categorization service."""
        self.model_path = model_path or Path("/tmp/manna_ml_models")
        self.model_path.mkdir(parents=True, exist_ok=True)
        
        # Thread locks for model loading
        self._model_lock = Lock()
        self._feature_cache_lock = Lock()
        
        # Initialize models (lazy loading)
        self.text_vectorizer: Optional[TfidfVectorizer] = None
        self.text_classifier: Optional[MultinomialNB] = None
        self.amount_classifier: Optional[RandomForestClassifier] = None
        self.models_loaded = False
        
        # Configuration
        self.confidence_threshold = 0.6
        self.batch_size = 100
        self.max_workers = 4
        
        # Caching
        self.cache_manager = CacheManager() if enable_cache else None
        self.feature_cache = {}  # In-memory feature cache
        
        # Performance metrics
        self.metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "total_predictions": 0,
            "avg_prediction_time_ms": 0,
            "batch_processed": 0
        }
        
        # Rule-based patterns (optimized with compiled regex)
        self.rule_patterns = self._initialize_optimized_rule_patterns()
        
        # Load models asynchronously if they exist
        self._try_load_models()
    
    def _initialize_optimized_rule_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize rule-based patterns with compiled regex for performance."""
        patterns = {
            "Food & Dining": [
                {"pattern": re.compile(r"(?i)(restaurant|cafe|coffee|starbucks|mcdonald|subway|pizza|food|dining|eat)"),
                 "confidence": 0.9},
                {"pattern": re.compile(r"(?i)(uber.*eats|doordash|grubhub|postmates|delivery)"),
                 "confidence": 0.85},
            ],
            "Transportation": [
                {"pattern": re.compile(r"(?i)(uber|lyft|taxi|transit|metro|bus|train|parking|gas|shell|exxon|chevron)"),
                 "confidence": 0.9},
                {"pattern": re.compile(r"(?i)(airline|flight|airport|car rental)"),
                 "confidence": 0.95},
            ],
            "Shopping": [
                {"pattern": re.compile(r"(?i)(amazon|walmart|target|best buy|home depot|costco|ebay|etsy)"),
                 "confidence": 0.9},
                {"pattern": re.compile(r"(?i)(store|shop|mall|retail|market)"),
                 "confidence": 0.7},
            ],
            "Bills & Utilities": [
                {"pattern": re.compile(r"(?i)(electric|gas|water|internet|cable|phone|verizon|at&t|comcast|utility)"),
                 "confidence": 0.95},
                {"pattern": re.compile(r"(?i)(insurance|mortgage|rent)"),
                 "confidence": 0.9},
            ],
            "Entertainment": [
                {"pattern": re.compile(r"(?i)(netflix|spotify|hulu|disney|movie|theater|cinema|concert|game|steam)"),
                 "confidence": 0.9},
                {"pattern": re.compile(r"(?i)(bar|club|nightlife|entertainment)"),
                 "confidence": 0.8},
            ],
            "Healthcare": [
                {"pattern": re.compile(r"(?i)(hospital|clinic|doctor|medical|pharmacy|cvs|walgreens|dental|health)"),
                 "confidence": 0.9},
                {"pattern": re.compile(r"(?i)(insurance.*health|medicare|medicaid)"),
                 "confidence": 0.95},
            ],
            "Income": [
                {"pattern": re.compile(r"(?i)(salary|payroll|deposit|direct deposit|income|payment from|reimbursement)"),
                 "confidence": 0.95},
                {"pattern": re.compile(r"(?i)(transfer from.*savings|interest earned|dividend)"),
                 "confidence": 0.9},
            ],
            "Transfer": [
                {"pattern": re.compile(r"(?i)(transfer|zelle|venmo|paypal|cash app|wire)"),
                 "confidence": 0.85},
            ],
            "Fees & Charges": [
                {"pattern": re.compile(r"(?i)(fee|charge|penalty|overdraft|interest charged|finance charge)"),
                 "confidence": 0.95},
            ],
        }
        return patterns
    
    def _try_load_models(self):
        """Try to load existing models without blocking."""
        try:
            if not self.models_loaded:
                self.load_models()
        except Exception as e:
            logger.debug(f"Could not load existing models: {e}")
    
    def _ensure_models_loaded(self):
        """Ensure models are loaded (lazy loading with thread safety)."""
        if not self.models_loaded:
            with self._model_lock:
                if not self.models_loaded:  # Double-check locking
                    self.load_models()
    
    @lru_cache(maxsize=1000)
    def _extract_cached_features(self, name: str, merchant: str, description: str) -> str:
        """Extract and cache text features for repeated transactions."""
        return f"{name} {merchant or ''} {description or ''}".lower().strip()
    
    def categorize_transaction(
        self,
        transaction: Transaction,
        use_ml: bool = True,
        use_rules: bool = True,
        use_cache: bool = True
    ) -> TransactionCategorization:
        """
        Optimized categorization with caching and performance improvements.
        """
        start_time = time.perf_counter()
        
        # Extract features for caching
        transaction_features = {
            "name": transaction.name,
            "merchant_name": transaction.merchant_name,
            "amount": float(transaction.amount),
            "description": transaction.original_description or ""
        }
        
        # Check cache first
        cached_result = None
        if use_cache and self.cache_manager:
            cache_key = self.cache_manager.get_cache_key(transaction_features)
            cached_result = self.cache_manager.get(cache_key)
            
            if cached_result:
                self.metrics["cache_hits"] += 1
                return TransactionCategorization(
                    transaction_id=transaction.id,
                    suggested_category=cached_result["category"],
                    confidence=cached_result["confidence"],
                    alternative_categories=cached_result.get("alternatives"),
                    rules_applied=cached_result.get("rules_applied")
                )
        
        self.metrics["cache_misses"] += 1
        
        # Perform categorization
        category = None
        confidence = 0.0
        alternatives = []
        rules_applied = []
        
        # Try rule-based categorization first (faster)
        if use_rules:
            rule_category, rule_confidence = self._apply_optimized_rules(transaction)
            if rule_category and rule_confidence >= self.confidence_threshold:
                category = rule_category
                confidence = rule_confidence
                rules_applied.append(f"Pattern match: {rule_category}")
        
        # Try ML categorization if needed
        if (use_ml and 
            (not category or confidence < 0.8) and 
            self._can_use_ml()):
            
            ml_category, ml_confidence, ml_alternatives = self._apply_optimized_ml(transaction)
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
        
        # Create result
        result = TransactionCategorization(
            transaction_id=transaction.id,
            suggested_category=category,
            confidence=confidence,
            alternative_categories=alternatives[:3] if alternatives else None,
            rules_applied=rules_applied if rules_applied else None
        )
        
        # Cache the result
        if use_cache and self.cache_manager and confidence >= 0.7:
            cache_data = {
                "category": category,
                "confidence": confidence,
                "alternatives": alternatives[:3] if alternatives else None,
                "rules_applied": rules_applied
            }
            self.cache_manager.set(cache_key, cache_data)
        
        # Update metrics
        end_time = time.perf_counter()
        prediction_time = (end_time - start_time) * 1000
        self._update_prediction_metrics(prediction_time)
        
        return result
    
    def _can_use_ml(self) -> bool:
        """Check if ML models are available."""
        try:
            self._ensure_models_loaded()
            return self.text_classifier is not None and self.text_vectorizer is not None
        except Exception:
            return False
    
    def _apply_optimized_rules(self, transaction: Transaction) -> Tuple[Optional[str], float]:
        """Apply rule-based categorization with optimized regex matching."""
        text_to_match = self._extract_cached_features(
            transaction.name,
            transaction.merchant_name or "",
            transaction.original_description or ""
        )
        
        best_category = None
        best_confidence = 0.0
        
        for category, patterns in self.rule_patterns.items():
            for pattern_dict in patterns:
                compiled_pattern = pattern_dict["pattern"]
                pattern_confidence = pattern_dict["confidence"]
                
                if compiled_pattern.search(text_to_match):
                    if pattern_confidence > best_confidence:
                        best_category = category
                        best_confidence = pattern_confidence
        
        # Amount-based rules (optimized)
        if transaction.amount > 0 and best_confidence < 0.8:
            if transaction.amount > 1000:
                best_category = "Income"
                best_confidence = max(best_confidence, 0.7)
        
        return best_category, best_confidence
    
    def _apply_optimized_ml(self, transaction: Transaction) -> Tuple[Optional[str], float, List[Dict[str, float]]]:
        """Apply ML model with optimized inference."""
        try:
            # Prepare features efficiently
            text_features = self._extract_cached_features(
                transaction.name,
                transaction.merchant_name or "",
                transaction.original_description or ""
            )
            
            # Vectorize text (batch of 1 for consistency)
            X_text = self.text_vectorizer.transform([text_features])
            
            # Get predictions with probabilities
            probabilities = self.text_classifier.predict_proba(X_text)[0]
            classes = self.text_classifier.classes_
            
            # Get top predictions efficiently
            top_indices = np.argpartition(probabilities, -3)[-3:]
            top_indices = top_indices[np.argsort(probabilities[top_indices])][::-1]
            
            best_category = classes[top_indices[0]]
            best_confidence = probabilities[top_indices[0]]
            
            alternatives = [
                {"category": classes[idx], "confidence": float(probabilities[idx])}
                for idx in top_indices[1:] if probabilities[idx] > 0.1
            ]
            
            return best_category, float(best_confidence), alternatives
            
        except Exception as e:
            logger.error(f"Optimized ML categorization failed: {e}")
            return None, 0.0, []
    
    def batch_categorize_optimized(
        self,
        transactions: List[Transaction],
        use_cache: bool = True,
        max_workers: Optional[int] = None
    ) -> List[TransactionCategorization]:
        """
        Optimized batch categorization with parallel processing and caching.
        """
        if not transactions:
            return []
        
        # Use configured max_workers if not specified
        max_workers = max_workers or self.max_workers
        
        # Split into chunks for processing
        chunk_size = min(self.batch_size, len(transactions))
        chunks = [
            transactions[i:i + chunk_size] 
            for i in range(0, len(transactions), chunk_size)
        ]
        
        results = []
        
        # Process chunks in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            chunk_results = list(executor.map(
                lambda chunk: self._process_transaction_chunk(chunk, use_cache),
                chunks
            ))
            
            # Flatten results
            for chunk_result in chunk_results:
                results.extend(chunk_result)
        
        self.metrics["batch_processed"] += len(results)
        return results
    
    def _process_transaction_chunk(
        self, 
        transactions: List[Transaction], 
        use_cache: bool = True
    ) -> List[TransactionCategorization]:
        """Process a chunk of transactions efficiently."""
        results = []
        
        # Separate cached and uncached transactions
        cached_results = {}
        uncached_transactions = []
        
        if use_cache and self.cache_manager:
            for transaction in transactions:
                features = {
                    "name": transaction.name,
                    "merchant_name": transaction.merchant_name,
                    "amount": float(transaction.amount),
                    "description": transaction.original_description or ""
                }
                cache_key = self.cache_manager.get_cache_key(features)
                cached = self.cache_manager.get(cache_key)
                
                if cached:
                    cached_results[transaction.id] = cached
                    self.metrics["cache_hits"] += 1
                else:
                    uncached_transactions.append(transaction)
                    self.metrics["cache_misses"] += 1
        else:
            uncached_transactions = transactions
        
        # Process uncached transactions
        if uncached_transactions and self._can_use_ml():
            # Batch ML processing for efficiency
            ml_results = self._batch_ml_categorize(uncached_transactions)
            
            # Apply rules and combine results
            for transaction, ml_result in zip(uncached_transactions, ml_results):
                category, confidence, alternatives, rules_applied = ml_result
                
                # Apply rules if ML confidence is low
                if confidence < 0.8:
                    rule_category, rule_confidence = self._apply_optimized_rules(transaction)
                    if rule_confidence > confidence:
                        category = rule_category
                        confidence = rule_confidence
                        rules_applied = [f"Pattern match: {rule_category}"]
                
                # Cache high-confidence results
                if use_cache and self.cache_manager and confidence >= 0.7:
                    cache_data = {
                        "category": category,
                        "confidence": confidence,
                        "alternatives": alternatives,
                        "rules_applied": rules_applied
                    }
                    features = {
                        "name": transaction.name,
                        "merchant_name": transaction.merchant_name,
                        "amount": float(transaction.amount),
                        "description": transaction.original_description or ""
                    }
                    cache_key = self.cache_manager.get_cache_key(features)
                    self.cache_manager.set(cache_key, cache_data)
                
                results.append(TransactionCategorization(
                    transaction_id=transaction.id,
                    suggested_category=category,
                    confidence=confidence,
                    alternative_categories=alternatives[:3] if alternatives else None,
                    rules_applied=rules_applied
                ))
        else:
            # Fallback to individual processing
            for transaction in uncached_transactions:
                result = self.categorize_transaction(transaction, use_cache=False)
                results.append(result)
        
        # Add cached results
        for transaction in transactions:
            if transaction.id in cached_results:
                cached = cached_results[transaction.id]
                results.append(TransactionCategorization(
                    transaction_id=transaction.id,
                    suggested_category=cached["category"],
                    confidence=cached["confidence"],
                    alternative_categories=cached.get("alternatives"),
                    rules_applied=cached.get("rules_applied")
                ))
        
        return results
    
    def _batch_ml_categorize(self, transactions: List[Transaction]) -> List[Tuple[str, float, List[Dict], List[str]]]:
        """Perform batch ML categorization for efficiency."""
        if not self._can_use_ml():
            return [("Other", 0.3, [], ["Fallback"]) for _ in transactions]
        
        try:
            # Extract features for all transactions
            text_features = [
                self._extract_cached_features(
                    t.name, t.merchant_name or "", t.original_description or ""
                )
                for t in transactions
            ]
            
            # Batch vectorization
            X_text = self.text_vectorizer.transform(text_features)
            
            # Batch prediction
            probabilities = self.text_classifier.predict_proba(X_text)
            classes = self.text_classifier.classes_
            
            results = []
            for probs in probabilities:
                # Get top predictions
                top_indices = np.argpartition(probs, -3)[-3:]
                top_indices = top_indices[np.argsort(probs[top_indices])][::-1]
                
                best_category = classes[top_indices[0]]
                best_confidence = probs[top_indices[0]]
                
                alternatives = [
                    {"category": classes[idx], "confidence": float(probs[idx])}
                    for idx in top_indices[1:] if probs[idx] > 0.1
                ]
                
                results.append((
                    best_category,
                    float(best_confidence),
                    alternatives,
                    ["ML classification"]
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Batch ML categorization failed: {e}")
            return [("Other", 0.3, [], ["Fallback"]) for _ in transactions]
    
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
    
    def _update_prediction_metrics(self, prediction_time_ms: float):
        """Update performance metrics."""
        self.metrics["total_predictions"] += 1
        
        # Update running average
        current_avg = self.metrics["avg_prediction_time_ms"]
        new_count = self.metrics["total_predictions"]
        self.metrics["avg_prediction_time_ms"] = (
            (current_avg * (new_count - 1) + prediction_time_ms) / new_count
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        cache_hit_rate = 0.0
        if self.metrics["cache_hits"] + self.metrics["cache_misses"] > 0:
            cache_hit_rate = (
                self.metrics["cache_hits"] / 
                (self.metrics["cache_hits"] + self.metrics["cache_misses"])
            ) * 100
        
        return {
            "cache_hit_rate_percent": cache_hit_rate,
            "total_predictions": self.metrics["total_predictions"],
            "avg_prediction_time_ms": self.metrics["avg_prediction_time_ms"],
            "batch_processed": self.metrics["batch_processed"],
            "models_loaded": self.models_loaded,
            "cache_enabled": self.cache_manager is not None and self.cache_manager.cache_enabled,
            **self.metrics
        }
    
    def clear_caches(self):
        """Clear all caches."""
        # Clear in-memory cache
        self._extract_cached_features.cache_clear()
        with self._feature_cache_lock:
            self.feature_cache.clear()
        
        # Clear Redis cache
        if self.cache_manager and self.cache_manager.cache_enabled:
            try:
                keys = self.cache_manager.redis_client.keys("ml_cat:*")
                if keys:
                    self.cache_manager.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cached predictions")
            except Exception as e:
                logger.error(f"Failed to clear Redis cache: {e}")
    
    def train_model(
        self,
        transactions: List[Transaction],
        test_size: float = 0.2,
        min_samples: int = 100,
        use_optimization: bool = True
    ) -> Dict[str, Any]:
        """
        Train the ML model with optimizations.
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
        
        logger.info(f"Training model with {len(labeled_transactions)} labeled transactions")
        
        # Prepare training data efficiently
        if use_optimization:
            df = pd.DataFrame([
                {
                    "text": self._extract_cached_features(
                        txn.name, 
                        txn.merchant_name or "", 
                        txn.original_description or ""
                    ),
                    "category": txn.user_category or txn.primary_category
                }
                for txn in labeled_transactions
            ])
            
            X_text = df["text"].tolist()
            y = df["category"].tolist()
        else:
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
        
        # Train text vectorizer with optimization
        self.text_vectorizer = TfidfVectorizer(
            max_features=2000,  # Increased for better performance
            ngram_range=(1, 2),
            stop_words='english',
            lowercase=True,
            min_df=2,  # Ignore terms that appear in less than 2 documents
            max_df=0.95  # Ignore terms that appear in more than 95% of documents
        )
        X_train_vectorized = self.text_vectorizer.fit_transform(X_train)
        X_test_vectorized = self.text_vectorizer.transform(X_test)
        
        # Train classifier with optimized parameters
        self.text_classifier = MultinomialNB(alpha=0.01)  # Lower alpha for better performance
        self.text_classifier.fit(X_train_vectorized, y_train)
        
        # Evaluate
        y_pred = self.text_classifier.predict(X_test_vectorized)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Mark models as loaded
        self.models_loaded = True
        
        # Save models
        self.save_models()
        
        # Clear caches after retraining
        self.clear_caches()
        
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
            "optimization_used": use_optimization,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def save_models(self):
        """Save trained models to disk."""
        if self.text_vectorizer:
            joblib.dump(self.text_vectorizer, self.model_path / "text_vectorizer_optimized.pkl")
        
        if self.text_classifier:
            joblib.dump(self.text_classifier, self.model_path / "text_classifier_optimized.pkl")
        
        # Save metadata
        metadata = {
            "saved_at": datetime.utcnow().isoformat(),
            "confidence_threshold": self.confidence_threshold,
            "categories": list(self.text_classifier.classes_) if self.text_classifier else [],
            "optimization_version": "1.0",
            "performance_metrics": self.get_performance_metrics()
        }
        
        with open(self.model_path / "metadata_optimized.json", "w") as f:
            json.dump(metadata, f, indent=2)
    
    def load_models(self):
        """Load trained models from disk."""
        try:
            vectorizer_path = self.model_path / "text_vectorizer_optimized.pkl"
            classifier_path = self.model_path / "text_classifier_optimized.pkl"
            
            # Try optimized versions first, then fall back to standard
            if vectorizer_path.exists():
                self.text_vectorizer = joblib.load(vectorizer_path)
                logger.info("Loaded optimized text vectorizer")
            elif (self.model_path / "text_vectorizer.pkl").exists():
                self.text_vectorizer = joblib.load(self.model_path / "text_vectorizer.pkl")
                logger.info("Loaded standard text vectorizer")
            
            if classifier_path.exists():
                self.text_classifier = joblib.load(classifier_path)
                logger.info("Loaded optimized text classifier")
            elif (self.model_path / "text_classifier.pkl").exists():
                self.text_classifier = joblib.load(self.model_path / "text_classifier.pkl")
                logger.info("Loaded standard text classifier")
            
            # Load metadata
            metadata_path = self.model_path / "metadata_optimized.json"
            if metadata_path.exists():
                with open(metadata_path) as f:
                    metadata = json.load(f)
                    self.confidence_threshold = metadata.get("confidence_threshold", 0.6)
                    logger.info(f"Loaded optimized model metadata from {metadata['saved_at']}")
            
            self.models_loaded = (
                self.text_vectorizer is not None and 
                self.text_classifier is not None
            )
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            self.models_loaded = False


# Optimized singleton instance
optimized_ml_service = OptimizedMLCategorizationService()