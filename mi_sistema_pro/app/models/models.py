# app/models/models.py

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ScanResult:
    total_matches: int = 0
    total_signals: int = 0
    signals: List[Dict[str, Any]] = field(default_factory=list)
    hot_matches: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
