# api/middleware/auth.py
"""
Supabase JWT authentication for FastAPI.

How it works
------------
1. The mobile app calls Supabase Auth directly (sign-up / sign-in).
2. Supabase returns a signed JWT access token (algorithm: ES256).
3. The mobile app sends the token as:
       Authorization: Bearer <token>
4. This module validates the token using Supabase's public JWKS endpoint
   (SUPABASE_URL/auth/v1/.well-known/jwks.json). Keys are cached in-process.
5. The validated user_id (UUID string) is stored on request.state so
   routers can access it via the `require_auth` dependency.

Environment variable required in backend/.env:
    SUPABASE_URL=https://<your-project-ref>.supabase.co
"""
from __future__ import annotations

import os
from typing import Optional

import jwt
from jwt import PyJWKClient
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False)

_jwks_client: Optional[PyJWKClient] = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
        if not supabase_url:
            raise RuntimeError(
                "Missing SUPABASE_URL env var. "
                "Add it to backend/.env (e.g. https://<ref>.supabase.co)."
            )
        _jwks_client = PyJWKClient(f"{supabase_url}/auth/v1/.well-known/jwks.json")
    return _jwks_client


def decode_supabase_token(token: str) -> dict:
    """
    Decode and verify a Supabase JWT (ES256).  Raises HTTPException on failure.
    """
    try:
        client = _get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            options={"verify_aud": False},  # Supabase tokens use 'authenticated' audience
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please sign in again.",
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )


async def require_auth(request: Request) -> str:
    """
    FastAPI dependency that extracts and validates the Bearer token.
    Returns the authenticated user_id (UUID string, the JWT `sub` claim).

    Usage in a router:
        @router.get("/me")
        def me(user_id: str = Depends(require_auth)):
            ...
    """
    credentials: Optional[HTTPAuthorizationCredentials] = await _bearer(request)
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header.",
        )
    payload = decode_supabase_token(credentials.credentials)
    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' claim.",
        )
    return user_id
