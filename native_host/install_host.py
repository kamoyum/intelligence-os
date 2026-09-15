from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
from pathlib import Path

HOST_NAME = "com.intelligenceos.native"
EXTENSION_ID = "aepgddfmbohnfpdddicpoomiophabban"
ROOT = Path(__file__).resolve().parents[1]
HOST_SCRIPT = ROOT / "native_host" / "host.py"
INSTALL_ROOT = Path.home() / ".intelligence-os" / "native-host"


def make_launcher() -> Path:
    INSTALL_ROOT.mkdir(parents=True, exist_ok=True)
    system = platform.system()
    if system == "Windows":
        # Chrome on Windows expects a native executable. If PyInstaller is available,
        # create a small single-file host. Otherwise the extension will safely fall
        # back to loopback HTTP mode.
        exe = INSTALL_ROOT / "intelligence_os_native.exe"
        pyinstaller = shutil.which("pyinstaller")
        if not pyinstaller:
            raise RuntimeError(
                "Native Messaging on Windows needs PyInstaller for this source build. "
                "Run `pip install pyinstaller`, retry, or use the built-in localhost fallback."
            )
        work = INSTALL_ROOT / "build"
        dist = INSTALL_ROOT / "dist"
        subprocess.run(
            [pyinstaller, "--onefile", "--noconfirm", "--clean", "--name", "intelligence_os_native",
             "--distpath", str(dist), "--workpath", str(work), "--specpath", str(work), str(HOST_SCRIPT)],
            check=True,
        )
        built = dist / "intelligence_os_native.exe"
        shutil.copy2(built, exe)
        return exe

    launcher = INSTALL_ROOT / "intelligence_os_native"
    content = f"#!/bin/sh\nexec {json.dumps(sys.executable)} {json.dumps(str(HOST_SCRIPT))}\n"
    launcher.write_text(content, encoding="utf-8")
    launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return launcher


def write_host_config() -> Path:
    INSTALL_ROOT.mkdir(parents=True, exist_ok=True)
    path = INSTALL_ROOT / "config.json"
    data = {
        "token_path": str((ROOT / "backend" / "data" / "local_api_token.txt").resolve()),
        "core_origin": os.getenv("INTELLIGENCE_CORE_ORIGIN", "http://127.0.0.1:8765"),
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path

def manifest(path: Path) -> dict:
    return {
        "name": HOST_NAME,
        "description": "Intelligence OS local Native Messaging bridge",
        "path": str(path.resolve()),
        "type": "stdio",
        "allowed_origins": [f"chrome-extension://{EXTENSION_ID}/"],
    }


def manifest_locations(browser: str) -> list[Path]:
    system = platform.system()
    home = Path.home()
    out: list[Path] = []
    if system == "Darwin":
        if browser in {"chrome", "both"}:
            out.append(home / "Library/Application Support/Google/Chrome/NativeMessagingHosts" / f"{HOST_NAME}.json")
        if browser in {"edge", "both"}:
            out.append(home / "Library/Application Support/Microsoft Edge/NativeMessagingHosts" / f"{HOST_NAME}.json")
    elif system == "Linux":
        if browser in {"chrome", "both"}:
            out.append(home / ".config/google-chrome/NativeMessagingHosts" / f"{HOST_NAME}.json")
            out.append(home / ".config/chromium/NativeMessagingHosts" / f"{HOST_NAME}.json")
        if browser in {"edge", "both"}:
            out.append(home / ".config/microsoft-edge/NativeMessagingHosts" / f"{HOST_NAME}.json")
    elif system == "Windows":
        # The manifest can live in our private install folder; registry points to it.
        out.append(INSTALL_ROOT / f"{HOST_NAME}.json")
    return out


def install_windows_registry(manifest_path: Path, browser: str) -> None:
    import winreg
    roots = []
    if browser in {"chrome", "both"}:
        roots.append(fr"Software\Google\Chrome\NativeMessagingHosts\{HOST_NAME}")
    if browser in {"edge", "both"}:
        roots.append(fr"Software\Microsoft\Edge\NativeMessagingHosts\{HOST_NAME}")
    for key_path in roots:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(manifest_path.resolve()))
        winreg.CloseKey(key)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--browser", choices=["chrome", "edge", "both"], default="both")
    args = p.parse_args()

    launcher = make_launcher()
    write_host_config()
    data = manifest(launcher)
    locations = manifest_locations(args.browser)
    if not locations:
        print(f"Unsupported platform: {platform.system()}", file=sys.stderr)
        return 2
    for loc in locations:
        loc.parent.mkdir(parents=True, exist_ok=True)
        loc.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Installed manifest: {loc}")
    if platform.system() == "Windows":
        install_windows_registry(locations[0], args.browser)
        print("Registered Native Messaging host in HKCU.")
    print(f"Extension ID: {EXTENSION_ID}")
    print("Reload the unpacked Intelligence OS extension after installation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
