import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


class SessionContainer(object):
    """dummy class"""

    pass


bearer_scheme = HTTPBearer()


def verify_session(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """dummy function"""

    def inner_function():
        """dummy function"""
        return SessionContainer()

    return inner_function


def authenticate_token(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    secret_token = "TK11"
    if not secrets.compare_digest(credentials.credentials, secret_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    return credentials.credentials
