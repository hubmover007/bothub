from typing import Generator, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_access_token

# Import models (needed for get_current_user)
from app.models.claim import User

# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)


def get_current_user_id_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UUID]:
    """Get current user ID from JWT token (optional)."""
    if not credentials:
        return None

    payload = decode_access_token(credentials.credentials)
    if payload and "sub" in payload:
        try:
            return UUID(payload["sub"])
        except ValueError:
            return None
    return None


def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UUID:
    """Get current user ID from JWT token (required)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    payload = decode_access_token(credentials.credentials)
    if payload is None or "sub" not in payload:
        raise credentials_exception

    try:
        user_id = UUID(payload["sub"])
    except ValueError:
        raise credentials_exception

    return user_id


def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from database."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


def get_current_user_optional(
    user_id: Optional[UUID] = Depends(get_current_user_id_optional),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from database (optional)."""
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


# Database dependency
db_dependency = Depends(get_db)
