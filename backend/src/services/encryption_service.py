"""Encryption service for sensitive data like GitHub OAuth tokens."""
import base64
import os
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from src.config import settings


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""
    
    def __init__(self):
        """Initialize encryption service with key from settings or generate new one."""
        self.key = self._get_or_generate_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_generate_key(self) -> bytes:
        """Get encryption key from settings or generate a new one.
        
        If GITHUB_OAUTH_ENCRYPTION_KEY is set, use it.
        Otherwise, generate a new key (for development only).
        """
        if settings.GITHUB_OAUTH_ENCRYPTION_KEY:
            # Key is stored as base64-encoded string
            try:
                return base64.urlsafe_b64decode(settings.GITHUB_OAUTH_ENCRYPTION_KEY.encode())
            except Exception:
                # If key is invalid, generate a new one
                pass
        
        # Generate a new key (for development only)
        # In production, this should be set via environment variable
        key = Fernet.generate_key()
        print(f"⚠️  WARNING: Generated new encryption key. Set GITHUB_OAUTH_ENCRYPTION_KEY in production!")
        print(f"   Generated key (base64): {base64.urlsafe_b64encode(key).decode()}")
        return key
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string.
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""
        
        encrypted_bytes = self.cipher.encrypt(plaintext.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
    
    def decrypt(self, ciphertext: str) -> Optional[str]:
        """Decrypt an encrypted string.
        
        Args:
            ciphertext: Base64-encoded encrypted string
            
        Returns:
            Decrypted plaintext string, or None if decryption fails
        """
        if not ciphertext:
            return None
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(ciphertext.encode('utf-8'))
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            print(f"⚠️  Decryption failed: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


# Global encryption service instance
encryption_service = EncryptionService()
