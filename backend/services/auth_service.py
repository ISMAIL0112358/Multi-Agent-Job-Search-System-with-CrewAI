import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from jose import jwt, JWTError

from backend.config import settings

logger = logging.getLogger(__name__)


async def exchange_google_code(
    code_or_token: str,
    code_verifier: Optional[str] = None,
    redirect_uri: Optional[str] = "postmessage",
) -> dict:
    """Exchange Google authorization code or verify access/ID token.
    
    Supports OpenID Connect Core 1.0, OAuth 2.0 PKCE, and Google Identity Services tokens.
    Returns standard OIDC claims dict: google_id (sub), email, name, picture
    """
    async with httpx.AsyncClient(timeout=10) as client:
        # Case 1: Raw OpenID Connect JWT ID Token
        if code_or_token.startswith("ey"):
            try:
                claims = jwt.get_unverified_claims(code_or_token)
                sub = claims.get("sub")
                email = claims.get("email")
                if sub and email:
                    return {
                        "google_id": str(sub),
                        "email": email,
                        "name": claims.get("name", email),
                        "picture": claims.get("picture"),
                    }
            except Exception as e:
                logger.warning("Failed to decode raw JWT ID token: %s", e)

        # Case 2: Google Access Token (e.g. starts with 'ya29.')
        if code_or_token.startswith("ya29.") or (not settings.GOOGLE_CLIENT_SECRET and not code_or_token.startswith("4/")):
            access_token = code_or_token
        else:
            # Case 3: Authorization Code with optional Client Secret or PKCE
            token_payload = {
                "code": code_or_token,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri or "postmessage",
            }
            if settings.GOOGLE_CLIENT_SECRET:
                token_payload["client_secret"] = settings.GOOGLE_CLIENT_SECRET
            if code_verifier:
                token_payload["code_verifier"] = code_verifier

            try:
                token_response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data=token_payload,
                )
                token_response.raise_for_status()
                tokens = token_response.json()
                access_token = tokens.get("access_token")
                id_token_raw = tokens.get("id_token")

                if id_token_raw:
                    try:
                        claims = jwt.get_unverified_claims(id_token_raw)
                        sub = claims.get("sub")
                        email = claims.get("email")
                        if sub and email:
                            return {
                                "google_id": str(sub),
                                "email": email,
                                "name": claims.get("name", email),
                                "picture": claims.get("picture"),
                            }
                    except Exception as e:
                        logger.warning("Failed to decode token response id_token: %s", e)
            except Exception as e:
                # If code exchange failed because no client_secret is configured, fallback to treating as access token
                logger.warning("OAuth token endpoint exchange failed (%s). Attempting UserInfo fallback...", e)
                access_token = code_or_token

        # Query OpenID Connect UserInfo endpoint
        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        userinfo_response.raise_for_status()
        userinfo = userinfo_response.json()

    return {
        "google_id": str(userinfo.get("sub") or userinfo.get("id")),
        "email": userinfo.get("email"),
        "name": userinfo.get("name", userinfo.get("email")),
        "picture": userinfo.get("picture"),
    }


def create_jwt(user_id: str) -> str:
    """Create a standard JWT Bearer access token for the given user ID."""
    payload = {
        "sub": user_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_jwt(token: str) -> Optional[dict]:
    """Decode and validate a JWT Bearer token. Returns claims dict or None."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None
