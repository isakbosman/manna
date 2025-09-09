"""
WebSocket Implementation for Real-time Updates
"""

import json
import logging
import asyncio
from typing import Dict, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User
from .schemas.websocket import (
    WebSocketMessage,
    WebSocketMessageType,
    TransactionUpdate,
    AccountUpdate,
    NotificationMessage,
)

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")


class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting
    """
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        # Message queue for offline users
        self.message_queue: Dict[str, list] = {}
        # Lock for thread safety
        self.lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, user_id: str, metadata: Optional[Dict] = None):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        
        async with self.lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            
            self.active_connections[user_id].add(websocket)
            self.connection_metadata[websocket] = {
                "user_id": user_id,
                "connected_at": datetime.utcnow(),
                "metadata": metadata or {},
            }
            
            logger.info(f"User {user_id} connected via WebSocket")
            
            # Send any queued messages
            if user_id in self.message_queue:
                for message in self.message_queue[user_id]:
                    await self.send_personal_message(message, websocket)
                del self.message_queue[user_id]
    
    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection"""
        async with self.lock:
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]
            
            logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}")
    
    async def send_user_message(self, user_id: str, message: Dict[str, Any]):
        """Send a message to all connections for a specific user"""
        message_str = json.dumps(message, default=str)
        
        async with self.lock:
            if user_id in self.active_connections:
                disconnected = []
                for connection in self.active_connections[user_id]:
                    try:
                        await connection.send_text(message_str)
                    except Exception as e:
                        logger.error(f"Error sending message to user {user_id}: {e}")
                        disconnected.append(connection)
                
                # Remove disconnected connections
                for conn in disconnected:
                    self.active_connections[user_id].discard(conn)
                    if conn in self.connection_metadata:
                        del self.connection_metadata[conn]
            else:
                # Queue message for offline user
                if user_id not in self.message_queue:
                    self.message_queue[user_id] = []
                self.message_queue[user_id].append(message_str)
                
                # Limit queue size to prevent memory issues
                if len(self.message_queue[user_id]) > 100:
                    self.message_queue[user_id] = self.message_queue[user_id][-100:]
    
    async def broadcast(self, message: Dict[str, Any], exclude_user: Optional[str] = None):
        """Broadcast a message to all connected users"""
        message_str = json.dumps(message, default=str)
        
        async with self.lock:
            disconnected = []
            for user_id, connections in self.active_connections.items():
                if exclude_user and user_id == exclude_user:
                    continue
                
                for connection in connections:
                    try:
                        await connection.send_text(message_str)
                    except Exception as e:
                        logger.error(f"Error broadcasting to user {user_id}: {e}")
                        disconnected.append((user_id, connection))
            
            # Remove disconnected connections
            for user_id, conn in disconnected:
                self.active_connections[user_id].discard(conn)
                if conn in self.connection_metadata:
                    del self.connection_metadata[conn]
    
    def get_online_users(self) -> Set[str]:
        """Get list of currently online user IDs"""
        return set(self.active_connections.keys())
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(conns) for conns in self.active_connections.values())
    
    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of connections for a specific user"""
        return len(self.active_connections.get(user_id, set()))


# Global connection manager instance
manager = ConnectionManager()


async def get_current_user_websocket(
    websocket: WebSocket,
    token: Optional[str] = None,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Authenticate WebSocket connection using JWT token
    """
    if not token:
        # Try to get token from query parameters
        token = websocket.query_params.get("token")
    
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        user_id: str = payload.get("user_id")
        if user_id is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    
    return user


async def websocket_endpoint(
    websocket: WebSocket,
    user: User = Depends(get_current_user_websocket),
):
    """
    Main WebSocket endpoint for real-time communication
    """
    if not user:
        return
    
    await manager.connect(websocket, str(user.id))
    
    try:
        # Send initial connection confirmation
        await manager.send_personal_message(
            json.dumps({
                "type": WebSocketMessageType.CONNECTION,
                "data": {
                    "status": "connected",
                    "user_id": str(user.id),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }),
            websocket,
        )
        
        # Keep connection alive and handle incoming messages
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                message_data = message.get("data", {})
                
                # Handle different message types
                if message_type == WebSocketMessageType.PING:
                    # Respond to ping with pong
                    await manager.send_personal_message(
                        json.dumps({
                            "type": WebSocketMessageType.PONG,
                            "data": {"timestamp": datetime.utcnow().isoformat()},
                        }),
                        websocket,
                    )
                
                elif message_type == WebSocketMessageType.SUBSCRIPTION:
                    # Handle subscription requests
                    subscription_type = message_data.get("subscription_type")
                    logger.info(f"User {user.id} subscribed to {subscription_type}")
                    
                    # Store subscription preferences in metadata
                    if websocket in manager.connection_metadata:
                        manager.connection_metadata[websocket]["metadata"]["subscriptions"] = \
                            manager.connection_metadata[websocket]["metadata"].get("subscriptions", [])
                        manager.connection_metadata[websocket]["metadata"]["subscriptions"].append(
                            subscription_type
                        )
                
                else:
                    # Echo unknown messages back (for debugging)
                    logger.warning(f"Unknown message type: {message_type}")
                    await manager.send_personal_message(
                        json.dumps({
                            "type": WebSocketMessageType.ERROR,
                            "data": {
                                "error": "Unknown message type",
                                "original_message": message,
                            },
                        }),
                        websocket,
                    )
            
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({
                        "type": WebSocketMessageType.ERROR,
                        "data": {"error": "Invalid JSON format"},
                    }),
                    websocket,
                )
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await manager.send_personal_message(
                    json.dumps({
                        "type": WebSocketMessageType.ERROR,
                        "data": {"error": str(e)},
                    }),
                    websocket,
                )
    
    except WebSocketDisconnect:
        await manager.disconnect(websocket, str(user.id))
    except Exception as e:
        logger.error(f"WebSocket error for user {user.id}: {e}")
        await manager.disconnect(websocket, str(user.id))


# Helper functions for sending specific types of updates

async def send_transaction_update(
    user_id: str,
    transaction_id: str,
    action: str,
    transaction_data: Dict[str, Any],
):
    """Send transaction update to user"""
    message = {
        "type": WebSocketMessageType.TRANSACTION_UPDATE,
        "data": {
            "action": action,  # "created", "updated", "deleted"
            "transaction_id": transaction_id,
            "transaction": transaction_data,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }
    await manager.send_user_message(user_id, message)


async def send_account_update(
    user_id: str,
    account_id: str,
    action: str,
    account_data: Dict[str, Any],
):
    """Send account update to user"""
    message = {
        "type": WebSocketMessageType.ACCOUNT_UPDATE,
        "data": {
            "action": action,  # "created", "updated", "deleted", "synced"
            "account_id": account_id,
            "account": account_data,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }
    await manager.send_user_message(user_id, message)


async def send_notification(
    user_id: str,
    title: str,
    message: str,
    notification_type: str = "info",
    data: Optional[Dict[str, Any]] = None,
):
    """Send notification to user"""
    notification = {
        "type": WebSocketMessageType.NOTIFICATION,
        "data": {
            "title": title,
            "message": message,
            "notification_type": notification_type,  # "info", "success", "warning", "error"
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat(),
        },
    }
    await manager.send_user_message(user_id, notification)


async def broadcast_system_message(message: str, severity: str = "info"):
    """Broadcast system message to all users"""
    system_message = {
        "type": WebSocketMessageType.SYSTEM,
        "data": {
            "message": message,
            "severity": severity,  # "info", "warning", "critical"
            "timestamp": datetime.utcnow().isoformat(),
        },
    }
    await manager.broadcast(system_message)