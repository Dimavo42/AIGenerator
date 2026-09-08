import threading
from collections import deque
from datetime import datetime
from constants import LogSource

class Logger:
    _lock = threading.Lock()
    _logs = { LogSource.GLOBAL: deque(maxlen=100)  }

    @classmethod
    def log(cls, message, instance_name = None):
        date_time = datetime.now()
        if instance_name is None:
            instance_name = LogSource.GLOBAL
        with cls._lock:
            if instance_name not in cls._logs:
                cls._logs[instance_name] = deque(maxlen=100)
            cls._logs[instance_name].append((date_time,f"[{date_time:%H:%M:%S}] [{instance_name}] {message}"))

    @classmethod
    def get_logs_by_name(cls,instance_name = None):
        if instance_name is None:
            instance_name = LogSource.GLOBAL
        with cls._lock:
            logs = cls._logs.get(instance_name)
            if logs is None:
                return []
            return [message for _,message in logs]

    @classmethod
    def get_all_logs(cls):
        logs = []
        with cls._lock:
            for instance_logs in cls._logs.values():
                logs.extend(instance_logs)
        logs.sort(key= lambda log : log[0])
        return [message for _,message in logs]

    @classmethod
    def get_instance_names(cls):
        """Names that currently hold logs - used to populate the viewer filter."""
        with cls._lock:
            return sorted(cls._logs)


