import tkinter as tk

from constants import STATUS_COLORS, LogSource, ModelStatus
from logger import logger
from ollamaServerManager import OllamaServerManager
from pages.pageBuilder import PageBuilder


class ChatModePage(PageBuilder):
    """The chat page: every widget of the mode, plus how an answer is shown."""

    mode_name = LogSource.CHAT_MODE

    def build(self, app):
        """Build the page inside `app.container` and return its frame."""
        self.app = app
        self.frame = tk.Frame(app.container)

        tk.Label(
            self.frame, text=f"Welcome to {self.mode_name}", font=("Arial", 16, "bold")
        ).pack(pady=10)

        input_row = tk.Frame(self.frame)
        input_row.pack(pady=10)
        tk.Label(input_row, text="Question:").pack(side=tk.LEFT, padx=5)
        self.entry = tk.Entry(input_row, width=50)
        self.entry.pack(side=tk.LEFT, padx=5)
        self.entry.bind("<Return>", lambda _event: self._ask_question())

        self.text_output = tk.Text(self.frame, height=10, width=70, wrap=tk.WORD)
        self.text_output.pack(pady=10, padx=10)

        status = OllamaServerManager.get_model_status()
        self.status_label = tk.Label(
            self.frame, text=status.value, fg=STATUS_COLORS.get(status)
        )
        self.status_label.pack(pady=5)

        tk.Label(
            self.frame,
            text="⚙️ Chat Mode: Specialized for social network insights",
            fg="purple",
        ).pack(pady=5)

        tk.Button(
            self.frame,
            text="Ask Qwen",
            command=self._ask_question,
            bg="blue",
            fg="white",
        ).pack(pady=10)
        tk.Button(
            self.frame, text="← Back to modes", command=app.show_selector
        ).pack(pady=5)

        return self.frame

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
            logger.log("Answer dropped - the user left the page.", self.mode_name)

    # ---- Tk thread ----
    def _ask_question(self):
        self.ask(self.entry.get())

    def _show_response(self, response, status: ModelStatus):
        if not self.frame.winfo_exists():
            return
        text = "The Ollama server is not running." if response is None else response
        self.text_output.config(state=tk.NORMAL)
        self.text_output.delete(1.0, tk.END)
        self.text_output.insert(tk.END, text)
        self.text_output.config(state=tk.DISABLED)
        self.on_status(status)
        self.entry.delete(0, tk.END)
        logger.log("Answer shown.", self.mode_name)
