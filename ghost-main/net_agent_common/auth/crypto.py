"""
Credential Encryption
======================
AES-GCM symmetric encryption for router credentials.
Each user gets a unique salt; the master key never leaves the config.

Security model:
  - Server stores only ciphertext + salt + nonce
  - Decryption happens ONLY on the local client
  - Server cannot reverse stored passwords without the master key
"""

import base64
import hashlib
import os

from net_agent_common.config.settings import AES_MASTER_KEY


class CredentialCrypto:
    """Encrypt / decrypt router credentials using AES-GCM."""

    def __init__(self, master_key: str = None):
        self._master_key = (master_key or AES_MASTER_KEY).encode() if (master_key or AES_MASTER_KEY) else b""

    @staticmethod
    def generate_salt() -> str:
        """Generate a random 16-byte salt (hex-encoded)."""
        return os.urandom(16).hex()

    def derive_key(self, salt: str) -> bytes:
        """
        Derive a 32-byte AES key from master key + user salt using PBKDF2.

        Raises:
            RuntimeError: If master key is empty (encryption must be explicitly configured).
        """
        if not self._master_key:
            raise RuntimeError(
                "AES master key is empty. Set AES_MASTER_KEY in environment. "
                "No insecure fallback is provided."
            )
        return hashlib.pbkdf2_hmac(
            "sha256",
            self._master_key,
            salt.encode(),
            iterations=100_000,
            dklen=32,
        )

    def encrypt(self, plaintext: str, salt: str) -> dict:
        """
        Encrypt a string, return {ciphertext, nonce, tag} as base64 strings.

        Raises:
            RuntimeError: If cryptography library is not installed.
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            raise RuntimeError(
                "cryptography library is required for encryption. "
                "Install with: pip install cryptography"
            )

        key = self.derive_key(salt)
        nonce = os.urandom(12)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        # ciphertext includes the 16-byte auth tag at the end
        ct = ciphertext[:-16]
        tag = ciphertext[-16:]
        return {
            "ciphertext": base64.b64encode(ct).decode(),
            "tag": base64.b64encode(tag).decode(),
            "nonce": base64.b64encode(nonce).decode(),
        }

    def decrypt(self, crypto_dict: dict, salt: str) -> str:
        """
        Decrypt a {ciphertext, nonce, tag} dict back to plaintext.

        Raises:
            RuntimeError: If cryptography library is not installed.
            ValueError: If decryption fails (wrong key or corrupted data).
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            raise RuntimeError(
                "cryptography library is required for decryption. "
                "Install with: pip install cryptography"
            )

        key = self.derive_key(salt)
        ct = base64.b64decode(crypto_dict["ciphertext"])
        tag = base64.b64decode(crypto_dict["tag"])
        nonce = base64.b64decode(crypto_dict["nonce"])
        aesgcm = AESGCM(key)
        try:
            plaintext = aesgcm.decrypt(nonce, ct + tag, None)
            return plaintext.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed — wrong key or corrupted data: {e}")


# ── convenience functions ────────────────────────────────────

_crypto = CredentialCrypto()


def encrypt_credential(plaintext: str, salt: str) -> dict:
    return _crypto.encrypt(plaintext, salt)


def decrypt_credential(crypto_dict: dict, salt: str) -> str:
    return _crypto.decrypt(crypto_dict, salt)


def generate_user_salt() -> str:
    return CredentialCrypto.generate_salt()
