"""
Multi-user Permission & Isolation
===================================
Every request to /v1/net/* must carry a valid JWT.
The JWT subject is used as the user_id for row-level data isolation.

Integration point:
  - Alpha-ID issues the JWT during login
  - Net-Agent verifies it using the shared secret
  - No direct user/password handling here
"""

import time
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer

from config.settings import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_HOURS

security = HTTPBearer()


def create_token(user_id: str, extra_claims: dict = None) -> str:
    """Create a JWT for a given user. (Usually called by Alpha-ID, not here.)"""
    try:
        from jose import jwt
        payload = {
            "sub": user_id,
            "iat": int(time.time()),
            "exp": int(time.time()) + JWT_EXPIRE_HOURS * 3600,
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    except ImportError:
        raise RuntimeError("python-jose not installed: pip install python-jose")


def verify_token(token: str) -> dict:
    """Verify a JWT and return its payload. Raises HTTPException on failure."""
    try:
        from jose import jwt, JWTError
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def get_current_user(request: Request) -> str:
    """
    FastAPI dependency: extract and validate the JWT, return user_id.
    Usage in routes::

        @app.get("/status")
        async def get_status(user_id: str = Depends(get_current_user)):
            ...
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = auth[7:]
    payload = verify_token(token)
    return payload["sub"]


def require_same_user(user_id: str, request_user_id: str) -> None:
    """Enforce that the requesting user can only access their own data."""
    if user_id != request_user_id:
        raise HTTPException(status_code=403, detail="Access denied: not your data")
