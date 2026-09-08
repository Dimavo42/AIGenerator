import tkinter as tk
from constants import STATUS_COLORS, LogSource, ModelStatus
from core.logger import Logger
from core.ollamaServerManager import OllamaServerManager
from pages.pageBuilder import PageBuilder


class ChatModePage(PageBuilder):
    """The chat page: every widget of the mode, plus how an answer is shown."""
    mode_name = LogSource.CHAT_MODE
    geometry = "800x600"

    def build(self, app, parent=None):
        """Build the page inside `parent` (app.container by default)."""
        self.app = app
        # Embedded in another page: that page owns the navigation.
        self.is_embedded = parent is not None
        self.frame = tk.Frame(parent or app.container)
        tk.Label(self.frame, text=f"Welcome to {self.mode_name}", font=("Arial", 16, "bold")).pack(pady=10)
        input_row = tk.Frame(self.frame)
        input_row.pack(pady=10)
        tk.Label(input_row, text="Question:").pack(side=tk.LEFT, padx=5)
        self.entry = tk.Entry(input_row, width=50)
        self.entry.pack(side=tk.LEFT, padx=5)
        self.entry.bind("<Return>", lambda _event: self._ask_question())
        tk.Label(self.frame,text="Output Area:",font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.text_output = tk.Text(self.frame, height=15, width=120, wrap=tk.WORD,state=tk.DISABLED)
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
            text="Ask Ollama",
            command=self._ask_question,
            bg="blue",
            fg="white",
        ).pack(pady=10)
        if not self.is_embedded:
            tk.Button(
                self.frame, text="← Back to modes", command=app.show_selector
            ).pack(pady=5)
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
