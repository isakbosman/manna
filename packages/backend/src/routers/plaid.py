"""
Plaid integration router for connecting and managing financial accounts.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging
import json

from ..database import get_db
from ..database.models import User, PlaidItem, Institution, Account, Transaction
from ..schemas.plaid import (
    PlaidLinkToken, PlaidPublicTokenExchange, PlaidWebhook,
    PlaidInstitution, PlaidError
)
from ..schemas.account import Account as AccountSchema, AccountList
from ..schemas.transaction import Transaction as TransactionSchema, TransactionList
from ..dependencies.auth import get_current_active_user
from ..services.plaid_service import plaid_service
from ..utils.redis import get_redis_client
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/create-link-token", response_model=PlaidLinkToken)
async def create_link_token(
    current_user: User = Depends(get_current_active_user),
    access_token: Optional[str] = None
) -> PlaidLinkToken:
    """
    Create a Plaid Link token for connecting bank accounts.
    
    - Generates a Link token for Plaid Link flow
    - Can be used for initial connection or update mode
    - Token expires after 30 minutes
    """
    try:
        # Get user name, handling None values
        user_name = current_user.full_name if hasattr(current_user, 'full_name') and current_user.full_name else \
                   current_user.username if hasattr(current_user, 'username') and current_user.username else \
                   current_user.email if hasattr(current_user, 'email') and current_user.email else \
                   "User"

        result = await plaid_service.create_link_token(
            user_id=str(current_user.id),
            user_name=user_name,
            access_token=access_token
        )
        
        return PlaidLinkToken(
            link_token=result["link_token"],
            expiration=result["expiration"],
            request_id=result.get("request_id")
        )
        
    except Exception as e:
        logger.error(f"Failed to create link token for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Plaid Link token"
        )


@router.post("/exchange-public-token", response_model=Dict[str, Any])
async def exchange_public_token(
    exchange_request: PlaidPublicTokenExchange,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Exchange a Plaid public token for an access token and store the connection.
    
    - Exchanges public token from Link for access token
    - Fetches and stores account information
    - Initiates transaction sync in background
    """
    try:
        # Exchange public token for access token
        access_token = await plaid_service.exchange_public_token(
            exchange_request.public_token
        )
        
        # Get item information
        item_info = await plaid_service.get_item(access_token)
        
        # Get institution information if available
        institution = None
        if item_info.get("institution_id"):
            try:
                inst_info = await plaid_service.get_institution(
                    item_info["institution_id"]
                )
                
                # Check if institution exists in database
                institution = db.query(Institution).filter(
                    Institution.plaid_institution_id == inst_info["institution_id"]
                ).first()
                
                if not institution:
                    # Create new institution record
                    institution = Institution(
                        plaid_institution_id=inst_info["institution_id"],
                        name=inst_info["name"],
                        url=inst_info.get("url"),
                        primary_color=inst_info.get("primary_color"),
                        logo_url=inst_info.get("logo")
                    )
                    db.add(institution)
                    db.flush()
                    
            except Exception as e:
                logger.warning(f"Failed to get institution info: {e}")
        
        # Check if item already exists (updating)
        plaid_item = db.query(PlaidItem).filter(
            and_(
                PlaidItem.plaid_item_id == item_info["item_id"],
                PlaidItem.user_id == current_user.id
            )
        ).first()
        
        if plaid_item:
            # Update existing item
            plaid_item.access_token = access_token
            plaid_item.webhook_url = item_info.get("webhook")
            plaid_item.error = None
            plaid_item.is_active = True
        else:
            # Create new Plaid item
            plaid_item = PlaidItem(
                user_id=current_user.id,
                institution_id=institution.id if institution else None,
                plaid_item_id=item_info["item_id"],
                access_token=access_token,
                webhook_url=item_info.get("webhook"),
                available_products=json.dumps(item_info.get("available_products", [])),
                billed_products=json.dumps(item_info.get("billed_products", [])),
                consent_expiration_time=item_info.get("consent_expiration_time"),
                is_active=True
            )
            db.add(plaid_item)
            db.flush()
        
        # Fetch and store accounts
        accounts_data = await plaid_service.get_accounts(access_token)
        
        account_ids = []
        for account_data in accounts_data:
            # Check if account exists
            account = db.query(Account).filter(
                and_(
                    Account.plaid_account_id == account_data["account_id"],
                    Account.plaid_item_id == plaid_item.id
                )
            ).first()
            
            if account:
                # Update existing account
                account.name = account_data["name"]
                account.official_name = account_data.get("official_name")
                account.current_balance = account_data["current_balance"]
                account.available_balance = account_data.get("available_balance")
                account.limit = account_data.get("limit")
                account.iso_currency_code = account_data["iso_currency_code"]
                account.is_active = True
            else:
                # Create new account
                account = Account(
                    user_id=current_user.id,
                    plaid_item_id=plaid_item.id,
                    plaid_account_id=account_data["account_id"],
                    name=account_data["name"],
                    official_name=account_data.get("official_name"),
                    type=account_data["type"],
                    subtype=account_data["subtype"],
                    mask=account_data.get("mask"),
                    current_balance=account_data["current_balance"],
                    available_balance=account_data.get("available_balance"),
                    limit=account_data.get("limit"),
                    iso_currency_code=account_data["iso_currency_code"],
                    is_active=True
                )
                db.add(account)
                db.flush()
            
            account_ids.append(str(account.id))
        
        # Commit all changes
        db.commit()
        
        # Initiate transaction fetch in background
        background_tasks.add_task(
            fetch_initial_transactions,
            plaid_item.id,
            access_token,
            current_user.id
        )
        
        logger.info(f"Successfully linked accounts for user {current_user.id}")
        
        return {
            "message": "Bank account successfully linked",
            "item_id": str(plaid_item.id),
            "institution": institution.name if institution else None,
            "accounts_connected": len(account_ids),
            "account_ids": account_ids
        }
        
    except Exception as e:
        logger.error(f"Failed to exchange public token: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to link bank account: {str(e)}"
        )


@router.get("/items", response_model=List[Dict[str, Any]])
async def get_linked_items(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get all linked Plaid items for the current user.
    
    - Returns list of connected bank accounts
    - Includes institution information
    - Shows connection status
    """
    items = db.query(PlaidItem).filter(
        PlaidItem.user_id == current_user.id
    ).all()
    
    result = []
    for item in items:
        institution = None
        if item.institution_id:
            inst = db.query(Institution).filter(
                Institution.id == item.institution_id
            ).first()
            if inst:
                institution = {
                    "name": inst.name,
                    "logo_url": inst.logo_url,
                    "primary_color": inst.primary_color
                }
        
        # Get account count
        account_count = db.query(Account).filter(
            Account.plaid_item_id == item.id
        ).count()
        
        result.append({
            "item_id": str(item.id),
            "institution": institution,
            "is_active": item.is_active,
            "error": item.error,
            "account_count": account_count,
            "last_synced": item.last_successful_sync,
            "created_at": item.created_at
        })
    
    return result


@router.delete("/items/{item_id}")
async def remove_linked_item(
    item_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Remove a linked Plaid item (unlink bank account).
    
    - Removes the connection to Plaid
    - Deactivates associated accounts
    - Preserves transaction history
    """
    # Get the Plaid item
    plaid_item = db.query(PlaidItem).filter(
        and_(
            PlaidItem.id == item_id,
            PlaidItem.user_id == current_user.id
        )
    ).first()
    
    if not plaid_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked item not found"
        )
    
    try:
        # Remove item from Plaid
        if plaid_item.access_token:
            await plaid_service.remove_item(plaid_item.access_token)
        
        # Deactivate the item and associated accounts
        plaid_item.is_active = False
        plaid_item.access_token = None  # Clear token for security
        
        db.query(Account).filter(
            Account.plaid_item_id == plaid_item.id
        ).update({"is_active": False})
        
        db.commit()
        
        logger.info(f"Removed Plaid item {item_id} for user {current_user.id}")
        
        return {"message": "Bank account unlinked successfully"}
        
    except Exception as e:
        logger.error(f"Failed to remove Plaid item: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlink bank account"
        )


@router.post("/transactions/sync/{item_id}")
async def sync_transactions(
    item_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Manually trigger transaction sync for a Plaid item.
    
    - Fetches latest transactions from Plaid
    - Updates local database
    - Returns sync status
    """
    # Get the Plaid item
    plaid_item = db.query(PlaidItem).filter(
        and_(
            PlaidItem.id == item_id,
            PlaidItem.user_id == current_user.id,
            PlaidItem.is_active == True
        )
    ).first()
    
    if not plaid_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active linked item not found"
        )
    
    # Check if sync is already in progress (using Redis lock)
    redis_client = await get_redis_client()
    if redis_client:
        lock_key = f"sync_lock:{item_id}"
        if await redis_client.exists(lock_key):
            return {
                "status": "in_progress",
                "message": "Transaction sync already in progress"
            }
        
        # Set lock with 5-minute expiration
        await redis_client.setex(lock_key, 300, "1")
    
    # Start sync in background
    background_tasks.add_task(
        sync_item_transactions,
        plaid_item.id,
        plaid_item.access_token,
        plaid_item.cursor,
        current_user.id
    )
    
    return {
        "status": "started",
        "message": "Transaction sync initiated",
        "item_id": str(plaid_item.id)
    }


@router.post("/webhook", include_in_schema=False)
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Handle Plaid webhooks for real-time updates.
    
    - Processes transaction updates
    - Handles item errors
    - Triggers appropriate sync actions
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        headers = dict(request.headers)
        
        # Verify webhook signature
        # if not await plaid_service.verify_webhook(body.decode(), headers):
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #         detail="Invalid webhook signature"
        #     )
        
        # Parse webhook data
        webhook_data = await request.json()
        
        webhook_type = webhook_data.get("webhook_type")
        webhook_code = webhook_data.get("webhook_code")
        item_id = webhook_data.get("item_id")
        error = webhook_data.get("error")
        
        logger.info(f"Received webhook: {webhook_type} - {webhook_code} for item {item_id}")
        
        # Handle the webhook
        result = await plaid_service.handle_webhook(
            webhook_type=webhook_type,
            webhook_code=webhook_code,
            item_id=item_id,
            error=error
        )
        
        # Find the Plaid item
        plaid_item = db.query(PlaidItem).filter(
            PlaidItem.plaid_item_id == item_id
        ).first()
        
        if not plaid_item:
            logger.warning(f"Received webhook for unknown item: {item_id}")
            return {"status": "ignored", "reason": "item_not_found"}
        
        # Take action based on webhook
        if result["action"] == "fetch_transactions":
            background_tasks.add_task(
                fetch_initial_transactions,
                plaid_item.id,
                plaid_item.access_token,
                plaid_item.user_id
            )
        elif result["action"] == "sync_transactions":
            background_tasks.add_task(
                sync_item_transactions,
                plaid_item.id,
                plaid_item.access_token,
                plaid_item.cursor,
                plaid_item.user_id
            )
        elif result["action"] == "notify_user":
            # Store error in database
            if error:
                plaid_item.error = json.dumps(error)
                db.commit()
            # TODO: Send notification to user
        elif result["action"] == "remove_item":
            plaid_item.is_active = False
            db.query(Account).filter(
                Account.plaid_item_id == plaid_item.id
            ).update({"is_active": False})
            db.commit()
        
        return {"status": "processed", "action": result["action"]}
        
    except Exception as e:
        logger.error(f"Failed to process webhook: {e}")
        return {"status": "error", "message": str(e)}


# Background task functions

async def fetch_initial_transactions(
    plaid_item_id: str,
    access_token: str,
    user_id: str
):
    """
    Background task to fetch initial transactions after linking.
    """
    try:
        logger.info(f"Fetching initial transactions for item {plaid_item_id}")
        
        # Fetch transactions for the last 2 years
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)
        
        db = next(get_db())
        
        # Get all transactions
        offset = 0
        total_added = 0
        
        while True:
            result = await plaid_service.get_transactions(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
                count=500,
                offset=offset
            )
            
            # Process transactions
            for txn_data in result["transactions"]:
                # Check if transaction exists
                existing = db.query(Transaction).filter(
                    Transaction.plaid_transaction_id == txn_data["transaction_id"]
                ).first()
                
                if not existing:
                    # Get account
                    account = db.query(Account).filter(
                        Account.plaid_account_id == txn_data["account_id"]
                    ).first()
                    
                    if account:
                        transaction = Transaction(
                            user_id=user_id,
                            account_id=account.id,
                            plaid_transaction_id=txn_data["transaction_id"],
                            amount=txn_data["amount"],
                            iso_currency_code=txn_data["iso_currency_code"],
                            category=json.dumps(txn_data.get("category", [])),
                            category_id=txn_data.get("category_id"),
                            transaction_date=txn_data["date"],
                            authorized_date=txn_data.get("authorized_date"),
                            name=txn_data["name"],
                            merchant_name=txn_data.get("merchant_name"),
                            payment_channel=txn_data["payment_channel"],
                            pending=txn_data["pending"],
                            pending_transaction_id=txn_data.get("pending_transaction_id"),
                            location_data=json.dumps(txn_data.get("location")) if txn_data.get("location") else None
                        )
                        db.add(transaction)
                        total_added += 1
            
            # Check if more transactions available
            offset += len(result["transactions"])
            if offset >= result["total_transactions"]:
                break
        
        # Update Plaid item
        plaid_item = db.query(PlaidItem).filter(
            PlaidItem.id == plaid_item_id
        ).first()
        
        if plaid_item:
            plaid_item.last_successful_sync = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Added {total_added} initial transactions for item {plaid_item_id}")
        
        # Clear sync lock
        redis_client = await get_redis_client()
        if redis_client:
            await redis_client.delete(f"sync_lock:{plaid_item_id}")
        
    except Exception as e:
        logger.error(f"Failed to fetch initial transactions: {e}")
        
        # Clear sync lock
        redis_client = await get_redis_client()
        if redis_client:
            await redis_client.delete(f"sync_lock:{plaid_item_id}")


async def sync_item_transactions(
    plaid_item_id: str,
    access_token: str,
    cursor: Optional[str],
    user_id: str
):
    """
    Background task to sync transactions incrementally.
    """
    try:
        logger.info(f"Syncing transactions for item {plaid_item_id}")
        
        db = next(get_db())
        
        has_more = True
        total_added = 0
        total_modified = 0
        total_removed = 0
        next_cursor = cursor
        
        while has_more:
            result = await plaid_service.sync_transactions(
                access_token=access_token,
                cursor=next_cursor
            )
            
            # Process added transactions
            for txn_data in result["added"]:
                # Get account
                account = db.query(Account).filter(
                    Account.plaid_account_id == txn_data["account_id"]
                ).first()
                
                if account:
                    transaction = Transaction(
                        user_id=user_id,
                        account_id=account.id,
                        plaid_transaction_id=txn_data["transaction_id"],
                        amount=txn_data["amount"],
                        iso_currency_code=txn_data.get("iso_currency_code", "USD"),
                        category=json.dumps(txn_data.get("category", [])),
                        category_id=txn_data.get("category_id"),
                        transaction_date=txn_data["date"],
                        authorized_date=txn_data.get("authorized_date"),
                        name=txn_data["name"],
                        merchant_name=txn_data.get("merchant_name"),
                        payment_channel=txn_data["payment_channel"],
                        pending=txn_data["pending"],
                        pending_transaction_id=txn_data.get("pending_transaction_id"),
                        location_data=json.dumps(txn_data.get("location")) if txn_data.get("location") else None
                    )
                    db.add(transaction)
                    total_added += 1
            
            # Process modified transactions
            for txn_data in result["modified"]:
                transaction = db.query(Transaction).filter(
                    Transaction.plaid_transaction_id == txn_data["transaction_id"]
                ).first()
                
                if transaction:
                    transaction.amount = txn_data["amount"]
                    transaction.category = json.dumps(txn_data.get("category", []))
                    transaction.category_id = txn_data.get("category_id")
                    transaction.name = txn_data["name"]
                    transaction.merchant_name = txn_data.get("merchant_name")
                    transaction.pending = txn_data["pending"]
                    total_modified += 1
            
            # Process removed transactions
            for removed_txn in result["removed"]:
                transaction = db.query(Transaction).filter(
                    Transaction.plaid_transaction_id == removed_txn["transaction_id"]
                ).first()
                
                if transaction:
                    db.delete(transaction)
                    total_removed += 1
            
            next_cursor = result["next_cursor"]
            has_more = result["has_more"]
        
        # Update Plaid item with new cursor
        plaid_item = db.query(PlaidItem).filter(
            PlaidItem.id == plaid_item_id
        ).first()
        
        if plaid_item:
            plaid_item.cursor = next_cursor
            plaid_item.last_successful_sync = datetime.utcnow()
        
        db.commit()
        
        logger.info(
            f"Sync complete for item {plaid_item_id}: "
            f"Added: {total_added}, Modified: {total_modified}, Removed: {total_removed}"
        )
        
        # Clear sync lock
        redis_client = await get_redis_client()
        if redis_client:
            await redis_client.delete(f"sync_lock:{plaid_item_id}")
        
    except Exception as e:
        logger.error(f"Failed to sync transactions: {e}")
        
        # Clear sync lock
        redis_client = await get_redis_client()
        if redis_client:
            await redis_client.delete(f"sync_lock:{plaid_item_id}")