import os
import requests
from typing import Dict, Any, List, Optional


BASE_URL = "https://api.the-odds-api.com/v4/sports/soccer/odds"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _normalize_team_name(name: str) -> str:
    return _safe_text(name).lower().replace(".", "").replace(",", "").strip()


def _match_score(home_a: str, away_a: str, home_b: str, away_b: str) -> int:
    score = 0

    ha = _normalize_team_name(home_a)
    aa = _normalize_team_name(away_a)
    hb = _normalize_team_name(home_b)
    ab = _normalize_team_name(away_b)

    if ha == hb:
        score += 2
    elif ha in hb or hb in ha:
        score += 1

    if aa == ab:
        score += 2
    elif aa in ab or ab in aa:
        score += 1

    return score


def _extract_totals_market(bookmakers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []

    for bookmaker in bookmakers or []:
        bookmaker_title = _safe_text(bookmaker.get("title"), "bookmaker_desconocido")
        markets = bookmaker.get("markets") or []

        for market in markets:
            if _safe_text(market.get("key")).lower() != "totals":
                continue

            outcomes = market.get("outcomes") or []
            pairs = {}

            for outcome in outcomes:
                name = _safe_text(outcome.get("name")).upper()
                point = _safe_float(outcome.get("point"), 0.0)
                price = _safe_float(outcome.get("price"), 0.0)

                if point <= 0 or price <= 0:
                    continue

                pairs.setdefault(point, {})
                pairs[point][name] = price

            for point, data in pairs.items():
                over_price = _safe_float(data.get("OVER"), 0.0)
                under_price = _safe_float(data.get("UNDER"), 0.0)

                results.append({
                    "bookmaker": bookmaker_title,
                    "line": point,
                    "over_price": over_price,
                    "under_price": under_price,
                })

    return results


def obtener_odds_partido(local: str, visitante: str) -> Dict[str, Any]:
    api_key = os.getenv("THE_ODDS_API_KEY", "").strip()

    if not api_key:
        return {
            "ok": False,
            "error": "THE_ODDS_API_KEY no configurada",
            "odds_data_available": False,
            "markets": [],
        }

    params = {
        "apiKey": api_key,
        "regions": "eu",
        "markets": "totals",
        "oddsFormat": "decimal",
        "bookmakers": "bet365,pinnacle,williamhill,unibet",
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=12)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            return {
                "ok": False,
                "error": "respuesta inválida de The Odds API",
                "odds_data_available": False,
                "markets": [],
            }

        best_event = None
        best_score = -1

        for event in data:
            home_team = _safe_text(event.get("home_team"))
            away_team = ""

            teams = event.get("teams") or []
            if len(teams) == 2:
                candidates = [t for t in teams if _safe_text(t) != home_team]
                if candidates:
                    away_team = _safe_text(candidates[0])

            if not away_team:
                commence_name = _safe_text(event.get("away_team"))
                away_team = commence_name

            score = _match_score(local, visitante, home_team, away_team)
            if score > best_score:
                best_score = score
                best_event = event

        if not best_event or best_score < 2:
            return {
                "ok": False,
                "error": "no se encontró partido compatible en The Odds API",
                "odds_data_available": False,
                "markets": [],
            }

        bookmakers = best_event.get("bookmakers") or []
        markets = _extract_totals_market(bookmakers)

        return {
            "ok": True,
            "error": "",
            "odds_data_available": len(markets) > 0,
            "home_team": _safe_text(best_event.get("home_team")),
            "away_team": _safe_text(
                next(
                    (t for t in (best_event.get("teams") or []) if _safe_text(t) != _safe_text(best_event.get("home_team"))),
                    ""
                )
            ),
            "commence_time": _safe_text(best_event.get("commence_time")),
            "markets": markets,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "odds_data_available": False,
            "markets": [],
  }
