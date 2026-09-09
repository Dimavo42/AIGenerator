import threading
import tkinter as tk
from tkinter import filedialog, ttk
from constants import STOCKS_TABLE_DEFAULT_COLUMNS, STOCKS_TABLE_DEFAULT_TICKERS, STATUS_COLORS, STOCKS_CHART_POPUP_LINE_COLOR, STOCKS_CHART_POPUP_PEN_COLOR, STOCKS_CHART_POPUP_PEN_INTERVALS, STOCKS_CHART_POPUP_PEN_WIDTH, STOCKS_CHART_POPUP_PERIODS, DataKey, LogSource, ModelStatus
from core.logger import Logger
from pages.chatModePage import ChatModePage
from pages.pageBuilder import PageBuilder
from core.yfinanceApi import YFinanceApi
from scripts.environment import Environment
from theme import Theme
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class StocksTable(PageBuilder):
    """The stocks half: the watchlist, as yfinance last saw it."""
    mode_name = LogSource.STOCKS_MODE
    COLUMNS = STOCKS_TABLE_DEFAULT_COLUMNS

    def __init__(self, on_pick=None):
        self.on_pick = on_pick
        self.symbols = list(Environment.get_data(DataKey.STOCKS_WATCHLIST, STOCKS_TABLE_DEFAULT_TICKERS))

    def build(self, app, parent=None):
        self.app = app
        self.frame = tk.Frame(parent or app.container, **(Theme.CARD if parent is not None else {}))
        Theme.heading(self.frame, "Stocks (yfinance)").pack(anchor="w", padx=14, pady=(14, 2))
        Theme.hint(self.frame, "Double click a row to open its chart.").pack(anchor="w", padx=14)
        add_row = tk.Frame(self.frame)
        add_row.pack(fill=tk.X, padx=14, pady=(12, 6))
        tk.Label(add_row, text="Symbol", fg=Theme.TEXT_MUTED, font=Theme.FONT_BOLD).pack(side=tk.LEFT, padx=(0, 8))
        self.symbol_entry = tk.Entry(add_row, width=12)
        self.symbol_entry.pack(side=tk.LEFT)
        self.symbol_entry.bind("<Return>", lambda _event: self._add_symbol())
        tk.Button(add_row, text="Add", command=self._add_symbol, **Theme.PRIMARY_BUTTON).pack(side=tk.LEFT, padx=(8, 4))
        tk.Button(add_row, text="Remove", command=self._remove_symbol).pack(side=tk.LEFT)
        self.tree = ttk.Treeview(self.frame, columns=[name for name, _, _ in self.COLUMNS], show="headings", height=15)
        for name, title, width in self.COLUMNS:
            self.tree.heading(name, text=title)
            self.tree.column(name, width=width, anchor=tk.W)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=14, pady=8)
        self.tree.bind("<Double-1>", self._on_double_click)
        footer = tk.Frame(self.frame)
        footer.pack(fill=tk.X, padx=14, pady=(0, 12))
        self.api_status = tk.Label(footer, text=ModelStatus.LOADING, fg=STATUS_COLORS[ModelStatus.LOADING], font=Theme.FONT_BOLD)
        self.api_status.pack(side=tk.LEFT)
        buttons = tk.Frame(footer)
        buttons.pack(side=tk.RIGHT)
        tk.Button(buttons, text="Refresh", command=self.refresh).pack(side=tk.LEFT, padx=4)
        if self.on_pick is not None:
            tk.Button(buttons, text="Ask the model about it", command=self._pick).pack(
                side=tk.LEFT, padx=4
            )

        self.refresh()
        return self.frame

    # ---- loading ----
    def refresh(self):
        """Reload the table in the background."""
        self.api_status.config(text="Loading from yfinance...", fg=STATUS_COLORS[ModelStatus.LOADING])
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self):
        rows = YFinanceApi.shared().get_quotes(self.symbols)
        if self.frame.winfo_exists():
            self.frame.after(0, self._show_rows, rows)

    def _show_rows(self, rows):
        if not self.frame.winfo_exists():
            return
        self.tree.delete(*self.tree.get_children())
        if not rows:
            self.api_status.config(text="No quotes came back - see the logger.", fg=STATUS_COLORS[ModelStatus.ERROR])
            return
        for row in rows:
            self.tree.insert("", tk.END, values=[row[name] for name, _, _ in self.COLUMNS])
        self.api_status.config(text=f"{len(rows)} symbols.", fg=STATUS_COLORS[ModelStatus.LOADED])

    # ---- the watchlist ----
    def _add_symbol(self):
        symbol = self.symbol_entry.get().strip().upper()
        if not symbol:
            return
        self.symbol_entry.delete(0, tk.END)
        if symbol in self.symbols:
            self.api_status.config(text=f"{symbol} is already on the list.", fg=STATUS_COLORS[ModelStatus.LOADING])
            return
        self.symbols.append(symbol)
        Environment.set_data(DataKey.STOCKS_WATCHLIST, self.symbols)
        Logger.log(f"Added {symbol} to the watchlist.", self.mode_name)
        self.refresh()

    def _remove_symbol(self):
        """Drop the selected row from the watchlist."""
        symbol = self._selected_symbol()
        if symbol is None:
            return
        self.symbols.remove(symbol)
        Environment.set_data(DataKey.STOCKS_WATCHLIST, self.symbols)
        Logger.log(f"Removed {symbol} from the watchlist.", self.mode_name)
        self.refresh()

    def _selected_symbol(self) -> str | None:
        selection = self.tree.selection()
        if not selection:
            self.api_status.config(text="Pick a row first.", fg=STATUS_COLORS[ModelStatus.LOADING])
            return None
        return self.tree.item(selection[0], "values")[0]

    def _pick(self):
        """Hand the selected symbol to whoever asked for it."""
        symbol = self._selected_symbol()
        if symbol is not None:
            self.on_pick(symbol)

    def _on_double_click(self,event):
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return
        values = self.tree.item(row_id, "values")
        if not values:
            return
        symbol = values[0]
        StockChartPopup(self.frame,symbol)

    # ---- PageBuilder hooks ----
    # This half never asks the model itself; the chat half does that.
    def on_status(self, status: ModelStatus):
        pass

    def on_response(self, response: str | None, status: ModelStatus):
        pass

class StocksPage(PageBuilder):
    """The stocks mode: a chat page and a stocks page sharing one window.

    Both halves are ordinary pages - this one only puts them side by side and
    turns a picked symbol into a question the model can actually answer.
    """
    mode_name = LogSource.STOCKS_MODE
    geometry = "1200x800"
    # The right half. A mode that shows a different table only swaps this.
    table_class = StocksTable

    def build(self, app, parent=None):
        self.app = app
        self.frame = tk.Frame(parent or app.container)
        # Make the content row expand
        self.frame.rowconfigure(1, weight=1)
        # Two equal-width columns
        self.frame.columnconfigure(0, weight=1, uniform="half")
        self.frame.columnconfigure(1, weight=1, uniform="half")
        # ---------- Header ----------
        header = tk.Frame(self.frame)
        header.grid(row=0,column=0,columnspan=2,sticky="ew",padx=14,pady=(12, 0))
        Theme.title(header,f"{self.mode_name}").pack(side=tk.LEFT)
        tk.Button(header,text="← Back to modes",command=app.show_selector).pack(side=tk.RIGHT)
        # ---------- Pages ----------
        self.chat_page = ChatModePage()
        self.table_page = self.table_class(on_pick=self._ask_about)
        chat_frame = self.chat_page.build(app,self.frame)
        stocks_frame = self.table_page.build(app,self.frame)
        chat_frame.grid(row=1,column=0,sticky="nsew",padx=(10, 5),pady=10)
        stocks_frame.grid(row=1,column=1,sticky="nsew",padx=(5, 10),pady=10)
        Logger.log(f"{self.mode_name} opened with the chat and the table pages.",self.mode_name)
        return self.frame

    def _ask_about(self, symbol: str):
        """Turn a picked symbol into a question waiting in the chat box.

        Fetching the numbers blocks, so it happens off the Tk thread and the
        box is filled once they are here.
        """
        self.chat_page.set_question(f"Fetching {symbol} from yfinance...")
        threading.Thread(target=self._ask_about_worker, args=(symbol,), daemon=True).start()

    def _ask_about_worker(self, symbol: str):
        summary = YFinanceApi.shared().get_summary(symbol)
        if self.frame.winfo_exists():
            self.frame.after(0, self._show_question, symbol, summary)

    def _show_question(self, symbol: str, summary: str | None):
        if not self.frame.winfo_exists():
            return
        if summary is None:
            self.chat_page.set_question(f"What should I know about the stock {symbol}?")
            Logger.log(f"No yfinance data for {symbol} - asked without it.", self.mode_name)
            return
        self.chat_page.set_question(
            "Here is live market data from yfinance:\n"
            f"{summary}\n"
            f"Explain in plain words how {symbol} is doing right now, what stands out "
            "in these numbers, and what a private investor should watch next. "
            "Use only the data above and say when something is not in it."
        )

    # ---- PageBuilder hooks ----
    # The mode page never asks on its own - the chat half owns the conversation.
    def on_status(self, status: ModelStatus):
        self.chat_page.on_status(status)

    def on_response(self, response: str | None, status: ModelStatus):
        self.chat_page.on_response(response, status)

class StockChartPopup(tk.Toplevel):
    PERIODS = STOCKS_CHART_POPUP_PERIODS
    INTERVALS = STOCKS_CHART_POPUP_PEN_INTERVALS
    PEN_COLOR = STOCKS_CHART_POPUP_PEN_COLOR
    PEN_WIDTH = STOCKS_CHART_POPUP_PEN_WIDTH

    def __init__(self, parent, symbol):
        super().__init__(parent)
        self.symbol = symbol
        # Finished strokes, in data coordinates, so they survive a redraw.
        self.strokes = []
        # The stroke the mouse is in the middle of, if any.
        self.active_stroke = None
        self.active_line = None
        # Open on the range and interval the last chart was left on.
        remembered = Environment.get_data(DataKey.CHART, {})
        self.current_period = remembered.get("period", "1mo")
        self.title(f"{symbol} Chart")
        self.geometry("1000x650")
        self.configure(bg=Theme.BG)
        # ---------- Title ----------
        head = tk.Frame(self)
        head.pack(fill=tk.X,padx=15,pady=(14, 0))
        Theme.title(head,f"{symbol} Price History").pack(side=tk.LEFT)
        # ---------- Status ----------
        self.status_label = tk.Label(head,text=ModelStatus.LOADING,fg=STATUS_COLORS[ModelStatus.LOADING],font=Theme.FONT_BOLD)
        self.status_label.pack(side=tk.RIGHT)
        # ---------- Controls ----------
        controls = tk.Frame(self)
        controls.pack(fill=tk.X,padx=15,pady=12)
        tk.Label(controls,text="Range",fg=Theme.TEXT_MUTED,font=Theme.FONT_BOLD).pack(side=tk.LEFT,padx=(0, 8))
        # Kept so the range in view can be the one that looks pressed.
        self.period_buttons = {}
        for text, period in self.PERIODS.items():
            button = tk.Button(
                controls,
                text=text,
                width=3,
                command=lambda p=period: self._change_period(p))
            button.pack(side=tk.LEFT,padx=2)
            self.period_buttons[period] = button
        self._mark_period()
        tk.Label(controls,text="Interval",fg=Theme.TEXT_MUTED,font=Theme.FONT_BOLD).pack( side=tk.LEFT,padx=(20, 8))
        self.interval_var = tk.StringVar(value=remembered.get("interval", "1d"))
        self.interval_combo = ttk.Combobox(
            controls,
            textvariable=self.interval_var,
            values=self.INTERVALS,
            state="readonly",
            width=8)
        self.interval_combo.pack(side=tk.LEFT)
        self.interval_combo.bind("<<ComboboxSelected>>",lambda _event: self.reload_chart())
        # ---------- Drawing ----------
        self.draw_var = tk.BooleanVar(value=False)
        tk.Checkbutton(controls,text="Draw",variable=self.draw_var).pack(side=tk.LEFT,padx=(20, 6))
        tk.Button(controls,text="Clear drawing",command=self._clear_drawing).pack(side=tk.LEFT,padx=2)
        tk.Button(controls,text="Save PNG",command=self._save_png,**Theme.PRIMARY_BUTTON).pack(side=tk.LEFT,padx=2)
        # ---------- Graph ----------
        self.figure = Figure(figsize=(8, 5),dpi=100,facecolor=Theme.BG)
        self.ax = self.figure.add_subplot(111)
        # Dark from the first frame, so an empty or failed chart matches the window.
        Theme.style_figure(self.figure, self.ax)
        self.canvas = FigureCanvasTkAgg(self.figure,master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH,expand=True,padx=15,pady=(0, 15))
        # The pen listens to matplotlib, not Tk, so it gets data coordinates.
        self.canvas.mpl_connect("button_press_event", self._on_pen_down)
        self.canvas.mpl_connect("motion_notify_event", self._on_pen_move)
        self.canvas.mpl_connect("button_release_event", self._on_pen_up)
        # Initial graph
        self.reload_chart()

    def _change_period(self, period):
        self.current_period = period
        self._mark_period()
        self.reload_chart()

    def _mark_period(self):
        """Show which range the chart is on by lighting up its button."""
        for period, button in self.period_buttons.items():
            style = Theme.PRIMARY_BUTTON if period == self.current_period else Theme.BUTTON
            button.config(bg=style["bg"], fg=style["fg"], activebackground=style["activebackground"])

    def reload_chart(self):
        self.status_label.config(text=ModelStatus.LOADING,fg=STATUS_COLORS[ModelStatus.LOADING])
        period = self.current_period
        interval = self.interval_var.get()
        # Every range or interval change comes through here, so remember it here.
        Environment.set_data(DataKey.CHART, {"period": period, "interval": interval})
        threading.Thread(target=self._load_data,args=(period, interval),daemon=True).start()

    def _load_data(self, period, interval):
        history = YFinanceApi.shared().get_history(
            self.symbol,
            period=period,
            interval=interval)
        if self.winfo_exists():
            self.after(0,self._draw_chart,history,period)

    def _draw_chart(self, history, period):
        if history is None or history.empty:
            self.status_label.config(text="No history available.",fg=STATUS_COLORS[ModelStatus.NOT_LOADED])
            return
        self.ax.clear()
        self.ax.plot(history.index,history["Close"],color=STOCKS_CHART_POPUP_LINE_COLOR,linewidth=1.6)
        self.ax.fill_between(history.index,history["Close"],history["Close"].min(),color=STOCKS_CHART_POPUP_LINE_COLOR,alpha=0.12)
        self.ax.set_title(f"{self.symbol} - {period}")
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Price")
        # ax.clear() drops the colors too, so they go back on with the data.
        Theme.style_figure(self.figure, self.ax)
        # ax.clear() wipes the strokes too, so put them back on top.
        for xs, ys in self.strokes:
            self.ax.plot(xs, ys, color=self.PEN_COLOR, linewidth=self.PEN_WIDTH)
        self.figure.autofmt_xdate()
        self.canvas.draw()
        self.status_label.config(text=f"{len(history)} points loaded.",fg=STATUS_COLORS[ModelStatus.LOADED])

    # ---- drawing ----
    def _on_pen_down(self, event):
        if not self.draw_var.get() or event.inaxes is not self.ax:
            return
        self.active_stroke = ([event.xdata], [event.ydata])
        self.active_line = self.ax.plot(
            *self.active_stroke,
            color=self.PEN_COLOR,
            linewidth=self.PEN_WIDTH)[0]
        self.canvas.draw_idle()

    def _on_pen_move(self, event):
        if self.active_stroke is None or event.inaxes is not self.ax:
            return
        xs, ys = self.active_stroke
        xs.append(event.xdata)
        ys.append(event.ydata)
        self.active_line.set_data(xs, ys)
        self.canvas.draw_idle()

    def _on_pen_up(self, _event):
        if self.active_stroke is None:
            return
        # A click without a drag leaves nothing worth keeping.
        if len(self.active_stroke[0]) > 1:
            self.strokes.append(self.active_stroke)
        else:
            self.active_line.remove()
            self.canvas.draw_idle()
        self.active_stroke = None
        self.active_line = None

    def _clear_drawing(self):
        if not self.strokes:
            return
        self.strokes.clear()
        self.reload_chart()

    def _save_png(self):
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Save chart as PNG",
            defaultextension=".png",
            initialfile=f"{self.symbol}_{self.current_period}.png",
            filetypes=[("PNG image", "*.png")])
        if not path:
            return
        self.figure.savefig(path, dpi=150, bbox_inches="tight")
        Logger.log(f"Saved the {self.symbol} chart to {path}.", LogSource.STOCKS_MODE)
        self.status_label.config(text=f"Saved to {path}", fg=STATUS_COLORS[ModelStatus.LOADED])
