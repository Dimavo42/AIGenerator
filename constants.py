from enum import Enum


MODELS = ["richardyoung/qwen2.5-coder-14b-instruct-abliterated"
          ,"thomboe/dolphin3.0-llama3.1-8b-abliterated"
            ,"R4C3R/gemma-3-12b-it-heretic"
            ,"igorls/gemma-4-12B-it-qat-q4_0-unquantized-heretic"
            ,"dolphin-mistral"
            ,"dolphin-mixtral"
            ,"dolphin-phi"]


class ServerStatus(Enum):
    NOT_RUNNING = "not running"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"

class ModelStatus(Enum):
    NOT_LOADED = "not loaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"

