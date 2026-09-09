import threading
import tkinter as tk
from tkinter import ttk
from constants import  STATUS_COLORS, DataKey, ModelStatus
from core.logger import Logger
from core.ollamaServerManager import OllamaServerManager
from pages.chatModePage import ChatModePage
from pages.environmentTablePopup import EnvironmentTablePopup
from pages.loggerPopup import LoggerPopup
from pages.modelAdderPopup import ModelAdderPopup
from pages.stocksPage import StocksPage
from scripts.environment import Environment
from scripts.modelsManager import ModelsManager


class ClientManager:
    """Owns the single window and builds every page in it on demand."""

    _MODES = {
        "ChatMode": ChatModePage,
        "Stocks": StocksPage
    }
    _models_manager = ModelsManager()

    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("600x500")
        # Closing the window is what ends the program, so it is what saves it.
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        # Every page is packed into this container; only one lives at a time.
        self.container = tk.Frame(self.root)
        self.container.pack(fill=tk.BOTH, expand=True)
        self.current_page = None
        # Side windows are built lazily and only ever exist one at a time.
        self.logger_instance = None
        self.environment_generator_instance = None
        self.model_pop_up_adder_instance = None
        self._models = self._models_manager.get_all_models()
        self._models_manager.subscribe(self._on_models_changed)
         # Kept on the instance so the vars outlive the selector frame.
        self.model_vars = {
            mode_name: tk.StringVar(value=self._remembered_model(mode_name))
            for mode_name in self._MODES
        }
        self.model_comboboxes = {}
        Logger.log("GUI started.")
        self.show_selector()

    # ---- what the last run left behind ----
    def _remembered_model(self, mode_name):
        """The model this mode was last opened with, if it is still on the list."""
        remembered = Environment.get_data(DataKey.SELECTED_MODELS, {}).get(mode_name)
        if remembered in self._models:
            return remembered
        return self._models[0] if self._models else ""

    # ---- page swapping ----
    def _swap_page(self, frame, title):
        if self.current_page is not None:
            self.current_page.destroy()
        self.current_page = frame
        self.root.title(title)
        frame.pack(fill=tk.BOTH, expand=True)

    def show_selector(self):
        """Show the mode-selection page."""
        # A mode may have grown the window; the selector is small again.
        self.root.geometry("600x500")
        self.model_comboboxes.clear()
        frame = tk.Frame(self.container)
        tk.Label(frame, text="Select Mode", font=("Arial", 18, "bold")).pack(pady=20)
        buttons = tk.Frame(frame)
        buttons.pack(pady=20)
        for index, (mode_name, builder_class) in enumerate(self._MODES.items()):
            tk.Button(
                buttons,
                text=f"Open {mode_name}",
                width=20,
                command=lambda n=mode_name, b=builder_class: self.load_model(n, b),
                bg="lightblue",
                font=("Arial", 12),
            ).grid(row=index, column=0, pady=5)
            combo = ttk.Combobox(
                buttons,
                textvariable=self.model_vars[mode_name],
                values=self._models,
                state="readonly",
                width=30,
            )
            combo.grid(row=index, column=1, padx=10)
            self.model_comboboxes[mode_name] = combo
        tk.Button(frame, text="Show Logger", command=self.show_logger).pack(pady=(20, 5))
        tk.Button(
            frame, text="Environment Generator", command=self.show_environment_generator
        ).pack(pady=5)
        tk.Button(frame, text="Add Model",command=self.show_add_model).pack(pady=5)
        self._swap_page(frame, "Ollama - Mode Selector")

    # ---- loading the model ----
    def load_model(self, mode_name, builder_class):
        """Load the model picked for this mode, then show the mode page."""
        selected_model = self.model_vars[mode_name].get()
        Logger.log(f"Opening {mode_name} with {selected_model}.", builder_class.mode_name)
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
        """Busy page with a spinning bar, shown while a model loads."""
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
            Logger.log(f"Ignoring late load result for {model_name}.")
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
        if page_class.geometry:
            # A mode that holds more than one page asks for a bigger window.
            self.root.geometry(page_class.geometry)
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
            lambda on_close: LoggerPopup(self.root, on_close=on_close),
        )

    def show_environment_generator(self):
        """Open the environment window, or raise the one that is already open."""
        return self._open_window(
            "environment_generator_instance",
            # Read fresh: the page shows what is in .env right now, not at startup.
            lambda on_close: EnvironmentTablePopup(
                self.root, Environment.get_all_environment(), on_close=on_close
            ),
        )

    def show_add_model(self):
        """Open the model add window, or raise the one that is already open."""
        return self._open_window(
            "model_pop_up_adder_instance",
            lambda on_close: ModelAdderPopup(self.root,self._models_manager,on_close=on_close),
        )

    # ---- subscriptions ----
    def _on_models_changed(self,models):
        self._models = models
        for combo in self.model_comboboxes.values():
             if combo.winfo_exists():
                combo["values"] = models

    # ---- shutdown ----
    def _on_close(self):
        """Hand the window's own state to Environment, then write everything out."""
        Environment.set_data(
            DataKey.SELECTED_MODELS,
            {mode_name: var.get() for mode_name, var in self.model_vars.items()},
        )
        Environment.save()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
