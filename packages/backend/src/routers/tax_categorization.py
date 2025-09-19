"""API endpoints for tax categorization system."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..dependencies.auth import get_current_user
from ..database.base import get_db
from ..schemas.tax_categorization import (
    TaxCategory, TaxCategoryCreate, TaxCategoryUpdate,
    ChartOfAccount, ChartOfAccountCreate, ChartOfAccountUpdate,
    BusinessExpenseTracking, BusinessExpenseTrackingCreate, BusinessExpenseTrackingUpdate,
    CategoryMapping, CategoryMappingCreate, CategoryMappingUpdate,
    TaxCategorizationRequest, TaxCategorizationResponse,
    BulkTaxCategorizationRequest, BulkTaxCategorizationResponse,
    TaxSummaryResponse, ScheduleCExportResponse,
    TrialBalanceResponse, FinancialStatementsResponse
)
from ..schemas.user import User
from ..services.tax_categorization_service import TaxCategorizationService
from ..services.chart_of_accounts_service import ChartOfAccountsService
from models.tax_categorization import (
    TaxCategory as TaxCategoryModel,
    ChartOfAccount as ChartOfAccountModel,
    BusinessExpenseTracking as BusinessExpenseTrackingModel,
    CategoryMapping as CategoryMappingModel
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tax", tags=["Tax Categorization"])


# Tax Categorization Endpoints
@router.post("/categorize/{transaction_id}", response_model=TaxCategorizationResponse)
async def categorize_transaction_for_tax(
    transaction_id: str,
    request: TaxCategorizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Categorize a transaction for tax purposes."""
    try:
        service = TaxCategorizationService(db)
        result = service.categorize_for_tax(
            transaction_id=transaction_id,
            user_id=str(current_user.id),
            tax_category_id=str(request.tax_category_id) if request.tax_category_id else None,
            chart_account_id=str(request.chart_account_id) if request.chart_account_id else None,
            business_percentage=request.business_percentage,
            business_purpose=request.business_purpose,
            override_automated=request.override_automated
        )
        return TaxCategorizationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error categorizing transaction {transaction_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/categorize/bulk", response_model=BulkTaxCategorizationResponse)
async def bulk_categorize_transactions_for_tax(
    request: BulkTaxCategorizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk categorize multiple transactions for tax purposes."""
    try:
        service = TaxCategorizationService(db)
        result = service.bulk_categorize_for_tax(
            transaction_ids=[str(tid) for tid in request.transaction_ids],
            user_id=str(current_user.id),
            tax_category_id=str(request.tax_category_id) if request.tax_category_id else None,
            chart_account_id=str(request.chart_account_id) if request.chart_account_id else None,
            business_percentage=request.business_percentage
        )
        return BulkTaxCategorizationResponse(**result)
    except Exception as e:
        logger.error(f"Error bulk categorizing transactions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/summary/{tax_year}", response_model=TaxSummaryResponse)
async def get_tax_summary(
    tax_year: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get tax summary for a specific year."""
    try:
        service = TaxCategorizationService(db)
        result = service.get_tax_summary(str(current_user.id), tax_year)
        return TaxSummaryResponse(**result)
    except Exception as e:
        logger.error(f"Error getting tax summary for {tax_year}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/export/schedule-c/{tax_year}", response_model=ScheduleCExportResponse)
async def export_schedule_c(
    tax_year: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export Schedule C data for tax filing."""
    try:
        service = TaxCategorizationService(db)
        result = service.get_schedule_c_export(str(current_user.id), tax_year)
        return ScheduleCExportResponse(**result)
    except Exception as e:
        logger.error(f"Error exporting Schedule C for {tax_year}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Tax Categories Endpoints
@router.get("/categories", response_model=List[TaxCategory])
async def get_tax_categories(
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    tax_form: Optional[str] = Query(None, description="Filter by tax form"),
    db: Session = Depends(get_db)
):
    """Get available tax categories."""
    try:
        query = db.query(TaxCategoryModel)

        if is_active is not None:
            query = query.filter(TaxCategoryModel.is_active == is_active)

        if tax_form:
            query = query.filter(TaxCategoryModel.tax_form == tax_form)

        categories = query.order_by(TaxCategoryModel.category_code).all()
        return [TaxCategory.from_orm(cat) for cat in categories]
    except Exception as e:
        logger.error(f"Error getting tax categories: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/categories", response_model=TaxCategory)
async def create_tax_category(
    category: TaxCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new tax category (admin only)."""
    try:
        # Check if user is admin (you might want to implement admin role checking)
        tax_category = TaxCategoryModel(**category.dict())
        db.add(tax_category)
        db.commit()
        db.refresh(tax_category)
        return TaxCategory.from_orm(tax_category)
    except Exception as e:
        logger.error(f"Error creating tax category: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


# Chart of Accounts Endpoints
@router.get("/chart-of-accounts", response_model=List[ChartOfAccount])
async def get_chart_of_accounts(
    account_type: Optional[str] = Query(None, description="Filter by account type"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's chart of accounts."""
    try:
        query = db.query(ChartOfAccountModel).filter(
            ChartOfAccountModel.user_id == current_user.id
        )

        if account_type:
            query = query.filter(ChartOfAccountModel.account_type == account_type)

        if is_active is not None:
            query = query.filter(ChartOfAccountModel.is_active == is_active)

        accounts = query.order_by(ChartOfAccountModel.account_code).all()
        return [ChartOfAccount.from_orm(acc) for acc in accounts]
    except Exception as e:
        logger.error(f"Error getting chart of accounts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/chart-of-accounts", response_model=ChartOfAccount)
async def create_chart_account(
    account: ChartOfAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chart of accounts entry."""
    try:
        service = ChartOfAccountsService(db)
        created_account = service.create_account(
            user_id=str(current_user.id),
            **account.dict()
        )
        return ChartOfAccount.from_orm(created_account)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating chart account: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/chart-of-accounts/{account_id}", response_model=ChartOfAccount)
async def update_chart_account(
    account_id: str,
    account_update: ChartOfAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a chart of accounts entry."""
    try:
        service = ChartOfAccountsService(db)
        updated_account = service.update_account(
            account_id=account_id,
            user_id=str(current_user.id),
            **account_update.dict(exclude_unset=True)
        )
        return ChartOfAccount.from_orm(updated_account)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating chart account {account_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/chart-of-accounts/{account_id}")
async def delete_chart_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a chart of accounts entry."""
    try:
        service = ChartOfAccountsService(db)
        service.delete_account(account_id, str(current_user.id))
        return {"message": "Account deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting chart account {account_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Financial Reporting Endpoints
@router.get("/trial-balance", response_model=TrialBalanceResponse)
async def get_trial_balance(
    as_of_date: Optional[str] = Query(None, description="As of date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trial balance report."""
    try:
        service = ChartOfAccountsService(db)
        result = service.get_trial_balance(str(current_user.id), as_of_date)
        return TrialBalanceResponse(**result)
    except Exception as e:
        logger.error(f"Error getting trial balance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/financial-statements", response_model=FinancialStatementsResponse)
async def get_financial_statements(
    as_of_date: Optional[str] = Query(None, description="As of date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get financial statements (Balance Sheet and Income Statement)."""
    try:
        service = ChartOfAccountsService(db)
        result = service.generate_financial_statements(str(current_user.id), as_of_date)
        return FinancialStatementsResponse(**result)
    except Exception as e:
        logger.error(f"Error generating financial statements: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Business Expense Tracking Endpoints
@router.post("/business-expense", response_model=BusinessExpenseTracking)
async def create_business_expense_tracking(
    tracking: BusinessExpenseTrackingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create business expense tracking record."""
    try:
        tracking_record = BusinessExpenseTrackingModel(
            user_id=current_user.id,
            **tracking.dict()
        )
        db.add(tracking_record)
        db.commit()
        db.refresh(tracking_record)
        return BusinessExpenseTracking.from_orm(tracking_record)
    except Exception as e:
        logger.error(f"Error creating business expense tracking: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/business-expense/{transaction_id}", response_model=BusinessExpenseTracking)
async def get_business_expense_tracking(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get business expense tracking for a transaction."""
    try:
        tracking = db.query(BusinessExpenseTrackingModel).filter(
            BusinessExpenseTrackingModel.transaction_id == transaction_id,
            BusinessExpenseTrackingModel.user_id == current_user.id
        ).first()

        if not tracking:
            raise HTTPException(status_code=404, detail="Business expense tracking not found")

        return BusinessExpenseTracking.from_orm(tracking)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting business expense tracking: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Category Mapping Endpoints
@router.get("/category-mappings", response_model=List[CategoryMapping])
async def get_category_mappings(
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's category mappings."""
    try:
        query = db.query(CategoryMappingModel).filter(
            CategoryMappingModel.user_id == current_user.id
        )

        if is_active is not None:
            query = query.filter(CategoryMappingModel.is_active == is_active)

        mappings = query.all()
        return [CategoryMapping.from_orm(mapping) for mapping in mappings]
    except Exception as e:
        logger.error(f"Error getting category mappings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/category-mappings", response_model=CategoryMapping)
async def create_category_mapping(
    mapping: CategoryMappingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new category mapping."""
    try:
        category_mapping = CategoryMappingModel(
            user_id=current_user.id,
            **mapping.dict()
        )
        db.add(category_mapping)
        db.commit()
        db.refresh(category_mapping)
        return CategoryMapping.from_orm(category_mapping)
    except Exception as e:
        logger.error(f"Error creating category mapping: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")