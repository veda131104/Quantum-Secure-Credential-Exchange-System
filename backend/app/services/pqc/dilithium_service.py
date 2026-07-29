"""
Post-Quantum Cryptography Service using CRYSTALS-Dilithium
"""

import oqs
import hashlib
import os
import json
import time
from typing import Tuple, Dict
from pathlib import Path

from app.core.config import settings
from app.services.pqc.key_encryption import key_encryption_service


class DilithiumService:
    """Service for PQC operations using Dilithium algorithm"""

    def __init__(self):
        self.algorithm = settings.PQC_ALGORITHM
        self.keys_dir = Path(settings.PQC_KEYS_DIR)
        self.keys_dir.mkdir(parents=True, exist_ok=True)

    def generate_keypair(self, identifier: str) -> Dict[str, str]:
        """
        Generate a new Dilithium keypair

        Args:
            identifier: Unique identifier for the keypair (e.g., issuer_id)

        Returns:
            Dictionary with public_key, private_key (hex encoded), and key_id
        """
        try:
            with oqs.Signature(self.algorithm) as signer:
                public_key = signer.generate_keypair()
                private_key = signer.export_secret_key()

                # Convert to hex for storage
                public_key_hex = public_key.hex()
                private_key_hex = private_key.hex()

                # Generate key ID (hash of public key)
                key_id = hashlib.sha256(public_key).hexdigest()

                # Save keys to files
                self._save_keypair(identifier, public_key_hex, private_key_hex, key_id)

                return {
                    "public_key": public_key_hex,
                    "private_key": private_key_hex,
                    "key_id": key_id,
                    "algorithm": self.algorithm,
                }
        except Exception as e:
            raise Exception(f"Failed to generate keypair: {str(e)}")

    def sign_data(self, data: bytes, private_key_hex: str) -> str:
        """
        Sign data using Dilithium private key

        Args:
            data: Data to sign (bytes)
            private_key_hex: Private key in hex format

        Returns:
            Signature as hex string
        """
        # INPUT VALIDATION
        if not isinstance(data, bytes):
            raise ValueError("Data must be bytes")
        if len(data) == 0:
            raise ValueError("Data cannot be empty")
        if len(data) > 1_000_000:  # 1MB limit
            raise ValueError("Data exceeds maximum size (1MB)")

        # Validate private key format
        if not isinstance(private_key_hex, str):
            raise ValueError("Private key must be hex string")
        if not all(c in '0123456789abcdefABCDEF' for c in private_key_hex):
            raise ValueError("Invalid hex format in private key")

        # Expected Dilithium2 private key length (2528 bytes * 2 for hex)
        EXPECTED_SK_LENGTH = 2528 * 2
        if len(private_key_hex) != EXPECTED_SK_LENGTH:
            raise ValueError(f"Invalid private key length: expected {EXPECTED_SK_LENGTH}, got {len(private_key_hex)}")

        try:
            private_key = bytes.fromhex(private_key_hex)

            with oqs.Signature(self.algorithm, secret_key=private_key) as signer:
                signature = signer.sign(data)
                return signature.hex()
        except Exception as e:
            raise Exception(f"Failed to sign data: {str(e)}")

    def verify_signature(
        self, data: bytes, signature_hex: str, public_key_hex: str
    ) -> bool:
        """
        Verify Dilithium signature

        Args:
            data: Original data (bytes)
            signature_hex: Signature in hex format
            public_key_hex: Public key in hex format

        Returns:
            True if signature is valid, False otherwise
        """
        # INPUT VALIDATION
        if not isinstance(data, bytes):
            raise ValueError("Data must be bytes")
        if len(data) == 0:
            raise ValueError("Data cannot be empty")

        # Validate signature format
        if not isinstance(signature_hex, str):
            raise ValueError("Signature must be hex string")
        if not all(c in '0123456789abcdefABCDEF' for c in signature_hex):
            raise ValueError("Invalid hex format in signature")

        # Expected Dilithium2 signature length (2420 bytes * 2 for hex)
        EXPECTED_SIG_LENGTH = 2420 * 2
        if len(signature_hex) != EXPECTED_SIG_LENGTH:
            raise ValueError(f"Invalid signature length: expected {EXPECTED_SIG_LENGTH}, got {len(signature_hex)}")

        # Validate public key format
        if not isinstance(public_key_hex, str):
            raise ValueError("Public key must be hex string")
        if not all(c in '0123456789abcdefABCDEF' for c in public_key_hex):
            raise ValueError("Invalid hex format in public key")

        # Expected Dilithium2 public key length (1312 bytes * 2 for hex)
        EXPECTED_PK_LENGTH = 1312 * 2
        if len(public_key_hex) != EXPECTED_PK_LENGTH:
            raise ValueError(f"Invalid public key length: expected {EXPECTED_PK_LENGTH}, got {len(public_key_hex)}")

        # Use constant-time verification
        return self._constant_time_verify(data, signature_hex, public_key_hex)

    def _constant_time_verify(self, data: bytes, signature_hex: str, public_key_hex: str) -> bool:
        """
        Constant-time signature verification to prevent timing attacks
        Uses liboqs verify but ensures consistent timing

        Args:
            data: Original data (bytes)
            signature_hex: Signature in hex format
            public_key_hex: Public key in hex format

        Returns:
            True if signature is valid, False otherwise
        """
        start_time = time.perf_counter()

        try:
            signature = bytes.fromhex(signature_hex)
            public_key = bytes.fromhex(public_key_hex)

            with oqs.Signature(self.algorithm) as verifier:
                result = verifier.verify(data, signature, public_key)
        except Exception as e:
            print(f"Signature verification failed: {str(e)}")
            result = False

        # Add constant delay to normalize timing
        # This helps prevent timing side-channels
        elapsed = time.perf_counter() - start_time
        MIN_VERIFICATION_TIME = 0.001  # 1ms minimum
        if elapsed < MIN_VERIFICATION_TIME:
            time.sleep(MIN_VERIFICATION_TIME - elapsed)

        return result

    def hash_data(self, data) -> bytes:
        """
        Create SHA-256 hash of data

        Args:
            data: Data to hash (bytes or str)

        Returns:
            Hash as bytes
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif not isinstance(data, bytes):
            raise ValueError("Data must be bytes or string")
        return hashlib.sha256(data).digest()

    def load_private_key(self, identifier: str) -> str:
        """
        Load private key from file and decrypt it

        Args:
            identifier: Unique identifier for the keypair

        Returns:
            Private key as hex string (decrypted)
        """
        key_file = self.keys_dir / f"{identifier}_private.key"
        if not key_file.exists():
            raise FileNotFoundError(f"Private key not found for {identifier}")

        with open(key_file, "r") as f:
            key_data = json.load(f)

            # Check if key is encrypted
            if "encrypted_key" in key_data:
                # Decrypt the key
                try:
                    decrypted_key = key_encryption_service.decrypt_private_key(key_data)
                    return decrypted_key
                except Exception as e:
                    raise ValueError(f"Failed to decrypt private key: {str(e)}")
            else:
                # Legacy unencrypted key
                return key_data["private_key"]

    def load_public_key(self, identifier: str) -> str:
        """
        Load public key from file

        Args:
            identifier: Unique identifier for the keypair

        Returns:
            Public key as hex string
        """
        key_file = self.keys_dir / f"{identifier}_public.key"
        if not key_file.exists():
            raise FileNotFoundError(f"Public key not found for {identifier}")

        with open(key_file, "r") as f:
            key_data = json.load(f)
            return key_data["public_key"]

    def _save_keypair(
        self, identifier: str, public_key: str, private_key: str, key_id: str
    ):
        """Save keypair to files with encrypted private key"""
        # Save public key
        public_key_file = self.keys_dir / f"{identifier}_public.key"
        with open(public_key_file, "w") as f:
            json.dump(
                {
                    "public_key": public_key,
                    "key_id": key_id,
                    "algorithm": self.algorithm,
                },
                f,
                indent=2,
            )

        # Encrypt and save private key
        encrypted_key_data = key_encryption_service.encrypt_private_key(private_key)

        private_key_file = self.keys_dir / f"{identifier}_private.key"
        with open(private_key_file, "w") as f:
            # Store encrypted data with metadata
            key_file_data = {
                **encrypted_key_data,
                "key_id": key_id,
                "algorithm": self.algorithm,
            }
            json.dump(key_file_data, f, indent=2)

        # Set restrictive permissions on private key
        os.chmod(private_key_file, 0o600)

    def keypair_exists(self, identifier: str) -> bool:
        """Check if keypair exists for given identifier"""
        public_key_file = self.keys_dir / f"{identifier}_public.key"
        private_key_file = self.keys_dir / f"{identifier}_private.key"
        return public_key_file.exists() and private_key_file.exists()


# Singleton instance
pqc_service = DilithiumService()
