"""
User model
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Wallet info
    wallet_address = Column(String(42), unique=True, nullable=True)
    public_key = Column(Text, nullable=True)

    # Biometric
    biometric_enrolled = Column(Boolean, default=False)
    biometric_hash = Column(String(64), nullable=True)  # Hash of embedding stored on blockchain

    # Profile
    full_name = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(String(20), default="user")  # user, issuer, admin

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    credentials = relationship("Credential", back_populates="user", cascade="all, delete-orphan")
    biometric_enrollments = relationship("BiometricEnrollment", back_populates="user", cascade="all, delete-orphan")
    issuer = relationship("Issuer", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username} ({self.email})>"
