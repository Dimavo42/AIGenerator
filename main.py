import threading
from core.clientManager import ClientManager
from core.ollamaServerManager import OllamaServerManager
from scripts.environment import Environment


def main():
    Environment.load()
    threading.Thread(target=OllamaServerManager().start_ollama_server, daemon=True).start()
    try:
        ClientManager().run()
    finally:
        Environment.save()

if __name__ == "__main__":
    main()
