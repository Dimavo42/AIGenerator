from enum import Enum


MODELS = ["richardyoung/qwen2.5-coder-14b-instruct-abliterated"
          ,"thomboe/dolphin3.0-llama3.1-8b-abliterated"
            ,"R4C3R/gemma-3-12b-it-heretic"
            ,"igorls/gemma-4-12B-it-qat-q4_0-unquantized-heretic"
            ,"dolphin-mistral"
            ,"dolphin-mixtral"
            ,"dolphin-phi"]
OLLAMA_LIBRARY_URL = "https://ollama.com/library/"

STOCKS_TABLE_DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "META", "^GSPC"]
STOCKS_TABLE_DEFAULT_COLUMNS = (
        ("symbol", "Symbol", 90),
        ("name", "Name", 200),
        ("last", "Last", 80),
        ("change", "Change %", 90),
        ("currency", "Currency", 80),
    )


STOCKS_CHART_POPUP_PERIODS = {
        "1M": "1mo",
        "3M": "3mo",
        "6M": "6mo",
        "1Y": "1y",
        "2Y": "2y",
        "5Y": "5y",
    }

STOCKS_CHART_POPUP_PEN_WIDTH = 2
STOCKS_CHART_POPUP_PEN_COLOR = "red"

STOCKS_CHART_POPUP_PEN_INTERVALS = [
        "1d",
        "5d",
        "1wk",
        "1mo",
    ]

class EnvKey(str, Enum):
    """The settings that live in .env, one line each."""

    OLLAMA_HOST = "OLLAMA_HOST"
    OLLAMA_PORT = "OLLAMA_PORT"
    OLLAMA_STARTUP_TIMEOUT = "OLLAMA_STARTUP_TIMEOUT"
    YFINANCE_MAX_WORKERS = "YFINANCE_MAX_WORKERS"

    def __str__(self):
        return self.value

class DataKey(str, Enum):
    """The top-level keys of app_data.json."""

    MODELS = "models"
    STOCKS_WATCHLIST = "stocks_watchlist"
    SELECTED_MODELS = "selected_models"
    CHART = "chart"

    def __str__(self):
        return self.value

# Written to .env on the first run; a key added here later shows up in an
# existing .env the next time the program starts.
DEFAULT_ENVIRONMENT = {
    EnvKey.OLLAMA_HOST: "localhost",
    EnvKey.OLLAMA_PORT: "11434",
    EnvKey.OLLAMA_STARTUP_TIMEOUT: "30",
    EnvKey.YFINANCE_MAX_WORKERS: "8",
}

# Written to app_data.json on the first run; the same rule applies.
DEFAULT_DATA = {
    DataKey.MODELS: MODELS,
    DataKey.STOCKS_WATCHLIST: STOCKS_TABLE_DEFAULT_TICKERS,
    DataKey.SELECTED_MODELS: {},
    DataKey.CHART: {"period": "1mo", "interval": "1d"},
}

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

class ServerStatus(str,Enum):
    NOT_RUNNING = "not running"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"

    def __str__(self):
        return self.value

class ModelStatus(str,Enum):
    NOT_LOADED = "not loaded"
    LOADING = "loading"
    LOADED = "loaded"
    GENERATING = "generating"
    ERROR = "error"

    def __str__(self):
        return self.value

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

