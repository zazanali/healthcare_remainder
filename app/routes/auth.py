import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from jose import jwt
from app.config import settings

router = APIRouter()

# Schemas
class LoginRequest(BaseModel):
    username: str = Field(
        description="Username for authentication",
        min_length=3,
        max_length=50,
        examples=["string"]
    )
    password: str = Field(
        description="User's password",
        min_length=4,
        examples=["string"]
    )

class TokenResponse(BaseModel):
    access_token: str = Field(
        description="JWT access token",
        examples=["eyJhbGciOiJIUzI1NiIs..."]
    )
    token_type: str = Field(
        description="Type of the token",
        examples=["bearer"],
        pattern="^bearer$"
    )

# Fake user store for demo (UUID assigned per user)
FAKE_USERS = {
    "zazan": {"password": "1234", "role": "admin", "id": str(uuid.uuid4())},
    "areesha": {"password": "1234", "role": "user", "id": str(uuid.uuid4())},
}

@router.post(
    "/token",
    tags=["auth"],
    summary="Create access token",
    response_model=TokenResponse,
    responses={
        200: {"description": "Successfully created access token"},
        401: {"description": "Invalid username or password"}
    }
)
def login(data: LoginRequest):
    user = FAKE_USERS.get(data.username)
    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    payload = {
        "sub": user["id"],          # UUID — unique user identity
        "username": data.username,  # optional, for display
        "role": user["role"],       # role for RBAC
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
    return {"access_token": token, "token_type": "bearer"}
