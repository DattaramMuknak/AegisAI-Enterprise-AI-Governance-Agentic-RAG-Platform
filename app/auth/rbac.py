"""
Lightweight JWT authentication + role-based access control.

Roles: admin (full access), analyst (chat + view audit/dashboard),
viewer (dashboard read-only). Kept intentionally simple — swap for
OAuth2/OIDC + an identity provider in a real enterprise deployment.
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

ROLE_HIERARCHY = {"admin": 3, "analyst": 2, "viewer": 1}


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as err:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token") from err


def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> dict:
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return decode_token(token)


def require_role(minimum_role: str):
    """Dependency factory: require_role('admin') / require_role('analyst')."""

    def dependency(user: dict = Depends(get_current_user)) -> dict:
        user_level = ROLE_HIERARCHY.get(user.get("role", "viewer"), 0)
        required_level = ROLE_HIERARCHY.get(minimum_role, 99)
        if user_level < required_level:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role permissions")
        return user

    return dependency
