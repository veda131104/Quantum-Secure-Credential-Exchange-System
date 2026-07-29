"""
Credential schemas
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class CredentialResponse(BaseModel):
    id: str
    user_id: str
    issuer_id: str
    credential_type: str
    credential_name: str
    credential_number: Optional[str]
    blockchain_tx_hash: Optional[str]
    ipfs_cid: Optional[str]
    credential_hash: str
    signature_algorithm: str
    credential_metadata: Optional[Dict[str, Any]]
    issue_date: datetime
    expiry_date: Optional[datetime]
    is_active: bool
    is_revoked: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ShareLinkCreateRequest(BaseModel):
    credential_id: str
    expiry_hours: Optional[int] = 24
    verifier_info: Optional[Dict[str, Any]] = None  # Name, organization, etc.


class ShareLinkCreateResponse(BaseModel):
    success: bool
    share_url: str
    share_token: str
    expires_at: datetime


class ShareLinkListItem(BaseModel):
    share_token: str
    credential_id: str
    credential_name: str
    verifier_info: Optional[Dict[str, Any]]
    created_at: datetime
    expires_at: datetime
    is_expired: bool


class ShareLinkRevokeResponse(BaseModel):
    success: bool
    message: str
