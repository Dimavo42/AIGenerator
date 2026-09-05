import threading
from clientGUI import ClientGUI
from ollamaServerManager import OllamaServerManager


def main():
    # Warm up Ollama + the model in the background so the GUI shows up instantly.
    threading.Thread(target=OllamaServerManager().start_ollama_server, daemon=True).start()
    ClientGUI().run()


if __name__ == "__main__":
    main()
