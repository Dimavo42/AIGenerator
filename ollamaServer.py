import threading
import ollama
import subprocess
import time
import socket
from constants import ServerStatus, ModelStatus


class OllamaServer:
    def __init__(self, model: str = "qwen2.5-coder:14b"):
        self.model = model
        self.server_status = ServerStatus.NOT_RUNNING
        self.model_status = ModelStatus.NOT_LOADED
        self.server_process = None

    def get_server_status(self):
        return self.server_status
    
    def get_model_status(self):
        return self.model_status

    def get_model(self):
        return self.model
    
    def is_server_running(self):
        """Check if Ollama server is already running"""
        try:
            with socket.create_connection(("localhost", 11434), timeout=1):
                return True
        except OSError:
            return False
    
    def start_server(self):
        """Start the Ollama server"""
        if self.is_server_running():
            print("Ollama server is already running on localhost:11434")
            self.server_status = ServerStatus.RUNNING
            return
        
        try:
            self.server_status = ServerStatus.STARTING
            print("Starting Ollama server...")
            # Start ollama serve in the background
            self.server_process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            for _ in range(60):  
                if self.is_server_running():
                    self.server_status = ServerStatus.RUNNING
                    print("Ollama server started successfully.")
                    self.initialize()
                    return True
                if self.server_process.poll() is not None:
                    break  # Process has exited, likely an error
                time.sleep(0.5)
           
            self.server_status = ServerStatus.ERROR
            print("Error: Ollama server failed to start.")
            return False
        except FileNotFoundError:
            print("Error: 'ollama' command not found. Please install Ollama from https://ollama.ai")
            return False
        except Exception as e:
            print(f"Error starting server: {e}")
            return False

    def pull_model(self):
        """Pull the model if not already present"""
        try:
            print(f"Checking for model: {self.model}...")
            ollama.pull(self.model)
            print(f"Model {self.model} is ready.")
        except Exception as e:
            print(f"Error pulling model: {e}")
            return False

    def initialize(self):
        """Initialize server and model"""
        if not self.is_server_running():
            return False
        try:
            self.pull_model()
            self.model_status = ModelStatus.LOADED
            return True
        except Exception as e:
            print(f"Error initializing Qwen: {e}")
            return False

    def ask(self, question: str) -> str:
        """Ask Qwen a question"""
        if not self.is_server_running():
            print("Server is not running. Call initialize() first.")
            return ""
        
        try:
            print(f"Asking question: {question}")
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": question
                    }
                ]
            )
            result = response["message"]["content"]
            print(f"Received response: {result}")
            return result
        except Exception as e:
            print(f"Error asking question: {e}")
            return f"Error: {str(e)}"
    
    def stop_server(self):
        """Stop the Ollama server"""
        if self.server_status == ServerStatus.RUNNING:
            print("Stopping Ollama server...")
            self.server_process.terminate()
            self.server_process = None  
            self.server_status = ServerStatus.NOT_RUNNING
            print("Server stopped.")

    def change_model(self, new_model: str):
        """Change the model being used"""
        if self.model != new_model:
            print(f"Changing model from {self.model} to {new_model}...")
            def worker():
                try:
                    self.server_status = ServerStatus.STARTING
                    self.pull_model()
                    self.model = new_model
                    self.server_status = ServerStatus.RUNNING
                except Exception as e:
                    print(f"Error changing model: {e}")
                    self.server_status = ServerStatus.ERROR
            threading.Thread(target=worker, daemon=True).start()
            print(f"Model changed to {self.model}.")
        else:
            print(f"Model is already set to {self.model}. No change needed.")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.stop_server()






