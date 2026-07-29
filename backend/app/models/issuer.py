"""
Issuer model
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.base import Base


class Issuer(Base):
    __tablename__ = "issuers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)

    # Organization info
    organization_name = Column(String(255), nullable=False)
    organization_type = Column(String(100), nullable=True)  # university, government, etc.
    registration_number = Column(String(100), nullable=True)

    # Contact
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)

    # Blockchain & PQC
    blockchain_address = Column(String(42), unique=True, nullable=True)
    pqc_public_key = Column(Text, nullable=False)  # Dilithium public key
    pqc_key_id = Column(String(64), nullable=False)  # Hash/ID of the key

    # Status
    is_approved = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    approved_by = Column(String(36), nullable=True)  # admin user_id
    approved_at = Column(DateTime, nullable=True)

    # Stats
    total_credentials_issued = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="issuer")
    credentials = relationship("Credential", back_populates="issuer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Issuer {self.organization_name}>"
