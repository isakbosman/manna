"""
Enhanced Machine Learning router for transaction categorization and model management.
Supports advanced ML models, rule-based categorization, and comprehensive analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Body
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
from uuid import UUID
import logging

from ..database import get_db
from ..database.models import Transaction, Account, Category, MLPrediction, CategorizationRule
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
from ..services.category_rules import category_rules_service

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


# Enhanced endpoints for advanced ML functionality

@router.post("/train/enhanced")
async def train_enhanced_model(
    use_ensemble: bool = Query(True, description="Use ensemble of multiple models"),
    min_samples: int = Query(100, description="Minimum samples required"),
    test_size: float = Query(0.2, ge=0.1, le=0.5, description="Test set proportion"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Train enhanced ML model with ensemble methods and advanced feature engineering.
    """
    try:
        # Use the enhanced training method
        result = ml_service.train_enhanced_model(
            db=db,
            user_id=str(current_user.id),
            test_size=test_size,
            min_samples=min_samples,
            use_ensemble=use_ensemble
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Training failed"))

        return {
            "success": True,
            "model_type": result.get("model_type", "ensemble"),
            "test_accuracy": result.get("test_accuracy", 0),
            "cv_mean_accuracy": result.get("cv_mean_accuracy", 0),
            "cv_std_accuracy": result.get("cv_std_accuracy", 0),
            "training_samples": result.get("training_samples", 0),
            "test_samples": result.get("test_samples", 0),
            "feature_count": result.get("feature_count", 0),
            "categories": result.get("categories", []),
            "message": "Enhanced model training completed successfully"
        }

    except Exception as e:
        logger.error(f"Enhanced model training failed: {e}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.get("/predictions/history")
async def get_prediction_history(
    limit: int = Query(100, le=1000, description="Maximum number of predictions to return"),
    offset: int = Query(0, ge=0, description="Number of predictions to skip"),
    include_feedback: bool = Query(True, description="Include user feedback information"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get history of ML predictions for user's transactions.
    """
    # Query ML predictions for user's transactions
    query = db.query(MLPrediction).join(Transaction).join(Account).filter(
        Account.user_id == current_user.id
    ).order_by(desc(MLPrediction.prediction_date))

    if not include_feedback:
        # Only predictions without user feedback
        query = query.filter(MLPrediction.user_feedback.is_(None))

    predictions = query.offset(offset).limit(limit).all()
    total_count = query.count()

    # Format response
    prediction_data = []
    for pred in predictions:
        prediction_data.append({
            "id": str(pred.id),
            "transaction_id": str(pred.transaction_id),
            "category_id": str(pred.category_id) if pred.category_id else None,
            "model_version": pred.model_version,
            "model_type": pred.model_type,
            "confidence": float(pred.confidence),
            "probability": float(pred.probability),
            "prediction_date": pred.prediction_date,
            "is_accepted": pred.is_accepted,
            "user_feedback": pred.user_feedback,
            "feedback_date": pred.feedback_date,
            "alternative_predictions": pred.alternative_predictions,
            "features_used": pred.features_used,
            "confidence_level": pred.confidence_level
        })

    return {
        "predictions": prediction_data,
        "total_count": total_count,
        "limit": limit,
        "offset": offset
    }


@router.get("/analytics/performance")
async def get_ml_performance_analytics(
    days_back: int = Query(30, ge=1, le=365, description="Days of data to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get comprehensive ML performance analytics.
    """
    start_date = datetime.utcnow() - timedelta(days=days_back)

    # Get predictions with feedback
    predictions_query = db.query(MLPrediction).join(Transaction).join(Account).filter(
        Account.user_id == current_user.id,
        MLPrediction.prediction_date >= start_date,
        MLPrediction.user_feedback.isnot(None)
    )

    predictions_with_feedback = predictions_query.all()

    if not predictions_with_feedback:
        return {
            "period_days": days_back,
            "total_predictions": 0,
            "accuracy": None,
            "confidence_distribution": {},
            "category_performance": {},
            "model_performance": {},
            "feedback_trends": []
        }

    # Calculate overall accuracy
    correct_predictions = sum(1 for p in predictions_with_feedback if p.is_accepted)
    accuracy = correct_predictions / len(predictions_with_feedback)

    # Confidence distribution
    confidence_bins = [0.0, 0.5, 0.7, 0.8, 0.9, 1.0]
    confidence_dist = {f"{confidence_bins[i]}-{confidence_bins[i+1]}": 0 for i in range(len(confidence_bins)-1)}

    for pred in predictions_with_feedback:
        conf = float(pred.confidence)
        for i in range(len(confidence_bins)-1):
            if confidence_bins[i] <= conf < confidence_bins[i+1]:
                confidence_dist[f"{confidence_bins[i]}-{confidence_bins[i+1]}"] += 1
                break

    # Category performance
    category_performance = {}
    for pred in predictions_with_feedback:
        if pred.category and pred.category.name:
            cat_name = pred.category.name
            if cat_name not in category_performance:
                category_performance[cat_name] = {"total": 0, "correct": 0, "accuracy": 0}

            category_performance[cat_name]["total"] += 1
            if pred.is_accepted:
                category_performance[cat_name]["correct"] += 1

    # Calculate category accuracies
    for cat_data in category_performance.values():
        if cat_data["total"] > 0:
            cat_data["accuracy"] = cat_data["correct"] / cat_data["total"]

    # Model performance by version
    model_performance = {}
    for pred in predictions_with_feedback:
        model_key = f"{pred.model_type}_{pred.model_version}"
        if model_key not in model_performance:
            model_performance[model_key] = {"total": 0, "correct": 0, "accuracy": 0}

        model_performance[model_key]["total"] += 1
        if pred.is_accepted:
            model_performance[model_key]["correct"] += 1

    # Calculate model accuracies
    for model_data in model_performance.values():
        if model_data["total"] > 0:
            model_data["accuracy"] = model_data["correct"] / model_data["total"]

    return {
        "period_days": days_back,
        "total_predictions": len(predictions_with_feedback),
        "accuracy": accuracy,
        "confidence_distribution": confidence_dist,
        "category_performance": category_performance,
        "model_performance": model_performance,
        "high_confidence_accuracy": sum(1 for p in predictions_with_feedback if p.is_accepted and p.confidence >= 0.8) / max(1, sum(1 for p in predictions_with_feedback if p.confidence >= 0.8)),
        "avg_confidence": sum(float(p.confidence) for p in predictions_with_feedback) / len(predictions_with_feedback)
    }


@router.post("/rules/create")
async def create_categorization_rule(
    rule_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Create a new categorization rule for the user.
    """
    try:
        # Validate required fields
        required_fields = ["name", "rule_type", "pattern", "category_name"]
        for field in required_fields:
            if field not in rule_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Create the rule
        rule = category_rules_service.create_user_rule(
            db=db,
            user_id=str(current_user.id),
            rule_data=rule_data
        )

        return {
            "success": True,
            "rule_id": str(rule.id),
            "message": f"Rule '{rule.name}' created successfully"
        }

    except Exception as e:
        logger.error(f"Failed to create rule: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create rule: {str(e)}")


@router.get("/rules/stats")
async def get_rule_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get statistics about user's categorization rules.
    """
    try:
        stats = category_rules_service.get_rule_statistics(
            db=db,
            user_id=str(current_user.id)
        )
        return stats

    except Exception as e:
        logger.error(f"Failed to get rule statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve rule statistics")


@router.post("/categorize/with-rules")
async def categorize_transaction_with_rules(
    transaction_id: UUID,
    apply_ml_if_no_rule_match: bool = Query(True, description="Apply ML if no rules match"),
    min_rule_confidence: float = Query(0.7, ge=0, le=1, description="Minimum rule confidence"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Categorize transaction using rules first, then ML as fallback.
    """
    # Get transaction
    transaction = db.query(Transaction).join(Account).filter(
        Transaction.id == transaction_id,
        Account.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Apply rules first
    rule_match = category_rules_service.get_best_rule_match(
        transaction=transaction,
        db=db,
        user_id=str(current_user.id)
    )

    if rule_match and rule_match.confidence >= min_rule_confidence:
        # Use rule-based categorization
        result = TransactionCategorization(
            transaction_id=transaction.id,
            suggested_category=rule_match.category_name,
            confidence=rule_match.confidence,
            alternative_categories=None,
            rules_applied=[f"Rule: {rule_match.rule_name}"]
        )

        # Store the prediction
        ml_service.store_prediction_feedback(
            db=db,
            transaction_id=str(transaction.id),
            predicted_category=rule_match.category_name,
            actual_category=rule_match.category_name,
            user_confidence=rule_match.confidence
        )

    elif apply_ml_if_no_rule_match:
        # Fall back to ML categorization
        result = ml_service.categorize_transaction(
            transaction,
            use_ml=True,
            use_rules=False  # We already tried rules
        )
        result.rules_applied = ["ML fallback (no rule match)"]

    else:
        # No categorization available
        result = TransactionCategorization(
            transaction_id=transaction.id,
            suggested_category="Uncategorized",
            confidence=0.0,
            alternative_categories=None,
            rules_applied=["No applicable rules found"]
        )

    return result


@router.post("/feedback/batch")
async def provide_batch_feedback(
    feedback_items: List[Dict[str, Any]] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Provide feedback on multiple categorizations at once.
    """
    try:
        feedback_results = []

        for item in feedback_items:
            transaction_id = item.get("transaction_id")
            correct_category = item.get("correct_category")
            was_correct = item.get("was_correct", False)

            if not transaction_id or not correct_category:
                continue

            # Verify transaction belongs to user
            transaction = db.query(Transaction).join(Account).filter(
                Transaction.id == transaction_id,
                Account.user_id == current_user.id
            ).first()

            if transaction:
                # Update transaction
                transaction.user_category_override = correct_category
                transaction.updated_at = datetime.utcnow()

                # Record feedback
                feedback_result = ml_service.update_from_feedback(
                    transaction_id=str(transaction_id),
                    correct_category=correct_category,
                    was_correct=was_correct
                )

                feedback_results.append({
                    "transaction_id": str(transaction_id),
                    "success": True,
                    "retrain_triggered": feedback_result.get("retrain_triggered", False)
                })
            else:
                feedback_results.append({
                    "transaction_id": str(transaction_id),
                    "success": False,
                    "error": "Transaction not found or unauthorized"
                })

        db.commit()

        # Check if any triggered retraining
        retrain_triggered = any(r.get("retrain_triggered", False) for r in feedback_results)

        return {
            "success": True,
            "processed_count": len(feedback_results),
            "successful_feedback": sum(1 for r in feedback_results if r["success"]),
            "retrain_triggered": retrain_triggered,
            "results": feedback_results
        }

    except Exception as e:
        logger.error(f"Batch feedback failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch feedback failed: {str(e)}")


@router.get("/model/feature-importance")
async def get_model_feature_importance(
    top_n: int = Query(20, ge=5, le=100, description="Number of top features to return"),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get the most important features from the trained model.
    """
    try:
        # Get model metrics which includes feature information
        metrics = ml_service.get_model_metrics()

        if not metrics.get("model_loaded"):
            raise HTTPException(status_code=404, detail="No trained model found")

        # Try to extract feature importance from the model
        feature_importance = []

        if ml_service.text_vectorizer and ml_service.ensemble_classifier:
            try:
                # Get feature names from vectorizer
                feature_names = ml_service.text_vectorizer.get_feature_names_out()

                # For ensemble, we'll try to get feature importance from random forest component
                if hasattr(ml_service.ensemble_classifier, 'estimators_'):
                    for name, estimator in ml_service.ensemble_classifier.estimators_:
                        if hasattr(estimator, 'feature_importances_'):
                            importances = estimator.feature_importances_
                            # Get top features
                            top_indices = importances.argsort()[-top_n:][::-1]
                            for idx in top_indices:
                                feature_importance.append({
                                    "feature": feature_names[idx],
                                    "importance": float(importances[idx]),
                                    "model_component": name
                                })
                            break

                # Sort by importance
                feature_importance.sort(key=lambda x: x["importance"], reverse=True)
                feature_importance = feature_importance[:top_n]

            except Exception as e:
                logger.warning(f"Could not extract feature importance: {e}")

        return {
            "model_loaded": metrics.get("model_loaded"),
            "model_version": metrics.get("model_version", "unknown"),
            "feature_count": metrics.get("feature_count", 0),
            "top_features": feature_importance,
            "note": "Feature importance may not be available for all model types"
        }

    except Exception as e:
        logger.error(f"Failed to get feature importance: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feature importance")