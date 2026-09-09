import tkinter as tk
from tkinter import ttk
from constants import LogSource
from core.logger import Logger
from theme import Theme


class LoggerPopup(tk.Toplevel):
    """Live view of the app log, filtered by source, refreshed twice a second."""

    def __init__(self, parent, on_close=None):
        super().__init__(parent)
        self.on_close = on_close
        self.title("Logger")
        self.geometry("760x440")
        self.configure(bg=Theme.BG)
        controls = tk.Frame(self)
        controls.pack(fill=tk.X, padx=14, pady=12)
        tk.Label(controls, text="Source", fg=Theme.TEXT_MUTED, font=Theme.FONT_BOLD).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        self.source_var = tk.StringVar(value=LogSource.ALL_SOURCES)
        self.source_box = ttk.Combobox(
            controls, textvariable=self.source_var, state="readonly", width=50
        )
        self.source_box.pack(side=tk.LEFT)
        self.protocol("WM_DELETE_WINDOW", self._close)
        # The log and its scrollbar sit together so the padding wraps both.
        body = tk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 14))
        # ttk's scrollbar is the one that takes the theme on Windows.
        scrollbar = ttk.Scrollbar(body)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.logger_text = tk.Text(
            body, wrap=tk.WORD, state=tk.DISABLED, yscrollcommand=scrollbar.set
        )
        self.logger_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.logger_text.yview)
        self._refresh()

    def _refresh(self):
        if not self.winfo_exists():
            return  # Window closed - stop the polling loop.
        # Tk stores the combobox values as plain strings, so hand it strings the
        # filter below can compare against.
        self.source_box["values"] = [str(LogSource.ALL_SOURCES)] + [
            str(name) for name in Logger.get_instance_names()
        ]
        source = self.source_var.get()
        lines = (
            Logger.get_all_logs()
            if source == LogSource.ALL_SOURCES
            else Logger.get_logs_by_name(source)
        )
        text = "\n".join(lines)
        # Only redraw on a real change, otherwise the user can never keep a
        # selection or a scroll position.
        if text != self.logger_text.get(1.0, tk.END).rstrip("\n"):
            was_at_bottom = self.logger_text.yview()[1] >= 0.99
            self.logger_text.config(state=tk.NORMAL)
            self.logger_text.delete(1.0, tk.END)
            self.logger_text.insert(tk.END, text)
            self.logger_text.config(state=tk.DISABLED)
            if was_at_bottom:
                self.logger_text.see(tk.END)
        self.after(500, self._refresh)

    def _close(self):
        self.destroy()
        if self.on_close is not None:
            self.on_close()