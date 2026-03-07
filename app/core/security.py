from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import hashlib
import secrets
from app.core.config import settings
from datetime import datetime, timedelta, timezone

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


# ─── Refresh Token Utilities ────────────────────────────────────────────────

def create_refresh_token() -> str:
    """
    Generate a cryptographically secure random refresh token.

    Why NOT a JWT here?
      - Refresh tokens are long-lived and must be revocable.
      - A random opaque string (stored hashed in DB) lets us invalidate any
        single token without rotating SECRET_KEY for everyone.

    Returns:
        A 64-byte URL-safe random string (86 characters when base64-encoded).
    """
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    """
    Hash a refresh token with SHA-256 for safe storage in the database.

    Why SHA-256 (not bcrypt)?
      - Refresh tokens are already cryptographically random (high entropy),
        so a fast hash is safe — dictionary/brute-force attacks are infeasible.
      - bcrypt is intentionally slow and is only needed for low-entropy inputs
        like user passwords.

    Args:
        token: Raw refresh token string.

    Returns:
        64-character hex digest (SHA-256 hash).
    """
    return hashlib.sha256(token.encode()).hexdigest()


def refresh_token_expires_at() -> datetime:
    """Return the UTC datetime when a new refresh token should expire."""
    return datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
