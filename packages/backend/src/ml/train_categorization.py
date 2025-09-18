"""
Training script for transaction categorization ML models.
This script handles data preprocessing, feature engineering, model training, and evaluation.
"""

import os
import sys
import argparse
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Scikit-learn imports
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB, ComplementNB
from sklearn.ensemble import RandomForestClassifier, VotingClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support, classification_report,
    confusion_matrix, roc_auc_score
)
from sklearn.preprocessing import LabelEncoder
import joblib

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Database imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Transaction, Category, Account, User
from config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TransactionDataProcessor:
    """Process and prepare transaction data for ML training."""

    def __init__(self):
        self.label_encoder = LabelEncoder()
        self.min_category_samples = 5  # Minimum samples per category

    def load_data_from_db(
        self,
        db_url: str,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Load transaction data from database."""

        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Build query
            query = session.query(Transaction).join(Category)

            if user_id:
                query = query.join(Account).filter(Account.user_id == user_id)

            if start_date:
                query = query.filter(Transaction.date >= start_date)

            if end_date:
                query = query.filter(Transaction.date <= end_date)

            # Only get labeled transactions
            query = query.filter(
                Transaction.category_id.isnot(None)
            )

            transactions = query.all()

            # Convert to DataFrame
            data = []
            for txn in transactions:
                data.append({
                    'id': str(txn.id),
                    'name': txn.name or '',
                    'merchant_name': txn.merchant_name or '',
                    'description': txn.description or '',
                    'amount': float(txn.amount),
                    'date': txn.date,
                    'category': txn.category.name if txn.category else None,
                    'user_category': txn.user_category_override,
                    'is_pending': txn.is_pending,
                    'is_recurring': txn.is_recurring,
                    'is_transfer': txn.is_transfer,
                    'transaction_type': txn.transaction_type,
                    'payment_method': txn.payment_method or '',
                    'payment_channel': txn.payment_channel or ''
                })

            df = pd.DataFrame(data)
            logger.info(f"Loaded {len(df)} transactions from database")

            return df

        except Exception as e:
            logger.error(f"Failed to load data from database: {e}")
            raise
        finally:
            session.close()

    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess the transaction data."""

        logger.info("Starting data preprocessing...")

        # Remove transactions without categories
        df = df.dropna(subset=['category'])

        # Use user category override if available, otherwise use category
        df['final_category'] = df['user_category'].fillna(df['category'])

        # Filter out categories with too few samples
        category_counts = df['final_category'].value_counts()
        valid_categories = category_counts[category_counts >= self.min_category_samples].index
        df = df[df['final_category'].isin(valid_categories)]

        # Create combined text field
        df['text_combined'] = (
            df['name'].fillna('') + ' ' +
            df['merchant_name'].fillna('') + ' ' +
            df['description'].fillna('')
        ).str.lower().str.strip()

        # Clean text
        df['text_combined'] = df['text_combined'].str.replace(r'[^\w\s]', ' ', regex=True)
        df['text_combined'] = df['text_combined'].str.replace(r'\s+', ' ', regex=True)

        # Add temporal features
        df['hour'] = df['date'].dt.hour
        df['day_of_week'] = df['date'].dt.dayofweek
        df['day_of_month'] = df['date'].dt.day
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

        # Add amount features
        df['amount_abs'] = df['amount'].abs()
        df['amount_log'] = np.log1p(df['amount_abs'])
        df['is_round_number'] = (df['amount'] % 1 == 0).astype(int)
        df['is_even_dollar'] = (df['amount'] % 10 == 0).astype(int)
        df['amount_magnitude'] = df['amount_abs'].apply(lambda x: len(str(int(x))))

        # Add merchant features
        df['has_merchant'] = df['merchant_name'].notna().astype(int)
        df['merchant_length'] = df['merchant_name'].fillna('').str.len()

        logger.info(f"Preprocessed data: {len(df)} transactions, {df['final_category'].nunique()} categories")
        logger.info(f"Category distribution:\n{df['final_category'].value_counts()}")

        return df

    def extract_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Extract features for ML training."""

        # Text features (primary)
        text_features = df['text_combined'].values

        # Target labels
        y = df['final_category'].values

        # Feature names for interpretability
        feature_names = ['text_combined']

        logger.info(f"Extracted features: {len(text_features)} samples")

        return text_features, y, feature_names


class ModelTrainer:
    """Train and evaluate multiple ML models for transaction categorization."""

    def __init__(self, model_path: Path):
        self.model_path = model_path
        self.model_path.mkdir(parents=True, exist_ok=True)

        # Best models found through experimentation
        self.model_configs = {
            'naive_bayes': {
                'model': MultinomialNB(),
                'params': {'alpha': [0.01, 0.1, 0.5, 1.0]}
            },
            'complement_nb': {
                'model': ComplementNB(),
                'params': {'alpha': [0.01, 0.1, 0.5, 1.0]}
            },
            'random_forest': {
                'model': RandomForestClassifier(random_state=42),
                'params': {
                    'n_estimators': [100, 200],
                    'max_depth': [10, 20, None],
                    'min_samples_split': [2, 5],
                    'min_samples_leaf': [1, 2]
                }
            },
            'svm': {
                'model': SVC(probability=True, random_state=42),
                'params': {
                    'C': [0.1, 1.0, 10.0],
                    'kernel': ['linear', 'rbf'],
                    'gamma': ['scale', 'auto']
                }
            },
            'logistic_regression': {
                'model': LogisticRegression(random_state=42, max_iter=1000),
                'params': {
                    'C': [0.1, 1.0, 10.0],
                    'solver': ['liblinear', 'lbfgs']
                }
            }
        }

    def create_text_vectorizer(self, max_features: int = 2000) -> TfidfVectorizer:
        """Create and configure TF-IDF vectorizer."""

        return TfidfVectorizer(
            max_features=max_features,
            ngram_range=(1, 3),  # Unigrams, bigrams, trigrams
            stop_words='english',
            lowercase=True,
            min_df=2,  # Ignore terms in fewer than 2 documents
            max_df=0.95,  # Ignore terms in more than 95% of documents
            sublinear_tf=True,  # Apply sublinear tf scaling
            strip_accents='unicode'
        )

    def train_single_model(
        self,
        model_name: str,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        use_grid_search: bool = True
    ) -> Tuple[Any, Dict[str, Any]]:
        """Train a single model with hyperparameter tuning."""

        logger.info(f"Training {model_name}...")

        config = self.model_configs[model_name]
        base_model = config['model']

        if use_grid_search and len(config['params']) > 0:
            # Grid search for best parameters
            grid_search = GridSearchCV(
                base_model,
                config['params'],
                cv=3,
                scoring='accuracy',
                n_jobs=-1,
                verbose=1
            )

            grid_search.fit(X_train, y_train)
            best_model = grid_search.best_estimator_
            best_params = grid_search.best_params_

            logger.info(f"Best parameters for {model_name}: {best_params}")
        else:
            # Use default parameters
            best_model = base_model
            best_model.fit(X_train, y_train)
            best_params = {}

        # Evaluate on validation set
        y_pred = best_model.predict(X_val)
        accuracy = accuracy_score(y_val, y_pred)

        # Get probabilities for multi-class ROC-AUC
        try:
            y_prob = best_model.predict_proba(X_val)
            # For multi-class, use macro average
            roc_auc = roc_auc_score(y_val, y_prob, multi_class='ovr', average='macro')
        except:
            roc_auc = None

        # Precision, recall, F1 for each class
        precision, recall, f1, support = precision_recall_fscore_support(
            y_val, y_pred, average='macro'
        )

        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'roc_auc': roc_auc,
            'best_params': best_params
        }

        logger.info(f"{model_name} - Accuracy: {accuracy:.4f}, F1: {f1:.4f}")

        return best_model, metrics

    def train_ensemble_model(
        self,
        individual_models: Dict[str, Any],
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray
    ) -> Tuple[VotingClassifier, Dict[str, Any]]:
        """Create and train ensemble model."""

        logger.info("Training ensemble model...")

        # Select best performing models for ensemble
        estimators = []
        for name, model in individual_models.items():
            estimators.append((name, model))

        # Create voting classifier
        ensemble = VotingClassifier(
            estimators=estimators,
            voting='soft'  # Use predicted probabilities
        )

        # Train ensemble
        ensemble.fit(X_train, y_train)

        # Evaluate ensemble
        y_pred = ensemble.predict(X_val)
        accuracy = accuracy_score(y_val, y_pred)

        # Get probabilities for ROC-AUC
        try:
            y_prob = ensemble.predict_proba(X_val)
            roc_auc = roc_auc_score(y_val, y_prob, multi_class='ovr', average='macro')
        except:
            roc_auc = None

        # Precision, recall, F1
        precision, recall, f1, support = precision_recall_fscore_support(
            y_val, y_pred, average='macro'
        )

        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'roc_auc': roc_auc,
            'n_estimators': len(estimators)
        }

        logger.info(f"Ensemble - Accuracy: {accuracy:.4f}, F1: {f1:.4f}")

        return ensemble, metrics

    def evaluate_model(
        self,
        model: Any,
        X_test: np.ndarray,
        y_test: np.ndarray,
        category_names: List[str]
    ) -> Dict[str, Any]:
        """Comprehensive model evaluation."""

        # Predictions
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)

        # Basic metrics
        accuracy = accuracy_score(y_test, y_pred)

        # Per-class metrics
        precision, recall, f1, support = precision_recall_fscore_support(
            y_test, y_pred, average=None
        )

        # Macro averages
        macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average='macro'
        )

        # Classification report
        class_report = classification_report(
            y_test, y_pred, target_names=category_names, output_dict=True
        )

        # Confusion matrix
        conf_matrix = confusion_matrix(y_test, y_pred)

        # ROC-AUC for multi-class
        try:
            roc_auc_macro = roc_auc_score(y_test, y_prob, multi_class='ovr', average='macro')
            roc_auc_weighted = roc_auc_score(y_test, y_prob, multi_class='ovr', average='weighted')
        except:
            roc_auc_macro = None
            roc_auc_weighted = None

        evaluation_results = {
            'test_accuracy': accuracy,
            'macro_precision': macro_precision,
            'macro_recall': macro_recall,
            'macro_f1': macro_f1,
            'roc_auc_macro': roc_auc_macro,
            'roc_auc_weighted': roc_auc_weighted,
            'classification_report': class_report,
            'confusion_matrix': conf_matrix.tolist(),
            'per_class_metrics': {
                'categories': category_names,
                'precision': precision.tolist(),
                'recall': recall.tolist(),
                'f1_score': f1.tolist(),
                'support': support.tolist()
            }
        }

        return evaluation_results

    def save_model_artifacts(
        self,
        vectorizer: TfidfVectorizer,
        model: Any,
        evaluation_results: Dict[str, Any],
        training_metadata: Dict[str, Any]
    ):
        """Save all model artifacts."""

        # Save vectorizer and model
        joblib.dump(vectorizer, self.model_path / 'text_vectorizer.pkl')
        joblib.dump(model, self.model_path / 'ensemble_classifier.pkl')

        # Save evaluation results
        with open(self.model_path / 'evaluation_results.json', 'w') as f:
            json.dump(evaluation_results, f, indent=2, default=str)

        # Save training metadata
        with open(self.model_path / 'training_metadata.json', 'w') as f:
            json.dump(training_metadata, f, indent=2, default=str)

        # Save model metadata for the service
        model_metadata = {
            'saved_at': datetime.utcnow().isoformat(),
            'model_version': 'enhanced_v1',
            'confidence_threshold': 0.75,
            'feature_count': len(vectorizer.vocabulary_),
            'categories': list(model.classes_),
            'test_accuracy': evaluation_results['test_accuracy'],
            'macro_f1': evaluation_results['macro_f1']
        }

        with open(self.model_path / 'metadata.json', 'w') as f:
            json.dump(model_metadata, f, indent=2)

        logger.info(f"Model artifacts saved to {self.model_path}")


def main():
    """Main training pipeline."""

    parser = argparse.ArgumentParser(description='Train transaction categorization models')
    parser.add_argument('--user-id', type=str, help='Specific user ID to train on')
    parser.add_argument('--days-back', type=int, default=365, help='Number of days of data to use')
    parser.add_argument('--test-size', type=float, default=0.2, help='Test set proportion')
    parser.add_argument('--val-size', type=float, default=0.2, help='Validation set proportion')
    parser.add_argument('--max-features', type=int, default=2000, help='Maximum TF-IDF features')
    parser.add_argument('--model-path', type=str, help='Path to save models')
    parser.add_argument('--grid-search', action='store_true', help='Use grid search for hyperparameters')
    parser.add_argument('--ensemble-only', action='store_true', help='Only train ensemble model')

    args = parser.parse_args()

    # Setup paths
    if args.model_path:
        model_path = Path(args.model_path)
    else:
        model_path = Path(settings.ml_model_path)

    # Initialize processors
    data_processor = TransactionDataProcessor()
    trainer = ModelTrainer(model_path)

    # Load and preprocess data
    start_date = datetime.now() - timedelta(days=args.days_back)

    logger.info("Loading transaction data...")
    df = data_processor.load_data_from_db(
        db_url=settings.database_url,
        user_id=args.user_id,
        start_date=start_date
    )

    if len(df) == 0:
        logger.error("No transaction data found")
        return

    df = data_processor.preprocess_data(df)

    if len(df) < 100:
        logger.error(f"Insufficient data for training: {len(df)} transactions")
        return

    # Extract features
    X_text, y, feature_names = data_processor.extract_features(df)

    # Create text vectorizer
    vectorizer = trainer.create_text_vectorizer(max_features=args.max_features)

    # Split data: train/val/test
    # First split: separate test set
    X_temp, X_test, y_temp, y_test = train_test_split(
        X_text, y, test_size=args.test_size, random_state=42, stratify=y
    )

    # Second split: train/validation from remaining data
    val_size_adjusted = args.val_size / (1 - args.test_size)
    X_train_text, X_val_text, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=val_size_adjusted, random_state=42, stratify=y_temp
    )

    # Vectorize text
    logger.info("Vectorizing text features...")
    X_train = vectorizer.fit_transform(X_train_text)
    X_val = vectorizer.transform(X_val_text)
    X_test_vec = vectorizer.transform(X_test)

    logger.info(f"Training set: {X_train.shape}")
    logger.info(f"Validation set: {X_val.shape}")
    logger.info(f"Test set: {X_test_vec.shape}")
    logger.info(f"Feature vocabulary size: {len(vectorizer.vocabulary_)}")

    # Training metadata
    training_metadata = {
        'start_time': datetime.utcnow().isoformat(),
        'user_id': args.user_id,
        'days_back': args.days_back,
        'total_samples': len(df),
        'train_samples': len(y_train),
        'val_samples': len(y_val),
        'test_samples': len(y_test),
        'n_categories': len(np.unique(y)),
        'categories': list(np.unique(y)),
        'max_features': args.max_features,
        'grid_search': args.grid_search,
        'feature_names': feature_names
    }

    # Train individual models or ensemble only
    if args.ensemble_only:
        logger.info("Training ensemble model only...")

        # Use predefined best models for ensemble
        base_models = {
            'nb': MultinomialNB(alpha=0.1),
            'rf': RandomForestClassifier(n_estimators=100, max_depth=20, random_state=42),
            'svm': SVC(probability=True, C=1.0, kernel='linear', random_state=42)
        }

        # Train base models
        for name, model in base_models.items():
            model.fit(X_train, y_train)

        # Create ensemble
        best_model, ensemble_metrics = trainer.train_ensemble_model(
            base_models, X_train, y_train, X_val, y_val
        )

        all_metrics = {'ensemble': ensemble_metrics}

    else:
        # Train all individual models
        individual_models = {}
        all_metrics = {}

        for model_name in trainer.model_configs.keys():
            try:
                model, metrics = trainer.train_single_model(
                    model_name, X_train, y_train, X_val, y_val, args.grid_search
                )
                individual_models[model_name] = model
                all_metrics[model_name] = metrics

            except Exception as e:
                logger.error(f"Failed to train {model_name}: {e}")
                continue

        if not individual_models:
            logger.error("No models trained successfully")
            return

        # Train ensemble with best models
        best_model, ensemble_metrics = trainer.train_ensemble_model(
            individual_models, X_train, y_train, X_val, y_val
        )

        all_metrics['ensemble'] = ensemble_metrics

    # Evaluate best model on test set
    logger.info("Evaluating final model on test set...")
    evaluation_results = trainer.evaluate_model(
        best_model, X_test_vec, y_test, list(np.unique(y))
    )

    # Add training metrics to metadata
    training_metadata.update({
        'end_time': datetime.utcnow().isoformat(),
        'all_model_metrics': all_metrics,
        'final_evaluation': evaluation_results
    })

    # Save all artifacts
    trainer.save_model_artifacts(
        vectorizer, best_model, evaluation_results, training_metadata
    )

    # Print summary
    print("\n" + "="*60)
    print("TRAINING COMPLETED SUCCESSFULLY")
    print("="*60)
    print(f"Final Model Test Accuracy: {evaluation_results['test_accuracy']:.4f}")
    print(f"Final Model Macro F1: {evaluation_results['macro_f1']:.4f}")
    print(f"Model saved to: {model_path}")
    print("="*60)

    # Print per-category performance
    print("\nPer-Category Performance:")
    print("-" * 40)
    for i, category in enumerate(evaluation_results['per_class_metrics']['categories']):
        precision = evaluation_results['per_class_metrics']['precision'][i]
        recall = evaluation_results['per_class_metrics']['recall'][i]
        f1 = evaluation_results['per_class_metrics']['f1_score'][i]
        support = evaluation_results['per_class_metrics']['support'][i]

        print(f"{category:20} | P: {precision:.3f} | R: {recall:.3f} | F1: {f1:.3f} | N: {support}")


if __name__ == '__main__':
    main()