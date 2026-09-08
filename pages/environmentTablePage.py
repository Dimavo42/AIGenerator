from core.logger import logger
import tkinter as tk
from constants import LogSource
from scripts.environment import Environment


class EnvironmentTablePage(tk.Toplevel):
    """Editable key/value grid for the .env file."""

    def __init__(self, parent, data,on_close=None):
        super().__init__(parent)
        self.on_close = on_close
        self.title("Environment Generator")
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.rows = []
        header = tk.Frame(self)
        header.pack(padx=10, pady=(10, 0), anchor=tk.W)
        tk.Label(header, text="Key", width=25, anchor=tk.W, font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        tk.Label(header, text="Value", width=35, anchor=tk.W, font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.rows_frame = tk.Frame(self)
        self.rows_frame.pack(padx=10, pady=5, anchor=tk.W)
        self.create_grid_of_values(data)
        buttons = tk.Frame(self)
        buttons.pack(pady=10)
        tk.Button(buttons, text="Save", command=self._save, bg="blue", fg="white").pack(side=tk.LEFT, padx=5)

    def create_grid_of_values(self, data):
        for name, value in data.items():
            row = tk.Frame(self.rows_frame)
            row.pack(anchor=tk.W)
            tk.Label(row, text=name, width=25, anchor=tk.W).pack(side=tk.LEFT)
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
        logger.log(f"Saved {len(Environment.get_all_enviorment())} environment keys.", LogSource.ENVIRONMENT)
        self._close()

    def _close(self):
        self.destroy()
        if self.on_close is not None:
            self.on_close()