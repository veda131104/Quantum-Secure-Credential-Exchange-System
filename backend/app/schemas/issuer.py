"""
Issuer schemas
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime


class IssuerRegisterRequest(BaseModel):
    organization_name: str
    organization_type: Optional[str] = None
    registration_number: Optional[str] = None
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    address: Optional[str] = None


class IssuerResponse(BaseModel):
    id: str
    user_id: str
    organization_name: str
    organization_type: Optional[str]
    contact_email: str
    blockchain_address: Optional[str]
    pqc_public_key: str
    is_approved: bool
    is_active: bool
    total_credentials_issued: int
    created_at: datetime

    class Config:
        from_attributes = True


class IssuerRegisterResponse(BaseModel):
    """Response for issuer registration - includes temp password"""
    id: str
    user_id: str
    organization_name: str
    organization_type: Optional[str]
    contact_email: str
    blockchain_address: Optional[str]
    pqc_public_key: str
    is_approved: bool
    is_active: bool
    total_credentials_issued: int
    created_at: datetime
    temp_password: str  # Only included during registration

    class Config:
        from_attributes = True


class CredentialIssueRequest(BaseModel):
    user_email: str  # Email of the user to issue credential to
    credential_type: str  # degree, license, certificate, etc.
    credential_name: str
    credential_number: Optional[str] = None
    document_base64: str  # Base64 encoded PDF
    credential_metadata: Optional[Dict[str, Any]] = None
    issue_date: datetime
    expiry_date: Optional[datetime] = None


class CredentialIssueResponse(BaseModel):
    success: bool
    message: str
    credential_id: Optional[str] = None
    blockchain_tx_hash: Optional[str] = None
    ipfs_cid: Optional[str] = None


class IssuerStatsResponse(BaseModel):
    total_credentials_issued: int
    active_credentials: int
    revoked_credentials: int
    recent_issuances: int  # Last 30 days
