from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps import get_current_user
from backend.models.user import User
from backend.schemas.user import GoogleAuthRequest, AuthTokenResponse, UserResponse
from backend.services.auth_service import exchange_google_code, create_jwt

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/google", response_model=AuthTokenResponse)
async def google_login(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate with Google OAuth authorization code.
    
    Exchanges the code for user info, creates or finds the user in DB,
    and returns a JWT token.
    """
    try:
        google_user = await exchange_google_code(request.code)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to authenticate with Google: {str(e)}",
        )

    # Determine the requested role (default job_seeker)
    requested_role = request.role if request.role in ("job_seeker", "hr") else "job_seeker"

    # Find or create user
    user = db.query(User).filter(User.google_id == google_user["google_id"]).first()
    if not user:
        user = User(
            google_id=google_user["google_id"],
            email=google_user["email"],
            name=google_user["name"],
            picture_url=google_user.get("picture"),
            role=requested_role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update profile info and role on each login
        user.name = google_user["name"]
        user.picture_url = google_user.get("picture")
        user.role = requested_role
        db.commit()
        db.refresh(user)

    # Create JWT
    token = create_jwt(user.id)

    return AuthTokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user's info."""
    return UserResponse.model_validate(current_user)

from backend.schemas.user import UserUpdate

@router.put("/me", response_model=UserResponse)
def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
        
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)
