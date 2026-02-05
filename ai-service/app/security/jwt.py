from app.core.config import settings
from fastapi import Header, HTTPException, status
from jose import JWTError, jwt


def verify_jwt_token(authorization: str = Header(...)):
    """
    Expected header:
    Authorization: Bearer <token>
    """

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    return payload
