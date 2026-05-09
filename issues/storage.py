import json
from pathlib import Path
from django.conf import settings


def _path(filename: str) -> Path:
    return settings.BASE_DIR / filename


def load(filename: str) -> list:
    path = _path(filename)
    if not path.exists():
        return []
    with open(path, 'r') as f:
        return json.load(f)


def save(filename: str, data: list) -> None:
    with open(_path(filename), 'w') as f:
        json.dump(data, f, indent=2)
