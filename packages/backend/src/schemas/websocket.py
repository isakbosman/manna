"""
WebSocket Message Schemas
"""

from enum import Enum
from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class WebSocketMessageType(str, Enum):
    """WebSocket message types"""
    CONNECTION = "connection"
    DISCONNECTION = "disconnection"
    PING = "ping"
    PONG = "pong"
    SUBSCRIPTION = "subscription"
    TRANSACTION_UPDATE = "transaction_update"
    ACCOUNT_UPDATE = "account_update"
    BALANCE_UPDATE = "balance_update"
    NOTIFICATION = "notification"
    SYSTEM = "system"
    ERROR = "error"
    ML_INSIGHT = "ml_insight"
    SYNC_STATUS = "sync_status"


class WebSocketMessage(BaseModel):
    """Base WebSocket message schema"""
    type: WebSocketMessageType
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConnectionMessage(BaseModel):
    """Connection status message"""
    status: str
    user_id: str
    timestamp: datetime


class TransactionUpdate(BaseModel):
    """Transaction update message"""
    action: str  # created, updated, deleted, categorized
    transaction_id: str
    transaction: Dict[str, Any]
    timestamp: datetime


class AccountUpdate(BaseModel):
    """Account update message"""
    action: str  # created, updated, deleted, synced
    account_id: str
    account: Dict[str, Any]
    timestamp: datetime


class BalanceUpdate(BaseModel):
    """Balance update message"""
    account_id: str
    current_balance: float
    available_balance: float
    currency: str
    timestamp: datetime


class NotificationMessage(BaseModel):
    """Notification message"""
    title: str
    message: str
    notification_type: str = "info"  # info, success, warning, error
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime


class SystemMessage(BaseModel):
    """System-wide message"""
    message: str
    severity: str = "info"  # info, warning, critical
    timestamp: datetime


class MLInsight(BaseModel):
    """Machine learning insight message"""
    insight_type: str  # anomaly, prediction, recommendation
    title: str
    description: str
    data: Dict[str, Any]
    confidence: float
    timestamp: datetime


class SyncStatus(BaseModel):
    """Sync status update"""
    account_id: str
    status: str  # started, in_progress, completed, failed
    progress: Optional[int] = None  # percentage
    transactions_added: Optional[int] = None
    transactions_modified: Optional[int] = None
    transactions_removed: Optional[int] = None
    error: Optional[str] = None
    timestamp: datetime