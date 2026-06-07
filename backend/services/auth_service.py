from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from jose import jwt, JWTError

from backend.config import settings


async def exchange_google_code(code_or_token: str) -> dict:
    """Exchange Google authorization code or verify access token for user info.
    
    Returns dict with: google_id, email, name, picture
    """
    async with httpx.AsyncClient() as client:
        # Check if we should use implicit flow (no client secret configured, or token starts with 'ya29.')
        if not settings.GOOGLE_CLIENT_SECRET or code_or_token.startswith("ya29."):
            access_token = code_or_token
        else:
            # Exchange the auth code for tokens
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code_or_token,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": "postmessage",  # For popup-based flow
                    "grant_type": "authorization_code",
                },
            )
            token_response.raise_for_status()
            tokens = token_response.json()
            access_token = tokens["access_token"]

        # Get user info from Google
        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        userinfo_response.raise_for_status()
        userinfo = userinfo_response.json()

    return {
        "google_id": userinfo["id"],
        "email": userinfo["email"],
        "name": userinfo.get("name", userinfo["email"]),
        "picture": userinfo.get("picture"),
    }


def create_jwt(user_id: str) -> str:
    """Create a JWT token for the given user ID."""
    payload = {
        "sub": user_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_jwt(token: str) -> Optional[dict]:
    """Decode and validate a JWT token. Returns payload or None."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None
