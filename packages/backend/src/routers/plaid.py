"""
Plaid integration router for connecting and managing financial accounts.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from decimal import Decimal
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging
import json
import asyncio

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
                    # Convert Plaid objects to strings for JSON serialization
                    institution = Institution(
                        plaid_institution_id=inst_info["institution_id"],
                        name=inst_info["name"],
                        url=inst_info.get("url"),
                        primary_color=inst_info.get("primary_color"),
                        logo_url=inst_info.get("logo"),
                        is_active=True,
                        country_codes=[str(code) for code in inst_info.get("country_codes", [])],
                        products=[str(product) for product in inst_info.get("products", [])],
                        routing_numbers=inst_info.get("routing_numbers", []),
                        oauth_required=inst_info.get("oauth", False),
                        institution_metadata={}
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
                account.current_balance = Decimal(str(account_data["current_balance"]))
                account.available_balance = Decimal(str(account_data["available_balance"])) if account_data.get("available_balance") is not None else None
                account.credit_limit = Decimal(str(account_data["limit"])) if account_data.get("limit") is not None else None
                account.iso_currency_code = account_data["iso_currency_code"]
                account.is_active = True
            else:
                # Create new account
                account = Account(
                    user_id=current_user.id,
                    plaid_item_id=plaid_item.id,
                    institution_id=institution.id if institution else None,
                    plaid_account_id=account_data["account_id"],
                    name=account_data["name"],
                    official_name=account_data.get("official_name"),
                    type=account_data["type"],
                    subtype=account_data["subtype"],
                    mask=account_data.get("mask"),
                    current_balance=Decimal(str(account_data["current_balance"])),
                    available_balance=Decimal(str(account_data["available_balance"])) if account_data.get("available_balance") is not None else None,
                    credit_limit=Decimal(str(account_data["limit"])) if account_data.get("limit") is not None else None,
                    iso_currency_code=account_data["iso_currency_code"],
                    is_active=True
                )
                db.add(account)
                db.flush()
            
            account_ids.append(str(account.id))
        
        # Commit all changes
        db.commit()

        # Refresh accounts to get full data
        db.refresh(plaid_item)

        # Get all accounts for this plaid_item to return to frontend
        linked_accounts = db.query(Account).filter(
            Account.plaid_item_id == plaid_item.id
        ).all()

        accounts_response = []
        for acc in linked_accounts:
            accounts_response.append({
                "id": str(acc.id),
                "name": acc.name,
                "type": acc.type,
                "subtype": acc.subtype,
                "mask": acc.mask,
                "current_balance": acc.current_balance_cents / 100 if acc.current_balance_cents else 0,
                "available_balance": acc.available_balance_cents / 100 if acc.available_balance_cents else None,
                "iso_currency_code": acc.iso_currency_code
            })

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
            "institution_name": institution.name if institution else "Unknown",
            "accounts_connected": len(accounts_response),
            "accounts": accounts_response,
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


from pydantic import BaseModel

class SyncTransactionsRequest(BaseModel):
    account_ids: Optional[List[str]] = None

@router.post("/sync-transactions")
async def sync_all_transactions(
    request: SyncTransactionsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Sync transactions for user's accounts with comprehensive error handling.
    If account_ids provided, sync only those accounts.
    Otherwise sync all active accounts.
    """
    logger.info(f"Starting transaction sync for user: {current_user.id}")

    try:
        # Get plaid items to sync
        query = db.query(PlaidItem).filter(
            PlaidItem.user_id == current_user.id,
            PlaidItem.is_active == True
        )

        if request.account_ids:
            # Get plaid items for specific accounts
            query = query.join(Account).filter(Account.id.in_(request.account_ids))

        plaid_items = query.all()
        logger.info(f"Found {len(plaid_items)} plaid items for user {current_user.id}")

        if not plaid_items:
            logger.warning(f"No active Plaid items found for user {current_user.id}")
            return {
                "synced_count": 0,
                "new_transactions": 0,
                "message": "No active accounts to sync"
            }

        total_synced = 0
        total_new = 0
        total_modified = 0
        total_removed = 0
        sync_errors = []

        for plaid_item in plaid_items:
            try:
                # Use the enhanced sync function
                result = await sync_plaid_item_transactions(
                    plaid_item=plaid_item,
                    db=db,
                    user_id=current_user.id
                )

                total_synced += result["synced_count"]
                total_new += result["new_transactions"]
                total_modified += result["modified_transactions"]
                total_removed += result["removed_transactions"]

                logger.info(f"Successfully synced item {plaid_item.id}: {result['synced_count']} transactions")

            except Exception as e:
                error_msg = f"Failed to sync item {plaid_item.id}: {str(e)}"
                logger.error(error_msg)
                sync_errors.append(error_msg)

                # Update error state in database
                try:
                    plaid_item.last_sync_attempt = datetime.utcnow()
                    plaid_item.error_code = 'SYNC_ERROR'
                    plaid_item.error_message = str(e)[:1000]  # Limit error message length

                    # Check for reauth errors
                    if any(err in str(e) for err in ['ITEM_LOGIN_REQUIRED', 'ACCESS_NOT_GRANTED']):
                        plaid_item.requires_reauth = True
                        plaid_item.status = 'error'

                    db.flush()
                except Exception as db_error:
                    logger.error(f"Failed to update error state for item {plaid_item.id}: {db_error}")

        # Commit all changes
        try:
            db.commit()
        except Exception as commit_error:
            logger.error(f"Failed to commit transaction sync: {commit_error}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save sync results: {str(commit_error)}"
            )

        # Prepare response
        response = {
            "synced_count": total_synced,
            "new_transactions": total_new,
            "modified_transactions": total_modified,
            "removed_transactions": total_removed,
            "message": f"Successfully synced {total_synced} transactions",
            "items_processed": len(plaid_items),
            "items_with_errors": len(sync_errors)
        }

        if sync_errors:
            response["errors"] = sync_errors
            response["message"] += f" (with {len(sync_errors)} errors)"

        return response

    except Exception as e:
        logger.error(f"Failed to sync transactions: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync transactions: {str(e)}"
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
        if result["action"] == "sync_transactions":
            # For all sync-related webhooks, use the sync endpoint
            background_tasks.add_task(
                sync_item_transactions,
                plaid_item.id,
                plaid_item.access_token,
                plaid_item.cursor,
                plaid_item.user_id
            )
            logger.info(f"Scheduled sync for item {plaid_item.id} via webhook: {webhook_code}")
        elif result["action"] == "fetch_transactions":
            # Legacy support - use sync instead
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
    Uses the sync method to properly handle cursor and transaction processing.
    """
    try:
        logger.info(f"Fetching initial transactions for item {plaid_item_id}")

        db = next(get_db())

        # Get the plaid item
        plaid_item = db.query(PlaidItem).filter(
            PlaidItem.id == plaid_item_id
        ).first()

        if not plaid_item:
            logger.error(f"PlaidItem {plaid_item_id} not found")
            return

        # Use the sync function which properly handles transactions and cursor
        result = await sync_plaid_item_transactions(
            plaid_item=plaid_item,
            db=db,
            user_id=user_id
        )

        db.commit()

        logger.info(f"Initial sync complete for item {plaid_item_id}: "
                   f"Added {result['new_transactions']} transactions")
        
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


async def sync_plaid_item_transactions(
    plaid_item: PlaidItem,
    db: Session,
    user_id: str
) -> Dict[str, int]:
    """
    Enhanced sync function for a single Plaid item with comprehensive error handling.
    Handles both initial sync (cursor=None/empty) and incremental updates.

    Returns:
        Dictionary with sync statistics
    """
    # Normalize cursor - ensure empty string is treated as None
    current_cursor = plaid_item.cursor if plaid_item.cursor and plaid_item.cursor.strip() else None
    is_initial_sync = current_cursor is None

    logger.info(f"Starting {'initial' if is_initial_sync else 'incremental'} sync for item {plaid_item.id}")
    logger.info(f"Cursor: {repr(current_cursor)}")

    # Mark sync attempt
    plaid_item.last_sync_attempt = datetime.utcnow()
    db.flush()

    # Sync statistics
    total_added = 0
    total_modified = 0
    total_removed = 0
    page_count = 0

    # Store original cursor for pagination error recovery
    original_cursor = current_cursor

    try:
        has_more = True

        while has_more:
            page_count += 1

            try:
                logger.info(f"Fetching sync page {page_count} for item {plaid_item.id}")
                sync_result = await plaid_service.sync_transactions(
                    access_token=plaid_item.access_token,
                    cursor=current_cursor,
                    count=500  # Use max page size for efficiency
                )

                logger.info(f"Page {page_count}: added={len(sync_result.get('added', []))}, "
                          f"modified={len(sync_result.get('modified', []))}, "
                          f"removed={len(sync_result.get('removed', []))}, "
                          f"has_more={sync_result.get('has_more', False)}")

            except Exception as sync_error:
                # Handle pagination mutation error by restarting from original cursor
                if 'TRANSACTIONS_SYNC_MUTATION_DURING_PAGINATION' in str(sync_error):
                    logger.warning(f"Pagination mutation detected, restarting from original cursor")
                    current_cursor = original_cursor
                    page_count = 0
                    total_added = 0
                    total_modified = 0
                    total_removed = 0
                    continue
                else:
                    raise

            # Process added transactions
            for txn_data in sync_result.get("added", []):
                if await process_added_transaction(txn_data, plaid_item, db):
                    total_added += 1

            # Process modified transactions
            for txn_data in sync_result.get("modified", []):
                if await process_modified_transaction(txn_data, db):
                    total_modified += 1

            # Process removed transactions
            for removed_txn in sync_result.get("removed", []):
                if await process_removed_transaction(removed_txn, db):
                    total_removed += 1

            # Update cursor and check for more pages
            current_cursor = sync_result.get("next_cursor")
            has_more = sync_result.get("has_more", False)

        # Update Plaid item with final cursor and mark as successful
        plaid_item.cursor = current_cursor
        plaid_item.last_successful_sync = datetime.utcnow()
        plaid_item.error_code = None
        plaid_item.error_message = None

        # Mark as healthy if it was in error state
        if plaid_item.status == 'error':
            plaid_item.status = 'active'
            plaid_item.requires_reauth = False

        # Flush changes for this item
        db.flush()

        logger.info(
            f"{'Initial' if is_initial_sync else 'Incremental'} sync complete for item {plaid_item.id}: "
            f"Added: {total_added}, Modified: {total_modified}, Removed: {total_removed}, "
            f"Pages: {page_count}, Final cursor: {current_cursor[:20] if current_cursor else 'None'}..."
        )

        return {
            "synced_count": total_added + total_modified,
            "new_transactions": total_added,
            "modified_transactions": total_modified,
            "removed_transactions": total_removed,
            "pages_processed": page_count
        }

    except Exception as e:
        logger.error(f"Failed to sync transactions for item {plaid_item.id}: {e}")
        raise


async def process_added_transaction(
    txn_data: Dict[str, Any],
    plaid_item: PlaidItem,
    db: Session
) -> bool:
    """
    Process a newly added transaction with deduplication and error handling.

    Returns:
        True if transaction was processed successfully, False otherwise
    """
    try:
        # Check if transaction already exists (deduplication)
        existing = db.query(Transaction).filter(
            Transaction.plaid_transaction_id == txn_data["transaction_id"]
        ).first()

        if existing:
            logger.debug(f"Transaction {txn_data['transaction_id']} already exists, skipping")
            return False

        # Get account with plaid_item verification
        account = db.query(Account).filter(
            Account.plaid_account_id == txn_data["account_id"],
            Account.plaid_item_id == plaid_item.id
        ).first()

        if not account:
            logger.warning(f"Account {txn_data['account_id']} not found for item {plaid_item.id}")
            return False

        # Parse and validate date
        txn_date = parse_transaction_date(txn_data["date"])
        auth_date = parse_transaction_date(txn_data.get("authorized_date"))

        # Create transaction using the correct model structure
        # Extract category information
        categories = txn_data.get("category", [])
        primary_cat = categories[0] if categories else None
        sub_cat = categories[-1] if len(categories) > 1 else None

        transaction = Transaction(
            account_id=account.id,
            plaid_transaction_id=txn_data["transaction_id"],
            amount=Decimal(str(txn_data["amount"])),  # Use amount column directly
            iso_currency_code=txn_data.get("iso_currency_code", "USD"),
            date=txn_date,
            authorized_date=auth_date,
            name=txn_data["name"][:500],  # Ensure name fits in column
            merchant_name=txn_data.get("merchant_name", "")[:255] if txn_data.get("merchant_name") else None,
            plaid_category=categories,  # Store full category array as JSON
            plaid_category_id=txn_data.get("category_id"),
            subcategory=sub_cat[:100] if sub_cat else None,  # Store subcategory
            pending=txn_data.get("pending", False),
            pending_transaction_id=txn_data.get("pending_transaction_id"),
            payment_channel=txn_data.get("payment_channel"),
            location=txn_data.get("location"),
            account_owner=txn_data.get("account_owner")
        )

        db.add(transaction)
        return True

    except Exception as e:
        logger.error(f"Failed to process added transaction {txn_data.get('transaction_id', 'unknown')}: {e}")
        return False


async def process_modified_transaction(
    txn_data: Dict[str, Any],
    db: Session
) -> bool:
    """
    Process a modified transaction with error handling.

    Returns:
        True if transaction was processed successfully, False otherwise
    """
    try:
        transaction = db.query(Transaction).filter(
            Transaction.plaid_transaction_id == txn_data["transaction_id"]
        ).first()

        if not transaction:
            logger.warning(f"Transaction to modify not found: {txn_data['transaction_id']}")
            return False

        # Update transaction fields
        # Extract category information
        categories = txn_data.get("category", [])
        sub_cat = categories[-1] if len(categories) > 1 else None

        transaction.amount = Decimal(str(txn_data["amount"]))  # Use amount column directly
        transaction.date = parse_transaction_date(txn_data["date"])
        transaction.name = txn_data["name"][:500]
        transaction.merchant_name = txn_data.get("merchant_name", "")[:255] if txn_data.get("merchant_name") else None
        transaction.plaid_category = categories  # Store full category array as JSON
        transaction.plaid_category_id = txn_data.get("category_id")
        transaction.subcategory = sub_cat[:100] if sub_cat else None  # Store subcategory
        transaction.pending = txn_data.get("pending", False)
        transaction.location = txn_data.get("location")

        return True

    except Exception as e:
        logger.error(f"Failed to process modified transaction {txn_data.get('transaction_id', 'unknown')}: {e}")
        return False


async def process_removed_transaction(
    removed_txn: Dict[str, Any],
    db: Session
) -> bool:
    """
    Process a removed transaction with error handling.

    Returns:
        True if transaction was processed successfully, False otherwise
    """
    try:
        transaction = db.query(Transaction).filter(
            Transaction.plaid_transaction_id == removed_txn["transaction_id"]
        ).first()

        if transaction:
            db.delete(transaction)
            return True
        else:
            logger.debug(f"Transaction to remove not found: {removed_txn['transaction_id']}")
            return False

    except Exception as e:
        logger.error(f"Failed to process removed transaction {removed_txn.get('transaction_id', 'unknown')}: {e}")
        return False


def parse_transaction_date(date_value: Any) -> Optional[date]:
    """
    Parse transaction date handling both string and date objects.

    Args:
        date_value: Date value from Plaid (string, date, or None)

    Returns:
        Parsed date object or None
    """
    if not date_value:
        return None

    if isinstance(date_value, str):
        try:
            return datetime.strptime(date_value, "%Y-%m-%d").date()
        except ValueError:
            logger.warning(f"Invalid date format: {date_value}")
            return None
    elif hasattr(date_value, 'date'):
        return date_value.date()
    elif isinstance(date_value, date):
        return date_value
    else:
        logger.warning(f"Unknown date type: {type(date_value)} - {date_value}")
        return None


async def sync_item_transactions(
    plaid_item_id: str,
    access_token: str,
    cursor: Optional[str],
    user_id: str
):
    """
    Background task wrapper for sync_plaid_item_transactions.
    Maintains compatibility with existing background task calls.
    """
    try:
        db = next(get_db())

        plaid_item = db.query(PlaidItem).filter(
            PlaidItem.id == plaid_item_id
        ).first()

        if not plaid_item:
            logger.error(f"Plaid item {plaid_item_id} not found")
            return

        # Update cursor if provided (for backward compatibility)
        if cursor is not None:
            plaid_item.cursor = cursor

        result = await sync_plaid_item_transactions(
            plaid_item=plaid_item,
            db=db,
            user_id=user_id
        )

        db.commit()

        logger.info(f"Background sync complete for item {plaid_item_id}: {result}")

    except Exception as e:
        logger.error(f"Background sync failed for item {plaid_item_id}: {e}")

        # Update error state
        try:
            db = next(get_db())
            plaid_item = db.query(PlaidItem).filter(
                PlaidItem.id == plaid_item_id
            ).first()

            if plaid_item:
                plaid_item.error_code = 'SYNC_ERROR'
                plaid_item.error_message = str(e)[:1000]
                plaid_item.last_sync_attempt = datetime.utcnow()

                # Check for reauth errors
                if any(err in str(e) for err in ['ITEM_LOGIN_REQUIRED', 'ACCESS_NOT_GRANTED']):
                    plaid_item.requires_reauth = True
                    plaid_item.status = 'error'

                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update error state: {db_error}")

    finally:
        # Clear sync lock
        try:
            redis_client = await get_redis_client()
            if redis_client:
                await redis_client.delete(f"sync_lock:{plaid_item_id}")
        except Exception as redis_error:
            logger.error(f"Failed to clear sync lock: {redis_error}")