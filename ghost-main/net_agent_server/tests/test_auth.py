"""
Auth 层测试：CredentialCrypto（AES-GCM）与 JWT 权限。
"""

import pytest
from fastapi import HTTPException

from net_agent_common.auth.crypto import CredentialCrypto, generate_user_salt
from net_agent_common.auth.permission import create_token, require_same_user, verify_token
from net_agent_common.config.settings import JWT_SECRET

# ── CredentialCrypto ────────────────────────────────────────────

class TestCredentialCrypto:
    def test_round_trip_encrypt_decrypt(self):
        crypto = CredentialCrypto(master_key="my-master-key")
        salt = generate_user_salt()
        blob = crypto.encrypt("sup3r-secret", salt)

        assert set(blob) == {"ciphertext", "tag", "nonce"}
        assert crypto.decrypt(blob, salt) == "sup3r-secret"

    def test_wrong_key_raises_value_error(self):
        crypto = CredentialCrypto(master_key="correct-key")
        salt = generate_user_salt()
        blob = crypto.encrypt("secret", salt)

        wrong = CredentialCrypto(master_key="wrong-key")
        with pytest.raises(ValueError):
            wrong.decrypt(blob, salt)

    def test_empty_master_key_raises_runtime_error(self, monkeypatch):
        # 环境变量 AES_MASTER_KEY 在 conftest 中已设置，这里强制清空以覆盖空 key 路径
        monkeypatch.setattr("net_agent_common.auth.crypto.AES_MASTER_KEY", "")
        crypto = CredentialCrypto(master_key="")
        with pytest.raises(RuntimeError):
            crypto.derive_key("salt")

    def test_salt_is_unique_hex(self):
        s1, s2 = generate_user_salt(), generate_user_salt()
        assert s1 != s2
        assert len(s1) == 32  # 16 bytes hex


# ── Permission / JWT ────────────────────────────────────────────

class TestPermission:
    def test_jwt_secret_configured(self):
        assert JWT_SECRET  # conftest 已设置

    def test_token_round_trip(self):
        token = create_token("user-123")
        payload = verify_token(token)
        assert payload["sub"] == "user-123"

    def test_tampered_token_rejected(self):
        token = create_token("user-123")
        # 篡改最后一位
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        with pytest.raises(HTTPException) as exc:
            verify_token(tampered)
        assert exc.value.status_code == 401

    def test_require_same_user(self):
        require_same_user("u1", "u1")  # 不抛
        with pytest.raises(HTTPException) as exc:
            require_same_user("u1", "u2")
        assert exc.value.status_code == 403
