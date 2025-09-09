"""Accounts management endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc
from typing import List, Optional
from uuid import UUID
import logging

from ..database import get_db
from ..database.models import User, Account, Institution, PlaidItem
from ..schemas.account import (
    Account as AccountSchema, 
    AccountWithInstitution,
    AccountList, 
    AccountUpdate,
    AccountBalance,
    AccountSyncStatus
)
from ..schemas.common import SuccessResponse
from ..dependencies.auth import get_current_verified_user
from ..services.plaid_service import plaid_service
from ..utils.redis import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=AccountList)
async def list_accounts(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    account_type: Optional[str] = Query(None, description="Filter by account type"),
    include_hidden: bool = Query(False, description="Include hidden accounts"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
) -> AccountList:
    """
    List all user's connected accounts with pagination and filtering.
    
    - Returns accounts with institution information
    - Supports filtering by type and hidden status
    - Includes balance information
    """
    try:
        # Build query
        query = (
            db.query(Account)
            .options(
                joinedload(Account.institution),
                joinedload(Account.plaid_item).joinedload(PlaidItem.institution)
            )
            .filter(Account.user_id == current_user.id)
        )
        
        # Apply filters
        if not include_hidden:
            query = query.filter(Account.is_hidden == False)
        
        if account_type:
            query = query.filter(Account.type == account_type)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination and ordering
        accounts = (
            query
            .order_by(desc(Account.current_balance_cents), Account.name)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        
        # Transform to response format
        account_list = []
        for account in accounts:
            institution = account.institution or (account.plaid_item.institution if account.plaid_item else None)
            
            account_data = AccountWithInstitution(
                id=account.id,
                user_id=account.user_id,
                plaid_account_id=account.plaid_account_id,
                plaid_item_id=account.plaid_item_id,
                institution_id=account.institution_id,
                name=account.name,
                official_name=account.official_name,
                type=account.type,
                subtype=account.subtype,
                mask=account.mask,
                current_balance_cents=account.current_balance_cents,
                available_balance_cents=account.available_balance_cents,
                limit_cents=account.limit_cents,
                iso_currency_code=account.iso_currency_code,
                is_active=account.is_active,
                is_hidden=account.is_hidden,
                created_at=account.created_at,
                updated_at=account.updated_at,
                institution_name=institution.name if institution else None,
                institution_logo=institution.logo if institution else None,
                institution_color=institution.primary_color if institution else None,
            )
            account_list.append(account_data)
        
        return AccountList(
            accounts=account_list,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Failed to list accounts for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve accounts"
        )


@router.get("/{account_id}", response_model=AccountWithInstitution)
async def get_account(
    account_id: UUID,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
) -> AccountWithInstitution:
    """
    Get specific account details with institution information.
    
    - Returns full account details
    - Includes institution branding
    - Shows current balance and status
    """
    try:
        # Get account with related data
        account = (
            db.query(Account)
            .options(
                joinedload(Account.institution),
                joinedload(Account.plaid_item).joinedload(PlaidItem.institution)
            )
            .filter(
                and_(
                    Account.id == account_id,
                    Account.user_id == current_user.id
                )
            )
            .first()
        )
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        # Get institution info
        institution = account.institution or (account.plaid_item.institution if account.plaid_item else None)
        
        return AccountWithInstitution(
            id=account.id,
            user_id=account.user_id,
            plaid_account_id=account.plaid_account_id,
            plaid_item_id=account.plaid_item_id,
            institution_id=account.institution_id,
            name=account.name,
            official_name=account.official_name,
            type=account.type,
            subtype=account.subtype,
            mask=account.mask,
            current_balance_cents=account.current_balance_cents,
            available_balance_cents=account.available_balance_cents,
            limit_cents=account.limit_cents,
            iso_currency_code=account.iso_currency_code,
            is_active=account.is_active,
            is_hidden=account.is_hidden,
            created_at=account.created_at,
            updated_at=account.updated_at,
            institution_name=institution.name if institution else None,
            institution_logo=institution.logo if institution else None,
            institution_color=institution.primary_color if institution else None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get account {account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve account"
        )


@router.put("/{account_id}", response_model=AccountWithInstitution)
async def update_account(
    account_id: UUID,
    account_update: AccountUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
) -> AccountWithInstitution:
    """
    Update account information (user-controlled settings only).
    
    - Update display name
    - Toggle hidden/visible status
    - Change active status
    """
    try:
        # Get account
        account = (
            db.query(Account)
            .options(
                joinedload(Account.institution),
                joinedload(Account.plaid_item).joinedload(PlaidItem.institution)
            )
            .filter(
                and_(
                    Account.id == account_id,
                    Account.user_id == current_user.id
                )
            )
            .first()
        )
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        # Update only provided fields
        update_data = account_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(account, field, value)
        
        db.commit()
        db.refresh(account)
        
        logger.info(f"Updated account {account_id} for user {current_user.id}")
        
        # Get institution info for response
        institution = account.institution or (account.plaid_item.institution if account.plaid_item else None)
        
        return AccountWithInstitution(
            id=account.id,
            user_id=account.user_id,
            plaid_account_id=account.plaid_account_id,
            plaid_item_id=account.plaid_item_id,
            institution_id=account.institution_id,
            name=account.name,
            official_name=account.official_name,
            type=account.type,
            subtype=account.subtype,
            mask=account.mask,
            current_balance_cents=account.current_balance_cents,
            available_balance_cents=account.available_balance_cents,
            limit_cents=account.limit_cents,
            iso_currency_code=account.iso_currency_code,
            is_active=account.is_active,
            is_hidden=account.is_hidden,
            created_at=account.created_at,
            updated_at=account.updated_at,
            institution_name=institution.name if institution else None,
            institution_logo=institution.logo if institution else None,
            institution_color=institution.primary_color if institution else None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update account {account_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update account"
        )


@router.delete("/{account_id}", response_model=SuccessResponse)
async def delete_account(
    account_id: UUID,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
) -> SuccessResponse:
    """
    Disconnect/deactivate account (soft delete).
    
    - Deactivates the account
    - Preserves transaction history
    - Account can be reactivated by reconnecting Plaid item
    """
    try:
        # Get account
        account = db.query(Account).filter(
            and_(
                Account.id == account_id,
                Account.user_id == current_user.id
            )
        ).first()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        # Soft delete - deactivate the account
        account.is_active = False
        db.commit()
        
        logger.info(f"Deactivated account {account_id} for user {current_user.id}")
        
        return SuccessResponse(
            message="Account successfully disconnected",
            details={"account_id": str(account_id), "account_name": account.name}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete account {account_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect account"
        )


@router.post("/sync", response_model=List[AccountSyncStatus])
async def sync_accounts(
    background_tasks: BackgroundTasks,
    account_ids: Optional[List[UUID]] = Query(None, description="Specific account IDs to sync"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
) -> List[AccountSyncStatus]:
    """
    Sync account data with Plaid (balances and recent transactions).
    
    - Updates account balances
    - Fetches recent transactions
    - Can sync specific accounts or all user accounts
    """
    try:
        # Get accounts to sync
        query = (
            db.query(Account)
            .join(PlaidItem)
            .filter(
                and_(
                    Account.user_id == current_user.id,
                    Account.is_active == True,
                    PlaidItem.is_active == True
                )
            )
        )
        
        if account_ids:
            query = query.filter(Account.id.in_(account_ids))
        
        accounts = query.all()
        
        if not accounts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active accounts found to sync"
            )
        
        # Group accounts by Plaid item to minimize API calls
        items_to_sync = {}
        account_status = []
        
        for account in accounts:
            plaid_item = account.plaid_item
            if plaid_item.id not in items_to_sync:
                items_to_sync[plaid_item.id] = {
                    'plaid_item': plaid_item,
                    'accounts': []
                }
            items_to_sync[plaid_item.id]['accounts'].append(account)
        
        # Check for existing sync locks and initiate sync
        redis_client = await get_redis_client()
        
        for item_id, item_data in items_to_sync.items():
            plaid_item = item_data['plaid_item']
            item_accounts = item_data['accounts']
            
            # Check if sync is already in progress
            sync_in_progress = False
            if redis_client:
                lock_key = f"sync_lock:{item_id}"
                sync_in_progress = await redis_client.exists(lock_key)
            
            for account in item_accounts:
                if sync_in_progress:
                    account_status.append(AccountSyncStatus(
                        account_id=account.id,
                        status="in_progress",
                        last_synced=plaid_item.last_successful_sync,
                        transaction_count=0
                    ))
                else:
                    # Start sync for this item
                    if redis_client:
                        await redis_client.setex(f"sync_lock:{item_id}", 300, "1")
                    
                    background_tasks.add_task(
                        sync_account_data,
                        str(item_id),
                        plaid_item.access_token,
                        current_user.id
                    )
                    
                    account_status.append(AccountSyncStatus(
                        account_id=account.id,
                        status="started",
                        last_synced=plaid_item.last_successful_sync,
                        transaction_count=0
                    ))
        
        logger.info(f"Initiated sync for {len(accounts)} accounts for user {current_user.id}")
        
        return account_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync accounts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate account sync"
        )


@router.get("/{account_id}/balance", response_model=AccountBalance)
async def get_account_balance(
    account_id: UUID,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
) -> AccountBalance:
    """
    Get current account balance information.
    
    - Returns current and available balances
    - Includes credit limit for credit accounts
    - Shows when balance was last updated
    """
    try:
        # Get account
        account = db.query(Account).filter(
            and_(
                Account.id == account_id,
                Account.user_id == current_user.id
            )
        ).first()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        return AccountBalance(
            account_id=account.id,
            current_balance=account.current_balance_cents / 100 if account.current_balance_cents else 0.0,
            available_balance=account.available_balance_cents / 100 if account.available_balance_cents else None,
            limit=account.limit_cents / 100 if account.limit_cents else None,
            currency=account.iso_currency_code,
            as_of=account.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get balance for account {account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve account balance"
        )


# Background task for syncing account data
async def sync_account_data(
    plaid_item_id: str,
    access_token: str,
    user_id: str
):
    """
    Background task to sync account balances and recent transactions.
    """
    try:
        logger.info(f"Syncing account data for item {plaid_item_id}")
        
        # Get accounts from Plaid
        accounts_data = await plaid_service.get_accounts(access_token)
        
        from ..database import SessionLocal
        db = SessionLocal()
        
        try:
            # Update account balances
            for account_data in accounts_data:
                account = db.query(Account).filter(
                    Account.plaid_account_id == account_data["account_id"]
                ).first()
                
                if account:
                    account.current_balance_cents = int(account_data["current_balance"] * 100)
                    if account_data.get("available_balance") is not None:
                        account.available_balance_cents = int(account_data["available_balance"] * 100)
                    if account_data.get("limit") is not None:
                        account.limit_cents = int(account_data["limit"] * 100)
            
            # Update last sync time
            plaid_item = db.query(PlaidItem).filter(
                PlaidItem.id == plaid_item_id
            ).first()
            
            if plaid_item:
                from datetime import datetime
                plaid_item.last_successful_sync = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Successfully synced account data for item {plaid_item_id}")
            
        finally:
            db.close()
        
        # Clear sync lock
        redis_client = await get_redis_client()
        if redis_client:
            await redis_client.delete(f"sync_lock:{plaid_item_id}")
            
    except Exception as e:
        logger.error(f"Failed to sync account data: {e}")
        
        # Clear sync lock on error
        redis_client = await get_redis_client()
        if redis_client:
            await redis_client.delete(f"sync_lock:{plaid_item_id}")