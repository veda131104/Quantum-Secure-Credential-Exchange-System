"""Database models"""

from app.models.base import Base

# Import all models here so they are registered with SQLAlchemy
from app.models.user import User
from app.models.issuer import Issuer
from app.models.credential import Credential
from app.models.audit_log import AuditLog
from app.models.biometric_enrollment import BiometricEnrollment

__all__ = ["Base", "User", "Issuer", "Credential", "AuditLog", "BiometricEnrollment"]
