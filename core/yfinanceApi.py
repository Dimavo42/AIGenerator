import threading
from concurrent.futures import ThreadPoolExecutor
import yfinance
from constants import LogSource
from core.logger import Logger


class YFinanceApi:
    """Yahoo Finance quotes, wrapped so the pages never touch yfinance itself.

    No key and no account: yfinance reads the public Yahoo endpoints, so the
    only thing that can go wrong is the network. Every call blocks - call them
    from a worker thread.
    """

    name = LogSource.YFINANCE_API
    # Company names never change during a run, and asking for one is the slow
    # part of a refresh, so each is looked up once.
    _names: dict[str, str] = {}
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def shared(cls):
        """The one client the pages use."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    # ---- quotes ----
    def get_quotes(self, symbols) -> list[dict]:
        """A row per symbol, in the order asked for; unknown symbols are dropped."""
        symbols = [symbol.strip().upper() for symbol in symbols if symbol.strip()]
        if not symbols:
            return []
        # One symbol is one HTTP round trip, so ask for them side by side.
        with ThreadPoolExecutor(max_workers=min(8, len(symbols))) as pool:
            rows = list(pool.map(self.get_quote, symbols))
        rows = [row for row in rows if row is not None]
        Logger.log(f"Loaded {len(rows)} of {len(symbols)} quotes.", self.name)
        return rows

    def get_quote(self, symbol: str) -> dict | None:
        """One symbol as a {symbol, name, last, change, currency} row, or None."""
        symbol = symbol.strip().upper()
        try:
            ticker = yfinance.Ticker(symbol)
            fast = ticker.fast_info
            last = self._pick(fast, "last_price", "lastPrice")
            previous = self._pick(fast, "previous_close", "previousClose")
            if last is None:
                # Yahoo answers with an empty quote for a symbol it does not know.
                Logger.log(f"No quote for {symbol}.", self.name)
                return None
            return {
                "symbol": symbol,
                "name": self.get_name(symbol),
                "last": self._round(last),
                "change": self._change(last, previous),
                "currency": self._pick(fast, "currency") or "",
            }
        except Exception as error:
            Logger.log(f"{symbol} failed: {error}", self.name)
            return None

    def get_name(self, symbol: str) -> str:
        """The company name, remembered after the first lookup."""
        symbol = symbol.strip().upper()
        if symbol in self._names:
            return self._names[symbol]
        name = symbol
        try:
            info = yfinance.Ticker(symbol).info or {}
            name = info.get("shortName") or info.get("longName") or symbol
        except Exception as error:
            Logger.log(f"No name for {symbol}: {error}", self.name)
        self._names[symbol] = name
        return name

    def get_history(self,symbol,period="1mo",interval="1d"):
        try:
            ticker = yfinance.Ticker(symbol)
            history = ticker.history(period=period,interval=interval)
            if history.empty:
                return None
            return history
        except Exception as e:
            Logger.log(
                f"Failed loading history for {symbol}: {e}"
            )
            return None
    # ---- what the model is told ----
    def get_summary(self, symbol: str) -> str | None:
        """The facts about one symbol, as the lines handed to the model.

        The model has no internet of its own, so anything it should reason
        about has to be written out here.
        """
        symbol = symbol.strip().upper()
        try:
            ticker = yfinance.Ticker(symbol)
            fast = ticker.fast_info
            info = ticker.info or {}
        except Exception as error:
            Logger.log(f"No summary for {symbol}: {error}", self.name)
            return None

        last = self._pick(fast, "last_price", "lastPrice")
        if last is None:
            return None
        previous = self._pick(fast, "previous_close", "previousClose")
        currency = self._pick(fast, "currency") or ""
        facts = {
            "Symbol": symbol,
            "Name": info.get("shortName") or info.get("longName") or symbol,
            "Exchange": info.get("exchange", ""),
            "Sector": info.get("sector", ""),
            "Industry": info.get("industry", ""),
            "Currency": currency,
            "Last price": self._round(last),
            "Previous close": self._round(previous),
            "Change %": self._change(last, previous),
            "Day range": self._range(
                self._pick(fast, "day_low", "dayLow"), self._pick(fast, "day_high", "dayHigh")
            ),
            "52 week range": self._range(
                self._pick(fast, "year_low", "yearLow"), self._pick(fast, "year_high", "yearHigh")
            ),
            "Market cap": self._big_number(self._pick(fast, "market_cap", "marketCap")),
            "P/E (trailing)": info.get("trailingPE", ""),
            "Closes of the last 5 sessions": self._recent_closes(ticker),
        }
        lines = [f"{label}: {value}" for label, value in facts.items() if value not in ("", None)]
        business = (info.get("longBusinessSummary") or "").strip()
        if business:
            lines.append(f"What the company does: {business[:600]}")
        return "\n".join(lines)

    def _recent_closes(self, ticker) -> str:
        """The last few daily closes, so the model can see the direction."""
        try:
            history = ticker.history(period="5d")
            closes = history["Close"].tail(5)
            return ", ".join(f"{date:%d/%m}: {close:.2f}" for date, close in closes.items())
        except Exception as error:
            Logger.log(f"No history: {error}", self.name)
            return ""

    # ---- shaping the numbers ----
    @staticmethod
    def _pick(fast, *keys):
        """A fast_info field under whichever name this yfinance version uses."""
        for key in keys:
            try:
                value = fast[key]
            except Exception:
                value = getattr(fast, key, None)
            if value is not None:
                return value
        return None

    @staticmethod
    def _round(value):
        return round(float(value), 2) if value is not None else ""

    @staticmethod
    def _change(last, previous) -> str:
        """The move since the previous close, in percent."""
        if not previous:
            return ""
        return f"{(float(last) - float(previous)) / float(previous) * 100:+.2f}"

    @staticmethod
    def _big_number(value) -> str:
        """A market cap the model can read, instead of 4669699792415.161."""
        return f"{float(value):,.0f}" if value else ""

    @classmethod
    def _range(cls, low, high) -> str:
        if low is None or high is None:
            return ""
        return f"{cls._round(low)} - {cls._round(high)}"
