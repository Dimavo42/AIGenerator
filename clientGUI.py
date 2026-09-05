import threading
import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import ttk
from constants import MODELS, ModelStatus
from ollamaServerManager import OllamaServerManager


class PageBuilder(ABC):
    """Abstract base builder: builds a mode page step by step.

    A page is a Frame that lives inside the app's container, so swapping
    modes means swapping frames instead of opening new windows.
    """
    mode_name = ""

    def create_page(self, app):
        self.app = app
        self.frame = tk.Frame(app.container)
        return self

    def add_title(self, title: str):
        tk.Label(self.frame, text=title, font=("Arial", 16, "bold")).pack(pady=10)
        return self

    def add_input_field(self):
        frame = tk.Frame(self.frame)
        frame.pack(pady=10)
        tk.Label(frame, text="Question:").pack(side=tk.LEFT, padx=5)
        self.entry = tk.Entry(frame, width=50)
        self.entry.pack(side=tk.LEFT, padx=5)
        self.entry.bind("<Return>", lambda _event: self._ask_question())
        return self

    def add_output_area(self):
        self.text_output = tk.Text(self.frame, height=10, width=70, wrap=tk.WORD)
        self.text_output.pack(pady=10, padx=10)
        return self

    def add_status_bar(self,model_status:ModelStatus):
        colors = {
            ModelStatus.NOT_LOADED: "red",
            ModelStatus.LOADING: "orange",
            ModelStatus.LOADED: "green",
            ModelStatus.ERROR: "red",
        }
        self.status_label = tk.Label(self.frame, text=model_status.value, fg=colors.get(model_status))
        self.status_label.pack(pady=5)
        return self

    @abstractmethod
    def add_mode_specific_widgets(self):
        """Mode-specific widgets - implemented by each concrete builder."""

    def add_ask_button(self):
        tk.Button(
            self.frame,
            text="Ask Qwen",
            command=self._ask_question,
            bg="blue",
            fg="white",
        ).pack(pady=10)
        return self

    def add_back_button(self):
        tk.Button(
            self.frame,
            text="\u2190 Back to modes",
            command=self.app.show_selector,
        ).pack(pady=5)
        return self

    def build(self):
        return self.frame

    # ---- ask flow ----
    def _ask_question(self):
        question = self.entry.get().strip()
        if not question:
            return
        self.status_label.config(text="Thinking...", fg="blue")
        threading.Thread(target=self._ask_worker, args=(question,), daemon=True).start()

    def _ask_worker(self, question):
        response = OllamaServerManager.ask_ollama(question)
        # Widgets may only be touched from the Tk main thread, and the page
        # may already be gone if the user swapped modes while waiting.
        if self.frame.winfo_exists():
            self.frame.after(0, self._show_response, response)

    def _show_response(self, response):
        if not self.frame.winfo_exists():
            return
        self.text_output.config(state=tk.NORMAL)
        self.text_output.delete(1.0, tk.END)
        self.text_output.insert(tk.END, response)
        self.text_output.config(state=tk.DISABLED)
        self.status_label.config(text="Ready", fg="green")
        self.entry.delete(0, tk.END)

    def _addLooger(self):
        pass

class FetLifeBuilder(PageBuilder):
    mode_name = "FetLife Mode"

    def add_mode_specific_widgets(self):
        tk.Label(
            self.frame,
            text="\u2699\ufe0f FetLife Mode: Specialized for social network insights",
            fg="purple",
        ).pack(pady=5)
        return self

class TelegramBuilder(PageBuilder):
    mode_name = "Telegram Mode"

    def add_mode_specific_widgets(self):
        tk.Label(
            self.frame,
            text="\U0001f4f1 Telegram Mode: Optimized for messaging insights",
            fg="blue",
        ).pack(pady=5)
        return self

class StocksBuilder(PageBuilder):
    mode_name = "Stocks Mode"

    def add_mode_specific_widgets(self):
        tk.Label(
            self.frame,
            text="\U0001f4c8 Stocks Mode: Financial analysis and insights",
            fg="green",
        ).pack(pady=5)
        return self


# ============ MAIN APPLICATION ============
class ClientGUI:
    MODES = {
        "FetLife": FetLifeBuilder,
        "Telegram": TelegramBuilder,
        "Stocks": StocksBuilder,
    }

    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("600x500")
        # Every page is packed into this container; only one lives at a time.
        self.container = tk.Frame(self.root)
        self.container.pack(fill=tk.BOTH, expand=True)
        self.current_page = None
        # Kept on the instance so the vars outlive the selector frame.
        self.model_vars = {
            mode_name: tk.StringVar(value=MODELS[0]) for mode_name in self.MODES
        }
        self.show_selector()

    # ---- page swapping ----
    def _swap_page(self, frame, title):
        if self.current_page is not None:
            self.current_page.destroy()
        self.current_page = frame
        self.root.title(title)
        frame.pack(fill=tk.BOTH, expand=True)

    def show_selector(self):
        """Show the mode-selection page."""
        frame = tk.Frame(self.container)
        tk.Label(frame, text="Select Mode", font=("Arial", 18, "bold")).pack(pady=20)
        buttons = tk.Frame(frame)
        buttons.pack(pady=20)
        for index, (mode_name, builder_class) in enumerate(self.MODES.items()):
            tk.Button(
                buttons,
                text=f"Open {mode_name}",
                width=20,
                command=lambda b=builder_class: self.show_mode(b),
                bg="lightblue",
                font=("Arial", 12),
            ).grid(row=index, column=0, pady=5)
            combo = ttk.Combobox(
                buttons,
                textvariable=self.model_vars[mode_name],
                values=MODELS,
                state="readonly",
                width=15,
            ).grid(row=index, column=1, padx=10)
        def on_click(event,builder_class,eventSelected):
            selected_model = self.model_vars[builder_class.mode_name].get()
            OllamaServerManager.change_model(selected_model)
            self.show_mode(builder_class)

            
            
        self._swap_page(frame, "Ollama - Mode Selector")

    def show_mode(self, builder_class):
        """Build a mode page through the builder chain and swap it in."""
        builder = builder_class()
        frame = (
            builder.create_page(self)
            .add_title(f"Welcome to {builder.mode_name}")
            .add_input_field()
            .add_output_area()
            .add_status_bar(self.getOllamaServerModelStatus())
            .add_mode_specific_widgets()
            .add_ask_button()
            .add_back_button()
            .build()
        )
        self._swap_page(frame, builder.mode_name)
        return frame

    def getOllamaServerModelStatus(self):
        return OllamaServerManager.get_model_status()

    def run(self):
        self.root.mainloop()



