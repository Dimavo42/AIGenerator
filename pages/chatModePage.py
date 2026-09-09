import tkinter as tk
from constants import STATUS_COLORS, LogSource, ModelStatus
from core.logger import Logger
from core.ollamaServerManager import OllamaServerManager
from pages.pageBuilder import PageBuilder
from theme import Theme


class ChatModePage(PageBuilder):
    """The chat page: every widget of the mode, plus how an answer is shown."""
    mode_name = LogSource.CHAT_MODE
    geometry = "800x600"

    def build(self, app, parent=None):
        """Build the page inside `parent` (app.container by default)."""
        self.app = app
        # Embedded in another page: that page owns the navigation.
        self.is_embedded = parent is not None
        # On its own the page is the window; inside another page it is a panel.
        self.frame = tk.Frame(parent or app.container, **(Theme.CARD if self.is_embedded else {}))
        Theme.heading(self.frame, f"Welcome to {self.mode_name}").pack(
            anchor="w", padx=14, pady=(14, 2)
        )
        Theme.hint(
            self.frame, "⚙️ Chat Mode: Specialized for social network insights"
        ).pack(anchor="w", padx=14)
        input_row = tk.Frame(self.frame)
        input_row.pack(fill=tk.X, padx=14, pady=(14, 6))
        tk.Label(input_row, text="Question", fg=Theme.TEXT_MUTED, font=Theme.FONT_BOLD).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        self.entry = tk.Entry(input_row)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", lambda _event: self._ask_question())
        tk.Button(
            input_row, text="Ask Ollama", command=self._ask_question, **Theme.PRIMARY_BUTTON
        ).pack(side=tk.LEFT, padx=(8, 0))
        tk.Label(self.frame, text="Answer", fg=Theme.TEXT_MUTED, font=Theme.FONT_BOLD).pack(
            anchor="w", padx=14, pady=(10, 4)
        )
        self.text_output = tk.Text(self.frame, height=12, wrap=tk.WORD, state=tk.DISABLED)
        self.text_output.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 10))
        footer = tk.Frame(self.frame)
        footer.pack(fill=tk.X, padx=14, pady=(0, 12))
        status = OllamaServerManager.get_model_status()
        self.status_label = tk.Label(
            footer, text=status.value, fg=STATUS_COLORS.get(status), font=Theme.FONT_BOLD
        )
        self.status_label.pack(side=tk.LEFT)
        if not self.is_embedded:
            tk.Button(footer, text="← Back to modes", command=app.show_selector).pack(
                side=tk.RIGHT
            )
        return self.frame

    def set_question(self, question: str):
        """Put a question in the box for the user to send (or edit first)."""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, question)
        self.entry.focus_set()

    # ---- PageBuilder hooks ----
    def on_status(self, status: ModelStatus):
        if self.frame.winfo_exists():
            self.status_label.config(text=status.value, fg=STATUS_COLORS.get(status))

    def on_response(self, response, status: ModelStatus):
        # Widgets may only be touched from the Tk main thread, and the page
        # may already be gone if the user swapped modes while waiting.
        if self.frame.winfo_exists():
            self.frame.after(0, self._show_response, response, status)
        else:
            Logger.log("Answer dropped - the user left the page.", self.mode_name)

    # ---- Tk thread ----
    def _ask_question(self):
        self.ask(self.entry.get())

    def _set_output(self, text: str):
        self.text_output.config(state=tk.NORMAL)
        self.text_output.delete("1.0", tk.END)
        self.text_output.insert(tk.END, text)
        self.text_output.config(state=tk.DISABLED)
    

    def _show_response(self, response, status: ModelStatus):
        if not self.frame.winfo_exists():
            return
        text = "The Ollama server is not running." if response is None else response
        self._set_output(text)
        self.on_status(status)
        self.entry.delete(0, tk.END)
        Logger.log("Answer shown.", self.mode_name)
