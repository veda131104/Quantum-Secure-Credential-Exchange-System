"""
Audit Log model
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Event info
    event_type = Column(String(50), nullable=False, index=True)  # verification, issuance, share, revoke, etc.
    credential_id = Column(String(36), ForeignKey("credentials.id"), nullable=False, index=True)

    # Actor info
    actor_id = Column(String(36), nullable=True)  # user_id if authenticated
    actor_type = Column(String(50), nullable=True)  # user, issuer, verifier, system
    actor_ip = Column(String(45), nullable=True)

    # Verification specific
    verifier_info = Column(JSON, nullable=True)  # Verifier details (if applicable)
    share_token = Column(String(255), nullable=True)

    # Result
    success = Column(String(20), nullable=False)  # success, failure, partial
    result_data = Column(JSON, nullable=True)  # Additional result information

    # Details
    description = Column(Text, nullable=True)
    event_metadata = Column(JSON, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    credential = relationship("Credential", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.event_type} for {self.credential_id}>"
