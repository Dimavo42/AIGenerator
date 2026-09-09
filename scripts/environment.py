import copy
import json
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
    """

    ROOT_PATH = Path(__file__).resolve().parent.parent
    ENVIRONMENT_PATH = ROOT_PATH / ".env"
    DATA_PATH = ROOT_PATH / "app_data.json"

    _environment_keys: dict[str, str] = {}
    _data: dict = {}
    _is_loaded = False

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
