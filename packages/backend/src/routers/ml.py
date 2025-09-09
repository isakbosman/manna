"""
Machine Learning router for transaction categorization and model management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
from uuid import UUID
import logging

from ..database import get_db
from ..database.models import Transaction, Account, Category
from ..schemas.transaction import TransactionCategorization
from ..schemas.ml import (
    MLTrainingRequest,
    MLTrainingResponse,
    MLFeedback,
    MLMetrics,
    BatchCategorizationRequest,
    BatchCategorizationResponse,
    ModelConfiguration
)
from ..dependencies.auth import get_current_verified_user
from ..database.models import User
from ..services.ml_categorization import ml_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/categorize", response_model=TransactionCategorization)
async def categorize_transaction(
    transaction_id: UUID,
    use_ml: bool = Query(True, description="Use ML model for categorization"),
    use_rules: bool = Query(True, description="Use rule-based categorization"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Categorize a single transaction using ML and/or rule-based methods.
    """
    # Get transaction
    transaction = db.query(Transaction).join(Account).filter(
        Transaction.id == transaction_id,
        Account.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Categorize transaction
    result = ml_service.categorize_transaction(
        transaction,
        use_ml=use_ml,
        use_rules=use_rules
    )
    
    # Optionally update transaction with suggested category
    if result.confidence >= 0.8 and not transaction.user_category:
        transaction.primary_category = result.suggested_category
        transaction.confidence_level = result.confidence
        transaction.updated_at = datetime.utcnow()
        db.commit()
    
    return result


@router.post("/categorize/batch", response_model=BatchCategorizationResponse)
async def categorize_batch(
    request: BatchCategorizationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Categorize multiple transactions in batch.
    """
    # Verify all transactions belong to user
    transactions = db.query(Transaction).join(Account).filter(
        Transaction.id.in_(request.transaction_ids),
        Account.user_id == current_user.id
    ).all()
    
    if len(transactions) != len(request.transaction_ids):
        raise HTTPException(
            status_code=403,
            detail="Some transactions not found or unauthorized"
        )
    
    # Categorize transactions
    results = ml_service.batch_categorize(transactions)
    
    # Update transactions if auto_apply is enabled
    updated_count = 0
    if request.auto_apply:
        for transaction, result in zip(transactions, results):
            if result.confidence >= request.min_confidence and not transaction.user_category:
                transaction.primary_category = result.suggested_category
                transaction.confidence_level = result.confidence
                transaction.updated_at = datetime.utcnow()
                updated_count += 1
        
        db.commit()
    
    return BatchCategorizationResponse(
        categorizations=results,
        total_processed=len(results),
        auto_applied=updated_count if request.auto_apply else 0,
        average_confidence=sum(r.confidence for r in results) / len(results) if results else 0
    )


@router.post("/categorize/auto")
async def auto_categorize_all(
    account_id: Optional[UUID] = Query(None, description="Specific account to process"),
    start_date: Optional[date] = Query(None, description="Start date for transactions"),
    end_date: Optional[date] = Query(None, description="End date for transactions"),
    min_confidence: float = Query(0.8, ge=0, le=1, description="Minimum confidence to apply"),
    dry_run: bool = Query(False, description="Preview without applying changes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Automatically categorize all uncategorized transactions.
    """
    # Build query for uncategorized transactions
    query = db.query(Transaction).join(Account).filter(
        Account.user_id == current_user.id,
        Transaction.user_category == None,
        Transaction.primary_category == None
    )
    
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    transactions = query.limit(1000).all()  # Limit for performance
    
    if not transactions:
        return {
            "success": True,
            "message": "No uncategorized transactions found",
            "processed": 0
        }
    
    # Categorize transactions
    results = ml_service.batch_categorize(transactions)
    
    # Apply categorizations
    categorized = []
    for transaction, result in zip(transactions, results):
        if result.confidence >= min_confidence:
            categorized.append({
                "transaction_id": str(transaction.id),
                "name": transaction.name,
                "amount": transaction.amount,
                "category": result.suggested_category,
                "confidence": result.confidence
            })
            
            if not dry_run:
                transaction.primary_category = result.suggested_category
                transaction.confidence_level = result.confidence
                transaction.updated_at = datetime.utcnow()
    
    if not dry_run:
        db.commit()
    
    return {
        "success": True,
        "dry_run": dry_run,
        "total_processed": len(transactions),
        "total_categorized": len(categorized),
        "average_confidence": sum(r.confidence for r in results) / len(results) if results else 0,
        "categorized": categorized[:100] if dry_run else [],  # Limit preview
        "message": f"{'Would categorize' if dry_run else 'Categorized'} {len(categorized)} transactions"
    }


@router.post("/train", response_model=MLTrainingResponse)
async def train_model(
    request: MLTrainingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Train or retrain the ML model with user's transaction data.
    """
    # Get training data
    query = db.query(Transaction).join(Account).filter(
        Account.user_id == current_user.id,
        or_(
            Transaction.user_category != None,
            Transaction.primary_category != None
        )
    )
    
    if request.start_date:
        query = query.filter(Transaction.date >= request.start_date)
    if request.end_date:
        query = query.filter(Transaction.date <= request.end_date)
    
    transactions = query.all()
    
    if len(transactions) < request.min_samples:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient training data. Need at least {request.min_samples} labeled transactions, found {len(transactions)}"
        )
    
    # Train model (in production, this would be async)
    result = ml_service.train_model(
        transactions,
        test_size=request.test_size,
        min_samples=request.min_samples
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Training failed"))
    
    return MLTrainingResponse(
        success=True,
        accuracy=result["accuracy"],
        training_samples=result["training_samples"],
        test_samples=result["test_samples"],
        categories_learned=len(result["categories"]),
        training_completed_at=datetime.utcnow(),
        model_version=f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        metrics=result.get("classification_report", {})
    )


@router.post("/feedback")
async def provide_feedback(
    feedback: MLFeedback,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Provide feedback on a categorization to improve the model.
    """
    # Verify transaction belongs to user
    transaction = db.query(Transaction).join(Account).filter(
        Transaction.id == feedback.transaction_id,
        Account.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Update transaction with correct category
    transaction.user_category = feedback.correct_category
    transaction.updated_at = datetime.utcnow()
    
    # Record feedback for model improvement
    result = ml_service.update_from_feedback(
        str(feedback.transaction_id),
        feedback.correct_category,
        feedback.was_correct
    )
    
    db.commit()
    
    return {
        "success": True,
        "feedback_recorded": True,
        "transaction_updated": True,
        "retrain_triggered": result.get("retrain_triggered", False),
        "message": "Thank you for your feedback. It will help improve future categorizations."
    }


@router.get("/metrics", response_model=MLMetrics)
async def get_model_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get current model performance metrics and statistics.
    """
    # Get model metrics
    model_metrics = ml_service.get_model_metrics()
    
    # Get usage statistics
    total_transactions = db.query(func.count(Transaction.id)).join(Account).filter(
        Account.user_id == current_user.id
    ).scalar()
    
    categorized_ml = db.query(func.count(Transaction.id)).join(Account).filter(
        Account.user_id == current_user.id,
        Transaction.primary_category != None,
        Transaction.confidence_level != None
    ).scalar()
    
    categorized_user = db.query(func.count(Transaction.id)).join(Account).filter(
        Account.user_id == current_user.id,
        Transaction.user_category != None
    ).scalar()
    
    # Get accuracy metrics from recent predictions
    recent_feedback = db.query(Transaction).join(Account).filter(
        Account.user_id == current_user.id,
        Transaction.user_category != None,
        Transaction.primary_category != None,
        Transaction.updated_at >= datetime.utcnow() - timedelta(days=30)
    ).all()
    
    accuracy = 0.0
    if recent_feedback:
        correct = sum(
            1 for t in recent_feedback
            if t.user_category == t.primary_category
        )
        accuracy = correct / len(recent_feedback)
    
    # Get category distribution
    category_dist = db.query(
        Transaction.primary_category,
        func.count(Transaction.id)
    ).join(Account).filter(
        Account.user_id == current_user.id,
        Transaction.primary_category != None
    ).group_by(Transaction.primary_category).all()
    
    return MLMetrics(
        model_loaded=model_metrics.get("model_loaded", False),
        model_version=model_metrics.get("model_version", "unknown"),
        last_trained=model_metrics.get("saved_at"),
        total_transactions=total_transactions,
        categorized_by_ml=categorized_ml,
        categorized_by_user=categorized_user,
        uncategorized=total_transactions - categorized_ml - categorized_user,
        accuracy=accuracy if recent_feedback else None,
        confidence_threshold=model_metrics.get("confidence_threshold", 0.6),
        categories_supported=model_metrics.get("rule_categories", []),
        category_distribution={cat: count for cat, count in category_dist},
        feedback_samples=len(recent_feedback)
    )


@router.post("/config", response_model=ModelConfiguration)
async def update_model_config(
    config: ModelConfiguration,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Update model configuration settings.
    """
    # Update confidence threshold
    if config.confidence_threshold:
        ml_service.confidence_threshold = config.confidence_threshold
    
    # Save configuration
    ml_service.save_models()
    
    return config


@router.post("/export-training-data")
async def export_training_data(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    format: str = Query("json", description="Export format (json, csv)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Export training data for external analysis or backup.
    """
    query = db.query(Transaction).join(Account).filter(
        Account.user_id == current_user.id,
        or_(
            Transaction.user_category != None,
            Transaction.primary_category != None
        )
    )
    
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    transactions = query.all()
    
    if not transactions:
        raise HTTPException(status_code=404, detail="No training data found")
    
    # Export data
    from pathlib import Path
    export_path = Path(f"/tmp/training_data_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}")
    
    result = ml_service.export_training_data(transactions, export_path)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail="Export failed")
    
    # In production, this would return a download URL or stream the file
    return {
        "success": True,
        "exported_transactions": result["exported_transactions"],
        "format": format,
        "message": f"Training data exported successfully",
        "path": str(export_path)  # In production, this would be a secure download URL
    }


@router.post("/retrain")
async def trigger_retraining(
    background_tasks: BackgroundTasks,
    force: bool = Query(False, description="Force retraining even with insufficient data"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Trigger model retraining with latest data.
    """
    # Get all labeled transactions
    transactions = db.query(Transaction).join(Account).filter(
        Account.user_id == current_user.id,
        or_(
            Transaction.user_category != None,
            Transaction.primary_category != None
        )
    ).all()
    
    min_required = 100 if not force else 10
    
    if len(transactions) < min_required:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient training data. Need at least {min_required} labeled transactions, found {len(transactions)}"
        )
    
    # Schedule retraining (in production, this would be a background job)
    background_tasks.add_task(
        ml_service.train_model,
        transactions,
        test_size=0.2,
        min_samples=min_required
    )
    
    return {
        "success": True,
        "message": "Model retraining has been scheduled",
        "training_samples": len(transactions),
        "estimated_time": "2-5 minutes"
    }