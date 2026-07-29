"""
Key Encryption Service
Provides AES-256-GCM encryption for PQC private keys at rest
"""

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class KeyEncryptionService:
    """
    Encrypts and decrypts PQC private keys using AES-256-GCM
    Uses PBKDF2 for key derivation from master key
    """

    def __init__(self, master_key: str = None):
        """
        Initialize the key encryption service

        Args:
            master_key: Master encryption key (from environment or config)
                        If None, will attempt to read from environment variable
        """
        self.master_key = master_key or os.getenv(
            "PQC_MASTER_KEY",
            "DEFAULT_INSECURE_KEY_CHANGE_IN_PRODUCTION_" + "x" * 32
        )

        # Ensure master key is long enough
        if len(self.master_key) < 32:
            raise ValueError("Master key must be at least 32 characters long")

    def _derive_encryption_key(self, salt: bytes) -> bytes:
        """
        Derive encryption key from master key using PBKDF2

        Args:
            salt: Random salt for key derivation

        Returns:
            32-byte encryption key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits for AES-256
            salt=salt,
            iterations=100000,  # OWASP recommended minimum
            backend=default_backend()
        )
        return kdf.derive(self.master_key.encode())

    def encrypt_private_key(self, private_key_hex: str) -> dict:
        """
        Encrypt a private key using AES-256-GCM

        Args:
            private_key_hex: Private key in hexadecimal format

        Returns:
            Dictionary containing:
                - encrypted_key: Base64-encoded encrypted key
                - nonce: Base64-encoded nonce (96 bits)
                - salt: Base64-encoded salt for key derivation
        """
        # Input validation
        if not isinstance(private_key_hex, str):
            raise TypeError("Private key must be a string")

        if not all(c in '0123456789abcdefABCDEF' for c in private_key_hex):
            raise ValueError("Private key must be in hexadecimal format")

        # Generate random salt and nonce
        salt = os.urandom(16)  # 128 bits
        nonce = os.urandom(12)  # 96 bits (recommended for GCM)

        # Derive encryption key
        encryption_key = self._derive_encryption_key(salt)

        # Initialize AES-GCM cipher
        aesgcm = AESGCM(encryption_key)

        # Convert hex to bytes and encrypt
        private_key_bytes = bytes.fromhex(private_key_hex)
        encrypted_key = aesgcm.encrypt(nonce, private_key_bytes, None)

        # Return as base64-encoded strings for storage
        return {
            "encrypted_key": base64.b64encode(encrypted_key).decode('utf-8'),
            "nonce": base64.b64encode(nonce).decode('utf-8'),
            "salt": base64.b64encode(salt).decode('utf-8'),
            "algorithm": "AES-256-GCM",
            "kdf": "PBKDF2-SHA256"
        }

    def decrypt_private_key(self, encrypted_data: dict) -> str:
        """
        Decrypt an encrypted private key

        Args:
            encrypted_data: Dictionary containing encrypted_key, nonce, salt

        Returns:
            Decrypted private key in hexadecimal format

        Raises:
            ValueError: If decryption fails (wrong key, tampered data, etc.)
        """
        # Validate input
        required_fields = ["encrypted_key", "nonce", "salt"]
        for field in required_fields:
            if field not in encrypted_data:
                raise ValueError(f"Missing required field: {field}")

        try:
            # Decode from base64
            encrypted_key = base64.b64decode(encrypted_data["encrypted_key"])
            nonce = base64.b64decode(encrypted_data["nonce"])
            salt = base64.b64decode(encrypted_data["salt"])

            # Derive encryption key
            encryption_key = self._derive_encryption_key(salt)

            # Initialize AES-GCM cipher
            aesgcm = AESGCM(encryption_key)

            # Decrypt
            decrypted_bytes = aesgcm.decrypt(nonce, encrypted_key, None)

            # Convert back to hex
            return decrypted_bytes.hex()

        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")

    def rotate_encryption(self, encrypted_data: dict, new_master_key: str) -> dict:
        """
        Re-encrypt a private key with a new master key (for key rotation)

        Args:
            encrypted_data: Currently encrypted data
            new_master_key: New master key to use

        Returns:
            New encrypted data dictionary
        """
        # Decrypt with current master key
        private_key_hex = self.decrypt_private_key(encrypted_data)

        # Create new service instance with new master key
        new_service = KeyEncryptionService(master_key=new_master_key)

        # Re-encrypt with new master key
        return new_service.encrypt_private_key(private_key_hex)


# Singleton instance
key_encryption_service = KeyEncryptionService()
