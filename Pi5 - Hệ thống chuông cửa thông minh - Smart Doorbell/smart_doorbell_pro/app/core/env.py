import os
from pathlib import Path
from typing import Callable, Optional


def _parse_env_value(value: str) -> str:
    value = value.strip()
    if value and value[0] == value[-1] and value[0] in ("\"", "'"):
        return value[1:-1]
    return value


def load_env_file(path: str | Path, override: bool = False) -> dict:
    env = {}
    path = Path(path)
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = _parse_env_value(value)
        env[key] = value
        if override or key not in os.environ:
            os.environ[key] = value
    return env


def get_env(key: str, default=None, cast: Optional[Callable] = None):
    value = os.environ.get(key, default)
    if value is None:
        return None
    if cast is None:
        return value
    try:
        return cast(value)
    except Exception:
        return default


def as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}