from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from intelligence_os import __version__
OUT = ROOT.parent / f"intelligence-os-v{__version__}.zip"
EXCLUDED_PARTS = {".venv", "__pycache__", ".pytest_cache", ".git"}
EXCLUDED_NAMES = {
    "intelligence.db", "intelligence.db-shm", "intelligence.db-wal",
    "local_api_token.txt", "google_token.json", "google_client_secret.json", ".env",
}


def run(cmd: list[str], *, cwd: Path = ROOT) -> None:
    print("+", " ".join(cmd))
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "backend") + os.pathsep + env.get("PYTHONPATH", "")
    subprocess.run(cmd, cwd=str(cwd), env=env, check=True)


def include(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDED_PARTS for part in rel.parts):
        return False
    if path.name in EXCLUDED_NAMES or path.suffix in {".pyc", ".pyo"}:
        return False
    if "backend/data" in rel.as_posix() and path.name != ".gitkeep":
        return False
    return path.is_file()


def verify_tree() -> None:
    run([sys.executable, "-m", "compileall", "-q", "backend", "desktop", "native_host", "scripts"])
    run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT / "backend")
    run([sys.executable, str(ROOT / "scripts" / "verify_version_sync.py")])
    run([sys.executable, str(ROOT / "scripts" / "public_repo_audit.py")])
    for script in (
        "simulate_kernel.py",
        "simulate_current_research.py",
        "simulate_http_research.py",
        "simulate_outcome_learning.py",
        "simulate_http_learning.py",
        "simulate_cognitive_guardrails.py",
        "simulate_observability.py",
        "benchmark_kernel.py",
        "benchmark_redteam.py",
        "benchmark_development_governance.py",
        "simulate_useful_automation.py",
    ):
        run([sys.executable, str(ROOT / "scripts" / script)])


def build() -> Path:
    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(ROOT.rglob("*")):
            if include(p):
                zf.write(p, arcname=f"{ROOT.name}/{p.relative_to(ROOT)}")
    return OUT


def verify_archive(path: Path) -> None:
    with zipfile.ZipFile(path) as zf:
        bad = []
        for name in zf.namelist():
            low = name.lower()
            if any(x in low for x in ("__pycache__", ".pyc", "intelligence.db", "local_api_token.txt", "google_token.json", "google_client_secret.json")):
                bad.append(name)
        if bad:
            raise SystemExit("release archive contains excluded artifacts: " + ", ".join(bad[:10]))
    print(f"release archive verified: {path}")


if __name__ == "__main__":
    verify_tree()
    out = build()
    verify_archive(out)
    print(out)
