"""Authentication routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.base import get_db
from app.models import User
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    BiometricLogin,
    TokenResponse,
    TokenRefresh,
    LogoutRequest,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    decode_token,
    get_current_user,
)
from app.core.config import settings
from app.services.biometric import face_recognition_service
from app.services.auth import redis_service
from app.services.blockchain import blockchain_service

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = (
            db.query(User)
            .filter(
                (User.email == user_data.email) | (User.username == user_data.username)
            )
            .first()
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists",
            )

        # Create blockchain account for user
        blockchain_account = blockchain_service.create_account()

        # Hash password
        hashed_pwd = hash_password(user_data.password)

        # Create user
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_pwd,
            full_name=user_data.full_name,
            phone=user_data.phone,
            wallet_address=blockchain_account["address"],
            role="user",
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Store private key securely (in production, use HSM or encrypted storage)
        # For now, we'll include it in the response (NOT RECOMMENDED FOR PRODUCTION)

        # Generate tokens
        access_token = create_access_token(
            data={"sub": new_user.id, "role": new_user.role}
        )
        refresh_token = create_refresh_token(
            data={"sub": new_user.id, "role": new_user.role}
        )

        # Store refresh token in Redis
        redis_service.store_refresh_token(
            new_user.id, refresh_token, settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login with username and password"""
    try:
        # Find user
        user = db.query(User).filter(User.username == credentials.username).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        # Verify password
        if not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated",
            )

        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()

        # Generate tokens
        access_token = create_access_token(data={"sub": user.id, "role": user.role})
        refresh_token = create_refresh_token(data={"sub": user.id, "role": user.role})

        # Store refresh token in Redis
        redis_service.store_refresh_token(
            user.id, refresh_token, settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}",
        )


@router.post("/login/biometric", response_model=TokenResponse)
async def login_biometric(
    biometric_data: BiometricLogin, db: Session = Depends(get_db)
):
    """Login with biometric authentication (face recognition)"""
    try:
        # Find user
        user = (
            db.query(User).filter(User.username == biometric_data.username).first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username",
            )

        # Check if user has biometric enrolled
        if not user.biometric_enrolled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Biometric not enrolled for this user",
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated",
            )

        # Verify face
        verification_result = face_recognition_service.verify_face_from_base64(
            biometric_data.biometric_data, user.id
        )

        if not verification_result.get("verified"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Biometric verification failed",
            )

        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()

        # Generate tokens
        access_token = create_access_token(data={"sub": user.id, "role": user.role})
        refresh_token = create_refresh_token(data={"sub": user.id, "role": user.role})

        # Store refresh token in Redis
        redis_service.store_refresh_token(
            user.id, refresh_token, settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Biometric login failed: {str(e)}",
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    try:
        # Decode refresh token
        payload = decode_token(token_data.refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        # Verify refresh token exists in Redis
        stored_token = redis_service.get_refresh_token(user_id)
        if not stored_token or stored_token != token_data.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Generate new access token
        access_token = create_access_token(data={"sub": user.id, "role": user.role})

        # Optionally generate new refresh token
        new_refresh_token = create_refresh_token(
            data={"sub": user.id, "role": user.role}
        )

        # Store new refresh token
        redis_service.store_refresh_token(
            user.id, new_refresh_token, settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}",
        )


@router.post("/logout")
async def logout(
    logout_data: LogoutRequest, current_user: dict = Depends(get_current_user)
):
    """Logout user (invalidate tokens)"""
    try:
        user_id = current_user.get("sub")

        # Add access token to blacklist
        redis_service.blacklist_token(
            logout_data.token, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

        # Delete refresh token
        redis_service.delete_refresh_token(user_id)

        # Delete user session if exists
        redis_service.delete_user_session(user_id)

        return {"message": "Logout successful"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}",
        )
