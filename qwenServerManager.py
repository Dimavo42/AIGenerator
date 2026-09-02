
from qwenServer import QwenServer


class QwenServerManager:
    _qwen_instance = None

    @classmethod
    def start_qwen_server(cls):
        if cls._qwen_instance is None:
            instance = QwenServer()
            if not instance.initialize():
                return None
            cls._qwen_instance = instance
        return cls._qwen_instance

    @classmethod
    def change_model(cls, new_model: str):
        if cls._qwen_instance is not None:
            cls._qwen_instance.change_model(new_model)

    @classmethod
    def get_qwen_instance(cls):
        return cls._qwen_instance