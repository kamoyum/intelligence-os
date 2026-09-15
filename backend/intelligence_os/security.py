from __future__ import annotations

import hmac
import os
import secrets
from pathlib import Path

from fastapi import Header, HTTPException

from .config import settings


def ensure_api_token(path: Path | None = None) -> str:
    path = path or settings.token_path
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        token = path.read_text(encoding="utf-8").strip()
        if token:
            return token
    token = secrets.token_urlsafe(32)
    path.write_text(token + "\n", encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return token


API_TOKEN = ensure_api_token()


def token_matches(candidate: str | None) -> bool:
    if not candidate:
        return False
    return hmac.compare_digest(candidate.strip(), API_TOKEN)


def require_api_token(
    authorization: str | None = Header(default=None),
    x_intelligence_token: str | None = Header(default=None),
) -> None:
    bearer = None
    if authorization and authorization.lower().startswith("bearer "):
        bearer = authorization[7:].strip()
    candidate = bearer or x_intelligence_token
    if not token_matches(candidate):
        raise HTTPException(status_code=401, detail="Invalid or missing Intelligence OS API token")
