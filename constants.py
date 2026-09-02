from enum import Enum


MODELS = ["Model 1", "Model 2", "Model 3"]


class ServerStatus(Enum):
    NOT_RUNNING = 0
    STARTING = 1
    RUNNING = 2
    ERROR = 3

class ModelStatus(Enum):
    NOT_LOADED = 0
    LOADING = 1
    DONE = 2
    ERROR = 3