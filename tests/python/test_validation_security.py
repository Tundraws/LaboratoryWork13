from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError

from social_mas.core.config import Settings
from social_mas.core.security import JWTVerifier
from social_mas.schemas import AnalyzeRequest


def test_analyze_request_rejects_short_query() -> None:
    with pytest.raises(ValidationError):
        AnalyzeRequest(query="x", limit=5)


def test_analyze_request_rejects_limit_out_of_range() -> None:
    with pytest.raises(ValidationError):
        AnalyzeRequest(query="соцсети", limit=100)


def test_jwt_verifier_accepts_valid_token() -> None:
    settings = Settings(jwt_secret="local-secret-for-tests", jwt_algorithm="HS256")
    token = jwt.encode(
        {"sub": "student", "scopes": ["run:analysis"], "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    principal = JWTVerifier(settings).verify(HTTPAuthorizationCredentials(scheme="Bearer", credentials=token))

    assert principal.subject == "student"
    assert principal.scopes == ("run:analysis",)


def test_jwt_verifier_rejects_missing_token() -> None:
    verifier = JWTVerifier(Settings(jwt_secret="local-secret-for-tests"))

    with pytest.raises(HTTPException) as exc_info:
        verifier.verify(None)

    assert exc_info.value.status_code == 401

