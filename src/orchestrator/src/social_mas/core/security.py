from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from social_mas.core.config import Settings


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    subject: str
    scopes: tuple[str, ...]


class JWTVerifier:
    """Small JWT verification service with explicit algorithm checks."""

    def __init__(self, settings: Settings) -> None:
        self._secret = settings.jwt_secret
        self._algorithm = settings.jwt_algorithm

    def verify(self, credentials: HTTPAuthorizationCredentials | None) -> Principal:
        if credentials is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token is required")
        try:
            header = jwt.get_unverified_header(credentials.credentials)
            if header.get("alg") != self._algorithm:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid JWT algorithm")
            payload: dict[str, Any] = jwt.decode(
                credentials.credentials,
                self._secret,
                algorithms=[self._algorithm],
                options={"require": ["sub"]},
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
        scopes = tuple(str(scope) for scope in payload.get("scopes", []))
        return Principal(subject=str(payload["sub"]), scopes=scopes)

