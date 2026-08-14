import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.deps import get_current_user
from backend.models.user import User
from backend.schemas.user import GoogleAuthRequest, AuthTokenResponse, UserResponse, UserUpdate
from backend.services.auth_service import verify_google_id_token, create_jwt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/google", response_model=AuthTokenResponse)
async def google_login(request: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate with Google OpenID Connect ID Token.
    
    Verifies the user's identity claims using Google's public JWKS certificates,
    creates or finds the user in DB, and returns a standard JWT Bearer access token.
    """
    try:
        google_user = verify_google_id_token(request.id_token)
    except Exception as e:
        logger.error("Google authentication failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google authentication failed: {str(e)}",
        )

    # Determine the requested role (default job_seeker)
    requested_role = request.role if request.role in ("job_seeker", "hr") else "job_seeker"

    # Find or create user by immutable google_id (sub)
    result = await db.execute(select(User).where(User.google_id == google_user["google_id"]))
    user = result.scalar_one_or_none()

    if not user:
        # First-time user: Create account
        user = User(
            google_id=google_user["google_id"],
            email=google_user["email"],
            name=google_user["name"],
            picture_url=google_user.get("picture"),
            role=requested_role,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Returning user: Update latest name / avatar from Google
        user.name = google_user["name"]
        user.picture_url = google_user.get("picture")
        user.role = requested_role
        await db.commit()
        await db.refresh(user)

    # Create application JWT Bearer access token
    token = create_jwt(user.id)

    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user's info."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update the authenticated user's profile."""
    if body.name is not None:
        current_user.name = body.name
    if body.picture_url is not None:
        current_user.picture_url = body.picture_url
    if body.skills is not None:
        current_user.skills = body.skills
    if body.role is not None and body.role in ("job_seeker", "hr"):
        current_user.role = body.role
        
    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.get("/config")
async def get_config():
    """Get public configurations, such as Google Client ID."""
    from backend.config import settings
    return {
        "google_client_id": settings.GOOGLE_CLIENT_ID
    }
