"""
Encryption service for sensitive data
Uses Fernet symmetric encryption (AES 128 in CBC mode)
"""
from cryptography.fernet import Fernet
from typing import Optional
import base64
import os


class EncryptionService:
    """Service for encrypting/decrypting sensitive credentials"""

    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize encryption service.

        Args:
            secret_key: Base64-encoded Fernet key (defaults to SECRET_KEY from env)
        """
        if secret_key is None:
            # Use SECRET_KEY from environment, but derive a Fernet key from it
            from .config import settings
            secret_key = settings.SECRET_KEY

        # Ensure we have a valid Fernet key (32 bytes base64-encoded)
        self.fernet = self._get_fernet_cipher(secret_key)

    def _get_fernet_cipher(self, secret_key: str) -> Fernet:
        """
        Get Fernet cipher from secret key.
        If secret_key is not a valid Fernet key, derive one from it.
        """
        try:
            # Try to use it directly as a Fernet key
            return Fernet(secret_key.encode())
        except Exception:
            # Derive a Fernet key from the secret
            # Take first 32 bytes, pad or truncate as needed
            key_bytes = secret_key.encode()[:32].ljust(32, b'0')
            fernet_key = base64.urlsafe_b64encode(key_bytes)
            return Fernet(fernet_key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""

        encrypted_bytes = self.fernet.encrypt(plaintext.encode())
        return encrypted_bytes.decode()

    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt encrypted string.

        Args:
            encrypted: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string

        Raises:
            Exception: If decryption fails (invalid key or corrupted data)
        """
        if not encrypted:
            return ""

        try:
            decrypted_bytes = self.fernet.decrypt(encrypted.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            raise Exception(f"Decryption failed: {str(e)}")


# Singleton instance
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """Get singleton encryption service instance"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service
