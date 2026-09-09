from tkinter import messagebox
import tkinter as tk
import webbrowser
from constants import OLLAMA_LIBRARY_URL


class ModelAdderPopup(tk.Toplevel):

    def __init__(self, parent,models_manager,on_close=None):
        super().__init__(parent)
        self.models_manager = models_manager
        self.on_close = on_close
        self.title("Add new model")
        self.geometry("650x400")
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.window = tk.Frame(self)
        self.window.pack(fill=tk.BOTH, expand=True)
        tk.Label(self.window,text="Current Models",font=("Arial", 14, "bold")).pack(pady=(10, 5))
        link_frame = tk.Frame(self.window)
        link_frame.pack(pady=(0, 0))
        tk.Label(link_frame,text="Open Ollama Library to see all models: ",font=("Arial", 10)).pack(side=tk.LEFT)
        link = tk.Label(link_frame,text=OLLAMA_LIBRARY_URL,fg="blue",cursor="hand2",font=("Arial", 10, "underline"))
        link.pack(side=tk.LEFT)
        link.bind("<Button-1>", self.open_library)
        tk.Label(self.window,text="Paste the model name into the box below and click Add Model",font=("Arial", 10)).pack(pady=(0, 10))
        self.models_list = tk.Listbox(self.window,width=80,height=12)
        self.models_list.pack(padx=15,pady=5,fill=tk.BOTH,expand=True)
        add_frame = tk.Frame(self.window)
        add_frame.pack(fill=tk.X,padx=15,pady=10)
        self.model_entry = tk.Entry(add_frame)
        self.model_entry.pack(side=tk.LEFT,fill=tk.X,expand=True,padx=(0, 10))
        tk.Button(add_frame,text="Add Model",width=15,command=self.add_model
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

