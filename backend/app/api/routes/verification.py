"""Credential verification routes"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.models.base import get_db
from app.models import AuditLog
from app.schemas.verification import (
    VerificationResponse,
    AttributeVerificationRequest,
    AttributeVerificationResponse,
    VerificationDetailsResponse,
    VerificationLogRequest,
)
from app.services.credentials import credential_service
from app.services.auth import redis_service

router = APIRouter()


@router.get("/{share_token}", response_model=VerificationResponse)
async def verify_credential(
    share_token: str, request: Request, db: Session = Depends(get_db)
):
    """Verify a credential using share token (public endpoint)"""
    try:
        # Get client IP
        client_ip = request.client.host if request.client else None

        # Use credential service to verify
        result = credential_service.verify_credential(
            db=db, share_token=share_token, actor_ip=client_ip
        )

        if not result.get("success"):
            return VerificationResponse(
                success=result["success"],
                verified=False,
                credential_type="",
                credential_name="",
                issuer_name="",
                issue_date=None,
                expiry_date=None,
                is_expired=False,
                signature_valid=False,
                blockchain_verified=False,
                message=result.get("message", "Verification failed"),
            )

        return VerificationResponse(
            success=result["success"],
            verified=result.get("verified", False),
            credential_type=result.get("credential_type", ""),
            credential_name=result.get("credential_name", ""),
            issuer_name=result.get("issuer_name", ""),
            issue_date=result.get("issue_date"),
            expiry_date=result.get("expiry_date"),
            is_expired=result.get("is_expired", False),
            signature_valid=result.get("signature_valid", False),
            blockchain_verified=result.get("blockchain_verified", False),
            message=result.get("message", ""),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}",
        )


@router.post(
    "/{share_token}/verify-attribute", response_model=AttributeVerificationResponse
)
async def verify_credential_attribute(
    share_token: str,
    attribute_data: AttributeVerificationRequest,
    db: Session = Depends(get_db),
):
    """Verify specific attribute without revealing full credential (Zero-Knowledge proof placeholder)"""
    try:
        # Get token data
        token_data = redis_service.get_share_token(share_token)

        if not token_data:
            return AttributeVerificationResponse(
                success=False,
                attribute_verified=False,
                query=attribute_data.attribute_query,
                message="Share link not found or expired",
            )

        credential_id = token_data.get("credential_id")

        # Get credential from database
        from app.models import Credential

        credential = (
            db.query(Credential).filter(Credential.id == credential_id).first()
        )

        if not credential:
            return AttributeVerificationResponse(
                success=False,
                attribute_verified=False,
                query=attribute_data.attribute_query,
                message="Credential not found",
            )

        # Parse and evaluate attribute query
        # This is a placeholder - in production, implement proper ZK proofs
        # For now, we'll do simple attribute checks
        query = attribute_data.attribute_query.lower()
        metadata = credential.credential_metadata or {}

        attribute_verified = False
        message = "Attribute verification not implemented"

        # Simple attribute checks (placeholder)
        if "active" in query and credential.is_active:
            attribute_verified = True
            message = "Credential is active"
        elif "revoked" in query and not credential.is_revoked:
            attribute_verified = True
            message = "Credential is not revoked"
        elif "valid" in query and credential.is_active and not credential.is_revoked:
            attribute_verified = True
            message = "Credential is valid"
        else:
            # Check metadata
            for key, value in metadata.items():
                if key.lower() in query:
                    attribute_verified = True
                    message = f"Attribute '{key}' verified"
                    break

        return AttributeVerificationResponse(
            success=True,
            attribute_verified=attribute_verified,
            query=attribute_data.attribute_query,
            message=message,
        )

    except Exception as e:
        return AttributeVerificationResponse(
            success=False,
            attribute_verified=False,
            query=attribute_data.attribute_query,
            message=f"Attribute verification error: {str(e)}",
        )


@router.get("/{share_token}/details", response_model=VerificationDetailsResponse)
async def get_verification_details(share_token: str, db: Session = Depends(get_db)):
    """Get details about a share link (metadata only - no credential data)"""
    try:
        # Get token data from Redis
        token_data = redis_service.get_share_token(share_token)

        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share link not found or expired",
            )

        credential_id = token_data.get("credential_id")

        # Get credential type and issuer info
        from app.models import Credential, Issuer
        from datetime import datetime

        credential = (
            db.query(Credential).filter(Credential.id == credential_id).first()
        )

        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found"
            )

        issuer = db.query(Issuer).filter(Issuer.id == credential.issuer_id).first()
        issuer_name = issuer.organization_name if issuer else "Unknown Issuer"

        # Parse expiry from token data
        expires_at = datetime.fromisoformat(token_data.get("expires_at"))
        is_expired = datetime.utcnow() > expires_at

        return VerificationDetailsResponse(
            credential_type=credential.credential_type,
            issuer_name=issuer_name,
            issue_date=credential.issue_date,
            expires_at=expires_at,
            is_expired=is_expired,
            verifier_info=token_data.get("verifier_info"),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch verification details: {str(e)}",
        )


@router.post("/log")
async def log_verification_event(
    log_data: VerificationLogRequest, db: Session = Depends(get_db)
):
    """Log a verification event for audit trail"""
    try:
        # Create audit log entry
        audit_log = AuditLog(
            event_type=log_data.event_type,
            credential_id=log_data.credential_id,
            actor_type=log_data.actor_type,
            verifier_info=log_data.verifier_info,
            success=log_data.success,
            result_data=log_data.result_data,
            description=log_data.description,
        )

        db.add(audit_log)
        db.commit()

        return {
            "message": "Verification event logged successfully",
            "log_id": audit_log.id,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log verification event: {str(e)}",
        )


@router.get("/audit/{credential_id}")
async def get_audit_logs(credential_id: str, db: Session = Depends(get_db)):
    """Get audit logs for a credential (requires authentication in production)"""
    try:
        # Get audit logs
        logs = (
            db.query(AuditLog)
            .filter(AuditLog.credential_id == credential_id)
            .order_by(AuditLog.created_at.desc())
            .limit(50)
            .all()
        )

        return {
            "credential_id": credential_id,
            "total_logs": len(logs),
            "logs": [
                {
                    "id": log.id,
                    "event_type": log.event_type,
                    "actor_type": log.actor_type,
                    "actor_ip": log.actor_ip,
                    "success": log.success,
                    "description": log.description,
                    "created_at": log.created_at,
                }
                for log in logs
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch audit logs: {str(e)}",
        )
