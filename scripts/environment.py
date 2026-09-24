import copy
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path
from constants import DEFAULT_DATA, DEFAULT_ENVIRONMENT


class Environment:
    """The one place the program reads its state from and writes it back to.

    Two files sit in the project root:
      .env           - flat KEY=VALUE settings, editable in the Environment page.
      app_data.json  - everything the app remembers between runs.

    Neither has to exist: the first run creates both from the defaults in
    constants.py. `load()` runs once before the GUI is built and `save()` once
    when the window closes - everything in between happens in memory, so no
    page ever waits on the disk.

    It is also the only place that knows which operating system it runs on:
    setup.py and the app ask it for paths and process options instead of
    checking the platform themselves.
    """

    WINDOWS = "Windows"
    MACOS = "Darwin"
    LINUX = "Linux"

    ROOT_PATH = Path(__file__).resolve().parent.parent
    ENVIRONMENT_PATH = ROOT_PATH / ".env"
    DATA_PATH = ROOT_PATH / "app_data.json"
    APP_FILE = ROOT_PATH / "app.py"
    REQUIREMENTS_FILE = ROOT_PATH / "requirements.txt"
    VENV_DIR = ROOT_PATH / ".venv"
    SYSTEM = platform.system()

    _environment_keys: dict[str, str] = {}
    _data: dict = {}
    _is_loaded = False

    # =========================================================
    # PLATFORM
    # =========================================================

    @classmethod
    def get_platform(cls) -> str:
        """"Windows", "Darwin" (macOS) or "Linux"."""
        return cls.SYSTEM

    @classmethod
    def is_windows(cls) -> bool:
        return cls.SYSTEM == cls.WINDOWS

    @classmethod
    def is_macos(cls) -> bool:
        return cls.SYSTEM == cls.MACOS

    @classmethod
    def is_linux(cls) -> bool:
        return cls.SYSTEM == cls.LINUX

    @classmethod
    def get_root(cls) -> Path:
        """The project root, where all the files are."""
        return cls.ROOT_PATH

    @classmethod
    def get_venv(cls) -> Path:
        return cls.VENV_DIR

    @classmethod
    def get_venv_python(cls) -> Path:
        """The venv's interpreter - Windows keeps it under Scripts, the rest under bin."""
        if cls.is_windows():
            return cls.VENV_DIR / "Scripts" / "python.exe"
        return cls.VENV_DIR / "bin" / "python"

    @classmethod
    def get_gui_python(cls) -> Path:
        """The interpreter the GUI runs under - pythonw on Windows, so no console opens."""
        if cls.is_windows():
            return cls.VENV_DIR / "Scripts" / "pythonw.exe"
        return cls.get_venv_python()

    @classmethod
    def get_ollama_executable(cls) -> str | None:
        """Ollama's path, or None when it is not installed.

        PATH comes first, then the places the installers put it - a shell
        opened before the install has an old PATH that does not include them.
        """
        found = shutil.which("ollama")
        if found:
            return found
        if cls.is_windows():
            candidates = [Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"]
        elif cls.is_macos():
            candidates = [
                Path("/Applications/Ollama.app/Contents/Resources/ollama"),
                Path("/opt/homebrew/bin/ollama"),
                Path("/usr/local/bin/ollama"),
            ]
        else:
            candidates = [Path("/usr/local/bin/ollama"), Path("/usr/bin/ollama")]
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)
        return None

    @classmethod
    def get_hidden_process_options(cls) -> dict:
        """Popen options for a background child that must not open a console window."""
        if cls.is_windows():
            return {"creationflags": subprocess.CREATE_NO_WINDOW}
        return {}

    @classmethod
    def get_detached_process_options(cls) -> dict:
        """Popen options for a child that outlives the terminal which started it."""
        if cls.is_windows():
            return {"creationflags": subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP}
        return {"start_new_session": True}

    # =========================================================
    # LIFECYCLE
    # =========================================================

    @classmethod
    def load(cls):
        """Read both files, creating them from the defaults on a first run."""
        if cls._is_loaded:
            return
        # Set first so a getter reached from a loader cannot recurse back here.
        cls._is_loaded = True
        cls._load_environment()
        cls._load_data()

    @classmethod
    def save(cls):
        """Write both files back. Called when the program closes."""
        cls._ensure_loaded()
        cls._save_environment()
        cls._save_data()

    @classmethod
    def _ensure_loaded(cls):
        """Nothing may read state before it exists, whoever asks first."""
        if not cls._is_loaded:
            cls.load()

    # =========================================================
    # ENVIRONMENT (.env)
    # =========================================================

    @classmethod
    def is_file_created(cls, output_file_path=None):
        path = Path(output_file_path) if output_file_path else cls.ENVIRONMENT_PATH
        return path.exists()

    @classmethod
    def _load_environment(cls):
        # Start from the defaults and let the file win, so a setting added to
        # DEFAULT_ENVIRONMENT later appears in an .env written before it.
        cls._environment_keys = {str(key): value for key, value in DEFAULT_ENVIRONMENT.items()}
        if not cls.ENVIRONMENT_PATH.exists():
            cls._save_environment()
            return
        with cls.ENVIRONMENT_PATH.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                cls._environment_keys[key.strip()] = value.strip()

    @classmethod
    def _save_environment(cls):
        with cls.ENVIRONMENT_PATH.open("w", encoding="utf-8") as file:
            for key, value in cls._environment_keys.items():
                file.write(f"{key}={value}\n")

    @classmethod
    def get(cls, key, default=None):
        return cls._environment_keys.get(str(key), default)

    @classmethod
    def get_int(cls, key, default):
        """A numeric setting, falling back when the file holds nonsense."""
        try:
            return int(cls.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def get_all_environment(cls):
        return cls._environment_keys.copy()

    @classmethod
    def save_all(cls, values):
        """Replace the settings and write them out - the Save button lands here."""
        cls._environment_keys = {
            str(key).strip(): value for key, value in values.items() if str(key).strip()
        }
        cls._save_environment()

    # =========================================================
    # SERIALIZATION / JSON (app_data.json)
    # =========================================================

    @classmethod
    def _load_data(cls):
        cls._data = copy.deepcopy({str(key): value for key, value in DEFAULT_DATA.items()})
        if not cls.DATA_PATH.exists():
            cls._save_data()
            return
        try:
            with cls.DATA_PATH.open("r", encoding="utf-8") as file:
                stored = json.load(file)
        except (json.JSONDecodeError, OSError):
            # A half-written file should cost the remembered state, not the run.
            stored = {}
        if isinstance(stored, dict):
            cls._data.update(stored)

    @classmethod
    def _save_data(cls):
        with cls.DATA_PATH.open("w", encoding="utf-8") as file:
            json.dump(cls._data, file, indent=4, ensure_ascii=False)

    @classmethod
    def get_data(cls, key, default=None):
        """A remembered value, copied so a caller cannot edit the store by accident."""
        if str(key) not in cls._data:
            return default
        return copy.deepcopy(cls._data[str(key)])

    @classmethod
    def set_data(cls, key, value):
        """Remember a value. It reaches the disk when the program closes."""
        cls._data[str(key)] = copy.deepcopy(value)

    @classmethod
    def get_all_data(cls):
        return copy.deepcopy(cls._data)

    @classmethod
    def remove_data(cls, key):
        cls._data.pop(str(key), None)
