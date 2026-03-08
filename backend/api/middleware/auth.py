# api/middleware/auth.py
"""
Supabase JWT authentication for FastAPI.

How it works
------------
1. The mobile app calls Supabase Auth directly (sign-up / sign-in).
2. Supabase returns a signed JWT access token.
3. The mobile app sends the token as:
       Authorization: Bearer <token>
4. This module validates the token using your SUPABASE_JWT_SECRET
   (found in: Supabase Dashboard → Settings → API → JWT Secret).
5. The validated user_id (UUID string) is stored on request.state so
   routers can access it via the `require_auth` dependency.

Environment variable required in backend/.env:
    SUPABASE_JWT_SECRET=<your_jwt_secret>
"""
from __future__ import annotations

import os
from typing import Optional

import jwt  # PyJWT
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False)

JWT_SECRET_ENV = "SUPABASE_JWT_SECRET"
JWT_ALGORITHM = "HS256"


def _get_jwt_secret() -> str:
    secret = os.getenv(JWT_SECRET_ENV)
    if not secret:
        raise RuntimeError(
            f"Missing {JWT_SECRET_ENV} env var. "
            "Add it to backend/.env (Supabase Dashboard → Settings → API → JWT Secret)."
        )
    return secret


def decode_supabase_token(token: str) -> dict:
    """
    Decode and verify a Supabase JWT.  Raises HTTPException on failure.
    """
    try:
        payload = jwt.decode(
            token,
            _get_jwt_secret(),
            algorithms=[JWT_ALGORITHM],
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
