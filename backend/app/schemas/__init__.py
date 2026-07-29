"""
Pydantic schemas for request/response validation
"""

from app.schemas.auth import (
    UserRegister,
    UserLogin,
    BiometricLogin,
    TokenResponse,
    TokenRefresh,
    LogoutRequest,
)
from app.schemas.user import (
    UserResponse,
    UserUpdate,
    BiometricEnrollRequest,
    BiometricEnrollResponse,
    WalletResponse,
    UserCredentialListItem,
)
from app.schemas.issuer import (
    IssuerRegisterRequest,
    IssuerResponse,
    CredentialIssueRequest,
    CredentialIssueResponse,
    IssuerStatsResponse,
)
from app.schemas.credential import (
    CredentialResponse,
    ShareLinkCreateRequest,
    ShareLinkCreateResponse,
    ShareLinkListItem,
    ShareLinkRevokeResponse,
)
from app.schemas.verification import (
    VerificationResponse,
    AttributeVerificationRequest,
    AttributeVerificationResponse,
    VerificationDetailsResponse,
    VerificationLogRequest,
)

__all__ = [
    "UserRegister",
    "UserLogin",
    "BiometricLogin",
    "TokenResponse",
    "TokenRefresh",
    "LogoutRequest",
    "UserResponse",
    "UserUpdate",
    "BiometricEnrollRequest",
    "BiometricEnrollResponse",
    "WalletResponse",
    "UserCredentialListItem",
    "IssuerRegisterRequest",
    "IssuerResponse",
    "CredentialIssueRequest",
    "CredentialIssueResponse",
    "IssuerStatsResponse",
    "CredentialResponse",
    "ShareLinkCreateRequest",
    "ShareLinkCreateResponse",
    "ShareLinkListItem",
    "ShareLinkRevokeResponse",
    "VerificationResponse",
    "AttributeVerificationRequest",
    "AttributeVerificationResponse",
    "VerificationDetailsResponse",
    "VerificationLogRequest",
]
