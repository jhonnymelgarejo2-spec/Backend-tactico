from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class Partido:
    id: str = ""
    local: str = "Local"
    visitante: str = "Visitante"
    liga: str = "Liga desconocida"
    pais: str = "Mundo"

    minuto: int = 0
    estado_partido: str = "en_juego"
    marcador_local: int = 0
    marcador_visitante: int = 0

    xG: float = 0.0
    shots: int = 0
    shots_on_target: int = 0
    dangerous_attacks: int = 0
    momentum: str = "MEDIO"

    prob_real: float = 0.0
    prob_implicita: float = 0.0
    cuota: float = 0.0

    goal_pressure: Dict[str, Any] = field(default_factory=dict)
    goal_predictor: Dict[str, Any] = field(default_factory=dict)
    chaos: Dict[str, Any] = field(default_factory=dict)

    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Senal:
    match_id: str = ""
    partido: str = ""
    market: str = ""
    selection: str = ""
    line: float = 0.0

    odd: float = 0.0
    prob_real: float = 0.0
    prob_implicita: float = 0.0
    confidence: float = 0.0
    value: float = 0.0
    risk_score: float = 0.0

    signal_score: float = 0.0
    signal_rank: str = "NORMAL"
    recomendacion_final: str = "OBSERVAR"
    publish_ready: bool = False

    reason: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScanResult:
    total_matches: int = 0
    total_signals: int = 0
    signals: List[Dict[str, Any]] = field(default_factory=list)
    hot_matches: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
