"""
Secrets management for the Agaip framework.

This module provides secure handling of sensitive configuration data
including encryption, key management, and secure storage.
"""

import base64
import os
from typing import Any, Dict, Optional, Union
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from agaip.core.exceptions import ConfigurationError


class SecretsManager:
    """Manages encrypted secrets and sensitive configuration data."""
    
    def __init__(self, master_key: Optional[str] = None, secrets_file: Optional[str] = None):
        """
        Initialize the secrets manager.
        
        Args:
            master_key: Master encryption key. If None, will be generated or loaded from env.
            secrets_file: Path to encrypted secrets file.
        """
        self.secrets_file = Path(secrets_file or "./config/secrets.enc")
        self._fernet = self._initialize_encryption(master_key)
        self._secrets_cache: Dict[str, Any] = {}
    
    def _initialize_encryption(self, master_key: Optional[str] = None) -> Fernet:
        """Initialize encryption with master key."""
        if master_key is None:
            master_key = os.getenv("AGAIP_MASTER_KEY")
        
        if master_key is None:
            # Generate a new master key for development
            key = Fernet.generate_key()
            print(f"Generated new master key: {key.decode()}")
            print("Set AGAIP_MASTER_KEY environment variable with this key")
            return Fernet(key)
        
        # Derive key from master key
        if isinstance(master_key, str):
            master_key = master_key.encode()
        
        # Use PBKDF2 to derive a proper key
        salt = b"agaip_salt_2024"  # In production, use a random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key))
        return Fernet(key)
    
    def encrypt_secret(self, value: str) -> str:
        """Encrypt a secret value."""
        if isinstance(value, str):
            value = value.encode()
        encrypted = self._fernet.encrypt(value)
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_secret(self, encrypted_value: str) -> str:
        """Decrypt a secret value."""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted = self._fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            raise ConfigurationError(f"Failed to decrypt secret: {e}")
    
    def set_secret(self, key: str, value: str) -> None:
        """Set an encrypted secret."""
        self._secrets_cache[key] = self.encrypt_secret(value)
        self._save_secrets()
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a decrypted secret."""
        if not self._secrets_cache:
            self._load_secrets()
        
        encrypted_value = self._secrets_cache.get(key)
        if encrypted_value is None:
            return default
        
        return self.decrypt_secret(encrypted_value)
    
    def delete_secret(self, key: str) -> bool:
        """Delete a secret."""
        if key in self._secrets_cache:
            del self._secrets_cache[key]
            self._save_secrets()
            return True
        return False
    
    def list_secrets(self) -> list[str]:
        """List all secret keys (not values)."""
        if not self._secrets_cache:
            self._load_secrets()
        return list(self._secrets_cache.keys())
    
    def _load_secrets(self) -> None:
        """Load secrets from encrypted file."""
        if not self.secrets_file.exists():
            self._secrets_cache = {}
            return
        
        try:
            with open(self.secrets_file, 'rb') as f:
                encrypted_data = f.read()
            
            if not encrypted_data:
                self._secrets_cache = {}
                return
            
            decrypted_data = self._fernet.decrypt(encrypted_data)
            import json
            self._secrets_cache = json.loads(decrypted_data.decode())
        except Exception as e:
            raise ConfigurationError(f"Failed to load secrets: {e}")
    
    def _save_secrets(self) -> None:
        """Save secrets to encrypted file."""
        try:
            # Ensure directory exists
            self.secrets_file.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            data = json.dumps(self._secrets_cache).encode()
            encrypted_data = self._fernet.encrypt(data)
            
            with open(self.secrets_file, 'wb') as f:
                f.write(encrypted_data)
        except Exception as e:
            raise ConfigurationError(f"Failed to save secrets: {e}")
    
    def rotate_master_key(self, new_master_key: str) -> None:
        """Rotate the master encryption key."""
        # Load current secrets
        if not self._secrets_cache:
            self._load_secrets()
        
        # Decrypt all secrets with current key
        decrypted_secrets = {}
        for key, encrypted_value in self._secrets_cache.items():
            decrypted_secrets[key] = self.decrypt_secret(encrypted_value)
        
        # Initialize new encryption with new key
        self._fernet = self._initialize_encryption(new_master_key)
        
        # Re-encrypt all secrets with new key
        self._secrets_cache = {}
        for key, value in decrypted_secrets.items():
            self._secrets_cache[key] = self.encrypt_secret(value)
        
        # Save with new encryption
        self._save_secrets()


# Global secrets manager instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get the global secrets manager instance."""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Convenience function to get a secret."""
    return get_secrets_manager().get_secret(key, default)


def set_secret(key: str, value: str) -> None:
    """Convenience function to set a secret."""
    get_secrets_manager().set_secret(key, value)
