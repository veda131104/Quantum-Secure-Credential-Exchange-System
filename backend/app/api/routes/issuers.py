"""Issuer management routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List

from app.models.base import get_db
from app.models import Issuer, User, Credential
from app.schemas.issuer import (
    IssuerRegisterRequest,
    IssuerResponse,
    IssuerRegisterResponse,
    CredentialIssueRequest,
    CredentialIssueResponse,
    IssuerStatsResponse,
)
from app.schemas.credential import CredentialResponse
from app.core.security import get_current_user, require_admin, require_issuer
from app.services.pqc import pqc_service
from app.services.blockchain import blockchain_service
from app.services.credentials import credential_service

router = APIRouter()


@router.post("/register", response_model=IssuerRegisterResponse)
async def register_issuer(
    issuer_data: IssuerRegisterRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Register a new issuer (admin only)"""
    try:
        admin_user_id = current_user.get("sub")

        # Check if issuer already exists
        existing_issuer = (
            db.query(Issuer)
            .filter(Issuer.contact_email == issuer_data.contact_email)
            .first()
        )

        if existing_issuer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Issuer with this email already exists",
            )

        # Check if a user with this email already exists
        existing_user = (
            db.query(User)
            .filter(User.email == issuer_data.contact_email)
            .first()
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user account with this email already exists",
            )

        # Create a user account for the issuer
        from app.core.security import hash_password
        import secrets

        # Generate temporary password (issuer should change it)
        temp_password = secrets.token_urlsafe(16)
        hashed_pwd = hash_password(temp_password)

        # Create blockchain account
        blockchain_account = blockchain_service.create_account()

        # Generate unique username from organization name
        base_username = issuer_data.organization_name.lower().replace(" ", "_")
        username = base_username
        counter = 1

        # Check if username exists and make it unique
        while db.query(User).filter(User.username == username).first():
            username = f"{base_username}_{counter}"
            counter += 1

        # Create user
        issuer_user = User(
            email=issuer_data.contact_email,
            username=username,
            hashed_password=hashed_pwd,
            full_name=issuer_data.organization_name,
            phone=issuer_data.contact_phone,
            wallet_address=blockchain_account["address"],
            role="issuer",
        )

        db.add(issuer_user)
        db.flush()  # Get the user ID

        # Generate PQC keypair for issuer
        keypair = pqc_service.generate_keypair(issuer_user.id)

        # Create issuer record
        new_issuer = Issuer(
            user_id=issuer_user.id,
            organization_name=issuer_data.organization_name,
            organization_type=issuer_data.organization_type,
            registration_number=issuer_data.registration_number,
            contact_email=issuer_data.contact_email,
            contact_phone=issuer_data.contact_phone,
            address=issuer_data.address,
            blockchain_address=blockchain_account["address"],
            pqc_public_key=keypair["public_key"],
            pqc_key_id=keypair["key_id"],
            is_approved=True,  # Auto-approve for now (can add manual approval later)
            approved_by=admin_user_id,
            approved_at=datetime.utcnow(),
        )

        db.add(new_issuer)

        # Register issuer on blockchain
        if blockchain_service.is_connected():
            try:
                # Note: This requires admin's private key - should be securely stored
                # For now, we'll skip actual blockchain registration
                print(
                    "Note: Blockchain registration requires admin wallet private key"
                )
            except Exception as e:
                print(f"Blockchain registration failed: {str(e)}")

        db.commit()
        db.refresh(new_issuer)

        # Create response with temp password
        issuer_dict = {
            "id": new_issuer.id,
            "user_id": new_issuer.user_id,
            "organization_name": new_issuer.organization_name,
            "organization_type": new_issuer.organization_type,
            "contact_email": new_issuer.contact_email,
            "blockchain_address": new_issuer.blockchain_address,
            "pqc_public_key": new_issuer.pqc_public_key,
            "is_approved": new_issuer.is_approved,
            "is_active": new_issuer.is_active,
            "total_credentials_issued": new_issuer.total_credentials_issued,
            "created_at": new_issuer.created_at,
            "temp_password": temp_password,
        }
        return IssuerRegisterResponse(**issuer_dict)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Issuer registration failed: {str(e)}",
        )


@router.get("/me", response_model=IssuerResponse)
async def get_issuer_info(
    current_user: dict = Depends(require_issuer), db: Session = Depends(get_db)
):
    """Get current issuer information"""
    try:
        user_id = current_user.get("sub")

        # Find issuer by user_id
        issuer = db.query(Issuer).filter(Issuer.user_id == user_id).first()

        if not issuer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Issuer not found"
            )

        return IssuerResponse.model_validate(issuer)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch issuer info: {str(e)}",
        )


@router.post("/issue-credential", response_model=CredentialIssueResponse)
async def issue_credential(
    credential_data: CredentialIssueRequest,
    current_user: dict = Depends(require_issuer),
    db: Session = Depends(get_db),
):
    """Issue a new credential to a user"""
    try:
        user_id = current_user.get("sub")

        # Get issuer
        issuer = db.query(Issuer).filter(Issuer.user_id == user_id).first()

        if not issuer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Issuer not found"
            )

        if not issuer.is_approved or not issuer.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Issuer is not approved or active",
            )

        # Use the credential service to issue
        result = credential_service.issue_credential(
            db=db,
            issuer_id=issuer.id,
            user_email=credential_data.user_email,
            credential_type=credential_data.credential_type,
            credential_name=credential_data.credential_name,
            document_base64=credential_data.document_base64,
            metadata=credential_data.credential_metadata,
            credential_number=credential_data.credential_number,
            issue_date=credential_data.issue_date,
            expiry_date=credential_data.expiry_date,
        )

        return CredentialIssueResponse(
            success=result["success"],
            message=result["message"],
            credential_id=result["credential_id"],
            blockchain_tx_hash=result["blockchain_tx_hash"],
            ipfs_cid=result["ipfs_cid"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Credential issuance failed: {str(e)}",
        )


@router.get("/issued-credentials", response_model=List[CredentialResponse])
async def get_issued_credentials(
    current_user: dict = Depends(require_issuer), db: Session = Depends(get_db)
):
    """Get all credentials issued by this issuer"""
    try:
        user_id = current_user.get("sub")

        # Get issuer
        issuer = db.query(Issuer).filter(Issuer.user_id == user_id).first()

        if not issuer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Issuer not found"
            )

        # Get all credentials issued by this issuer
        credentials = (
            db.query(Credential)
            .filter(Credential.issuer_id == issuer.id)
            .order_by(Credential.created_at.desc())
            .all()
        )

        return [CredentialResponse.model_validate(cred) for cred in credentials]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch issued credentials: {str(e)}",
        )


@router.get("/stats", response_model=IssuerStatsResponse)
async def get_issuer_stats(
    current_user: dict = Depends(require_issuer), db: Session = Depends(get_db)
):
    """Get issuer statistics"""
    try:
        user_id = current_user.get("sub")

        # Get issuer
        issuer = db.query(Issuer).filter(Issuer.user_id == user_id).first()

        if not issuer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Issuer not found"
            )

        # Count total credentials
        total_credentials = (
            db.query(Credential).filter(Credential.issuer_id == issuer.id).count()
        )

        # Count active credentials
        active_credentials = (
            db.query(Credential)
            .filter(
                Credential.issuer_id == issuer.id,
                Credential.is_active == True,
                Credential.is_revoked == False,
            )
            .count()
        )

        # Count revoked credentials
        revoked_credentials = (
            db.query(Credential)
            .filter(Credential.issuer_id == issuer.id, Credential.is_revoked == True)
            .count()
        )

        # Count recent issuances (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_issuances = (
            db.query(Credential)
            .filter(
                Credential.issuer_id == issuer.id,
                Credential.created_at >= thirty_days_ago,
            )
            .count()
        )

        return IssuerStatsResponse(
            total_credentials_issued=total_credentials,
            active_credentials=active_credentials,
            revoked_credentials=revoked_credentials,
            recent_issuances=recent_issuances,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch issuer stats: {str(e)}",
        )


@router.patch("/revoke-credential/{credential_id}")
async def revoke_credential(
    credential_id: str,
    current_user: dict = Depends(require_issuer),
    db: Session = Depends(get_db),
):
    """Revoke a credential"""
    try:
        user_id = current_user.get("sub")

        # Get issuer
        issuer = db.query(Issuer).filter(Issuer.user_id == user_id).first()

        if not issuer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Issuer not found"
            )

        # Get credential
        credential = (
            db.query(Credential)
            .filter(
                Credential.id == credential_id, Credential.issuer_id == issuer.id
            )
            .first()
        )

        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found or you don't have permission",
            )

        if credential.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credential is already revoked",
            )

        # Revoke on blockchain
        if blockchain_service.is_connected():
            try:
                # Note: Requires issuer's blockchain private key
                print("Note: Blockchain revocation requires issuer wallet private key")
            except Exception as e:
                print(f"Blockchain revocation failed: {str(e)}")

        # Update credential
        credential.is_revoked = True
        credential.revoked_at = datetime.utcnow()
        credential.is_active = False

        db.commit()

        return {
            "message": "Credential revoked successfully",
            "credential_id": credential_id,
            "revoked_at": credential.revoked_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Credential revocation failed: {str(e)}",
        )


@router.get("/all", response_model=List[IssuerResponse])
async def get_all_issuers(
    current_user: dict = Depends(require_admin), db: Session = Depends(get_db)
):
    """Get all issuers (admin only)"""
    try:
        issuers = db.query(Issuer).order_by(Issuer.created_at.desc()).all()
        return [IssuerResponse.model_validate(issuer) for issuer in issuers]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch issuers: {str(e)}",
        )
