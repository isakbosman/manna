"""
Authentication router for user registration, login, and token management.
"""

from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import or_
import logging

from ..database import get_db
from ..database.models import User
from ..schemas.user import (
    UserCreate, User as UserSchema, Token, UserLogin,
    PasswordResetRequest, PasswordResetConfirm, EmailVerification
)
from ..utils.security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token, generate_password_reset_token,
    generate_email_verification_token, validate_password_strength
)
from ..utils.redis import get_redis_client
from ..config import settings
from ..dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


async def send_verification_email(email: str, token: str):
    """
    Send email verification link to user.
    This is a placeholder - implement with actual email service.
    """
    verification_link = f"{settings.frontend_url}/verify-email?token={token}"
    logger.info(f"Verification email would be sent to {email} with link: {verification_link}")
    # TODO: Implement actual email sending with SendGrid/AWS SES


async def send_password_reset_email(email: str, token: str):
    """
    Send password reset link to user.
    This is a placeholder - implement with actual email service.
    """
    reset_link = f"{settings.frontend_url}/reset-password?token={token}"
    logger.info(f"Password reset email would be sent to {email} with link: {reset_link}")
    # TODO: Implement actual email sending


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> UserSchema:
    """
    Register a new user account.
    
    - Validates email and username uniqueness
    - Hashes password securely
    - Sends verification email
    - Returns created user
    """
    # Check if user already exists
    existing_user = db.query(User).filter(
        or_(User.email == user_create.email, User.username == user_create.username)
    ).first()
    
    if existing_user:
        if existing_user.email == user_create.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(user_create.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Create new user
    hashed_password = hash_password(user_create.password)
    db_user = User(
        email=user_create.email,
        username=user_create.username,
        full_name=user_create.full_name,
        hashed_password=hashed_password,
        is_active=True,
        email_verified=False,
        role="user"
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Generate and store email verification token
    verification_token = generate_email_verification_token()
    redis_client = await get_redis_client()
    
    if redis_client:
        # Store token in Redis with 24-hour expiration
        await redis_client.setex(
            f"email_verify:{verification_token}",
            86400,  # 24 hours
            str(db_user.id)
        )
    
    # Send verification email in background
    background_tasks.add_task(send_verification_email, db_user.email, verification_token)
    
    logger.info(f"New user registered: {db_user.username} ({db_user.email})")
    
    return db_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Token:
    """
    User login endpoint.
    
    - Accepts username or email
    - Validates credentials
    - Returns access and refresh tokens
    """
    # Find user by username or email
    user = db.query(User).filter(
        or_(User.username == form_data.username, User.email == form_data.username)
    ).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.jwt_expiration_minutes)
    refresh_token_expires = timedelta(days=settings.jwt_refresh_expiration_days)
    
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "username": user.username,
        "role": user.role
    }
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data=token_data,
        expires_delta=refresh_token_expires
    )
    
    # Store refresh token in Redis for session management
    redis_client = await get_redis_client()
    if redis_client:
        await redis_client.setex(
            f"refresh_token:{user.id}:{refresh_token[-10:]}",
            settings.jwt_refresh_expiration_days * 86400,
            refresh_token
        )
    
    logger.info(f"User logged in: {user.username}")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_expiration_minutes * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Token:
    """
    Refresh access token using refresh token.
    
    - Validates refresh token
    - Checks if token is still valid in Redis
    - Issues new access token
    """
    try:
        payload = decode_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        
        # Verify token exists in Redis (not revoked)
        redis_client = await get_redis_client()
        if redis_client:
            stored_token = await redis_client.get(f"refresh_token:{user_id}:{refresh_token[-10:]}")
            if not stored_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.jwt_expiration_minutes)
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": user.role
        }
        
        new_access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        
        logger.info(f"Token refreshed for user: {user.username}")
        
        return Token(
            access_token=new_access_token,
            refresh_token=refresh_token,  # Return same refresh token
            token_type="bearer",
            expires_in=settings.jwt_expiration_minutes * 60
        )
        
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


@router.post("/logout", response_model=Dict[str, str])
async def logout(
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    User logout endpoint.
    
    - Revokes refresh tokens
    - Clears session data from Redis
    """
    redis_client = await get_redis_client()
    if redis_client:
        # Remove all refresh tokens for this user
        pattern = f"refresh_token:{current_user.id}:*"
        cursor = 0
        while True:
            cursor, keys = await redis_client.scan(cursor, match=pattern)
            if keys:
                await redis_client.delete(*keys)
            if cursor == 0:
                break
    
    logger.info(f"User logged out: {current_user.username}")
    
    return {"message": "Successfully logged out"}


@router.post("/password-reset-request", response_model=Dict[str, str])
async def request_password_reset(
    request_data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Request password reset token.
    
    - Validates email exists
    - Generates reset token
    - Sends reset email
    """
    user = db.query(User).filter(User.email == request_data.email).first()
    
    # Always return success to prevent email enumeration
    if user:
        # Generate reset token
        reset_token = generate_password_reset_token()
        
        # Store token in Redis with 1-hour expiration
        redis_client = await get_redis_client()
        if redis_client:
            await redis_client.setex(
                f"password_reset:{reset_token}",
                3600,  # 1 hour
                str(user.id)
            )
        
        # Send reset email in background
        background_tasks.add_task(send_password_reset_email, user.email, reset_token)
        
        logger.info(f"Password reset requested for: {user.email}")
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset-confirm", response_model=Dict[str, str])
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Reset password with token.
    
    - Validates reset token
    - Updates user password
    - Invalidates all existing sessions
    """
    # Get user ID from Redis token
    redis_client = await get_redis_client()
    if not redis_client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cache service unavailable"
        )
    
    user_id = await redis_client.get(f"password_reset:{reset_data.token}")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id.decode()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate new password
    is_valid, error_msg = validate_password_strength(reset_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Update password
    user.hashed_password = hash_password(reset_data.new_password)
    db.commit()
    
    # Delete reset token
    await redis_client.delete(f"password_reset:{reset_data.token}")
    
    # Invalidate all refresh tokens for this user
    pattern = f"refresh_token:{user.id}:*"
    cursor = 0
    while True:
        cursor, keys = await redis_client.scan(cursor, match=pattern)
        if keys:
            await redis_client.delete(*keys)
        if cursor == 0:
            break
    
    logger.info(f"Password reset completed for: {user.email}")
    
    return {"message": "Password has been reset successfully"}


@router.post("/verify-email", response_model=Dict[str, str])
async def verify_email(
    verification_data: EmailVerification,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Verify user email address.
    
    - Validates verification token
    - Updates user email_verified status
    """
    # Get user ID from Redis token
    redis_client = await get_redis_client()
    if not redis_client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cache service unavailable"
        )
    
    user_id = await redis_client.get(f"email_verify:{verification_data.token}")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id.decode()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update email verified status
    user.email_verified = True
    db.commit()
    
    # Delete verification token
    await redis_client.delete(f"email_verify:{verification_data.token}")
    
    logger.info(f"Email verified for: {user.email}")
    
    return {"message": "Email has been verified successfully"}


@router.post("/resend-verification", response_model=Dict[str, str])
async def resend_verification_email(
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> Dict[str, str]:
    """
    Resend email verification link.
    
    - Generates new verification token
    - Sends verification email
    """
    if current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Generate new verification token
    verification_token = generate_email_verification_token()
    
    # Store token in Redis with 24-hour expiration
    redis_client = await get_redis_client()
    if redis_client:
        await redis_client.setex(
            f"email_verify:{verification_token}",
            86400,  # 24 hours
            str(current_user.id)
        )
    
    # Send verification email in background
    background_tasks.add_task(send_verification_email, current_user.email, verification_token)
    
    logger.info(f"Verification email resent to: {current_user.email}")
    
    return {"message": "Verification email has been sent"}