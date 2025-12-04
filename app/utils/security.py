import hmac
import hashlib
from fastapi import Header, HTTPException, Depends
from jose import jwt, JWTError
from app.config import settings

class User:
    def __init__(self, user_id: str, role: str, username: str = ""):
        self.id = user_id       # unique UUID
        self.role = role        # user/admin
        self.username = username  # optional display name

def get_current_user(authorization: str = Header(default=None, alias="Authorization")) -> User:
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])

        # Always present
        user_id = payload.get("sub")
        role = payload.get("role", "user")

        # Optional field
        username = payload.get("username") or ""

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        return User(user_id=user_id, role=role, username=username)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return user

def require_user(user: User = Depends(get_current_user)) -> User:
    return user

def verify_hmac_signature(raw_body: bytes, signature_header: str) -> bool:
    if not signature_header:
        return False
    mac = hmac.new(settings.WEBHOOK_SECRET.encode(), msg=raw_body, digestmod=hashlib.sha256)
    expected = mac.hexdigest()
    return hmac.compare_digest(signature_header, expected)
