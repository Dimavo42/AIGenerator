import threading
from collections import deque
from datetime import datetime, timedelta

GLOBAL = 'global'


class Logger:
    def __init__(self):
        # Worker threads write while the Tk thread reads, so every touch of
        # _logs goes through the lock.
        self._lock = threading.Lock()
        self._logs = {
            GLOBAL: deque(maxlen=100)  # Keep the last 100 global logs
        }

    def log(self, message, instance_name = None):
        date_time = datetime.now()
        if instance_name is None:
            instance_name = GLOBAL
        with self._lock:
            if instance_name not in self._logs:
                self._logs[instance_name] = deque(maxlen=100)
            self._logs[instance_name].append((date_time,f"[{date_time:%H:%M:%S}] [{instance_name}] {message}"))

    def get_logs_by_name(self,instance_name = None):
        if instance_name is None:
            instance_name = GLOBAL
        with self._lock:
            logs = self._logs.get(instance_name)
            if logs is None:
                return []
            return [message for _,message in logs]

    def get_logs_by_time_frame(self,seconds,instance_name = None):
        if instance_name is None:
            instance_name = GLOBAL
        cut_time = datetime.now() - timedelta(seconds=seconds)
        with self._lock:
            logs = self._logs.get(instance_name)
            if logs is None:
                return []
            return [message for timestamp,message in logs if timestamp >= cut_time]

    def get_all_logs(self):
        logs = []
        with self._lock:
            for instance_logs in self._logs.values():
                logs.extend(instance_logs)
        logs.sort(key= lambda log : log[0])
        return [message for _,message in logs]

    def get_instance_names(self):
        """Names that currently hold logs - used to populate the viewer filter."""
        with self._lock:
            return sorted(self._logs)


# One logger shared by the whole app; import this rather than building your own.
logger = Logger()
