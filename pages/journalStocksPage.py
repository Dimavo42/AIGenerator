import threading
import tkinter as tk
from datetime import datetime
from tkinter import ttk
from constants import JOURNAL_DATE_FORMAT, JOURNAL_ENTRY_EDIT_FIELDS, JOURNAL_TABLE_DEFAULT_COLUMNS, STATUS_COLORS, DataKey, LogSource, ModelStatus
from core.logger import Logger
from core.yfinanceApi import YFinanceApi
from pages.pageBuilder import PageBuilder
from pages.stocksPage import StockChartPopup, StocksPage
from scripts.environment import Environment
from theme import Theme


class JournalTable(PageBuilder):
    """The journal half: what was bought, when, and what it is worth now.

    An entry keeps the price and the date it was written down; everything
    else on the row is worked out again from the live quote.
    """
    mode_name = LogSource.JOURNAL_STOCKS_MODE
    COLUMNS = JOURNAL_TABLE_DEFAULT_COLUMNS

    def __init__(self, on_pick=None):
        self.on_pick = on_pick
        self.entries = list(Environment.get_data(DataKey.STOCKS_JOURNAL, []))

    def build(self, app, parent=None):
        self.app = app
        self.frame = tk.Frame(parent or app.container, **(Theme.CARD if parent is not None else {}))
        Theme.heading(self.frame, "Journal (yfinance)").pack(anchor="w", padx=14, pady=(14, 2))
        Theme.hint(self.frame, "Double click a row to edit the entry behind it.").pack(anchor="w", padx=14)
        add_row = tk.Frame(self.frame)
        add_row.pack(fill=tk.X, padx=14, pady=(12, 6))
        tk.Label(add_row, text="Symbol", fg=Theme.TEXT_MUTED, font=Theme.FONT_BOLD).pack(side=tk.LEFT, padx=(0, 8))
        self.symbol_entry = tk.Entry(add_row, width=12)
        self.symbol_entry.pack(side=tk.LEFT)
        self.symbol_entry.bind("<Return>", lambda _event: self._add_to_journal())
        tk.Button(add_row, text="Add", command=self._add_to_journal, **Theme.PRIMARY_BUTTON).pack(side=tk.LEFT, padx=(8, 4))
        tk.Button(add_row, text="Remove", command=self._remove_from_journal).pack(side=tk.LEFT)
        self.tree = ttk.Treeview(self.frame, columns=[name for name, _, _ in self.COLUMNS], show="headings", height=15)
        for name, title, width in self.COLUMNS:
            self.tree.heading(name, text=title)
            self.tree.column(name, width=width, anchor=tk.W)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=14, pady=8)
        self.tree.bind("<Double-1>", self._on_double_click)
        # A row is read for its profit, so the profit is what colors it.
        self.tree.tag_configure("gain", foreground=Theme.SUCCESS)
        self.tree.tag_configure("loss", foreground=Theme.DANGER)
        footer = tk.Frame(self.frame)
        footer.pack(fill=tk.X, padx=14, pady=(0, 12))
        self.api_status = tk.Label(footer, text=ModelStatus.LOADING, fg=STATUS_COLORS[ModelStatus.LOADING], font=Theme.FONT_BOLD)
        self.api_status.pack(side=tk.LEFT)
        buttons = tk.Frame(footer)
        buttons.pack(side=tk.RIGHT)
        tk.Button(buttons, text="Refresh", command=self.refresh).pack(side=tk.LEFT, padx=4)
        tk.Button(buttons, text="Edit", command=self._edit_selected).pack(side=tk.LEFT, padx=4)
        # Double click edits now, so the chart needs a button of its own.
        tk.Button(buttons, text="Chart", command=self._chart_selected).pack(side=tk.LEFT, padx=4)
        if self.on_pick is not None:
            tk.Button(buttons, text="Ask the model about it", command=self._pick).pack(
                side=tk.LEFT, padx=4
            )

        self.refresh()
        return self.frame

    # ---- loading ----
    def refresh(self):
        """Reload the prices behind the journal in the background."""
        if not self.entries:
            self._show_rows({})
            return
        self.api_status.config(text="Loading from yfinance...", fg=STATUS_COLORS[ModelStatus.LOADING])
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self):
        rows = YFinanceApi.shared().get_quotes([entry["symbol"] for entry in self.entries])
        # The journal decides the order, so the quotes only have to be findable.
        quotes = {row["symbol"]: row for row in rows}
        if self.frame.winfo_exists():
            self.frame.after(0, self._show_rows, quotes)

    def _show_rows(self, quotes):
        if not self.frame.winfo_exists():
            return
        self.tree.delete(*self.tree.get_children())
        if not self.entries:
            self.api_status.config(text="The journal is empty.", fg=STATUS_COLORS[ModelStatus.LOADING])
            return
        for index, entry in enumerate(self.entries):
            row = self._row(entry, quotes.get(entry["symbol"]))
            # The row id is where the entry sits in the journal, so a picked
            # row leads straight back to the entry behind it.
            self.tree.insert(
                "",
                tk.END,
                iid=str(index),
                values=[row[name] for name, _, _ in self.COLUMNS],
                tags=self._tags(row["profit"]),
            )
        missing = len(self.entries) - len(quotes)
        if missing:
            self.api_status.config(
                text=f"{len(quotes)} of {len(self.entries)} priced - see the logger.",
                fg=STATUS_COLORS[ModelStatus.ERROR],
            )
        else:
            self.api_status.config(text=f"{len(self.entries)} entries.", fg=STATUS_COLORS[ModelStatus.LOADED])

    def _row(self, entry, quote) -> dict:
        """One journal entry as the row the table shows."""
        price_now = quote["last"] if quote else ""
        return {
            "symbol": entry["symbol"],
            "name": (quote["name"] if quote else "") or entry.get("name", entry["symbol"]),
            "begin_price": entry.get("begin_price", ""),
            "price_now": price_now,
            "date": entry.get("date", ""),
            "profit": self._profit(entry.get("begin_price"), price_now),
        }

    @staticmethod
    def _tags(profit: str) -> tuple:
        """Green for a row that is up, red for one that is down, plain for neither."""
        if profit.startswith("+") and float(profit) > 0:
            return ("gain",)
        if profit.startswith("-"):
            return ("loss",)
        # Flat, or no quote at all: the row stays the color the table is.
        return ()

    @staticmethod
    def _profit(begin_price, price_now) -> str:
        """The move since the entry was opened, in percent."""
        try:
            begin = float(begin_price)
            now = float(price_now)
        except (TypeError, ValueError):
            return ""
        if not begin:
            return ""
        return f"{(now - begin) / begin * 100:+.2f}"

    # ---- the journal ----
    def _add_to_journal(self):
        """Write today's price down as the entry price for a symbol."""
        symbol = self.symbol_entry.get().strip().upper()
        if not symbol:
            return
        self.symbol_entry.delete(0, tk.END)
        if any(entry["symbol"] == symbol for entry in self.entries):
            self.api_status.config(text=f"{symbol} is already in the journal.", fg=STATUS_COLORS[ModelStatus.LOADING])
            return
        # The entry price is the price right now, so it has to be fetched first.
        self.api_status.config(text=f"Looking up {symbol}...", fg=STATUS_COLORS[ModelStatus.LOADING])
        threading.Thread(target=self._add_worker, args=(symbol,), daemon=True).start()

    def _add_worker(self, symbol: str):
        quote = YFinanceApi.shared().get_quote(symbol)
        if self.frame.winfo_exists():
            self.frame.after(0, self._finish_add, symbol, quote)

    def _finish_add(self, symbol: str, quote):
        if not self.frame.winfo_exists():
            return
        if quote is None:
            self.api_status.config(text=f"No quote for {symbol}.", fg=STATUS_COLORS[ModelStatus.ERROR])
            return
        self.entries.append(
            {
                "symbol": symbol,
                "name": quote["name"],
                "begin_price": quote["last"],
                "date": datetime.now().strftime(JOURNAL_DATE_FORMAT),
            }
        )
        self._save()
        Logger.log(f"Added {symbol} to the journal at {quote['last']}.", self.mode_name)
        self.refresh()

    def _remove_from_journal(self):
        """Drop the selected row from the journal."""
        symbol = self._selected_symbol()
        if symbol is None:
            return
        self.entries = [entry for entry in self.entries if entry["symbol"] != symbol]
        self._save()
        Logger.log(f"Removed {symbol} from the journal.", self.mode_name)
        self.refresh()

    def _save(self):
        Environment.set_data(DataKey.STOCKS_JOURNAL, self.entries)

    def _selected_index(self) -> int | None:
        selection = self.tree.selection()
        if not selection:
            self.api_status.config(text="Pick a row first.", fg=STATUS_COLORS[ModelStatus.LOADING])
            return None
        return int(selection[0])

    def _selected_symbol(self) -> str | None:
        index = self._selected_index()
        if index is None:
            return None
        return self.entries[index]["symbol"]

    def _pick(self):
        """Hand the selected symbol to whoever asked for it."""
        symbol = self._selected_symbol()
        if symbol is not None:
            self.on_pick(symbol)

    def _chart_selected(self):
        symbol = self._selected_symbol()
        if symbol is not None:
            StockChartPopup(self.frame, symbol)

    # ---- editing ----
    def _edit_selected(self):
        index = self._selected_index()
        if index is not None:
            self._edit(index)

    def _on_double_click(self, event):
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return
        self._edit(int(row_id))

    def _edit(self, index: int):
        JournalEntryEditPopup(self.frame, self.entries[index], lambda entry: self._apply_edit(index, entry))

    def _apply_edit(self, index: int, entry: dict) -> str | None:
        """Take an edited entry back into the journal, or say why it cannot go.

        The popup stays open on a rejected edit, so the reason goes back to it
        instead of to the status line.
        """
        symbol = entry["symbol"]
        if any(other["symbol"] == symbol for position, other in enumerate(self.entries) if position != index):
            return f"{symbol} is already in the journal."
        was = self.entries[index]["symbol"]
        self.entries[index] = entry
        self._save()
        Logger.log(f"Edited the {was} journal entry.", self.mode_name)
        self.refresh()
        return None

    # ---- PageBuilder hooks ----
    # This half never asks the model itself; the chat half does that.
    def on_status(self, status: ModelStatus):
        pass

    def on_response(self, response: str | None, status: ModelStatus):
        pass


class JournalEntryEditPopup(tk.Toplevel):
    """One journal entry, in boxes, until it is saved or dropped."""
    FIELDS = JOURNAL_ENTRY_EDIT_FIELDS

    def __init__(self, parent, entry: dict, on_save):
        super().__init__(parent)
        self.entry = entry
        self.on_save = on_save
        self.title(f"Edit {entry['symbol']}")
        self.geometry("440x300")
        self.configure(bg=Theme.BG)
        self.transient(parent)
        Theme.heading(self, "Edit journal entry").pack(anchor="w", padx=18, pady=(16, 10))
        fields = tk.Frame(self)
        fields.pack(fill=tk.X, padx=18)
        fields.columnconfigure(1, weight=1)
        self.entries = {}
        for row, (name, title) in enumerate(self.FIELDS):
            tk.Label(fields, text=title, fg=Theme.TEXT_MUTED, font=Theme.FONT_SMALL).grid(
                row=row, column=0, sticky=tk.W, pady=5
            )
            box = tk.Entry(fields)
            box.insert(0, str(entry.get(name, "")))
            box.grid(row=row, column=1, sticky="ew", padx=(12, 0), pady=5)
            box.bind("<Return>", lambda _event: self._save())
            self.entries[name] = box
        self.error_label = tk.Label(self, text="", fg=STATUS_COLORS[ModelStatus.ERROR], font=Theme.FONT_SMALL)
        self.error_label.pack(pady=8)
        buttons = tk.Frame(self)
        buttons.pack(pady=(4, 14))
        tk.Button(buttons, text="Save", width=10, command=self._save, **Theme.PRIMARY_BUTTON).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons, text="Cancel", width=10, command=self.destroy).pack(side=tk.LEFT, padx=5)

    def _save(self):
        edited = self._read()
        if edited is None:
            return
        rejected = self.on_save(edited)
        if rejected is not None:
            self.error_label.config(text=rejected)
            return
        self.destroy()

    def _read(self) -> dict | None:
        """The boxes as an entry, or None once the reason is on show."""
        values = {name: self.entries[name].get().strip() for name, _ in self.FIELDS}
        symbol = values["symbol"].upper()
        if not symbol:
            self.error_label.config(text="A symbol is needed.")
            return None
        try:
            begin_price = float(values["begin_price"])
        except ValueError:
            self.error_label.config(text="The begin price has to be a number.")
            return None
        try:
            datetime.strptime(values["date"], JOURNAL_DATE_FORMAT)
        except ValueError:
            self.error_label.config(text="The date has to look like 2025-01-31.")
            return None
        # Anything the entry carried that is not on show stays as it was.
        return {
            **self.entry,
            "symbol": symbol,
            "name": values["name"] or symbol,
            "begin_price": begin_price,
            "date": values["date"],
        }


class JournalStocksPage(StocksPage):
    """The journal stocks mode: the same split window, with the journal on the right."""
    mode_name = LogSource.JOURNAL_STOCKS_MODE
    table_class = JournalTable
