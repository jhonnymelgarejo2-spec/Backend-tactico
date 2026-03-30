# app/utils/helpers.py

from typing import Any


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        return float(value)
    except Exception:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        return int(float(value))
    except Exception:
        return default


def safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def safe_upper(value: Any, default: str = "") -> str:
    return safe_text(value, default).upper()


def safe_lower(value: Any, default: str = "") -> str:
    return safe_text(value, default).lower()


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))# app/utils/helpers.py

from typing import Any


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        return float(value)
    except Exception:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        return int(float(value))
    except Exception:
        return default


def safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def safe_upper(value: Any, default: str = "") -> str:
    return safe_text(value, default).upper()


def safe_lower(value: Any, default: str = "") -> str:
    return safe_text(value, default).lower()


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))
