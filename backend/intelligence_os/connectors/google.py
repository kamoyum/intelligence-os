from __future__ import annotations

import base64
import json
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ..config import settings

SAFE_SCOPES = [
    "https://www.googleapis.com/auth/calendar.events.readonly",
    "https://www.googleapis.com/auth/drive.file",
]
FULL_PERSONAL_SCOPES = [
    "https://www.googleapis.com/auth/calendar.events.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
]
STATE_FILE = settings.data_dir / "google_oauth_state.json"


def scopes() -> list[str]:
    if settings.google_mode == "personal_full":
        return FULL_PERSONAL_SCOPES
    if settings.google_mode == "safe":
        return SAFE_SCOPES
    return []


def available() -> bool:
    return bool(scopes()) and settings.google_client_secret_file.exists()


def credentials_exist() -> bool:
    return settings.google_token_file.exists()


def _imports():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    return Credentials, Flow, build


def start_oauth() -> str:
    if not available():
        raise RuntimeError("Google connector is disabled or google_client_secret.json is missing")
    _, Flow, _ = _imports()
    flow = Flow.from_client_secrets_file(
        str(settings.google_client_secret_file),
        scopes=scopes(),
        redirect_uri=f"{settings.core_origin}/oauth/google/callback",
    )
    state = secrets.token_urlsafe(24)
    auth_url, returned_state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    STATE_FILE.write_text(json.dumps({"state": returned_state, "created": time.time()}), encoding="utf-8")
    try:
        os.chmod(STATE_FILE, 0o600)
    except OSError:
        pass
    return auth_url


def finish_oauth(full_url: str, state: str) -> None:
    if not STATE_FILE.exists():
        raise RuntimeError("OAuth state not found")
    payload = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    if payload.get("state") != state or time.time() - float(payload.get("created", 0)) > 900:
        raise RuntimeError("OAuth state is invalid or expired")
    _, Flow, _ = _imports()
    flow = Flow.from_client_secrets_file(
        str(settings.google_client_secret_file),
        scopes=scopes(),
        redirect_uri=f"{settings.core_origin}/oauth/google/callback",
        state=state,
    )
    flow.fetch_token(authorization_response=full_url)
    creds = flow.credentials
    settings.google_token_file.write_text(creds.to_json(), encoding="utf-8")
    try:
        os.chmod(settings.google_token_file, 0o600)
    except OSError:
        pass
    STATE_FILE.unlink(missing_ok=True)


def creds():
    Credentials, _, _ = _imports()
    if not settings.google_token_file.exists():
        raise RuntimeError("Google is not connected")
    return Credentials.from_authorized_user_file(str(settings.google_token_file), scopes=scopes())


def status() -> dict[str, Any]:
    return {
        "mode": settings.google_mode,
        "configured": available(),
        "connected": credentials_exist(),
        "scopes": scopes(),
        "warning": (
            "personal_full uses restricted Gmail/Drive scopes and is intended for private testing. Public distribution requires Google verification and may require a security assessment."
            if settings.google_mode == "personal_full" else
            "safe mode uses narrow scopes; Drive access is limited to files explicitly available to the app."
        ),
    }


def list_calendar(days: int = 14, max_results: int = 50) -> list[dict[str, Any]]:
    _, _, build = _imports()
    service = build("calendar", "v3", credentials=creds(), cache_discovery=False)
    now = datetime.now(timezone.utc)
    result = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=(now + timedelta(days=days)).isoformat(),
        singleEvents=True,
        orderBy="startTime",
        maxResults=max_results,
    ).execute()
    out = []
    for e in result.get("items", []):
        out.append({
            "id": e.get("id"),
            "summary": e.get("summary", "(no title)"),
            "start": e.get("start", {}).get("dateTime") or e.get("start", {}).get("date"),
            "end": e.get("end", {}).get("dateTime") or e.get("end", {}).get("date"),
            "location": e.get("location", ""),
            "description": e.get("description", ""),
            "htmlLink": e.get("htmlLink", ""),
        })
    return out


def list_drive(max_results: int = 30) -> list[dict[str, Any]]:
    _, _, build = _imports()
    service = build("drive", "v3", credentials=creds(), cache_discovery=False)
    result = service.files().list(
        pageSize=max_results,
        orderBy="modifiedTime desc",
        fields="files(id,name,mimeType,modifiedTime,webViewLink,description)",
    ).execute()
    return result.get("files", [])


def _decode_b64(data: str) -> str:
    try:
        return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")
    except Exception:
        return ""


def _text_from_payload(payload: dict[str, Any]) -> str:
    mime = payload.get("mimeType", "")
    body = payload.get("body", {}).get("data")
    if body and mime.startswith("text/plain"):
        return _decode_b64(body)
    parts = payload.get("parts", []) or []
    texts = [_text_from_payload(p) for p in parts]
    return "\n".join(t for t in texts if t)


def list_gmail(max_results: int = 20) -> list[dict[str, Any]]:
    if settings.google_mode != "personal_full":
        raise RuntimeError("Gmail reading requires INTELLIGENCE_GOOGLE_MODE=personal_full")
    _, _, build = _imports()
    service = build("gmail", "v1", credentials=creds(), cache_discovery=False)
    result = service.users().messages().list(userId="me", maxResults=max_results, q="newer_than:14d").execute()
    out = []
    for item in result.get("messages", []):
        msg = service.users().messages().get(userId="me", id=item["id"], format="full").execute()
        headers = {h.get("name", "").lower(): h.get("value", "") for h in msg.get("payload", {}).get("headers", [])}
        body = _text_from_payload(msg.get("payload", {}))[:12000]
        out.append({
            "id": msg.get("id"),
            "threadId": msg.get("threadId"),
            "subject": headers.get("subject", "(no subject)"),
            "from": headers.get("from", ""),
            "date": headers.get("date", ""),
            "snippet": msg.get("snippet", ""),
            "body": body,
        })
    return out
