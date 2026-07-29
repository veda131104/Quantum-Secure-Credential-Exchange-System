"""User management routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.models.base import get_db
from app.models import User, Credential, BiometricEnrollment, Issuer
from app.schemas.user import (
    UserResponse,
    UserUpdate,
    BiometricEnrollRequest,
    BiometricEnrollResponse,
    WalletResponse,
    UserCredentialListItem,
)
from app.core.security import get_current_user
from app.services.biometric import face_recognition_service
from app.services.blockchain import blockchain_service

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get current user information"""
    try:
        user_id = current_user.get("sub")
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return UserResponse.model_validate(user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user info: {str(e)}",
        )


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user information"""
    try:
        user_id = current_user.get("sub")
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Update fields if provided
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        if user_data.phone is not None:
            user.phone = user_data.phone

        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

        return UserResponse.model_validate(user)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}",
        )


@router.post("/enroll-biometric", response_model=BiometricEnrollResponse)
async def enroll_biometric(
    biometric_data: BiometricEnrollRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enroll user's biometric data (face)"""
    try:
        user_id = current_user.get("sub")
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Check if already enrolled
        if user.biometric_enrolled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Biometric already enrolled. Delete existing enrollment first.",
            )

        # Extract face embedding
        embedding = face_recognition_service.extract_embedding_from_base64(
            biometric_data.biometric_data
        )

        # Hash embedding
        embedding_hash = face_recognition_service.hash_embedding(embedding)

        # Save embedding to file
        face_recognition_service.save_embedding(user_id, embedding)

        # Store embedding hash on blockchain (optional - for additional security)
        blockchain_tx_hash = None
        if blockchain_service.is_connected() and user.wallet_address:
            try:
                # In production, you'd call a smart contract method to store the hash
                # For now, we'll just note that it would be stored
                blockchain_tx_hash = "pending_blockchain_implementation"
            except Exception as e:
                print(f"Blockchain storage failed: {str(e)}")

        # Create biometric enrollment record
        enrollment = BiometricEnrollment(
            user_id=user_id,
            biometric_type=biometric_data.biometric_type,
            embedding_hash=embedding_hash,
            blockchain_tx_hash=blockchain_tx_hash,
            blockchain_stored=blockchain_tx_hash is not None,
            model_name=face_recognition_service.model_name,
            is_primary=True,
        )

        db.add(enrollment)

        # Update user
        user.biometric_enrolled = True
        user.biometric_hash = embedding_hash
        user.updated_at = datetime.utcnow()

        db.commit()

        return BiometricEnrollResponse(
            success=True,
            message="Biometric enrolled successfully",
            embedding_hash=embedding_hash,
            blockchain_tx_hash=blockchain_tx_hash,
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        # Clean up saved embedding if it exists
        try:
            face_recognition_service.delete_embedding(user_id)
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Biometric enrollment failed: {str(e)}",
        )


@router.delete("/enroll-biometric")
async def delete_biometric_enrollment(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Delete user's biometric enrollment"""
    try:
        user_id = current_user.get("sub")
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if not user.biometric_enrolled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No biometric enrollment found",
            )

        # Delete embedding file
        face_recognition_service.delete_embedding(user_id)

        # Delete enrollment records
        db.query(BiometricEnrollment).filter(
            BiometricEnrollment.user_id == user_id
        ).delete()

        # Update user
        user.biometric_enrolled = False
        user.biometric_hash = None
        user.updated_at = datetime.utcnow()

        db.commit()

        return {"message": "Biometric enrollment deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete biometric enrollment: {str(e)}",
        )


@router.get("/wallet", response_model=WalletResponse)
async def get_user_wallet(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get user's wallet information"""
    try:
        user_id = current_user.get("sub")
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if not user.wallet_address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found for user",
            )

        return WalletResponse(
            wallet_address=user.wallet_address,
            public_key=user.public_key,
            user_id=user.id,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch wallet info: {str(e)}",
        )


@router.get("/credentials", response_model=List[UserCredentialListItem])
async def get_user_credentials(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get all credentials belonging to the user"""
    try:
        user_id = current_user.get("sub")

        # Fetch credentials with issuer info
        credentials = (
            db.query(Credential)
            .filter(Credential.user_id == user_id)
            .order_by(Credential.created_at.desc())
            .all()
        )

        # Build response with issuer names
        result = []
        for cred in credentials:
            issuer = db.query(Issuer).filter(Issuer.id == cred.issuer_id).first()
            issuer_name = issuer.organization_name if issuer else "Unknown Issuer"

            result.append(
                UserCredentialListItem(
                    id=cred.id,
                    credential_type=cred.credential_type,
                    credential_name=cred.credential_name,
                    issuer_name=issuer_name,
                    issue_date=cred.issue_date,
                    expiry_date=cred.expiry_date,
                    is_active=cred.is_active,
                    ipfs_cid=cred.ipfs_cid,
                )
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch credentials: {str(e)}",
        )


@router.get("/credentials/{credential_id}")
async def get_credential_details(
    credential_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details of a specific credential"""
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

        # Get issuer info
        issuer = db.query(Issuer).filter(Issuer.id == credential.issuer_id).first()

        # Get blockchain verification
        blockchain_verified = False
        if blockchain_service.is_connected():
            try:
                blockchain_data = blockchain_service.verify_credential(
                    credential.credential_hash
                )
                blockchain_verified = blockchain_data is not None and blockchain_data.get(
                    "exists"
                )
            except Exception as e:
                print(f"Blockchain verification failed: {str(e)}")

        return {
            "id": credential.id,
            "credential_type": credential.credential_type,
            "credential_name": credential.credential_name,
            "credential_number": credential.credential_number,
            "issuer": {
                "id": issuer.id if issuer else None,
                "name": issuer.organization_name if issuer else "Unknown",
                "organization_type": issuer.organization_type if issuer else None,
            },
            "blockchain_tx_hash": credential.blockchain_tx_hash,
            "blockchain_verified": blockchain_verified,
            "ipfs_cid": credential.ipfs_cid,
            "credential_hash": credential.credential_hash,
            "pqc_signature": credential.pqc_signature[:50] + "...",  # Truncate for display
            "signature_algorithm": credential.signature_algorithm,
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
            detail=f"Failed to fetch credential details: {str(e)}",
        )
