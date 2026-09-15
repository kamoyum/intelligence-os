import base64
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def extension_id_from_key(key: str) -> str:
    raw = base64.b64decode(key)
    digest = hashlib.sha256(raw).digest()[:16]
    alphabet = "abcdefghijklmnop"
    return "".join(alphabet[b >> 4] + alphabet[b & 0x0F] for b in digest)


def test_extension_has_stable_native_id():
    manifest = json.loads((ROOT / "extension" / "manifest.json").read_text(encoding="utf-8"))
    assert "nativeMessaging" in manifest["permissions"]
    assert extension_id_from_key(manifest["key"]) == "aepgddfmbohnfpdddicpoomiophabban"


def test_native_host_ping():
    path = ROOT / "native_host" / "host.py"
    spec = importlib.util.spec_from_file_location("ios_native_host", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    result = mod.handle({"action": "ping"})
    assert result["ok"] is True
    assert result["bridge"] == "native"
    assert result["version"] == "0.7.2-alpha"


def test_native_host_rejects_privileged_route():
    path = ROOT / "native_host" / "host.py"
    spec = importlib.util.spec_from_file_location("ios_native_host_restrict", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    result = mod.request_core({"action":"request", "path":"/api/connectors/google/sync", "method":"POST", "body":{}})
    assert result["status"] == 403


def test_native_installer_writes_runtime_config(tmp_path):
    path = ROOT / "native_host" / "install_host.py"
    spec = importlib.util.spec_from_file_location("ios_native_installer", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    mod.INSTALL_ROOT = tmp_path
    cfg = mod.write_host_config()
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert data["core_origin"] == "http://127.0.0.1:8765"
    assert data["token_path"].endswith("backend/data/local_api_token.txt")


def test_native_host_configures_windows_binary_stdio():
    text = (ROOT / "native_host" / "host.py").read_text(encoding="utf-8")
    assert "msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)" in text
    assert "msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)" in text
    assert "_configure_stdio_binary_mode()" in text
