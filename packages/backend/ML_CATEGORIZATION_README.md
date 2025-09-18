# ML-Powered Transaction Categorization System

A comprehensive machine learning system for automatically categorizing financial transactions with high accuracy and user-friendly features.

## Overview

This system provides intelligent transaction categorization using:
- **Multiple ML algorithms** with ensemble voting (Naive Bayes, Random Forest, SVM)
- **Advanced feature engineering** (TF-IDF, temporal, merchant, amount features)
- **Rule-based categorization** with priority system and regex patterns
- **Redis caching** for performance optimization
- **Incremental learning** from user feedback
- **Comprehensive analytics** and performance monitoring

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Router    │    │  ML Service     │    │ Category Rules  │
│                 │───▶│                 │───▶│    Service      │
│ /api/v1/ml/*    │    │ - Ensemble ML   │    │ - Regex Rules   │
└─────────────────┘    │ - Feature Eng.  │    │ - Priority Sys. │
                       │ - Redis Cache   │    │ - User Rules    │
                       └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Database      │
                       │                 │
                       │ - Transactions  │
                       │ - Categories    │
                       │ - ML Predictions│
                       │ - Rules         │
                       └─────────────────┘
```

## Key Components

### 1. ML Categorization Service (`ml_categorization.py`)

The core service providing ML-powered categorization with:

**Features:**
- Ensemble classifier combining multiple algorithms
- TF-IDF text vectorization with n-grams (1-3)
- Advanced feature extraction (temporal, merchant, amount patterns)
- Redis caching for performance
- Confidence scoring (0-100%)
- Alternative category suggestions

**Models Supported:**
- Multinomial Naive Bayes
- Complement Naive Bayes
- Random Forest Classifier
- Support Vector Machine (SVM)
- Logistic Regression
- Ensemble voting classifier

### 2. Category Rules Service (`category_rules.py`)

Rule-based categorization engine with:

**Rule Types:**
- Keyword matching
- Regex patterns
- Merchant-specific rules
- Amount-based rules
- Compound conditions
- ML-assisted rules

**Features:**
- Priority-based rule application
- User-customizable rules
- Pattern matching types (contains, exact, regex, starts_with, ends_with, fuzzy)
- Rule performance tracking
- Automatic rule optimization

### 3. Training Pipeline (`train_categorization.py`)

Comprehensive model training with:
- Data preprocessing and cleaning
- Feature engineering pipeline
- Hyperparameter optimization (Grid Search)
- Cross-validation evaluation
- Model comparison and selection
- Performance analytics

### 4. Enhanced API Endpoints (`ml.py`)

Rich API providing:
- Single and batch categorization
- Model training and retraining
- Performance analytics
- Rule management
- Feature importance analysis
- Prediction history

## API Endpoints

### Core Categorization

```python
# Single transaction categorization
POST /api/v1/ml/categorize
{
    "transaction_id": "uuid",
    "use_ml": true,
    "use_rules": true
}

# Batch categorization
POST /api/v1/ml/categorize/batch
{
    "transaction_ids": ["uuid1", "uuid2"],
    "auto_apply": true,
    "min_confidence": 0.8
}

# Rule-based categorization
POST /api/v1/ml/categorize/with-rules
{
    "transaction_id": "uuid",
    "min_rule_confidence": 0.7
}
```

### Model Training

```python
# Enhanced model training
POST /api/v1/ml/train/enhanced
{
    "use_ensemble": true,
    "min_samples": 100,
    "test_size": 0.2
}

# Model retraining
POST /api/v1/ml/retrain
{
    "force": false
}
```

### Analytics & Monitoring

```python
# Performance analytics
GET /api/v1/ml/analytics/performance?days_back=30

# Model metrics
GET /api/v1/ml/metrics

# Feature importance
GET /api/v1/ml/model/feature-importance?top_n=20

# Prediction history
GET /api/v1/ml/predictions/history?limit=100
```

### Rule Management

```python
# Create custom rule
POST /api/v1/ml/rules/create
{
    "name": "Coffee Shops",
    "rule_type": "regex",
    "pattern": "(?i)(starbucks|coffee|cafe)",
    "category_name": "Food & Dining",
    "priority": 10
}

# Rule statistics
GET /api/v1/ml/rules/stats
```

### Feedback & Learning

```python
# Single feedback
POST /api/v1/ml/feedback
{
    "transaction_id": "uuid",
    "correct_category": "Food & Dining",
    "was_correct": false
}

# Batch feedback
POST /api/v1/ml/feedback/batch
[
    {
        "transaction_id": "uuid1",
        "correct_category": "Transportation",
        "was_correct": true
    }
]
```

## Usage Examples

### Basic Categorization

```python
from services.ml_categorization import ml_service

# Categorize a transaction
result = ml_service.categorize_transaction(
    transaction=transaction,
    use_ml=True,
    use_rules=True
)

print(f"Category: {result.suggested_category}")
print(f"Confidence: {result.confidence:.2%}")
print(f"Rules: {result.rules_applied}")
```

### Batch Processing

```python
# Categorize multiple transactions
results = ml_service.batch_categorize(
    transactions=transaction_list,
    use_cache=True
)

# Apply high-confidence categorizations
for transaction, result in zip(transaction_list, results):
    if result.confidence >= 0.8:
        transaction.category = result.suggested_category
```

### Custom Rules

```python
from services.category_rules import category_rules_service

# Create a custom rule
rule_data = {
    "name": "Gym Memberships",
    "rule_type": "regex",
    "pattern": r"(?i)(gym|fitness|planet)",
    "category_name": "Health & Fitness",
    "priority": 5
}

rule = category_rules_service.create_user_rule(
    db=db_session,
    user_id=user_id,
    rule_data=rule_data
)
```

### Model Training

```python
# Train enhanced model
result = ml_service.train_enhanced_model(
    db=db_session,
    user_id=user_id,
    use_ensemble=True,
    min_samples=100
)

print(f"Accuracy: {result['test_accuracy']:.2%}")
print(f"Categories: {len(result['categories'])}")
```

## Performance Features

### Caching Strategy

- **Redis caching** for prediction results
- **Cache keys** based on transaction characteristics
- **TTL-based expiration** (1 hour default)
- **Cache invalidation** on feedback
- **Hit rate monitoring**

### Optimization Features

- **Batch processing** for multiple transactions
- **Feature pre-computation** and reuse
- **Model persistence** with joblib
- **Incremental learning** support
- **Parallel processing** options

## Configuration

### Environment Variables

```bash
# ML Settings
ML_MODEL_PATH="/app/models/categorization"
ML_CONFIDENCE_THRESHOLD=0.75
ML_BATCH_SIZE=32

# Redis Settings
REDIS_URL="redis://localhost:6379/0"
REDIS_TTL=3600

# Database
DATABASE_URL="postgresql://user:pass@localhost/db"
```

### Model Configuration

```python
# TF-IDF Vectorizer
TfidfVectorizer(
    max_features=2000,
    ngram_range=(1, 3),
    stop_words='english',
    min_df=2,
    max_df=0.95,
    sublinear_tf=True
)

# Ensemble Classifier
VotingClassifier([
    ('nb', MultinomialNB(alpha=0.1)),
    ('cnb', ComplementNB(alpha=0.1)),
    ('rf', RandomForestClassifier(n_estimators=100)),
    ('svm', SVC(probability=True, C=1.0))
], voting='soft')
```

## Default Rules

The system includes comprehensive default rules for common categories:

### Food & Dining
- Major chains: Starbucks, McDonald's, Subway
- Delivery services: Uber Eats, DoorDash, Grubhub
- General food keywords

### Transportation
- Rideshare: Uber, Lyft, Taxi
- Gas stations: Shell, Exxon, Chevron
- Public transit: Metro, Bus, Train

### Shopping
- Major retailers: Amazon, Walmart, Target
- Online marketplaces: eBay, Etsy

### Bills & Utilities
- Utilities: Electric, Gas, Water, Internet
- Telecom: Verizon, AT&T, Comcast

### Entertainment
- Streaming: Netflix, Spotify, Hulu
- Gaming: Steam, PlayStation, Xbox

### Healthcare
- Medical: Hospital, Clinic, Pharmacy
- Pharmacies: CVS, Walgreens

### Income
- Payroll: Salary, Direct Deposit
- Investments: Interest, Dividends

## Performance Metrics

### Model Evaluation
- **Accuracy**: Overall correctness
- **Precision/Recall/F1**: Per-category performance
- **Confidence distribution**: Model certainty analysis
- **Cross-validation scores**: Robustness testing

### Rule Performance
- **Match count**: Usage frequency
- **Accuracy score**: User feedback based
- **Priority effectiveness**: Rule ordering optimization

### System Performance
- **Cache hit rate**: Performance optimization
- **Processing time**: Response speed
- **Throughput**: Batch processing capacity

## Integration Points

### Plaid Transaction Sync
- **Auto-categorization** on new transactions
- **Background processing** for bulk imports
- **Confidence thresholds** for auto-application

### User Interface
- **Category suggestions** with confidence
- **Alternative options** display
- **Feedback collection** workflows
- **Rule management** interface

### Reporting System
- **Categorized spending** analysis
- **Budget tracking** by category
- **Financial insights** generation

## Monitoring & Maintenance

### Health Checks
- Model availability and performance
- Cache connectivity and efficiency
- Database query performance
- Rule effectiveness analysis

### Retraining Triggers
- Feedback threshold reached (50+ items)
- Performance degradation detected
- New category patterns identified
- Scheduled periodic retraining

### Analytics Dashboard
- Categorization accuracy trends
- User feedback patterns
- Rule performance metrics
- Model comparison analytics

## Getting Started

1. **Install Dependencies**
   ```bash
   pip install scikit-learn pandas numpy redis
   ```

2. **Setup Configuration**
   ```bash
   export ML_MODEL_PATH="/app/models"
   export REDIS_URL="redis://localhost:6379/0"
   ```

3. **Initialize Services**
   ```python
   from services.ml_categorization import ml_service
   from services.category_rules import category_rules_service
   ```

4. **Train Initial Model**
   ```bash
   python src/ml/train_categorization.py --user-id USER_ID
   ```

5. **Start Categorizing**
   ```python
   result = ml_service.categorize_transaction(transaction)
   ```

## Advanced Features

### Custom Feature Engineering
- Merchant pattern analysis
- Amount clustering
- Temporal pattern detection
- Geographic categorization

### Ensemble Optimization
- Model weight optimization
- Dynamic model selection
- Performance-based weighting

### Incremental Learning
- Online learning algorithms
- Concept drift detection
- Adaptive threshold adjustment

This ML categorization system provides a robust, scalable, and user-friendly solution for automatically categorizing financial transactions with high accuracy and comprehensive customization options.