"""Prepares the machine and launches the app. Every start_* script ends up here.

This runs under the system Python, before the venv exists, so it may only
import the standard library and Environment - never app.py or anything that
needs requirements.txt. The app itself is started with the venv's Python.
"""
import hashlib
import shutil
import subprocess
import sys
from scripts.environment import Environment


def run(command):
    print()
    print("Running:", " ".join(str(part) for part in command), flush=True)
    result = subprocess.run([str(part) for part in command], cwd=Environment.get_root())
    if result.returncode != 0:
        print("Error running command:", " ".join(str(part) for part in command))
        sys.exit(result.returncode)


# =========================================================
# OLLAMA
# =========================================================

def install_ollama():
    if Environment.is_windows():
        run([
            "winget", "install",
            "--id", "Ollama.Ollama",
            "-e",
            "--accept-package-agreements",
            "--accept-source-agreements",
        ])
    elif Environment.is_linux():
        run(["sh", "-c", "curl -fsSL https://ollama.com/install.sh | sh"])
    elif Environment.is_macos():
        if not shutil.which("brew"):
            print("Homebrew is not installed. Download Ollama from https://ollama.com/download and run this again.")
            sys.exit(1)
        run(["brew", "install", "--cask", "ollama"])
    else:
        raise RuntimeError(f"Unsupported OS: {Environment.get_platform()}")


def setup_ollama():
    print("Checking Ollama...")
    path = Environment.get_ollama_executable()
    if path:
        print(f"Ollama found: {path}")
        return
    print("Ollama not found.")
    install_ollama()
    if not Environment.get_ollama_executable():
        print("Ollama was installed but could not be found. Restart the computer and run this again.")
        sys.exit(1)


# =========================================================
# PYTHON ENVIRONMENT
# =========================================================

def setup_venv():
    if Environment.get_venv_python().exists():
        print("Virtual environment exists.")
        return
    print("Creating virtual environment...")
    run([sys.executable, "-m", "venv", Environment.get_venv()])


def install_requirements():
    """pip install, skipped when requirements.txt has not changed since the last run."""
    marker = Environment.get_venv() / ".requirements.sha256"
    digest = hashlib.sha256(Environment.REQUIREMENTS_FILE.read_bytes()).hexdigest()
    if marker.exists() and marker.read_text(encoding="utf-8") == digest:
        print("Requirements are up to date.")
        return
    python = Environment.get_venv_python()
    run([python, "-m", "pip", "install", "--upgrade", "pip"])
    run([python, "-m", "pip", "install", "-r", Environment.REQUIREMENTS_FILE])
    marker.write_text(digest, encoding="utf-8")


# =========================================================
# LAUNCH
# =========================================================

def launch_app():
    """Start app.py in the venv, detached, so the launcher's terminal may close."""
    print("Starting AIGenerator...")
    subprocess.Popen(
        [str(Environment.get_gui_python()), str(Environment.APP_FILE)],
        cwd=Environment.get_root(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **Environment.get_detached_process_options(),
    )


def main():
    print("==========================")
    print("AIGenerator Setup")
    print("==========================")
    print(f"OS: {Environment.get_platform()}")
    setup_ollama()
    setup_venv()
    install_requirements()
    launch_app()


if __name__ == "__main__":
    main()
