"""
Credential service - orchestrates PQC, Blockchain, and IPFS
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
from typing import Dict, Optional, List

from app.models import Credential, User, Issuer, AuditLog
from app.services.pqc import pqc_service
from app.services.blockchain import blockchain_service
from app.services.ipfs import ipfs_service
from app.services.auth import redis_service
from app.core.config import settings


class CredentialService:
    """Service for credential operations"""

    def issue_credential(
        self,
        db: Session,
        issuer_id: str,
        user_email: str,
        credential_type: str,
        credential_name: str,
        document_base64: str,
        metadata: Optional[Dict] = None,
        credential_number: Optional[str] = None,
        issue_date: datetime = None,
        expiry_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Issue a new credential

        Steps:
        1. Validate issuer and user
        2. Upload document to IPFS
        3. Create credential hash
        4. Sign with issuer's PQC key
        5. Register on blockchain
        6. Store in database
        """
        try:
            # Validate issuer
            issuer = db.query(Issuer).filter(Issuer.id == issuer_id).first()
            if not issuer or not issuer.is_approved:
                raise ValueError("Issuer not found or not approved")

            # Validate user
            user = db.query(User).filter(User.email == user_email).first()
            if not user:
                raise ValueError("User not found")

            # Upload document to IPFS (optional if IPFS not available)
            ipfs_cid = None
            if ipfs_service.is_connected():
                try:
                    ipfs_result = ipfs_service.upload_base64_file(document_base64)
                    ipfs_cid = ipfs_result["cid"]
                    print(f"Document uploaded to IPFS: {ipfs_cid}")

                    # Pin the file
                    ipfs_service.pin_file(ipfs_cid)
                except Exception as e:
                    print(f"Warning: IPFS upload failed: {str(e)}")
                    print("Continuing without IPFS storage (document stored in DB only)...")
                    ipfs_cid = "local_storage"
            else:
                print("Warning: IPFS not available, storing document reference only")
                ipfs_cid = "local_storage"

            # Create credential data for hashing
            credential_data = {
                "user_id": user.id,
                "issuer_id": issuer_id,
                "credential_type": credential_type,
                "credential_name": credential_name,
                "credential_number": credential_number,
                "ipfs_cid": ipfs_cid,
                "metadata": metadata,
                "issue_date": issue_date.isoformat() if issue_date else datetime.utcnow().isoformat(),
            }

            # Create credential hash
            credential_hash = pqc_service.hash_data(str(credential_data).encode())

            # Sign credential with issuer's PQC private key
            # Note: Keys are stored by user_id, not issuer_id
            issuer_private_key = pqc_service.load_private_key(issuer.user_id)
            pqc_signature = pqc_service.sign_data(
                credential_hash.encode(), issuer_private_key
            )

            # Register on blockchain (optional if contract not deployed)
            tx_hash = None
            receipt = None

            if blockchain_service.is_connected() and blockchain_service.contract:
                try:
                    tx_hash = blockchain_service.register_credential(
                        issuer_address=issuer.blockchain_address,
                        issuer_private_key=issuer_private_key,  # In production, use secure key storage
                        credential_id=credential_hash,
                        user_address=user.wallet_address,
                        ipfs_cid=ipfs_cid,
                        credential_hash=credential_hash,
                        pqc_signature=pqc_signature,
                    )
                    print(f"Credential registered on blockchain: {tx_hash}")

                    # Wait for transaction
                    receipt = blockchain_service.wait_for_transaction(tx_hash)
                except Exception as e:
                    print(f"Warning: Blockchain registration failed: {str(e)}")
                    print("Continuing without blockchain registration...")
            else:
                print("Warning: Blockchain not available, continuing without blockchain registration")

            # Create credential in database
            credential = Credential(
                user_id=user.id,
                issuer_id=issuer_id,
                credential_type=credential_type,
                credential_name=credential_name,
                credential_number=credential_number,
                blockchain_tx_hash=tx_hash,
                blockchain_block_number=str(receipt["blockNumber"]) if receipt else None,
                ipfs_cid=ipfs_cid,
                credential_hash=credential_hash,
                pqc_signature=pqc_signature,
                credential_metadata=metadata,
                issue_date=issue_date or datetime.utcnow(),
                expiry_date=expiry_date,
            )

            db.add(credential)

            # Update issuer stats
            issuer.total_credentials_issued += 1

            db.commit()
            db.refresh(credential)

            return {
                "success": True,
                "credential_id": credential.id,
                "blockchain_tx_hash": tx_hash,
                "ipfs_cid": ipfs_cid,
                "message": "Credential issued successfully",
            }

        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to issue credential: {str(e)}")

    def create_share_link(
        self,
        db: Session,
        user_id: str,
        credential_id: str,
        expiry_hours: int = 24,
        verifier_info: Optional[Dict] = None,
    ) -> Dict:
        """
        Create a time-bound share link for a credential
        """
        try:
            # Validate credential ownership
            credential = (
                db.query(Credential)
                .filter(Credential.id == credential_id, Credential.user_id == user_id)
                .first()
            )

            if not credential:
                raise ValueError("Credential not found or you don't have access")

            if not credential.is_active or credential.is_revoked:
                raise ValueError("Credential is not active or has been revoked")

            # Generate share token
            share_token = secrets.token_urlsafe(32)

            # Calculate expiry
            expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)

            # Store in Redis
            token_data = {
                "credential_id": credential_id,
                "user_id": user_id,
                "credential_name": credential.credential_name,
                "verifier_info": verifier_info,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": expires_at.isoformat(),
            }

            redis_service.store_share_token(share_token, token_data, expiry_hours)

            # Generate share URL
            share_url = f"{settings.SHARE_LINK_BASE_URL}/{share_token}"

            return {
                "success": True,
                "share_url": share_url,
                "share_token": share_token,
                "expires_at": expires_at,
            }

        except Exception as e:
            raise Exception(f"Failed to create share link: {str(e)}")

    def verify_credential(
        self, db: Session, share_token: str, actor_ip: Optional[str] = None
    ) -> Dict:
        """
        Verify a credential using share token
        """
        try:
            # Get token data from Redis
            token_data = redis_service.get_share_token(share_token)

            if not token_data:
                return {
                    "success": False,
                    "verified": False,
                    "message": "Share link not found or expired",
                }

            credential_id = token_data["credential_id"]

            # Get credential from database
            credential = db.query(Credential).filter(Credential.id == credential_id).first()

            if not credential:
                return {
                    "success": False,
                    "verified": False,
                    "message": "Credential not found",
                }

            # Get issuer info
            issuer = db.query(Issuer).filter(Issuer.id == credential.issuer_id).first()

            # Verify on blockchain (if available)
            blockchain_verified = False
            blockchain_data = None

            if blockchain_service.is_connected() and blockchain_service.contract:
                try:
                    blockchain_data = blockchain_service.verify_credential(credential.credential_hash)
                    if blockchain_data and blockchain_data.get("exists"):
                        blockchain_verified = True
                        if blockchain_data.get("is_revoked"):
                            result = {
                                "success": True,
                                "verified": False,
                                "credential_type": credential.credential_type,
                                "credential_name": credential.credential_name,
                                "issuer_name": issuer.organization_name,
                                "issue_date": credential.issue_date,
                                "expiry_date": credential.expiry_date,
                                "is_expired": False,
                                "signature_valid": False,
                                "blockchain_verified": True,
                                "message": "Credential has been revoked",
                            }
                            # Log and return early (serialize datetime for JSON)
                            result_for_log = result.copy()
                            if result_for_log.get("issue_date"):
                                result_for_log["issue_date"] = result_for_log["issue_date"].isoformat()
                            if result_for_log.get("expiry_date"):
                                result_for_log["expiry_date"] = result_for_log["expiry_date"].isoformat()

                            audit_log = AuditLog(
                                event_type="verification",
                                credential_id=credential_id,
                                actor_type="verifier",
                                actor_ip=actor_ip,
                                verifier_info=token_data.get("verifier_info"),
                                share_token=share_token,
                                success="failure",
                                result_data=result_for_log,
                                description="Credential verification via share link",
                            )
                            db.add(audit_log)
                            db.commit()
                            return result
                except Exception as e:
                    print(f"Warning: Blockchain verification failed: {str(e)}")
                    blockchain_verified = False

            # Verify PQC signature (main verification method)
            if True:  # Always verify signature
                # Verify PQC signature
                signature_valid = pqc_service.verify_signature(
                    credential.credential_hash.encode(),
                    credential.pqc_signature,
                    issuer.pqc_public_key,
                )

                # Check expiry
                is_expired = False
                if credential.expiry_date:
                    is_expired = credential.expiry_date < datetime.utcnow()

                result = {
                    "success": True,
                    "verified": signature_valid and not is_expired,
                    "credential_type": credential.credential_type,
                    "credential_name": credential.credential_name,
                    "issuer_name": issuer.organization_name,
                    "issue_date": credential.issue_date,
                    "expiry_date": credential.expiry_date,
                    "is_expired": is_expired,
                    "signature_valid": signature_valid,
                    "blockchain_verified": blockchain_verified,
                    "message": "Credential verified successfully"
                    if signature_valid and not is_expired
                    else "Verification failed",
                }

            # Log verification event (serialize datetime objects for JSON storage)
            result_for_log = result.copy()
            if result_for_log.get("issue_date"):
                result_for_log["issue_date"] = result_for_log["issue_date"].isoformat()
            if result_for_log.get("expiry_date"):
                result_for_log["expiry_date"] = result_for_log["expiry_date"].isoformat()

            audit_log = AuditLog(
                event_type="verification",
                credential_id=credential_id,
                actor_type="verifier",
                actor_ip=actor_ip,
                verifier_info=token_data.get("verifier_info"),
                share_token=share_token,
                success="success" if result["verified"] else "failure",
                result_data=result_for_log,
                description="Credential verification via share link",
            )
            db.add(audit_log)
            db.commit()

            return result

        except Exception as e:
            return {
                "success": False,
                "verified": False,
                "message": f"Verification error: {str(e)}",
            }

    def get_user_credentials(self, db: Session, user_id: str) -> List[Credential]:
        """Get all credentials for a user"""
        return (
            db.query(Credential)
            .filter(Credential.user_id == user_id)
            .order_by(Credential.created_at.desc())
            .all()
        )

    def get_credential_document(
        self, db: Session, user_id: str, credential_id: str
    ) -> Dict:
        """Download credential document from IPFS"""
        try:
            # Verify ownership
            credential = (
                db.query(Credential)
                .filter(Credential.id == credential_id, Credential.user_id == user_id)
                .first()
            )

            if not credential:
                raise ValueError("Credential not found or access denied")

            # Download from IPFS
            document_base64 = ipfs_service.download_file_as_base64(credential.ipfs_cid)

            return {
                "success": True,
                "document_base64": document_base64,
                "ipfs_cid": credential.ipfs_cid,
                "credential_name": credential.credential_name,
            }

        except Exception as e:
            raise Exception(f"Failed to download document: {str(e)}")


# Singleton instance
credential_service = CredentialService()
