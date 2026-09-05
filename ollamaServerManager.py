
import threading

from constants import ModelStatus
from logger import logger
from ollamaServer import OllamaServer


class OllamaServerManager:
    _ollama_instance = None
    _lock = threading.Lock()

    @classmethod
    def start_ollama_server(cls):
        with cls._lock:
            if cls._ollama_instance is None:
                instance = OllamaServer()
                if not instance.initialize():
                    logger.log("Could not start the Ollama server.")
                    return None
                cls._ollama_instance = instance
            return cls._ollama_instance

    @classmethod
    def change_model(cls, new_model: str) -> bool:
        """Load `new_model`, starting the server first if needed. Blocks."""
        instance = cls.start_ollama_server()
        if instance is None:
            return False
        with cls._lock:
            return instance.change_model(new_model)

    @classmethod
    def ask_ollama(cls, question: str) -> str:
        if cls._ollama_instance is None:
            logger.log("Question rejected: Ollama server is not running.")
            return "Error: Ollama server is not running."
        return cls._ollama_instance.ask(question)

    @classmethod
    def get_model_status(cls) -> ModelStatus:
        if cls._ollama_instance is None:
            return ModelStatus.NOT_LOADED
        return cls._ollama_instance.get_model_status()

    @classmethod
    def get_model(cls):
        if cls._ollama_instance is None:
            return None
        return cls._ollama_instance.get_model()