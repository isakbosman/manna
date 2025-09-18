# Transaction Categorization System

A comprehensive machine learning and rule-based system for automatically categorizing financial transactions in the Manna Financial Platform.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [API Endpoints](#api-endpoints)
- [Machine Learning Model](#machine-learning-model)
- [Rule-Based Engine](#rule-based-engine)
- [Configuration](#configuration)
- [Installation & Setup](#installation--setup)
- [Usage Examples](#usage-examples)
- [Performance & Monitoring](#performance--monitoring)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)

## Overview

The Transaction Categorization System automatically classifies financial transactions into meaningful categories using a hybrid approach that combines:

- **Machine Learning**: Ensemble models trained on transaction features
- **Rule-Based Matching**: Configurable patterns for high-precision categorization
- **User Feedback**: Continuous learning from user corrections
- **Fallback Logic**: Intelligent defaults for unknown transactions

### Key Benefits

- **95%+ accuracy** on common transaction types
- **Sub-100ms response time** for single transaction categorization
- **Batch processing** support for thousands of transactions
- **Real-time learning** from user feedback
- **Extensible category system** with custom rules

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer                                │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Routers  │  Authentication  │  Request Validation  │
├─────────────────────────────────────────────────────────────┤
│                 Business Logic Layer                        │
├─────────────────────────────────────────────────────────────┤
│ ML Categorization │ Rule Engine │ Category Management      │
├─────────────────────────────────────────────────────────────┤
│                  Data Layer                                 │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL DB   │  Redis Cache  │  Feature Store         │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Transaction Input** → Feature extraction
2. **Rule Evaluation** → Pattern matching with confidence scores
3. **ML Prediction** → Ensemble model inference (if needed)
4. **Result Combination** → Best prediction with alternatives
5. **Cache Storage** → Redis caching for performance
6. **User Feedback** → Model retraining triggers

### Database Schema

```sql
-- Core transaction table
CREATE TABLE transactions (
    id UUID PRIMARY KEY,
    account_id UUID REFERENCES accounts(id),
    amount_cents INTEGER NOT NULL,
    date DATE NOT NULL,
    name TEXT NOT NULL,
    merchant_name TEXT,
    description TEXT,
    user_category TEXT,           -- User override
    primary_category TEXT,        -- ML prediction
    confidence_level FLOAT,       -- Prediction confidence
    is_reconciled BOOLEAN DEFAULT FALSE,
    tags TEXT[],
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Category management
CREATE TABLE categories (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name TEXT NOT NULL,
    parent_category TEXT,
    description TEXT,
    color TEXT,
    icon TEXT,
    rules JSONB,                 -- Rule definitions
    is_system BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ML prediction tracking
CREATE TABLE ml_predictions (
    id UUID PRIMARY KEY,
    transaction_id UUID REFERENCES transactions(id),
    category_id UUID REFERENCES categories(id),
    model_version TEXT,
    confidence FLOAT,
    probability FLOAT,
    is_accepted BOOLEAN,
    user_feedback TEXT,
    prediction_date TIMESTAMP DEFAULT NOW(),
    feedback_date TIMESTAMP
);
```

## Features

### 🤖 Machine Learning Categorization

- **Ensemble Models**: Combines Naive Bayes, Random Forest, and SVM classifiers
- **Feature Engineering**: Advanced text processing, amount analysis, temporal patterns
- **Incremental Learning**: Continuous improvement from user feedback
- **Cross-Validation**: Robust model evaluation and selection

### 📝 Rule-Based Engine

- **Pattern Matching**: Flexible regex and text matching rules
- **Priority System**: Hierarchical rule application with confidence scoring
- **Dynamic Rules**: User-configurable category rules
- **Merchant Detection**: Smart merchant name parsing and categorization

### 🔄 Batch Processing

- **High Throughput**: Process thousands of transactions per minute
- **Efficient Caching**: Redis-based result caching
- **Parallel Processing**: Multi-threaded batch operations
- **Progress Tracking**: Real-time processing status

### 📊 Analytics & Reporting

- **Category Statistics**: Transaction counts and amounts by category
- **Confidence Metrics**: Model performance monitoring
- **Trend Analysis**: Historical categorization patterns
- **Export/Import**: CSV and Excel data exchange

## API Endpoints

### Transaction Endpoints

#### List Transactions with Categorization
```http
GET /api/transactions/
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 50, max: 500)
- `start_date` (date): Filter by start date
- `end_date` (date): Filter by end date
- `category` (string): Filter by category
- `search` (string): Search in transaction name/merchant
- `sort_by` (string): Sort field (default: date)
- `sort_order` (string): asc/desc (default: desc)

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Starbucks Coffee",
      "merchant_name": "Starbucks",
      "amount": -5.75,
      "date": "2024-01-15",
      "user_category": "Coffee & Cafes",
      "confidence_level": 0.95,
      "is_reconciled": false,
      "tags": ["coffee", "morning"],
      "created_at": "2024-01-15T08:30:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "total_pages": 3,
  "has_next": true,
  "has_previous": false
}
```

#### Update Transaction Category
```http
PUT /api/transactions/{transaction_id}
```

**Request Body:**
```json
{
  "user_category": "Coffee & Cafes",
  "notes": "Morning coffee run",
  "tags": ["coffee", "daily"],
  "is_reconciled": true
}
```

#### Bulk Transaction Operations
```http
POST /api/transactions/bulk
```

**Request Body:**
```json
{
  "transaction_ids": ["uuid1", "uuid2", "uuid3"],
  "operation": "categorize",
  "category": "Food & Dining"
}
```

**Operations:**
- `categorize`: Set category for selected transactions
- `reconcile`: Mark transactions as reconciled
- `add_tag`: Add tag to transactions
- `remove_tag`: Remove tag from transactions
- `delete`: Delete transactions

### Category Endpoints

#### List Categories
```http
GET /api/categories/
```

**Query Parameters:**
- `include_system` (boolean): Include system categories (default: true)
- `include_stats` (boolean): Include usage statistics (default: false)

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Food & Dining",
    "parent_category": "Expenses",
    "description": "Restaurant meals and food purchases",
    "color": "#FF5722",
    "icon": "restaurant",
    "rules": [
      {
        "type": "text_match",
        "field": "merchant",
        "operator": "contains",
        "value": "restaurant",
        "confidence": 0.9
      }
    ],
    "is_system": true,
    "is_active": true,
    "transaction_count": 45
  }
]
```

#### Create Category
```http
POST /api/categories/
```

**Request Body:**
```json
{
  "name": "Coffee Shops",
  "parent_category": "Food & Dining",
  "description": "Coffee and cafe purchases",
  "color": "#8D6E63",
  "icon": "local_cafe",
  "rules": [
    {
      "type": "text_match",
      "field": "merchant",
      "operator": "contains",
      "value": "starbucks",
      "confidence": 0.95
    }
  ]
}
```

#### Apply Category Rules
```http
POST /api/categories/apply-rules
```

**Query Parameters:**
- `dry_run` (boolean): Preview changes without applying (default: false)
- `account_id` (UUID): Apply to specific account only

**Response:**
```json
{
  "success": true,
  "dry_run": false,
  "transactions_processed": 150,
  "transactions_categorized": 42,
  "updated_count": 42,
  "matches": []
}
```

### ML Categorization Endpoints

#### Categorize Single Transaction
```http
POST /api/ml/categorize/{transaction_id}
```

**Response:**
```json
{
  "transaction_id": "uuid",
  "suggested_category": "Food & Dining",
  "confidence": 0.92,
  "alternative_categories": [
    {"category": "Coffee & Cafes", "confidence": 0.85},
    {"category": "Fast Food", "confidence": 0.73}
  ],
  "rules_applied": ["Rule: Food & Dining (P1)"]
}
```

#### Batch Categorization
```http
POST /api/ml/categorize/batch
```

**Request Body:**
```json
{
  "transaction_ids": ["uuid1", "uuid2", "uuid3"]
}
```

#### Train ML Model
```http
POST /api/ml/train
```

**Request Body:**
```json
{
  "min_samples": 100,
  "test_size": 0.2,
  "use_ensemble": true
}
```

**Response:**
```json
{
  "success": true,
  "test_accuracy": 0.94,
  "cv_mean_accuracy": 0.92,
  "cv_std_accuracy": 0.03,
  "training_samples": 800,
  "test_samples": 200,
  "categories": ["Food & Dining", "Transportation", "Shopping"],
  "feature_count": 1500,
  "model_type": "ensemble"
}
```

#### Submit Feedback
```http
POST /api/ml/feedback
```

**Request Body:**
```json
{
  "transaction_id": "uuid",
  "predicted_category": "Food & Dining",
  "actual_category": "Coffee & Cafes",
  "user_confidence": 0.95
}
```

### Export/Import Endpoints

#### Export Transactions (CSV)
```http
GET /api/transactions/export/csv
```

**Query Parameters:**
- `start_date` (date): Start date for export
- `end_date` (date): End date for export
- `account_id` (UUID): Filter by account

#### Export Transactions (Excel)
```http
GET /api/transactions/export/excel
```

**Query Parameters:**
- `include_summary` (boolean): Include summary sheet (default: true)

#### Import Transactions (CSV)
```http
POST /api/transactions/import/csv
```

**Form Data:**
- `file`: CSV file
- `account_id`: Target account UUID

**CSV Format:**
```csv
Date,Description,Merchant,Amount,Category,Notes,Reconciled,Tags
2024-01-15,Starbucks Coffee,Starbucks,-5.75,Coffee & Cafes,Morning coffee,No,coffee,daily
```

## Machine Learning Model

### Model Architecture

The system uses an ensemble approach combining multiple algorithms:

1. **Multinomial Naive Bayes**: Fast text classification
2. **Complement Naive Bayes**: Handles imbalanced categories
3. **Random Forest**: Feature importance and non-linear patterns
4. **Support Vector Machine**: High-dimensional decision boundaries

### Feature Engineering

#### Text Features
- **TF-IDF Vectorization**: Term frequency-inverse document frequency
- **N-gram Analysis**: Unigrams, bigrams, and trigrams
- **Text Cleaning**: Normalization, special character removal
- **Merchant Parsing**: Smart extraction of merchant names

#### Amount Features
- **Raw Amount**: Transaction amount
- **Amount Bins**: Categorical amount ranges (micro, small, medium, large)
- **Logarithmic Scale**: Log-transformed amounts
- **Round Number Detection**: Even dollar amounts, round numbers

#### Temporal Features
- **Day of Week**: Monday=0, Sunday=6
- **Hour of Day**: 24-hour format
- **Month/Quarter**: Seasonal patterns
- **Weekend Detection**: Boolean weekend flag

#### Merchant Features
- **Merchant Type Detection**: Gas stations, restaurants, online retailers
- **Chain Recognition**: Common merchant patterns
- **Location Hints**: Geographic indicators

### Model Training Process

1. **Data Preparation**
   - Extract features from labeled transactions
   - Split into training/validation/test sets
   - Handle class imbalance with appropriate sampling

2. **Feature Engineering**
   - Text vectorization with TF-IDF
   - Numerical feature scaling
   - Feature selection and dimensionality reduction

3. **Model Training**
   - Train individual models on different feature subsets
   - Optimize hyperparameters with grid search
   - Validate with cross-validation

4. **Ensemble Creation**
   - Combine models with soft voting
   - Weight models by validation performance
   - Final evaluation on holdout test set

5. **Model Deployment**
   - Save trained models to disk
   - Load models into production service
   - Monitor performance metrics

### Performance Metrics

- **Accuracy**: Overall correctness (target: >90%)
- **Precision**: Category-specific accuracy (target: >85%)
- **Recall**: Category coverage (target: >80%)
- **F1-Score**: Harmonic mean of precision and recall
- **Confusion Matrix**: Detailed classification errors

## Rule-Based Engine

### Rule Types

#### Text Matching Rules
```json
{
  "type": "text_match",
  "field": "merchant",        // "name", "merchant", "description"
  "operator": "contains",     // "contains", "equals", "starts_with"
  "value": "starbucks",
  "confidence": 0.95
}
```

#### Amount Range Rules
```json
{
  "type": "amount_range",
  "field": "amount",
  "operator": "greater_than", // "greater_than", "less_than", "between"
  "value": "1000",
  "confidence": 0.8
}
```

#### Date Pattern Rules
```json
{
  "type": "date_pattern",
  "field": "date",
  "operator": "day_of_month", // "day_of_week", "day_of_month", "month"
  "value": "1",               // First of month
  "confidence": 0.7
}
```

### Rule Priority System

Rules are evaluated in order of priority:

1. **Priority 1**: High-confidence, specific patterns (merchant exact matches)
2. **Priority 2**: Medium-confidence, broader patterns (category keywords)
3. **Priority 3**: Low-confidence, general patterns (amount ranges)

### Rule Management

#### Adding Rules to Categories
```python
category.rules.append({
    "type": "text_match",
    "field": "merchant",
    "operator": "contains",
    "value": "new_merchant",
    "confidence": 0.9
})
```

#### Testing Rules
Use the `/api/categories/apply-rules?dry_run=true` endpoint to preview rule effects before applying them.

## Configuration

### Environment Variables

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/manna
REDIS_URL=redis://localhost:6379/0

# ML Configuration
ML_MODEL_PATH=/app/models
ML_CONFIDENCE_THRESHOLD=0.75
ML_RETRAIN_THRESHOLD=50  # Feedback items before retraining

# Cache Configuration
CACHE_TTL=3600  # Cache time-to-live in seconds

# API Configuration
API_RATE_LIMIT=1000  # Requests per minute
MAX_BATCH_SIZE=1000  # Maximum transactions per batch
```

### Model Configuration

```python
# Feature extraction settings
TFIDF_CONFIG = {
    "max_features": 2000,
    "ngram_range": (1, 3),
    "stop_words": "english",
    "min_df": 2,
    "max_df": 0.95,
    "sublinear_tf": True
}

# Ensemble model settings
ENSEMBLE_CONFIG = {
    "voting": "soft",
    "models": [
        ("nb", MultinomialNB(alpha=0.1)),
        ("cnb", ComplementNB(alpha=0.1)),
        ("rf", RandomForestClassifier(n_estimators=100)),
        ("svm", SVC(probability=True, kernel="linear"))
    ]
}
```

## Installation & Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- 4GB+ RAM (for ML model training)

### Installation Steps

1. **Clone Repository**
```bash
git clone https://github.com/your-org/manna-financial
cd manna-financial/packages/backend
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Set Up Database**
```bash
# Create database
createdb manna

# Run migrations
alembic upgrade head

# Seed sample data
python seeds/seed_categories.py
```

4. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Start Services**
```bash
# Start Redis
redis-server

# Start application
uvicorn src.main:app --reload
```

### Docker Setup

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: .
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/manna
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    ports:
      - "8000:8000"

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: manna
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

```bash
docker-compose up -d
```

## Usage Examples

### Python SDK Example

```python
from manna_client import MannaClient

client = MannaClient(api_key="your-api-key")

# Get transactions
transactions = client.transactions.list(
    start_date="2024-01-01",
    category="Food & Dining",
    page_size=100
)

# Categorize transaction
result = client.ml.categorize_transaction("transaction-uuid")
print(f"Suggested category: {result.suggested_category}")
print(f"Confidence: {result.confidence}")

# Bulk categorize
batch_results = client.ml.categorize_batch([
    "transaction-uuid-1",
    "transaction-uuid-2"
])

# Create custom category
category = client.categories.create(
    name="Coffee Shops",
    parent_category="Food & Dining",
    rules=[
        {
            "type": "text_match",
            "field": "merchant",
            "operator": "contains",
            "value": "coffee",
            "confidence": 0.9
        }
    ]
)

# Train model
training_result = client.ml.train_model(
    min_samples=100,
    use_ensemble=True
)
print(f"Training accuracy: {training_result.test_accuracy}")
```

### JavaScript/TypeScript Example

```typescript
import { MannaClient } from '@manna/client';

const client = new MannaClient({ apiKey: 'your-api-key' });

// Get categorized transactions
const transactions = await client.transactions.list({
  startDate: '2024-01-01',
  category: 'Food & Dining',
  pageSize: 50
});

// Categorize single transaction
const categorization = await client.ml.categorizeTransaction('transaction-uuid');
console.log('Suggested category:', categorization.suggestedCategory);

// Apply category rules
const ruleResults = await client.categories.applyRules({
  dryRun: true
});
console.log('Transactions would be categorized:', ruleResults.transactionsCategorized);

// Export transactions
const csvData = await client.transactions.exportCsv({
  startDate: '2024-01-01',
  endDate: '2024-12-31'
});
```

### cURL Examples

```bash
# Get transactions
curl -X GET "http://localhost:8000/api/transactions/?page=1&page_size=50" \
     -H "Authorization: Bearer your-token"

# Categorize transaction
curl -X POST "http://localhost:8000/api/ml/categorize/transaction-uuid" \
     -H "Authorization: Bearer your-token"

# Bulk categorize
curl -X POST "http://localhost:8000/api/transactions/bulk" \
     -H "Authorization: Bearer your-token" \
     -H "Content-Type: application/json" \
     -d '{
       "transaction_ids": ["uuid1", "uuid2"],
       "operation": "categorize",
       "category": "Food & Dining"
     }'

# Export CSV
curl -X GET "http://localhost:8000/api/transactions/export/csv" \
     -H "Authorization: Bearer your-token" \
     -o transactions.csv
```

## Performance & Monitoring

### Key Metrics

#### Response Time Targets
- Single categorization: < 100ms
- Batch processing (100 transactions): < 5s
- Model training: < 5 minutes (1000 samples)
- Export (10k transactions): < 30s

#### Accuracy Targets
- Overall accuracy: > 90%
- High-confidence predictions (>0.8): > 95%
- Rule-based matches: > 98%

#### Throughput Targets
- API requests: 1000/minute
- Batch categorization: 1000 transactions/minute
- Concurrent users: 100+

### Monitoring Setup

#### Application Metrics
```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

categorization_requests = Counter(
    'categorization_requests_total',
    'Total categorization requests',
    ['method', 'status']
)

categorization_duration = Histogram(
    'categorization_duration_seconds',
    'Time spent categorizing transactions'
)

model_accuracy = Gauge(
    'ml_model_accuracy',
    'Current ML model accuracy'
)
```

#### Health Checks
```python
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "ml_model_loaded": ml_service.model_loaded,
        "database_connected": await check_db_connection(),
        "redis_connected": await check_redis_connection(),
        "timestamp": datetime.utcnow().isoformat()
    }
```

#### Logging Configuration
```python
import logging
import structlog

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Structured logging for production
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
```

### Performance Optimization

#### Database Optimization
```sql
-- Indexes for transaction queries
CREATE INDEX idx_transactions_date ON transactions(date DESC);
CREATE INDEX idx_transactions_user_category ON transactions(user_category);
CREATE INDEX idx_transactions_amount ON transactions(amount_cents);
CREATE INDEX idx_transactions_search ON transactions USING gin(to_tsvector('english', name || ' ' || coalesce(merchant_name, '')));

-- Partitioning for large datasets
CREATE TABLE transactions_2024 PARTITION OF transactions
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

#### Caching Strategy
```python
# Redis caching for predictions
@cache(ttl=3600, key_prefix="ml_prediction")
async def get_prediction(transaction_hash: str):
    # Expensive ML computation
    pass

# Application-level caching
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_category_rules(user_id: str):
    # Cache category rules per user
    pass
```

#### Connection Pooling
```python
# Database connection pool
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Redis connection pool
redis_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    max_connections=50
)
```

## Testing

### Test Suite Structure

```
tests/
├── test_categorization_flow.py      # Integration tests
├── test_api_endpoints.py            # API endpoint tests
├── test_ml_categorization.py        # ML service tests
├── test_category_rules.py           # Rule engine tests
├── test_performance.py              # Performance tests
├── test_security.py                 # Security tests
└── conftest.py                      # Test fixtures
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m integration  # Integration tests
pytest -m unit         # Unit tests
pytest -m performance  # Performance tests

# Run tests in parallel
pytest -n auto

# Run with verbose output
pytest -v
```

### Test Categories

#### Unit Tests
```python
def test_feature_extraction():
    """Test transaction feature extraction."""
    extractor = FeatureExtractor()
    transaction = create_test_transaction()
    features = extractor.extract_all_features(transaction)

    assert len(features.text_features) > 0
    assert features.amount_features["amount_raw"] == transaction.amount
    assert features.temporal_features["month"] == transaction.date.month
```

#### Integration Tests
```python
def test_complete_categorization_flow():
    """Test end-to-end categorization workflow."""
    # Create test data
    transaction = create_test_transaction()

    # Test rule-based categorization
    result = ml_service.categorize_transaction(transaction)
    assert result.suggested_category is not None
    assert 0 <= result.confidence <= 1

    # Test user feedback
    feedback = ml_service.store_prediction_feedback(
        db, transaction.id, result.suggested_category, "Correct Category"
    )
    assert feedback.is_accepted is not None
```

#### Performance Tests
```python
def test_batch_processing_performance():
    """Test batch processing performance."""
    transactions = create_test_transactions(1000)

    start_time = time.time()
    results = ml_service.batch_categorize(transactions)
    duration = time.time() - start_time

    assert len(results) == len(transactions)
    assert duration < 60  # Should complete in under 1 minute

    throughput = len(results) / duration
    assert throughput > 16  # At least 16 transactions/second
```

### Test Data

#### Demo Script
```bash
# Run categorization demo
python scripts/demo_categorization.py

# Seed test data
python seeds/seed_categories.py

# Run performance tests
python scripts/performance_test.py
```

#### Test Database Setup
```python
# conftest.py
@pytest.fixture(scope="session")
def test_database():
    """Create test database for integration tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def test_ml_service():
    """Create ML service with test model."""
    service = MLCategorizationService(model_path=tempfile.mkdtemp())
    # Load pre-trained test model
    return service
```

## Deployment

### Production Deployment

#### Docker Production Image
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Create model directory
RUN mkdir -p /app/models

# Set environment variables
ENV PYTHONPATH=/app
ENV ML_MODEL_PATH=/app/models

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: manna-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: manna-backend
  template:
    metadata:
      labels:
        app: manna-backend
    spec:
      containers:
      - name: backend
        image: manna/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: manna-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: manna-secrets
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: manna-backend-service
spec:
  selector:
    app: manna-backend
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add categorization tables"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Model Deployment

#### Model Versioning
```python
class ModelVersion:
    def __init__(self, version: str, path: Path):
        self.version = version
        self.path = path
        self.metrics = self.load_metrics()

    def load_metrics(self) -> Dict[str, float]:
        """Load model performance metrics."""
        metrics_file = self.path / "metrics.json"
        if metrics_file.exists():
            with open(metrics_file) as f:
                return json.load(f)
        return {}

class ModelRegistry:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.models = self.discover_models()

    def get_best_model(self) -> ModelVersion:
        """Get the best performing model."""
        return max(self.models, key=lambda m: m.metrics.get("test_accuracy", 0))
```

#### Blue-Green Deployment
```python
# Model deployment strategy
async def deploy_new_model(new_model_path: Path):
    """Deploy new model with zero downtime."""
    # Load new model
    new_service = MLCategorizationService(model_path=new_model_path)

    # Validate model
    validation_result = await validate_model(new_service)
    if not validation_result.is_valid:
        raise ModelValidationError(validation_result.errors)

    # Switch traffic gradually
    await gradual_traffic_switch(new_service)

    # Monitor performance
    await monitor_model_performance(new_service)
```

### Monitoring & Alerting

#### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Manna Categorization System",
    "panels": [
      {
        "title": "Categorization Requests",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(categorization_requests_total[5m])",
            "legendFormat": "{{method}}"
          }
        ]
      },
      {
        "title": "ML Model Accuracy",
        "type": "singlestat",
        "targets": [
          {
            "expr": "ml_model_accuracy",
            "legendFormat": "Accuracy"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "histogram",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, categorization_duration_seconds_bucket)",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

#### Alerting Rules
```yaml
groups:
- name: manna-categorization
  rules:
  - alert: HighErrorRate
    expr: rate(categorization_requests_total{status!="200"}[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High error rate in categorization system"

  - alert: ModelAccuracyDrop
    expr: ml_model_accuracy < 0.85
    for: 10m
    labels:
      severity: critical
    annotations:
      summary: "ML model accuracy below threshold"

  - alert: SlowResponseTime
    expr: histogram_quantile(0.95, categorization_duration_seconds_bucket) > 1.0
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Slow categorization response times"
```

## Contributing

### Development Setup

1. **Fork Repository**
2. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-categorization-feature
   ```

3. **Set Up Development Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements-dev.txt
   pre-commit install
   ```

4. **Run Tests**
   ```bash
   pytest
   ```

5. **Submit Pull Request**

### Code Style

- **Python**: Follow PEP 8, use Black formatter
- **Type Hints**: Required for all function signatures
- **Docstrings**: Google-style docstrings for all public functions
- **Testing**: Minimum 80% test coverage required

### Commit Guidelines

```
feat: add new categorization algorithm
fix: resolve issue with batch processing
docs: update API documentation
test: add integration tests for ML service
refactor: improve feature extraction performance
```

### Review Process

1. **Automated Checks**: All CI checks must pass
2. **Code Review**: At least one approving review required
3. **Testing**: New features must include comprehensive tests
4. **Documentation**: Update relevant documentation

---

## Support

For questions, issues, or contributions:

- **GitHub Issues**: [Report bugs or request features](https://github.com/your-org/manna-financial/issues)
- **Documentation**: [Full API documentation](https://docs.manna.financial)
- **Discord**: [Join our community](https://discord.gg/manna-financial)
- **Email**: support@manna.financial

---

**Last Updated**: January 2025
**Version**: 1.0.0
**License**: MIT