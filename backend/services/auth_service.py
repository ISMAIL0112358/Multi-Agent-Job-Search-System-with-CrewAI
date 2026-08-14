import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from jose import jwt, JWTError

from backend.config import settings

logger = logging.getLogger(__name__)


def verify_google_id_token(token: str) -> dict:
    """Verify a Google OpenID Connect ID Token (JWT) using Google's public JWKS certificates.
    
    Validates token signature, audience, and expiration.
    Returns OpenID claims dict: google_id (sub), email, name, picture
    """
    token_str = token.strip()
    if not token_str:
        raise ValueError("Empty ID token provided.")

    try:
        # Cryptographically verify the ID token signature against Google's public JWKS certificates
        id_info = google_id_token.verify_oauth2_token(
            token_str,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID if settings.GOOGLE_CLIENT_ID else None,
        )

        sub = id_info.get("sub")
        email = id_info.get("email")

        if not sub or not email:
            raise ValueError("ID Token missing required OpenID claims (sub, email).")

        return {
            "google_id": str(sub),
            "email": email,
            "name": id_info.get("name", email),
            "picture": id_info.get("picture"),
        }
    except Exception as e:
        logger.error("OpenID Connect ID Token cryptographic verification failed: %s", e)
        raise ValueError(f"Invalid Google ID Token: {str(e)}")


def create_jwt(user_id: str) -> str:
    """Create an application JWT Bearer access token for the authenticated user ID."""
    payload = {
        "sub": user_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_jwt(token: str) -> Optional[dict]:
    """Decode and validate an application JWT Bearer token."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None
