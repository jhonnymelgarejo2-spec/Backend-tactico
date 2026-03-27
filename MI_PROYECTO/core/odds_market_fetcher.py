import os
from typing import Dict, Any, List, Optional

import requests


BASE_URL = "https://api.the-odds-api.com/v4/sports/soccer/odds"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        return float(value)
    except Exception:
        return default


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _normalize_team_name(name: str) -> str:
    text = _safe_text(name).lower()
    text = text.replace(".", " ")
    text = text.replace(",", " ")
    text = text.replace("-", " ")
    text = text.replace("_", " ")
    text = " ".join(text.split())
    return text


def _tokenize_team_name(name: str) -> List[str]:
    text = _normalize_team_name(name)
    if not text:
        return []
    return [tok for tok in text.split() if tok]


def _similar_team_score(name_a: str, name_b: str) -> int:
    a = _normalize_team_name(name_a)
    b = _normalize_team_name(name_b)

    if not a or not b:
        return 0

    if a == b:
        return 100

    if a in b or b in a:
        return 70

    tokens_a = set(_tokenize_team_name(a))
    tokens_b = set(_tokenize_team_name(b))

    if not tokens_a or not tokens_b:
        return 0

    common = tokens_a.intersection(tokens_b)
    if not common:
        return 0

    score = len(common) * 20

    if len(common) >= 2:
        score += 10

    return min(score, 95)


def _match_score(local_a: str, visitante_a: str, local_b: str, visitante_b: str) -> int:
    direct_score = _similar_team_score(local_a, local_b) + _similar_team_score(visitante_a, visitante_b)
    inverse_score = _similar_team_score(local_a, visitante_b) + _similar_team_score(visitante_a, local_b)
    return max(direct_score, inverse_score)


def _extract_away_team(event: Dict[str, Any]) -> str:
    home_team = _safe_text(event.get("home_team"))
    away_team = _safe_text(event.get("away_team"))

    if away_team:
        return away_team

    teams = event.get("teams") or []
    if isinstance(teams, list) and len(teams) == 2:
        for team in teams:
            team_name = _safe_text(team)
            if team_name and team_name != home_team:
                return team_name

    return ""


def _extract_totals_market(bookmakers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    for bookmaker in bookmakers or []:
        bookmaker_title = _safe_text(bookmaker.get("title"), "bookmaker_desconocido")
        markets = bookmaker.get("markets") or []

        for market in markets:
            market_key = _safe_text(market.get("key")).lower()
            if market_key != "totals":
                continue

            outcomes = market.get("outcomes") or []
            grouped: Dict[float, Dict[str, float]] = {}

            for outcome in outcomes:
                outcome_name = _safe_text(outcome.get("name")).upper()
                point = _safe_float(outcome.get("point"), 0.0)
                price = _safe_float(outcome.get("price"), 0.0)

                if point <= 0 or price <= 0:
                    continue

                grouped.setdefault(point, {})
                grouped[point][outcome_name] = price

            for point, prices in grouped.items():
                over_price = _safe_float(prices.get("OVER"), 0.0)
                under_price = _safe_float(prices.get("UNDER"), 0.0)

                results.append({
                    "bookmaker": bookmaker_title,
                    "line": point,
                    "over_price": over_price,
                    "under_price": under_price,
                })

    return results


def _choose_best_event(events: List[Dict[str, Any]], local: str, visitante: str) -> Optional[Dict[str, Any]]:
    best_event = None
    best_score = -1

    for event in events or []:
        home_team = _safe_text(event.get("home_team"))
        away_team = _extract_away_team(event)

        score = _match_score(local, visitante, home_team, away_team)

        if score > best_score:
            best_score = score
            best_event = event

    if best_event is None:
        return None

    if best_score < 40:
        return None

    return best_event


def obtener_odds_partido(local: str, visitante: str) -> Dict[str, Any]:
    api_key = os.getenv("THE_ODDS_API_KEY", "").strip()

    if not api_key:
        return {
            "ok": False,
            "error": "THE_ODDS_API_KEY no configurada",
            "odds_data_available": False,
            "home_team": "",
            "away_team": "",
            "commence_time": "",
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
                "home_team": "",
                "away_team": "",
                "commence_time": "",
                "markets": [],
            }

        best_event = _choose_best_event(data, local, visitante)

        if not best_event:
            return {
                "ok": False,
                "error": "no se encontró partido compatible en The Odds API",
                "odds_data_available": False,
                "home_team": "",
                "away_team": "",
                "commence_time": "",
                "markets": [],
            }

        home_team = _safe_text(best_event.get("home_team"))
        away_team = _extract_away_team(best_event)
        commence_time = _safe_text(best_event.get("commence_time"))
        bookmakers = best_event.get("bookmakers") or []

        markets = _extract_totals_market(bookmakers)

        return {
            "ok": True,
            "error": "",
            "odds_data_available": len(markets) > 0,
            "home_team": home_team,
            "away_team": away_team,
            "commence_time": commence_time,
            "markets": markets,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "odds_data_available": False,
            "home_team": "",
            "away_team": "",
            "commence_time": "",
            "markets": [],
    }
