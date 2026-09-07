import ollama
import subprocess
import time
import socket
from constants import MODELS, LogSource, ServerStatus, ModelStatus
from logger import logger


class OllamaServer:
    def __init__(self, model: str = MODELS[0]):
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
    
    def start_server(self) -> ServerStatus:
        """Start the Ollama server. Returns the resulting ServerStatus."""
        if self.is_server_running():
            logger.log("Ollama server is already running on localhost:11434", LogSource.SERVER)
            self.server_status = ServerStatus.RUNNING
            return self.server_status
        try:
            self.server_status = ServerStatus.STARTING
            logger.log("Starting Ollama server...", LogSource.SERVER)
            # Start ollama serve in the background
            self.server_process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            for _ in range(60):
                if self.is_server_running():
                    self.server_status = ServerStatus.RUNNING
                    logger.log("Ollama server started successfully.", LogSource.SERVER)
                    return self.server_status
                if self.server_process.poll() is not None:
                    break  # Process has exited, likely an error
                time.sleep(0.5)

            self.server_status = ServerStatus.ERROR
            logger.log("Error: Ollama server failed to start.", LogSource.SERVER)
            return self.server_status
        except FileNotFoundError:
            self.server_status = ServerStatus.ERROR
            logger.log("Error: 'ollama' command not found. Please install Ollama from https://ollama.ai", LogSource.SERVER)
            return self.server_status
        except Exception as e:
            self.server_status = ServerStatus.ERROR
            logger.log(f"Error starting server: {e}", LogSource.SERVER)
            return self.server_status

    def pull_model(self) -> ModelStatus:
        """Pull the current model if not already present. Blocks until ready."""
        try:
            logger.log(f"Checking for model: {self.model}...", self.model)
            self.model_status = ModelStatus.LOADING
            ollama.pull(self.model)
            self.model_status = ModelStatus.LOADED
            logger.log(f"Model {self.model} is ready.", self.model)
            return self.model_status
        except Exception as e:
            self.model_status = ModelStatus.ERROR
            logger.log(f"Error pulling model: {e}", self.model)
            return self.model_status

    def initialize(self) -> ModelStatus:
        """Start the server (if needed) and make the current model ready."""
        if self.start_server() != ServerStatus.RUNNING:
            self.model_status = ModelStatus.ERROR
            return self.model_status
        return self.pull_model()

    def ask(self, question: str) -> str:
        """Ask Qwen a question"""
        if not self.is_server_running():
            self.server_status = ServerStatus.NOT_RUNNING
            logger.log("Server is not running. Call initialize() first.", LogSource.SERVER)
            return ""

        try:
            logger.log(f"Asking question: {question}", self.model)
            self.model_status = ModelStatus.GENERATING
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
            self.model_status = ModelStatus.LOADED
            logger.log(f"Received response ({len(result)} chars)", self.model)
            return result
        except Exception as e:
            self.model_status = ModelStatus.ERROR
            logger.log(f"Error asking question: {e}", self.model)
            return f"Error: {str(e)}"

    def stop_server(self) -> ServerStatus:
        """Stop the Ollama server. Returns the resulting ServerStatus."""
        # Only a server this object spawned can be stopped; one that was
        # already up belongs to somebody else.
        if self.server_status == ServerStatus.RUNNING and self.server_process is not None:
            logger.log("Stopping Ollama server...", LogSource.SERVER)
            self.server_process.terminate()
            self.server_process = None
            self.server_status = ServerStatus.NOT_RUNNING
            self.model_status = ModelStatus.NOT_LOADED
            logger.log("Server stopped.", LogSource.SERVER)
        return self.server_status

    def change_model(self, new_model: str) -> ModelStatus:
        """Switch to another model. Blocks while it downloads - call from a worker thread."""
        if self.model == new_model and self.model_status == ModelStatus.LOADED:
            logger.log(f"Model is already set to {self.model}. No change needed.", self.model)
            return self.model_status

        logger.log(f"Changing model from {self.model} to {new_model}...", new_model)
        previous_model = self.model
        previous_status = self.model_status
        self.model = new_model
        if self.initialize() == ModelStatus.LOADED:
            logger.log(f"Model changed to {self.model}.", self.model)
            return self.model_status
        # Keep the object honest about what is actually loaded.
        logger.log(f"Failed to load {new_model}, staying on {previous_model}.", new_model)
        self.model = previous_model
        self.model_status = previous_status
        return ModelStatus.ERROR

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.stop_server()






