"""
User schemas
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserResponse(UserBase):
    id: str
    wallet_address: Optional[str]
    biometric_enrolled: bool
    is_active: bool
    is_verified: bool
    role: str
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class BiometricEnrollRequest(BaseModel):
    biometric_data: str  # Base64 encoded face image
    biometric_type: str = "face"


class BiometricEnrollResponse(BaseModel):
    success: bool
    message: str
    embedding_hash: Optional[str] = None
    blockchain_tx_hash: Optional[str] = None


class WalletResponse(BaseModel):
    wallet_address: str
    public_key: Optional[str]
    user_id: str


class UserCredentialListItem(BaseModel):
    id: str
    credential_type: str
    credential_name: str
    issuer_name: str
    issue_date: datetime
    expiry_date: Optional[datetime]
    is_active: bool
    ipfs_cid: str

    class Config:
        from_attributes = True
