import threading
import tkinter as tk
from tkinter import ttk
from constants import MODELS, STATUS_COLORS, ModelStatus
from logger import logger
from ollamaServerManager import OllamaServerManager
from pages.chatModePage import ChatModePage
from pages.environmentTablePage import EnvironmentTablePage
from pages.loggerPage import LoggerPage
from scripts.environment import Environment


class ClientManager:
    """Owns the single window and builds every page in it on demand."""

    MODES = {
        "ChatMode": ChatModePage,
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
        # Side windows are built lazily and only ever exist one at a time.
        self.logger_instance = None
        self.environment_generator_instance = None
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
                width=30,
            ).grid(row=index, column=1, padx=10)
        tk.Button(frame, text="Show Logger", command=self.show_logger).pack(pady=(20, 5))
        tk.Button(
            frame, text="Environment Generator", command=self.show_environment_generator
        ).pack(pady=5)
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
            status = OllamaServerManager.change_model(selected_model)
            # Widgets are Tk-thread only, and the user may have left the page.
            if loading.winfo_exists():
                loading.after(
                    0, self._on_model_loaded, loading, builder_class, selected_model, status
                )

        threading.Thread(target=worker, daemon=True).start()

    def show_loading(self, model_name):
        """Busy page shown while a model is downloading / loading."""
        frame = tk.Frame(self.container)
        tk.Label(frame, text=f"Loading {model_name}", font=("Arial", 14, "bold")).pack(
            pady=(120, 5)
        )
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

    def _on_model_loaded(self, loading, builder_class, model_name, status: ModelStatus):
        # Ignore a late callback from a page the user already navigated away from.
        if self.current_page is not loading:
            logger.log(f"Ignoring late load result for {model_name}.")
            return
        if status == ModelStatus.LOADED:
            self.show_mode(builder_class)
        else:
            self.show_load_error(model_name, status)

    def show_load_error(self, model_name, status: ModelStatus = ModelStatus.ERROR):
        frame = tk.Frame(self.container)
        tk.Label(
            frame,
            text=f"Could not load {model_name} ({status.value})",
            font=("Arial", 14, "bold"),
            fg=STATUS_COLORS.get(status),
        ).pack(pady=(120, 5))
        tk.Label(
            frame,
            text="Check that Ollama is installed and the model name is correct.",
            fg="gray",
        ).pack(pady=5)
        tk.Button(frame, text="← Back to modes", command=self.show_selector).pack(pady=15)
        self._swap_page(frame, "Ollama - Error")

    def show_mode(self, page_class):
        """Build a mode page and swap it in."""
        page = page_class()
        frame = page.build(self)
        self._swap_page(frame, str(page.mode_name))
        return frame

    # ---- side windows ----
    def _open_window(self, attribute, factory):
        """Raise the window held in `attribute`, or build it once with `factory`."""
        window = getattr(self, attribute)
        if window is not None and window.winfo_exists():
            window.lift()
            window.focus_force()
            return window
        window = factory(lambda: setattr(self, attribute, None))
        setattr(self, attribute, window)
        return window

    def show_logger(self):
        """Open the logger window, or raise the one that is already open."""
        return self._open_window(
            "logger_instance",
            lambda on_close: LoggerPage(self.root, on_close=on_close),
        )

    def show_environment_generator(self):
        """Open the environment window, or raise the one that is already open."""
        data = Environment.get_all_enviorment()
        if not data:
            data = {key: "" for key in self.MODES}
        return self._open_window(
            "environment_generator_instance",
            lambda on_close: EnvironmentTablePage(self.root, data, on_close=on_close),
        )

    def run(self):
        self.root.mainloop()
