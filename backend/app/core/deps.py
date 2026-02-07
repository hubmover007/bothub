from typing import Generator, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_access_token

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


# Database dependency
db_dependency = Depends(get_db)
