"""Credential management routes"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.models.base import get_db
from app.models import Credential
from app.schemas.credential import (
    ShareLinkCreateRequest,
    ShareLinkCreateResponse,
    ShareLinkListItem,
    ShareLinkRevokeResponse,
)
from app.core.security import get_current_user
from app.services.credentials import credential_service
from app.services.auth import redis_service

router = APIRouter()


@router.post("/share", response_model=ShareLinkCreateResponse)
async def create_share_link(
    share_data: ShareLinkCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a time-bound share link for a credential"""
    try:
        user_id = current_user.get("sub")

        result = credential_service.create_share_link(
            db=db,
            user_id=user_id,
            credential_id=share_data.credential_id,
            expiry_hours=share_data.expiry_hours or 24,
            verifier_info=share_data.verifier_info,
        )

        return ShareLinkCreateResponse(
            success=result["success"],
            share_url=result["share_url"],
            share_token=result["share_token"],
            expires_at=result["expires_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create share link: {str(e)}",
        )


@router.get("/shared", response_model=List[ShareLinkListItem])
async def get_shared_credentials(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get list of credentials shared by user"""
    try:
        user_id = current_user.get("sub")

        # Get all active share tokens for this user from Redis
        share_tokens = redis_service.get_user_share_tokens(user_id)

        result = []
        for token_info in share_tokens:
            token_data = token_info["data"]
            ttl_seconds = token_info["ttl_seconds"]

            # Calculate if expired
            is_expired = ttl_seconds is None or ttl_seconds <= 0

            result.append(
                ShareLinkListItem(
                    share_token=token_info["token"],
                    credential_id=token_data.get("credential_id"),
                    credential_name=token_data.get("credential_name"),
                    verifier_info=token_data.get("verifier_info"),
                    created_at=datetime.fromisoformat(token_data.get("created_at")),
                    expires_at=datetime.fromisoformat(token_data.get("expires_at")),
                    is_expired=is_expired,
                )
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch shared credentials: {str(e)}",
        )


@router.delete("/share/{token_id}", response_model=ShareLinkRevokeResponse)
async def revoke_share_link(
    token_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke a share link before expiry"""
    try:
        user_id = current_user.get("sub")

        # Get token data to verify ownership
        token_data = redis_service.get_share_token(token_id)

        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share link not found or already expired",
            )

        # Verify user owns this share link
        if token_data.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to revoke this share link",
            )

        # Delete token from Redis
        redis_service.revoke_share_token(token_id)

        return ShareLinkRevokeResponse(
            success=True, message="Share link revoked successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke share link: {str(e)}",
        )


@router.get("/{credential_id}/document")
async def get_credential_document(
    credential_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download the actual credential document from IPFS"""
    try:
        user_id = current_user.get("sub")

        result = credential_service.get_credential_document(
            db=db, user_id=user_id, credential_id=credential_id
        )

        # Return as downloadable file
        import base64

        document_bytes = base64.b64decode(result["document_base64"])

        return Response(
            content=document_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{result["credential_name"]}.pdf"'
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download document: {str(e)}",
        )


@router.get("/{credential_id}")
async def get_credential_by_id(
    credential_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get credential details by ID"""
    try:
        user_id = current_user.get("sub")

        # Verify user owns this credential
        credential = (
            db.query(Credential)
            .filter(Credential.id == credential_id, Credential.user_id == user_id)
            .first()
        )

        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found or access denied",
            )

        return {
            "id": credential.id,
            "credential_type": credential.credential_type,
            "credential_name": credential.credential_name,
            "credential_number": credential.credential_number,
            "issuer_id": credential.issuer_id,
            "blockchain_tx_hash": credential.blockchain_tx_hash,
            "ipfs_cid": credential.ipfs_cid,
            "credential_hash": credential.credential_hash,
            "metadata": credential.credential_metadata,
            "issue_date": credential.issue_date,
            "expiry_date": credential.expiry_date,
            "is_active": credential.is_active,
            "is_revoked": credential.is_revoked,
            "created_at": credential.created_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch credential: {str(e)}",
        )
