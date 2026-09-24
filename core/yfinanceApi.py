import threading
from concurrent.futures import ThreadPoolExecutor
import yfinance
from yfinance.const import EQUITY_SCREENER_EQ_MAP, ETF_SCREENER_EQ_MAP
from constants import STOCKS_SEARCH_ALL, EnvKey, LogSource
from core.logger import Logger
from scripts.environment import Environment


class YFinanceApi:
    """Yahoo Finance quotes, wrapped so the pages never touch yfinance itself.

    No key and no account: yfinance reads the public Yahoo endpoints, so the
    only thing that can go wrong is the network. Every call blocks - call them
    from a worker thread.
    """
    name = LogSource.YFINANCE_API
    # Name, sector and industry per symbol - they come from the same slow
    # .info call and hardly ever change, so it is made once per symbol.
    _profiles: dict[str, dict] = {}
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
        max_workers = Environment.get_int(EnvKey.YFINANCE_MAX_WORKERS, 8)
        with ThreadPoolExecutor(max_workers=min(max_workers, len(symbols))) as pool:
            rows = list(pool.map(self.get_quote, symbols))
        rows = [row for row in rows if row is not None]
        Logger.log(f"Loaded {len(rows)} of {len(symbols)} quotes.", self.name)
        return rows

    def get_quote(self, symbol: str) -> dict | None:
        """One symbol as a {symbol, name, last, change, currency, sector, industry} row, or None."""
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
            profile = self.get_profile(symbol)
            return {
                "symbol": symbol,
                "name": profile["name"],
                "last": self._round(last),
                "change": self._change(last, previous),
                "currency": self._pick(fast, "currency") or "",
                "sector": profile["sector"],
                "industry": profile["industry"],
            }
        except Exception as error:
            Logger.log(f"{symbol} failed: {error}", self.name)
            return None

    def get_name(self, symbol: str) -> str:
        """The company name, remembered after the first lookup."""
        return self.get_profile(symbol)["name"]

    def get_profile(self, symbol: str) -> dict:
        """{name, sector, industry} for a symbol, remembered after the first lookup.

        An index or a fund has no sector, so those two can come back empty.
        """
        symbol = symbol.strip().upper()
        if symbol in self._profiles:
            return self._profiles[symbol]
        profile = {"name": symbol, "sector": "", "industry": ""}
        try:
            info = yfinance.Ticker(symbol).info or {}
            profile = {
                "name": info.get("shortName") or info.get("longName") or symbol,
                "sector": info.get("sector") or "",
                "industry": info.get("industry") or "",
            }
        except Exception as error:
            Logger.log(f"No profile for {symbol}: {error}", self.name)
        self._profiles[symbol] = profile
        return profile

    # ---- searching the market ----
    # Yahoo refuses a screener page bigger than this.
    SCREEN_PAGE_SIZE = 250

    @staticmethod
    def _etf_categories() -> list[str]:
        return sorted(ETF_SCREENER_EQ_MAP.get("categoryname", []))

    @staticmethod
    def _is_bond_category(category: str) -> bool:
        """Yahoo has no bond screener - bonds are the ETFs in a bond category."""
        return "Bond" in category or category.startswith("Muni") or "Government" in category

    @classmethod
    def get_search_choices(cls, key: str) -> list[str]:
        """Every value Yahoo's screener accepts for a category, like every sector.

        ETFs and bonds start with STOCKS_SEARCH_ALL, since outside the US Yahoo
        files its ETFs under no category at all.
        """
        if key == "etf":
            return [STOCKS_SEARCH_ALL, *(c for c in cls._etf_categories() if not cls._is_bond_category(c))]
        if key == "bond":
            return [STOCKS_SEARCH_ALL, *(c for c in cls._etf_categories() if cls._is_bond_category(c))]
        choices = EQUITY_SCREENER_EQ_MAP.get(key, [])
        # Industries come grouped by the sector they belong to.
        if isinstance(choices, dict):
            choices = set().union(*choices.values())
        return sorted(choices)

    @classmethod
    def _search_query(cls, key: str, value: str, region: str):
        """The screener query for a search, and the field its biggest results sort by."""
        if key not in ("etf", "bond"):
            query = yfinance.EquityQuery(
                "and", [yfinance.EquityQuery("eq", [key, value]), yfinance.EquityQuery("eq", ["region", region])]
            )
            return query, "intradaymarketcap"
        in_region = yfinance.ETFQuery("eq", ["region", region])
        if key == "etf" and value == STOCKS_SEARCH_ALL:
            return in_region, "fundnetassets"
        if value == STOCKS_SEARCH_ALL:
            categories = [category for category in cls._etf_categories() if cls._is_bond_category(category)]
            in_category = yfinance.ETFQuery("or", [yfinance.ETFQuery("eq", ["categoryname", c]) for c in categories])
        else:
            in_category = yfinance.ETFQuery("eq", ["categoryname", value])
        return yfinance.ETFQuery("and", [in_category, in_region]), "fundnetassets"

    def search(self, key: str, value: str, region: str, count: int) -> tuple[list[dict], int] | None:
        """The `count` biggest stocks or ETFs in `region` whose `key` is `value`, and how many there are in all.

        Rows come in the same shape as get_quote's, straight from the screener,
        so a hundred results cost a request instead of a hundred.
        """
        rows, total = [], 0
        try:
            query, sort_field = self._search_query(key, value, region)
            while len(rows) < count:
                size = min(self.SCREEN_PAGE_SIZE, count - len(rows))
                page = yfinance.screen(query, offset=len(rows), size=size, sortField=sort_field, sortAsc=False)
                quotes = page.get("quotes") or []
                total = page.get("total") or 0
                rows.extend(self._screen_row(quote) for quote in quotes)
                if len(quotes) < size or len(rows) >= total:
                    break
        except Exception as error:
            Logger.log(f"Search for {key} {value} failed: {error}", self.name)
            # Pages that did arrive are still worth showing.
            if not rows:
                return None
        Logger.log(f"Found {len(rows)} of {total} for {key} {value} in {region}.", self.name)
        return rows, total

    def _screen_row(self, quote: dict) -> dict:
        symbol = quote["symbol"]
        change = quote.get("regularMarketChangePercent")
        return {
            "symbol": symbol,
            "name": quote.get("shortName") or quote.get("longName") or symbol,
            "last": self._round(quote.get("regularMarketPrice")),
            "change": f"{float(change):+.2f}" if change is not None else "",
            "currency": quote.get("currency") or "",
        }

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
