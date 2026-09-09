import tkinter as tk
from constants import LogSource
from core.logger import Logger
from scripts.environment import Environment
from theme import Theme


class EnvironmentTablePopup(tk.Toplevel):
    """Editable key/value grid for the .env file."""

    def __init__(self, parent, data,on_close=None):
        super().__init__(parent)
        self.on_close = on_close
        self.title("Environment Generator")
        self.configure(bg=Theme.BG)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.rows = []
        Theme.heading(self, "Environment").pack(anchor=tk.W, padx=18, pady=(16, 2))
        Theme.hint(self, "These lines are what gets written to .env.").pack(anchor=tk.W, padx=18)
        header = tk.Frame(self)
        header.pack(padx=18, pady=(14, 0), anchor=tk.W)
        tk.Label(header, text="Key", width=25, anchor=tk.W, fg=Theme.TEXT_MUTED, font=Theme.FONT_SMALL).pack(side=tk.LEFT)
        tk.Label(header, text="Value", width=35, anchor=tk.W, fg=Theme.TEXT_MUTED, font=Theme.FONT_SMALL).pack(side=tk.LEFT)
        Theme.separator(self).pack(fill=tk.X, padx=18, pady=(4, 0))
        self.rows_frame = tk.Frame(self)
        self.rows_frame.pack(padx=18, pady=8, anchor=tk.W)
        self.create_grid_of_values(data)
        buttons = tk.Frame(self)
        buttons.pack(pady=(6, 16))
        tk.Button(buttons, text="Save", width=12, command=self._save, **Theme.PRIMARY_BUTTON).pack(side=tk.LEFT, padx=5)

    def create_grid_of_values(self, data):
        for name, value in data.items():
            row = tk.Frame(self.rows_frame)
            row.pack(anchor=tk.W, pady=3)
            tk.Label(row, text=name, width=25, anchor=tk.W, font=Theme.FONT_BOLD).pack(side=tk.LEFT)
            value_entry = tk.Entry(row, width=35)
            value_entry.insert(0, value)
            value_entry.pack(side=tk.LEFT)
            # The key is fixed for these rows, so keep the name instead of a widget.
            self.rows.append((name, value_entry))

    def _save(self):
        values = {
            key:value.get() for key, value in self.rows
        }
        Environment.save_all(values)
        Logger.log(f"Saved {len(Environment.get_all_environment())} environment keys.", LogSource.ENVIRONMENT)
        self._close()

    def _close(self):
        self.destroy()
        if self.on_close is not None:
            self.on_close()