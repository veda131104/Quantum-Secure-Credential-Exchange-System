"""
Verification schemas
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class VerificationResponse(BaseModel):
    success: bool
    verified: bool
    credential_type: Optional[str] = None
    credential_name: Optional[str] = None
    issuer_name: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    is_expired: Optional[bool] = None
    signature_valid: Optional[bool] = None
    blockchain_verified: Optional[bool] = None
    message: str


class AttributeVerificationRequest(BaseModel):
    attribute_query: str  # e.g., "age > 18", "degree_type == 'Masters'"


class AttributeVerificationResponse(BaseModel):
    success: bool
    attribute_verified: bool
    query: str
    message: str


class VerificationDetailsResponse(BaseModel):
    credential_type: str
    issuer_name: str
    issue_date: datetime
    expires_at: datetime  # Share link expiry
    is_expired: bool
    verifier_info: Optional[Dict[str, Any]]


class VerificationLogRequest(BaseModel):
    credential_id: str
    event_type: str
    actor_type: Optional[str] = None
    verifier_info: Optional[Dict[str, Any]] = None
    success: str  # success, failure, partial
    result_data: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
