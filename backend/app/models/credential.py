"""
Credential model
"""

from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.base import Base


class Credential(Base):
    __tablename__ = "credentials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Ownership
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    issuer_id = Column(String(36), ForeignKey("issuers.id"), nullable=False, index=True)

    # Credential info
    credential_type = Column(String(100), nullable=False)  # degree, license, certificate, etc.
    credential_name = Column(String(255), nullable=False)
    credential_number = Column(String(100), nullable=True)

    # Blockchain & IPFS
    blockchain_tx_hash = Column(String(66), unique=True, nullable=True)
    blockchain_block_number = Column(String(20), nullable=True)
    ipfs_cid = Column(String(100), nullable=True)  # Document CID
    credential_hash = Column(String(64), nullable=False)  # SHA-256 of credential data

    # PQC Signature
    pqc_signature = Column(Text, nullable=False)  # Dilithium signature
    signature_algorithm = Column(String(50), default="Dilithium2")

    # Metadata
    credential_metadata = Column(JSON, nullable=True)  # Additional credential data
    issue_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="credentials")
    issuer = relationship("Issuer", back_populates="credentials")
    audit_logs = relationship("AuditLog", back_populates="credential", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Credential {self.credential_type}: {self.credential_name}>"
