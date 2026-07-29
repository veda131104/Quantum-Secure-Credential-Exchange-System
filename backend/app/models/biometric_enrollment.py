"""
Biometric Enrollment model
"""

from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.base import Base


class BiometricEnrollment(Base):
    __tablename__ = "biometric_enrollments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Biometric info
    biometric_type = Column(String(50), default="face")  # face, fingerprint, iris, etc.
    embedding_hash = Column(String(64), nullable=False)  # SHA-256 of embedding

    # Blockchain
    blockchain_tx_hash = Column(String(66), nullable=True)  # TX where embedding hash was stored
    blockchain_stored = Column(Boolean, default=False)

    # Model info
    model_name = Column(String(100), nullable=True)  # Facenet, VGGFace, etc.
    model_version = Column(String(50), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=True)  # Primary enrollment for this biometric type

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="biometric_enrollments")

    def __repr__(self):
        return f"<BiometricEnrollment {self.biometric_type} for user {self.user_id}>"
