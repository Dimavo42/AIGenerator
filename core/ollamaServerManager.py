
import threading
from constants import ModelStatus
from core.logger import logger
from core.ollamaServer import OllamaServer


class OllamaServerManager:
    _ollama_instance = None
    _lock = threading.Lock()

    @classmethod
    def start_ollama_server(cls):
        """Return the shared server instance, creating and initializing it once."""
        with cls._lock:
            if cls._ollama_instance is None:
                instance = OllamaServer()
                if instance.initialize() != ModelStatus.LOADED:
                    logger.log("Could not start the Ollama server.")
                    return None
                cls._ollama_instance = instance
            return cls._ollama_instance

    @classmethod
    def change_model(cls, new_model: str) -> ModelStatus:
        """Load `new_model`, starting the server first if needed. Blocks."""
        instance = cls.start_ollama_server()
        if instance is None:
            return ModelStatus.ERROR
        with cls._lock:
            return instance.change_model(new_model)

    @classmethod
    def ask_ollama(cls, question: str) -> str | ModelStatus:
        if cls._ollama_instance is None:
            logger.log("Question rejected: Ollama server is not running.")
            return ModelStatus.ERROR
        return cls._ollama_instance.ask(question)

    @classmethod
    def get_model_status(cls) -> ModelStatus:
        if cls._ollama_instance is None:
            return ModelStatus.NOT_LOADED
        return cls._ollama_instance.get_model_status()

    @classmethod
    def get_model(cls) -> str | None:
        """The model name currently selected, or None when nothing is loaded."""
        if cls._ollama_instance is None:
            return None
        return cls._ollama_instance.get_model()