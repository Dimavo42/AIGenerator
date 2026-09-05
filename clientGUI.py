import threading
import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import ttk
from constants import MODELS, ModelStatus
from logger import logger
from ollamaServerManager import OllamaServerManager

ALL_SOURCES = "all"


class PageBuilder(ABC):
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
        logger.log(f"Asking: {question}", self.mode_name)
        self.status_label.config(text="Thinking...", fg="blue")
        threading.Thread(target=self._ask_worker, args=(question,), daemon=True).start()

    def _ask_worker(self, question):
        response = OllamaServerManager.ask_ollama(question)
        # Widgets may only be touched from the Tk main thread, and the page
        # may already be gone if the user swapped modes while waiting.
        if self.frame.winfo_exists():
            self.frame.after(0, self._show_response, response)
        else:
            logger.log("Answer dropped - the user left the page.", self.mode_name)

    def _show_response(self, response):
        if not self.frame.winfo_exists():
            return
        self.text_output.config(state=tk.NORMAL)
        self.text_output.delete(1.0, tk.END)
        self.text_output.insert(tk.END, response)
        self.text_output.config(state=tk.DISABLED)
        self.status_label.config(text="Ready", fg="green")
        self.entry.delete(0, tk.END)
        logger.log("Answer shown.", self.mode_name)


class FetLifeBuilder(PageBuilder):
    mode_name = "FetLife Mode"

    def __init__(self):
        super().__init__()

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
        logger.log("GUI started.")
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
                command=lambda n=mode_name, b=builder_class: self.open_mode(n, b),
                bg="lightblue",
                font=("Arial", 12),
            ).grid(row=index, column=0, pady=5)
            ttk.Combobox(
                buttons,
                textvariable=self.model_vars[mode_name],
                values=MODELS,
                state="readonly",
                width=15,
            ).grid(row=index, column=1, padx=10)
        tk.Label(frame,text="Show Logger:").pack(pady=(20,5))
        tk.Button(frame, text="Show Logger", command=self.show_Logger).pack(pady=5)
        self._swap_page(frame, "Ollama - Mode Selector")

    # ---- opening a mode ----
    def open_mode(self, mode_name, builder_class):
        """Load the model picked for this mode, then show the mode page."""
        selected_model = self.model_vars[mode_name].get()
        logger.log(f"Opening {mode_name} with {selected_model}.", builder_class.mode_name)
        if (
            selected_model == OllamaServerManager.get_model()
            and OllamaServerManager.get_model_status() == ModelStatus.LOADED
        ):
            self.show_mode(builder_class)
            return

        loading = self.show_loading(selected_model)

        def worker():
            loaded = OllamaServerManager.change_model(selected_model)
            # Widgets are Tk-thread only, and the user may have left the page.
            if loading.winfo_exists():
                loading.after(0, self._on_model_loaded, loading, builder_class, selected_model, loaded)

        threading.Thread(target=worker, daemon=True).start()

    def show_loading(self, model_name):
        """Busy page shown while a model is downloading / loading."""
        frame = tk.Frame(self.container)
        tk.Label(frame, text=f"Loading {model_name}", font=("Arial", 14, "bold")).pack(pady=(120, 5))
        tk.Label(
            frame,
            text="First run downloads the model - this can take a few minutes.",
            fg="gray",
        ).pack(pady=5)
        bar = ttk.Progressbar(frame, mode="indeterminate", length=320)
        bar.pack(pady=15)
        bar.start(12)
        self._swap_page(frame, "Loading model...")
        return frame

    def _on_model_loaded(self, loading, builder_class, model_name, loaded):
        # Ignore a late callback from a page the user already navigated away from.
        if self.current_page is not loading:
            logger.log(f"Ignoring late load result for {model_name}.")
            return
        if loaded:
            self.show_mode(builder_class)
        else:
            self.show_load_error(model_name)

    def show_load_error(self, model_name):
        frame = tk.Frame(self.container)
        tk.Label(
            frame,
            text=f"Could not load {model_name}",
            font=("Arial", 14, "bold"),
            fg="red",
        ).pack(pady=(120, 5))
        tk.Label(
            frame,
            text="Check that Ollama is installed and the model name is correct.",
            fg="gray",
        ).pack(pady=5)
        tk.Button(frame, text="← Back to modes", command=self.show_selector).pack(pady=15)
        self._swap_page(frame, "Ollama - Error")

    def show_mode(self, builder_class):
        """Build a mode page through the builder chain and swap it in."""
        builder = builder_class()
        frame = (
            builder.create_page(self)
            .add_title(f"Welcome to {builder.mode_name}")
            .add_input_field()
            .add_output_area()
            .add_status_bar(self.get_ollama_server_model_status())
            .add_mode_specific_widgets()
            .add_ask_button()
            .add_back_button()
            .build()
        )
        self._swap_page(frame, builder.mode_name)
        return frame

    def get_ollama_server_model_status(self):
        return OllamaServerManager.get_model_status()

    def show_Logger(self):
        """Live view of the app log, filtered by source, refreshed twice a second."""
        logger_window = tk.Toplevel(self.root)
        logger_window.title("Logger")
        logger_window.geometry("700x400")

        controls = tk.Frame(logger_window)
        controls.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(controls, text="Source:").pack(side=tk.LEFT)
        source_var = tk.StringVar(value=ALL_SOURCES)
        source_box = ttk.Combobox(
            controls, textvariable=source_var, state="readonly", width=50
        )
        source_box.pack(side=tk.LEFT, padx=5)

        scrollbar = tk.Scrollbar(logger_window)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        logger_text = tk.Text(
            logger_window, wrap=tk.WORD, state=tk.DISABLED, yscrollcommand=scrollbar.set
        )
        logger_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=logger_text.yview)

        def refresh():
            if not logger_window.winfo_exists():
                return  # Window closed - stop the polling loop.
            source_box["values"] = [ALL_SOURCES] + logger.get_instance_names()
            source = source_var.get()
            lines = (
                logger.get_all_logs()
                if source == ALL_SOURCES
                else logger.get_logs_by_name(source)
            )
            text = "\n".join(lines)
            # Only redraw on a real change, otherwise the user can never keep a
            # selection or a scroll position.
            if text != logger_text.get(1.0, tk.END).rstrip("\n"):
                was_at_bottom = logger_text.yview()[1] >= 0.99
                logger_text.config(state=tk.NORMAL)
                logger_text.delete(1.0, tk.END)
                logger_text.insert(tk.END, text)
                logger_text.config(state=tk.DISABLED)
                if was_at_bottom:
                    logger_text.see(tk.END)
            logger_window.after(500, refresh)

        refresh()

    def run(self):
        self.root.mainloop()



