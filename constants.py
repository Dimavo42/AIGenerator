from enum import Enum


MODELS = ["richardyoung/qwen2.5-coder-14b-instruct-abliterated"
          ,"thomboe/dolphin3.0-llama3.1-8b-abliterated"
            ,"R4C3R/gemma-3-12b-it-heretic"
            ,"igorls/gemma-4-12B-it-qat-q4_0-unquantized-heretic"
            ,"dolphin-mistral"
            ,"dolphin-mixtral"
            ,"dolphin-phi"]


DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "META", "^GSPC"]


class LogSource(str, Enum):
    GLOBAL = "global"
    ALL_SOURCES = "all"
    SERVER = "server"
    ENVIRONMENT = "Environment"
    CHAT_MODE = "Chat Mode"
    STOCKS_MODE = "Stocks"
    YFINANCE_API = "yfinance Api"

    def __str__(self):
        return self.value


class ServerStatus(Enum):
    NOT_RUNNING = "not running"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"

class ModelStatus(Enum):
    NOT_LOADED = "not loaded"
    LOADING = "loading"
    LOADED = "loaded"
    GENERATING = "generating"
    ERROR = "error"


STATUS_COLORS = {
    ModelStatus.NOT_LOADED: "red",
    ModelStatus.LOADING: "orange",
    ModelStatus.LOADED: "green",
    ModelStatus.GENERATING: "blue",
    ModelStatus.ERROR: "red",
    ServerStatus.NOT_RUNNING: "red",
    ServerStatus.STARTING: "orange",
    ServerStatus.RUNNING: "green",
    ServerStatus.ERROR: "red",
}

