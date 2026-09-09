from tkinter import messagebox
import tkinter as tk
import webbrowser
from constants import OLLAMA_LIBRARY_URL
from theme import Theme


class ModelAdderPopup(tk.Toplevel):

    def __init__(self, parent,models_manager,on_close=None):
        super().__init__(parent)
        self.models_manager = models_manager
        self.on_close = on_close
        self.title("Add new model")
        self.geometry("650x430")
        self.configure(bg=Theme.BG)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.window = tk.Frame(self)
        self.window.pack(fill=tk.BOTH, expand=True)
        Theme.heading(self.window,"Current Models").pack(anchor=tk.W,padx=15,pady=(16, 2))
        link_frame = tk.Frame(self.window)
        link_frame.pack(anchor=tk.W,padx=15)
        Theme.hint(link_frame,"Open the Ollama library to see all models: ").pack(side=tk.LEFT)
        link = tk.Label(link_frame,text=OLLAMA_LIBRARY_URL,fg=Theme.INFO,cursor="hand2",font=(*Theme.FONT_SMALL, "underline"))
        link.pack(side=tk.LEFT)
        link.bind("<Button-1>", self.open_library)
        Theme.hint(self.window,"Paste the model name into the box below and click Add Model.").pack(anchor=tk.W,padx=15,pady=(2, 0))
        self.models_list = tk.Listbox(self.window,width=80,height=12)
        self.models_list.pack(padx=15,pady=12,fill=tk.BOTH,expand=True)
        add_frame = tk.Frame(self.window)
        add_frame.pack(fill=tk.X,padx=15,pady=(0, 15))
        self.model_entry = tk.Entry(add_frame)
        self.model_entry.pack(side=tk.LEFT,fill=tk.X,expand=True,padx=(0, 10))
        tk.Button(add_frame,text="Add Model",width=15,command=self.add_model,**Theme.PRIMARY_BUTTON
        ).pack(side=tk.RIGHT)
        self.models_manager.subscribe(self.update_models)
        self.update_models(self.models_manager.get_all_models())

    def open_library(self, event=None):
        webbrowser.open_new_tab(OLLAMA_LIBRARY_URL)

    def update_models(self, models):
        self.models_list.delete(0, tk.END)
        for model in models:
            self.models_list.insert(tk.END, model)

    def add_model(self):
        model = self.model_entry.get().strip()
        if not model:
            messagebox.showwarning("Invalid Model","Please enter a model name.")
            return
        if model in self.models_manager.get_all_models():
            messagebox.showinfo("Model Exists","This model already exists.")
            return
        self.models_manager.add_model(model)
        self.model_entry.delete(0, tk.END)

    def _close(self):
        self.destroy()
        if self.on_close is not None:
            self.on_close()
            self.models_manager.unsubscribe(self.update_models)

