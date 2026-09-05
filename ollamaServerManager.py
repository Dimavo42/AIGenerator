
from constants import ModelStatus, ServerStatus
from ollamaServer import OllamaServer


class OllamaServerManager:
    _ollama_instance = None
    def __init__(self,on_status_change_callback=None):
        self.on_status_change_callback = on_status_change_callback
        
        

    @classmethod
    def start_ollama_server(cls):
        if cls._ollama_instance is None:
            instance = OllamaServer()
            if not instance.initialize():
                return None
            cls._ollama_instance = instance
        return cls._ollama_instance

    @classmethod
    def change_model(cls, new_model: str):
        if cls._ollama_instance is not None:
            cls._ollama_instance.change_model(new_model)
            if cls._ollama_instance.on_status_change_callback:
                cls._ollama_instance.on_status_change_callback(new_model)
        return ServerStatus.ERROR

    @classmethod
    def ask_ollama(cls, question: str) -> str:
        if cls._ollama_instance is not None:
            return cls._ollama_instance.ask(question)
        return ServerStatus.ERROR

    @classmethod
    def get_model_status(cls):
        if cls._ollama_instance is not None:
            return cls._ollama_instance.get_model_status()
        return ServerStatus.ERROR