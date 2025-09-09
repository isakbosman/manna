"""
Category management router for transaction categorization.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from ..database import get_db
from ..database.models import Category, Transaction, Account
from ..schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryWithStats,
    CategoryRule
)
from ..dependencies.auth import get_current_verified_user
from ..database.models import User

router = APIRouter()


@router.get("/", response_model=List[CategoryResponse])
async def list_categories(
    include_system: bool = Query(True, description="Include system categories"),
    include_stats: bool = Query(False, description="Include usage statistics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    List all categories available to the user.
    """
    query = db.query(Category).filter(
        or_(
            Category.user_id == current_user.id,
            and_(Category.is_system == True, include_system == True)
        ),
        Category.is_active == True
    )
    
    categories = query.order_by(Category.parent_category, Category.name).all()
    
    if include_stats:
        # Get transaction counts for each category
        result = []
        for category in categories:
            txn_count = db.query(func.count(Transaction.id)).join(Account).filter(
                Account.user_id == current_user.id,
                or_(
                    Transaction.user_category == category.name,
                    Transaction.primary_category == category.name
                )
            ).scalar()
            
            category_with_stats = CategoryWithStats.from_orm(category)
            category_with_stats.transaction_count = txn_count
            result.append(category_with_stats)
        
        return result
    
    return categories


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get a specific category by ID.
    """
    category = db.query(Category).filter(
        Category.id == category_id,
        or_(
            Category.user_id == current_user.id,
            Category.is_system == True
        )
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category


@router.post("/", response_model=CategoryResponse)
async def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Create a new custom category.
    """
    # Check if category name already exists for user
    existing = db.query(Category).filter(
        Category.user_id == current_user.id,
        Category.name == category_data.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Category '{category_data.name}' already exists"
        )
    
    # Create new category
    category = Category(
        user_id=current_user.id,
        name=category_data.name,
        parent_category=category_data.parent_category,
        description=category_data.description,
        color=category_data.color,
        icon=category_data.icon,
        is_system=False,
        is_active=True,
        rules=category_data.rules
    )
    
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    update_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Update a custom category.
    """
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id,
        Category.is_system == False
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found or cannot be modified"
        )
    
    # Check for name conflicts if name is being changed
    if update_data.name and update_data.name != category.name:
        existing = db.query(Category).filter(
            Category.user_id == current_user.id,
            Category.name == update_data.name,
            Category.id != category_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Category '{update_data.name}' already exists"
            )
    
    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(category, field, value)
    
    category.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(category)
    
    return category


@router.delete("/{category_id}")
async def delete_category(
    category_id: UUID,
    reassign_to: Optional[UUID] = Query(None, description="Category to reassign transactions to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Delete a custom category.
    """
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id,
        Category.is_system == False
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found or cannot be deleted"
        )
    
    # Handle transactions using this category
    transactions = db.query(Transaction).join(Account).filter(
        Account.user_id == current_user.id,
        Transaction.user_category == category.name
    ).all()
    
    if transactions:
        if reassign_to:
            # Verify reassignment category exists and is accessible
            new_category = db.query(Category).filter(
                Category.id == reassign_to,
                or_(
                    Category.user_id == current_user.id,
                    Category.is_system == True
                )
            ).first()
            
            if not new_category:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid reassignment category"
                )
            
            # Reassign transactions
            for txn in transactions:
                txn.user_category = new_category.name
                txn.updated_at = datetime.utcnow()
        else:
            # Clear category from transactions
            for txn in transactions:
                txn.user_category = None
                txn.updated_at = datetime.utcnow()
    
    # Soft delete the category
    category.is_active = False
    category.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Category deleted successfully",
        "transactions_affected": len(transactions)
    }


@router.post("/{category_id}/rules", response_model=CategoryResponse)
async def add_category_rule(
    category_id: UUID,
    rule: CategoryRule,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Add a matching rule to a category.
    """
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id,
        Category.is_system == False
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found or cannot be modified"
        )
    
    # Add rule to category
    rules = category.rules or []
    rules.append(rule.dict())
    category.rules = rules
    category.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(category)
    
    return category


@router.delete("/{category_id}/rules/{rule_index}")
async def remove_category_rule(
    category_id: UUID,
    rule_index: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Remove a matching rule from a category.
    """
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id,
        Category.is_system == False
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found or cannot be modified"
        )
    
    rules = category.rules or []
    
    if rule_index < 0 or rule_index >= len(rules):
        raise HTTPException(
            status_code=400,
            detail="Invalid rule index"
        )
    
    # Remove rule
    rules.pop(rule_index)
    category.rules = rules
    category.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "success": True,
        "message": "Rule removed successfully"
    }


@router.post("/apply-rules")
async def apply_category_rules(
    account_id: Optional[UUID] = Query(None, description="Apply to specific account"),
    dry_run: bool = Query(False, description="Preview changes without applying"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Apply category rules to uncategorized transactions.
    """
    # Get user's categories with rules
    categories = db.query(Category).filter(
        Category.user_id == current_user.id,
        Category.is_active == True,
        Category.rules != None
    ).all()
    
    # Get uncategorized transactions
    query = db.query(Transaction).join(Account).filter(
        Account.user_id == current_user.id,
        Transaction.user_category == None
    )
    
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    
    transactions = query.all()
    
    matches = []
    updated_count = 0
    
    for txn in transactions:
        for category in categories:
            if apply_rules_to_transaction(txn, category.rules):
                matches.append({
                    "transaction_id": str(txn.id),
                    "transaction_name": txn.name,
                    "category": category.name,
                    "rule_matched": True
                })
                
                if not dry_run:
                    txn.user_category = category.name
                    txn.updated_at = datetime.utcnow()
                    updated_count += 1
                
                break  # Apply first matching category
    
    if not dry_run:
        db.commit()
    
    return {
        "success": True,
        "dry_run": dry_run,
        "transactions_processed": len(transactions),
        "transactions_categorized": len(matches),
        "updated_count": updated_count if not dry_run else 0,
        "matches": matches[:100] if dry_run else []  # Limit preview results
    }


def apply_rules_to_transaction(transaction: Transaction, rules: List[Dict]) -> bool:
    """
    Check if transaction matches any of the category rules.
    """
    if not rules:
        return False
    
    for rule in rules:
        rule_type = rule.get("type")
        field = rule.get("field")
        operator = rule.get("operator")
        value = rule.get("value")
        
        if not all([rule_type, field, operator, value]):
            continue
        
        # Get transaction field value
        if field == "name":
            txn_value = transaction.name.lower() if transaction.name else ""
        elif field == "merchant":
            txn_value = transaction.merchant_name.lower() if transaction.merchant_name else ""
        elif field == "amount":
            txn_value = transaction.amount
        else:
            continue
        
        # Apply operator
        if operator == "contains" and isinstance(txn_value, str):
            if value.lower() in txn_value:
                return True
        elif operator == "equals":
            if txn_value == value or (isinstance(txn_value, str) and txn_value == value.lower()):
                return True
        elif operator == "starts_with" and isinstance(txn_value, str):
            if txn_value.startswith(value.lower()):
                return True
        elif operator == "greater_than" and isinstance(txn_value, (int, float)):
            if txn_value > float(value):
                return True
        elif operator == "less_than" and isinstance(txn_value, (int, float)):
            if txn_value < float(value):
                return True
    
    return False