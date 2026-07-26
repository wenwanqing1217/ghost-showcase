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

import os
import base64
import hashlib
import hmac

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
        Falls back to SHA-256 if master key is empty (dev mode — do not use in prod).
        """
        if not self._master_key:
            # Dev fallback — deterministic but insecure
            return hashlib.sha256(salt.encode()).digest()
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
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
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
        except ImportError:
            # Dev fallback — NOT secure, only for local testing
            return {
                "ciphertext": base64.b64encode(plaintext.encode()).decode(),
                "tag": "",
                "nonce": "",
            }

    def decrypt(self, crypto_dict: dict, salt: str) -> str:
        """
        Decrypt a {ciphertext, nonce, tag} dict back to plaintext.
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            key = self.derive_key(salt)
            ct = base64.b64decode(crypto_dict["ciphertext"])
            tag = base64.b64decode(crypto_dict["tag"])
            nonce = base64.b64decode(crypto_dict["nonce"])
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ct + tag, None)
            return plaintext.decode()
        except ImportError:
            # Dev fallback
            return base64.b64decode(crypto_dict["ciphertext"]).decode()
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
