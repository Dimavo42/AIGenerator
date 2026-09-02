import threading
from clientGUI import ClientGUI
from qwenServerManager import QwenServerManager


def main():
    # Warm up Ollama + the model in the background so the GUI shows up instantly.
    threading.Thread(target=QwenServerManager().start_qwen_server, daemon=True).start()
    ClientGUI().run()


if __name__ == "__main__":
    main()
