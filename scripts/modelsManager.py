from constants import MODELS


class ModelsManager:
    def __init__(self):
        self._models = MODELS
        self._subscribers = []

    def subscribe(self, callback):
        self._subscribers.append(callback)

    def unsubscribe(self, callback):
        self._subscribers.remove(callback)

    def _notify(self):
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



