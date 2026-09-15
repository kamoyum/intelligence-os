from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"Tkinter is required for the Desktop launcher: {exc}")

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
DATA = BACKEND / "data"
DESKTOP_CONFIG = DATA / "desktop_settings.json"
HOST_INSTALLER = ROOT / "native_host" / "install_host.py"
EXTENSION_DIR = ROOT / "extension"
CORE_URL = "http://127.0.0.1:8765"


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _open_folder(path: Path) -> None:
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif system == "Darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        webbrowser.open(path.as_uri())


def _health(timeout: float = 0.6) -> dict | None:
    try:
        with urllib.request.urlopen(f"{CORE_URL}/api/health", timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


class DesktopApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Intelligence OS Desktop")
        self.root.geometry("760x610")
        self.root.minsize(680, 560)
        self.proc: subprocess.Popen | None = None
        self.settings = _load_json(DESKTOP_CONFIG)
        self._build_ui()
        self._poll()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(350, self.start_core)

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=20)
        outer.pack(fill="both", expand=True)

        title = ttk.Label(outer, text="Intelligence OS", font=("Arial", 22, "bold"))
        title.pack(anchor="w")
        ttk.Label(outer, text="Desktop Core · local-first cognitive infrastructure", foreground="#666").pack(anchor="w", pady=(0, 16))

        status_box = ttk.LabelFrame(outer, text="Core status", padding=12)
        status_box.pack(fill="x")
        self.status_var = tk.StringVar(value="STARTING…")
        self.detail_var = tk.StringVar(value="")
        ttk.Label(status_box, textvariable=self.status_var, font=("Arial", 13, "bold")).pack(anchor="w")
        ttk.Label(status_box, textvariable=self.detail_var).pack(anchor="w", pady=(4, 0))

        buttons = ttk.Frame(outer)
        buttons.pack(fill="x", pady=12)
        ttk.Button(buttons, text="Start Core", command=self.start_core).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Stop Core", command=self.stop_core).pack(side="left", padx=6)
        ttk.Button(buttons, text="Open Console", command=lambda: webbrowser.open(f"{CORE_URL}/console")).pack(side="left", padx=6)
        ttk.Button(buttons, text="Browser Extension Folder", command=lambda: _open_folder(EXTENSION_DIR)).pack(side="left", padx=6)

        ai_box = ttk.LabelFrame(outer, text="Reasoning provider (optional)", padding=12)
        ai_box.pack(fill="x", pady=(4, 10))
        ttk.Label(ai_box, text="Without an API key/model, Intelligence OS works in Mock mode. Ask text is sent to the configured remote model when enabled.", wraplength=690).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.key_var = tk.StringVar(value="")
        self.model_var = tk.StringVar(value=self.settings.get("model", ""))
        self.eval_model_var = tk.StringVar(value=self.settings.get("eval_model", ""))
        self.embedding_model_var = tk.StringVar(value=self.settings.get("embedding_model", ""))

        fields = [
            ("OpenAI API key (session only)", self.key_var, True),
            ("Reasoning model", self.model_var, False),
            ("Eval model (optional)", self.eval_model_var, False),
            ("Embedding model (optional)", self.embedding_model_var, False),
        ]
        for i, (label, var, secret) in enumerate(fields, start=1):
            ttk.Label(ai_box, text=label).grid(row=i, column=0, sticky="w", pady=4)
            ent = ttk.Entry(ai_box, textvariable=var, show="•" if secret else "")
            ent.grid(row=i, column=1, sticky="ew", padx=(12, 0), pady=4)
        ai_box.columnconfigure(1, weight=1)
        ttk.Button(ai_box, text="Apply & Restart Core", command=self.apply_settings).grid(row=5, column=1, sticky="e", pady=(10, 0))

        bridge_box = ttk.LabelFrame(outer, text="Browser bridge", padding=12)
        bridge_box.pack(fill="x", pady=(0, 10))
        ttk.Label(
            bridge_box,
            text=("Recommended: Native Messaging. The extension talks to a local native bridge, which forwards only to the loopback Core. "
                  "If Native Messaging is unavailable, the extension can use the legacy localhost/token mode."),
            wraplength=690,
        ).pack(anchor="w")
        bridge_buttons = ttk.Frame(bridge_box)
        bridge_buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(bridge_buttons, text="Install Chrome/Edge Bridge", command=self.install_bridge).pack(side="left", padx=(0, 6))
        ttk.Button(bridge_buttons, text="Open Extension Setup", command=lambda: _open_folder(EXTENSION_DIR)).pack(side="left", padx=6)
        self.bridge_msg = tk.StringVar(value="")
        ttk.Label(bridge_box, textvariable=self.bridge_msg, foreground="#666").pack(anchor="w", pady=(8, 0))

        privacy_box = ttk.LabelFrame(outer, text="Privacy boundary", padding=12)
        privacy_box.pack(fill="x")
        ttk.Label(
            privacy_box,
            text=("Local Memory is not automatically external LLM context. Gmail/Drive/Calendar sync stays local by default. "
                  "External side effects remain approval-gated. Closing this Desktop app stops the managed Core process."),
            wraplength=690,
        ).pack(anchor="w")

    def _env(self) -> dict:
        env = os.environ.copy()
        env["INTELLIGENCE_DATA_DIR"] = str(DATA)
        env["INTELLIGENCE_DB"] = str(DATA / "intelligence.db")
        env["INTELLIGENCE_TOKEN_PATH"] = str(DATA / "local_api_token.txt")
        env["INTELLIGENCE_CORE_ORIGIN"] = CORE_URL
        if self.key_var.get().strip():
            env["OPENAI_API_KEY"] = self.key_var.get().strip()
        elif "OPENAI_API_KEY" in env:
            # Respect a shell-provided key if present.
            pass
        if self.model_var.get().strip():
            env["INTELLIGENCE_MODEL"] = self.model_var.get().strip()
        else:
            env.pop("INTELLIGENCE_MODEL", None)
        if self.eval_model_var.get().strip():
            env["INTELLIGENCE_EVAL_MODEL"] = self.eval_model_var.get().strip()
        else:
            env.pop("INTELLIGENCE_EVAL_MODEL", None)
        if self.embedding_model_var.get().strip():
            env["INTELLIGENCE_EMBEDDING_MODEL"] = self.embedding_model_var.get().strip()
        else:
            env.pop("INTELLIGENCE_EMBEDDING_MODEL", None)
        return env

    def start_core(self) -> None:
        if self.proc and self.proc.poll() is None:
            return
        if _health():
            self.status_var.set("CORE ONLINE")
            self.detail_var.set("An Intelligence OS Core is already running on 127.0.0.1:8765")
            return
        cmd = [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8765"]
        kwargs: dict = {
            "cwd": str(BACKEND),
            "env": self._env(),
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if platform.system() == "Windows":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self.proc = subprocess.Popen(cmd, **kwargs)
        self.status_var.set("STARTING…")

    def stop_core(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.proc = None
        self.status_var.set("CORE STOPPED")
        self.detail_var.set("")

    def apply_settings(self) -> None:
        self.settings.update({
            "model": self.model_var.get().strip(),
            "eval_model": self.eval_model_var.get().strip(),
            "embedding_model": self.embedding_model_var.get().strip(),
        })
        _save_json(DESKTOP_CONFIG, self.settings)
        self.stop_core()
        self.root.after(250, self.start_core)
        messagebox.showinfo("Intelligence OS", "Settings applied. API key is kept only for this Desktop session unless supplied by your OS environment.")

    def install_bridge(self) -> None:
        def worker():
            try:
                cmd = [sys.executable, str(HOST_INSTALLER), "--browser", "both"]
                p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=60)
                msg = (p.stdout + "\n" + p.stderr).strip()
                if p.returncode != 0:
                    raise RuntimeError(msg or f"installer exited {p.returncode}")
                self.root.after(0, lambda: self.bridge_msg.set("Bridge installed. Load/reload the extension in Chrome/Edge."))
            except Exception as exc:
                self.root.after(0, lambda: self.bridge_msg.set(f"Bridge install failed: {exc}"))
        self.bridge_msg.set("Installing…")
        threading.Thread(target=worker, daemon=True).start()

    def _poll(self) -> None:
        h = _health()
        if h:
            self.status_var.set("CORE ONLINE")
            self.detail_var.set(
                f"v{h.get('version','?')} · reasoning={h.get('reasoning','?')} · eval={h.get('eval','?')} · privacy={h.get('external_llm_mode','?')}"
            )
        else:
            if self.proc and self.proc.poll() is None:
                self.status_var.set("CORE STARTING…")
            else:
                self.status_var.set("CORE OFFLINE")
                self.detail_var.set("Press Start Core if it does not start automatically.")
        self.root.after(1500, self._poll)

    def on_close(self) -> None:
        self.stop_core()
        self.root.destroy()


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    root = tk.Tk()
    DesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
