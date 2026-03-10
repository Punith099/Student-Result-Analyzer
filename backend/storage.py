import json
import os
import tempfile
from typing import Any
from filelock import FileLock


class JsonStore:
    def __init__(self, path: str, default: Any):
        self.path = path
        self.default = default
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            self.write(default)

    def read(self):
        lock = FileLock(self.path + ".lock")
        with lock:
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self.default

    def write(self, data):
        lock = FileLock(self.path + ".lock")
        with lock:
            atomic_write(self.path, data)


def atomic_write(path: str, data: Any):
    directory = os.path.dirname(path)
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".tmp_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
            json.dump(data, tmp_file, ensure_ascii=False, indent=2)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(tmp_path, path)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass


