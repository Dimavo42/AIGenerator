from abc import ABC, abstractmethod
import threading
from constants import ModelStatus
from core.logger import Logger
from core.ollamaServerManager import OllamaServerManager


class PageBuilder(ABC):
    """Mode logic only: take a question, ask the server, hand back the answer.

    Nothing here knows about Tk or any other toolkit - a concrete page decides
    how the status and the answer are shown.
    """

    mode_name = ""
    # Window size the page wants, or None to keep whatever the window has.
    geometry = None

    def ask(self, question: str) -> bool:
        """Ask the model in the background.

        Returns False when there was nothing to ask, so the caller can skip
        clearing its input.
        """
        question = (question or "").strip()
        if not question:
            return False
        Logger.log(f"Asking: {question}", self.mode_name)
        self.on_status(ModelStatus.GENERATING)
        threading.Thread(target=self._ask_worker, args=(question,), daemon=True).start()
        return True

    def _ask_worker(self, question: str):
        response = OllamaServerManager.ask_ollama(question)
        # The manager answers with a ModelStatus instead of text when it could
        # not reach the model at all.
        if isinstance(response, ModelStatus):
            self.on_response(None, response)
        else:
            self.on_response(response, OllamaServerManager.get_model_status())

    @abstractmethod
    def build(self, app, parent=None):
        """Build the page inside `parent` (app.container by default) and return it.

        Called on the caller's thread. `parent` lets a page be embedded in
        another page instead of filling the window on its own.
        """

    @abstractmethod
    def on_status(self, status: ModelStatus):
        """Model status changed. Called on the caller's thread."""

    @abstractmethod
    def on_response(self, response: str | None, status: ModelStatus):
        """The answer arrived, or None when the ask failed.

        Called from a worker thread - marshal to the UI thread if needed.
        """
