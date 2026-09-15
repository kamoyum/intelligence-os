from __future__ import annotations

import importlib
import os
import socket
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
DATA = BACKEND / "data"

REQUIRED = {
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "httpx": "httpx",
    "pypdf": "pypdf",
}
OPTIONAL = {
    "openai": "OpenAI reasoning/research/embeddings",
    "googleapiclient": "Google connectors",
    "google_auth_oauthlib": "Google OAuth",
}


def check_python() -> tuple[bool, str]:
    ok = sys.version_info >= (3, 11)
    return ok, f"Python {sys.version.split()[0]} (need 3.11+)"


def check_imports() -> tuple[bool, list[str], list[str]]:
    missing_required: list[str] = []
    missing_optional: list[str] = []
    for module in REQUIRED:
        try:
            importlib.import_module(module)
        except Exception:
            missing_required.append(module)
    for module, label in OPTIONAL.items():
        try:
            importlib.import_module(module)
        except Exception:
            missing_optional.append(label)
    return not missing_required, missing_required, missing_optional


def check_data_dir() -> tuple[bool, str]:
    try:
        DATA.mkdir(parents=True, exist_ok=True)
        probe = DATA / ".preflight-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True, str(DATA)
    except Exception as exc:
        return False, f"{DATA}: {exc}"


def check_port(port: int = 8765) -> tuple[bool, str]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(0.25)
        in_use = s.connect_ex(("127.0.0.1", port)) == 0
        return True, "already in use by a local service (Core may already be running)" if in_use else "available"
    finally:
        s.close()


def main() -> int:
    ok_py, py_msg = check_python()
    ok_imp, missing_required, missing_optional = check_imports()
    ok_data, data_msg = check_data_dir()
    _ok_port, port_msg = check_port()

    print("Intelligence OS preflight")
    print(f"[{'OK' if ok_py else 'FAIL'}] {py_msg}")
    print(f"[{'OK' if ok_imp else 'FAIL'}] required imports" + (f": missing {', '.join(missing_required)}" if missing_required else ""))
    print(f"[{'OK' if ok_data else 'FAIL'}] writable data dir: {data_msg}")
    print(f"[INFO] loopback port 8765: {port_msg}")
    try:
        pc = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True, timeout=20)
        print(f"[{'OK' if pc.returncode == 0 else 'WARN'}] pip dependency consistency" + ("" if pc.returncode == 0 else f": {(pc.stdout + pc.stderr).strip()}"))
    except Exception as exc:
        print(f"[WARN] pip check unavailable: {exc}")
    if missing_optional:
        print("[INFO] optional capabilities unavailable until installed/configured: " + ", ".join(missing_optional))
    if os.getenv("OPENAI_API_KEY"):
        print("[INFO] OPENAI_API_KEY detected in process environment (value not printed).")
    else:
        print("[INFO] No OPENAI_API_KEY in process environment; Mock/local modes remain available.")
    return 0 if ok_py and ok_imp and ok_data else 1


if __name__ == "__main__":
    raise SystemExit(main())
