from constants import MODELS, DataKey
from scripts.environment import Environment


class ModelsManager:
    def __init__(self):
        # The list the user last left behind, or the built-in one on a first run.
        self._models = list(Environment.get_data(DataKey.MODELS, MODELS))
        self._subscribers = []

    def subscribe(self, callback):
        self._subscribers.append(callback)

    def unsubscribe(self, callback):
        self._subscribers.remove(callback)

    def _notify(self):
        # The list just changed, so this is also where it is remembered.
        Environment.set_data(DataKey.MODELS, self._models)
        for callback in self._subscribers:
            callback(self._models)

    def get_all_models(self):
        return self._models.copy()

    def add_model(self,model):
        if model not in self._models:
            self._models.append(model)
            self._notify()

    def remove_model(self,model):
        if model in self._models:
            self._models.remove(model)
            self._notify()
