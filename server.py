import importlib
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser

REQUIRED_PACKAGES = [
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("httpx", "httpx"),
    ("PIL", "pillow"),
    ("pydantic", "pydantic"),
    ("multipart", "python-multipart"),
    ("edge_tts", "edge-tts"),
]


def ensure_dependencies() -> None:
    missing = []
    for import_name, pip_name in REQUIRED_PACKAGES:
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print(f"[Da RoastBox!] Installing missing dependencies: {', '.join(missing)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        print("[Da RoastBox!] All dependencies installed.")
    else:
        print("[Da RoastBox!] All dependencies verified.")


def open_browser_when_ready(url: str) -> None:
    for _ in range(30):
        try:
            with urllib.request.urlopen(f"{url}/api/health", timeout=1) as resp:
                if resp.status == 200:
                    print(f"[Da RoastBox!] Opening browser at {url}")
                    webbrowser.open(url)
                    return
        except Exception:
            time.sleep(0.5)


def main() -> None:
    ensure_dependencies()
    import uvicorn

    host = "127.0.0.1"
    port = 8000
    url = f"http://{host}:{port}"

    threading.Thread(target=open_browser_when_ready, args=(url,), daemon=True).start()
    print(f"[Da RoastBox!] Starting local server at {url} ...")
    uvicorn.run("backend.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
