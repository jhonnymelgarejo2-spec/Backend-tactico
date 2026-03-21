from typing import Dict, List, Any


# =========================================================
# HELPERS
# =========================================================
def _safe_float(value, default=0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value, default=0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _safe_upper(value) -> str:
    return str(value or "").strip().upper()


def _clamp(value, low, high):
    return max(low, min(high, value))


# =========================================================
# EXTRACTORES
# =========================================================
def _extraer_partidos_recientes(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in (
        "recent_matches",
        "last_matches",
        "form_matches",
        "ultimos_partidos",
        "team_last_matches",
    ):
        value = data.get(key)
        if isinstance(value, list):
            return value
    return []


def _extraer_h2h(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in (
        "h2h",
        "head_to_head",
        "historial_h2h",
        "h2h_matches",
    ):
        value = data.get(key)
        if isinstance(value, list):
            return value
    return []


# =========================================================
# ANALISIS DE FORMA RECIENTE
# =========================================================
def analizar_forma_reciente(partido: Dict[str, Any]) -> Dict[str, Any]:
    partidos = _extraer_partidos_recientes(partido)

    if not partidos:
        return {
            "pre_form_score": 0.0,
            "pre_form_label": "SIN_DATOS",
            "pre_form_reason": "No hay partidos recientes disponibles",
            "pre_avg_goals_recent": 0.0,
            "pre_avg_conceded_recent": 0.0,
            "pre_btts_recent": 0.0,
            "pre_over25_recent": 0.0,
        }

    total = len(partidos)
    goles_favor = 0
    goles_contra = 0
    btts_count = 0
    over25_count = 0
    wins = 0
    draws = 0

    for p in partidos:
        gf = _safe_int(p.get("gf", p.get("goles_favor", 0)), 0)
        gc = _safe_int(p.get("gc", p.get("goles_contra", 0)), 0)

        goles_favor += gf
        goles_contra += gc

        if gf > 0 and gc > 0:
            btts_count += 1

        if (gf + gc) >= 3:
            over25_count += 1

        if gf > gc:
            wins += 1
        elif gf == gc:
            draws += 1

    avg_favor = round(goles_favor / total, 2)
    avg_contra = round(goles_contra / total, 2)
    btts_pct = round((btts_count / total) * 100, 2)
    over25_pct = round((over25_count / total) * 100, 2)

    score = 0.0
    score += wins * 2.0
    score += draws * 0.8
    score += avg_favor * 5.0
    score -= avg_contra * 2.0
    score += (btts_pct / 100.0) * 4.0
    score += (over25_pct / 100.0) * 4.0
    score = round(_clamp(score, 0, 20), 2)

    if score >= 15:
        label = "MUY_FUERTE"
        reason = "Forma reciente muy positiva con producción ofensiva alta"
    elif score >= 10:
        label = "FUERTE"
        reason = "Buena tendencia reciente y métricas ofensivas aceptables"
    elif score >= 6:
        label = "MEDIA"
        reason = "Forma reciente mixta sin dominio claro"
    else:
        label = "DEBIL"
        reason = "Forma reciente pobre o poco consistente"

    return {
        "pre_form_score": score,
        "pre_form_label": label,
        "pre_form_reason": reason,
        "pre_avg_goals_recent": avg_favor,
        "pre_avg_conceded_recent": avg_contra,
        "pre_btts_recent": btts_pct,
        "pre_over25_recent": over25_pct,
    }


# =========================================================
# ANALISIS H2H
# =========================================================
def analizar_h2h(partido: Dict[str, Any]) -> Dict[str, Any]:
    h2h = _extraer_h2h(partido)

    if not h2h:
        return {
            "pre_h2h_score": 0.0,
            "pre_h2h_label": "SIN_DATOS",
            "pre_h2h_reason": "No hay historial H2H disponible",
            "pre_h2h_avg_goals": 0.0,
            "pre_h2h_btts": 0.0,
            "pre_h2h_over25": 0.0,
        }

    total = len(h2h)
    total_goals = 0
    btts_count = 0
    over25_count = 0

    for p in h2h:
        hg = _safe_int(p.get("home_goals", p.get("hg", 0)), 0)
        ag = _safe_int(p.get("away_goals", p.get("ag", 0)), 0)

        total_goals += (hg + ag)

        if hg > 0 and ag > 0:
            btts_count += 1

        if (hg + ag) >= 3:
            over25_count += 1

    avg_goals = round(total_goals / total, 2)
    btts_pct = round((btts_count / total) * 100, 2)
    over25_pct = round((over25_count / total) * 100, 2)

    score = 0.0
    score += avg_goals * 3.0
    score += (btts_pct / 100.0) * 5.0
    score += (over25_pct / 100.0) * 5.0
    score = round(_clamp(score, 0, 20), 2)

    if score >= 14:
        label = "ABIERTO"
        reason = "Historial H2H con tendencia clara a goles"
    elif score >= 9:
        label = "MIXTO"
        reason = "Historial H2H moderadamente favorable para goles"
    else:
        label = "CERRADO"
        reason = "Historial H2H cerrado o poco productivo"

    return {
        "pre_h2h_score": score,
        "pre_h2h_label": label,
        "pre_h2h_reason": reason,
        "pre_h2h_avg_goals": avg_goals,
        "pre_h2h_btts": btts_pct,
        "pre_h2h_over25": over25_pct,
    }


# =========================================================
# LECTURA PRE MATCH GLOBAL
# =========================================================
def evaluar_pre_match(partido: Dict[str, Any]) -> Dict[str, Any]:
    forma = analizar_forma_reciente(partido)
    h2h = analizar_h2h(partido)

    score_forma = _safe_float(forma.get("pre_form_score", 0), 0)
    score_h2h = _safe_float(h2h.get("pre_h2h_score", 0), 0)

    avg_goals_recent = _safe_float(forma.get("pre_avg_goals_recent", 0), 0)
    avg_goals_h2h = _safe_float(h2h.get("pre_h2h_avg_goals", 0), 0)
    over25_recent = _safe_float(forma.get("pre_over25_recent", 0), 0)
    over25_h2h = _safe_float(h2h.get("pre_h2h_over25", 0), 0)

    score_total = round((score_forma * 0.55) + (score_h2h * 0.45), 2)

    supports_over = (
        avg_goals_recent >= 1.4 or
        avg_goals_h2h >= 2.2 or
        over25_recent >= 55 or
        over25_h2h >= 55
    )

    supports_hold = (
        avg_goals_recent < 1.2 and
        avg_goals_h2h < 2.1 and
        over25_recent < 50 and
        over25_h2h < 50
    )

    if score_total >= 14:
        state = "MUY_FAVORABLE"
        reason = "El contexto previo apoya un partido abierto y con buena tendencia ofensiva"
    elif score_total >= 9:
        state = "FAVORABLE"
        reason = "El pre-partido muestra señales mixtas pero utilizables"
    elif score_total >= 5:
        state = "NEUTRO"
        reason = "No hay ventaja pre-match clara"
    else:
        state = "DESFAVORABLE"
        reason = "El contexto previo no apoya escenarios ofensivos fuertes"

    return {
        **forma,
        **h2h,
        "pre_match_score": score_total,
        "pre_match_state": state,
        "pre_match_reason": reason,
        "pre_match_supports_over": supports_over,
        "pre_match_supports_hold": supports_hold,
    }


# =========================================================
# APLICAR SOBRE SEÑAL
# =========================================================
def aplicar_pre_match(signal: Dict[str, Any], partido: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(signal, dict):
        return signal

    pre = evaluar_pre_match(partido)
    signal.update(pre)

    market = _safe_upper(signal.get("market", ""))

    # =========================================
    # AJUSTE SUAVE DE CONFIANZA
    # =========================================
    confidence = _safe_float(signal.get("confidence", 0), 0)
    score = _safe_float(pre.get("pre_match_score", 0), 0)

    ajuste = 0.0
    if score >= 14:
        ajuste += 4.0
    elif score >= 9:
        ajuste += 2.0
    elif score < 5:
        ajuste -= 3.0

    if "OVER" in market or "GOAL" in market or "NEXT_GOAL" in market:
        if pre.get("pre_match_supports_over"):
            ajuste += 2.0
        if pre.get("pre_match_supports_hold"):
            ajuste -= 2.0

    if "HOLD" in market or "RESULT_HOLDS" in market:
        if pre.get("pre_match_supports_hold"):
            ajuste += 2.0
        if pre.get("pre_match_supports_over"):
            ajuste -= 2.0

    signal["confidence"] = round(_clamp(confidence + ajuste, 0, 100), 2)
    signal["pre_match_adjustment"] = round(ajuste, 2)

    return signal
