#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import struct
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL_CONFIG = Path.home() / ".intelligence-os" / "native-host" / "config.json"

def _installed_config() -> dict:
    try:
        return json.loads(INSTALL_CONFIG.read_text(encoding="utf-8"))
    except Exception:
        return {}

_CONFIG = _installed_config()
DATA = ROOT / "backend" / "data"
TOKEN_FILE = Path(os.getenv("INTELLIGENCE_TOKEN_PATH") or _CONFIG.get("token_path") or (DATA / "local_api_token.txt"))
CORE = str(os.getenv("INTELLIGENCE_CORE_ORIGIN") or _CONFIG.get("core_origin") or "http://127.0.0.1:8765").rstrip("/")
MAX_MESSAGE = 4 * 1024 * 1024
MAX_OUTPUT = 1024 * 1024


def _configure_stdio_binary_mode() -> None:
    """Chrome Native Messaging requires binary stdio on Windows.

    O_TEXT may translate newlines and corrupt the 32-bit length-prefixed protocol.
    macOS/Linux already expose byte streams without this translation.
    """
    if os.name != "nt":
        return
    import msvcrt  # Windows-only
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

# The browser companion gets only the minimum Core surface it needs.
# Connector sync, approvals, audit, OAuth and other authority-bearing routes are intentionally excluded.
ALLOWED_ROUTES = {
    ("GET", "/api/health"),
    ("GET", "/api/memories"),
    ("GET", "/api/attention"),
    ("GET", "/api/attention/queue"),
    ("GET", "/api/brief"),
    ("GET", "/api/skills"),
    ("GET", "/api/skills/runs"),
    ("GET", "/api/system/evals"),
    ("GET", "/api/feedback/summary"),
    ("GET", "/api/actions/specs"),
    ("GET", "/api/actions"),
    ("GET", "/api/claims"),
    ("GET", "/api/knowledge/status"),
    ("GET", "/api/research/runs"),
    ("GET", "/api/learning/status"),
    ("GET", "/api/learning/due"),
    ("GET", "/api/goals"),
    ("POST", "/api/capture"),
    ("POST", "/api/plan"),
    ("POST", "/api/ask"),
    ("POST", "/api/feedback"),
    ("POST", "/api/verify"),
    ("POST", "/api/research/verify"),
}


def read_message() -> dict | None:
    raw = sys.stdin.buffer.read(4)
    if not raw:
        return None
    if len(raw) != 4:
        raise RuntimeError("invalid native message header")
    length = struct.unpack("<I", raw)[0]
    if length <= 0 or length > MAX_MESSAGE:
        raise RuntimeError("native message too large")
    payload = sys.stdin.buffer.read(length)
    if len(payload) != length:
        raise RuntimeError("truncated native message")
    return json.loads(payload.decode("utf-8"))


def write_message(obj: dict) -> None:
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    if len(data) > MAX_OUTPUT:
        data = json.dumps({"ok": False, "status": 502, "error": "Native host response exceeded Chrome's 1 MiB limit"}).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(data)))
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


def token() -> str:
    try:
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def request_core(msg: dict) -> dict:
    path = str(msg.get("path") or "/api/health")
    if not path.startswith("/") or ".." in path:
        return {"ok": False, "status": 400, "error": "invalid path"}
    method = str(msg.get("method") or "GET").upper()
    if method not in {"GET", "POST"}:
        return {"ok": False, "status": 405, "error": "method not allowed"}
    route = path.split("?", 1)[0]
    if (method, route) not in ALLOWED_ROUTES:
        return {"ok": False, "status": 403, "error": "route not allowed through browser bridge"}
    body = msg.get("body")
    data = None
    headers = {"Accept": "application/json"}
    t = token()
    if t:
        headers["Authorization"] = f"Bearer {t}"
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(CORE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read().decode("utf-8")
            parsed = json.loads(raw) if raw else {}
            return {"ok": True, "status": r.status, "data": parsed}
    except urllib.error.HTTPError as exc:
        try:
            parsed = json.loads(exc.read().decode("utf-8"))
        except Exception:
            parsed = {"detail": str(exc)}
        return {"ok": False, "status": exc.code, "data": parsed}
    except Exception as exc:
        return {"ok": False, "status": 503, "error": f"Core unavailable: {type(exc).__name__}: {exc}"}


def handle(msg: dict) -> dict:
    action = msg.get("action", "request")
    if action == "ping":
        return {"ok": True, "bridge": "native", "version": "0.7.2-alpha"}
    if action == "request":
        return request_core(msg)
    return {"ok": False, "status": 400, "error": "unknown action"}


def main() -> None:
    _configure_stdio_binary_mode()
    while True:
        try:
            msg = read_message()
            if msg is None:
                return
            write_message(handle(msg))
        except Exception as exc:
            try:
                write_message({"ok": False, "status": 500, "error": f"Native host error: {type(exc).__name__}: {exc}"})
            except Exception:
                return


if __name__ == "__main__":
    main()
