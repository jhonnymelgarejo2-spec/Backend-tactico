import os
from typing import Dict, Any, List, Optional, Tuple

import requests


SPORTS_URL = "https://api.the-odds-api.com/v4/sports"
SPORT_ODDS_URL_TEMPLATE = "https://api.the-odds-api.com/v4/sports/{sport_key}/odds"


# =========================================================
# HELPERS
# =========================================================
def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        return int(float(value))
    except Exception:
        return default


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _normalize_text(text: str) -> str:
    t = _safe_text(text).lower()
    for ch in [".", ",", "-", "_", "/", "(", ")", ":", ";", "'"]:
        t = t.replace(ch, " ")
    t = " ".join(t.split())
    return t


def _normalize_team_name(name: str) -> str:
    text = _normalize_text(name)

    replacements = {
        "fc": "",
        "cf": "",
        "sc": "",
        "ac": "",
        "cd": "",
        "deportivo": "depor",
        "athletic": "ath",
        "atletico": "atletico",
        "club": "",
    }

    tokens = text.split()
    out = []
    for tok in tokens:
        mapped = replacements.get(tok, tok)
        if mapped:
            out.append(mapped)

    return " ".join(out).strip()


def _tokenize_team_name(name: str) -> List[str]:
    text = _normalize_team_name(name)
    return [tok for tok in text.split() if tok]


def _similar_team_score(name_a: str, name_b: str) -> int:
    a = _normalize_team_name(name_a)
    b = _normalize_team_name(name_b)

    if not a or not b:
        return 0

    if a == b:
        return 100

    if a in b or b in a:
        return 78

    tokens_a = set(_tokenize_team_name(a))
    tokens_b = set(_tokenize_team_name(b))
    if not tokens_a or not tokens_b:
        return 0

    common = tokens_a.intersection(tokens_b)
    if not common:
        return 0

    score = len(common) * 20

    if len(common) >= 2:
        score += 12

    if len(common) == len(tokens_a) or len(common) == len(tokens_b):
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


def _request_json(url: str, params: Dict[str, Any], timeout: int = 15) -> Any:
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


# =========================================================
# MAPEO DE LIGAS -> SPORT KEY
# =========================================================
def _league_mapping_candidates(league: str, country: str = "") -> List[str]:
    l = _normalize_text(league)
    c = _normalize_text(country)

    candidates: List[str] = []

    if "liga mx femenil" in l:
        candidates.append("soccer_mexico_ligamx")
    if "liga mx" in l:
        candidates.append("soccer_mexico_ligamx")
    if "liga de expansion" in l or "expansion mx" in l:
        candidates.append("soccer_mexico_ligamx")

    if "brasileirao" in l or ("serie a" in l and "brazil" in c):
        candidates.append("soccer_brazil_campeonato")

    if "primera nacional" in l:
        candidates.append("soccer_argentina_primera_nacional")
    if "primera division" in l or ("liga profesional" in l and "argentina" in c):
        candidates.append("soccer_argentina_primera_division")

    if "primera a" in l or "liga betplay" in l:
        candidates.append("soccer_colombia_primera_a")

    if "primera division" in l and "chile" in c:
        candidates.append("soccer_chile_campeonato")

    if "primera division" in l and "uruguay" in c:
        candidates.append("soccer_uruguay_primera_division")

    if "division profesional" in l and "paraguay" in c:
        candidates.append("soccer_paraguay_division_profesional")

    if "liga 1" in l and "peru" in c:
        candidates.append("soccer_peru_primera_division")

    if "mls" in l:
        candidates.append("soccer_usa_mls")

    if "la liga 2" in l or "segunda division" in l:
        candidates.append("soccer_spain_segunda_division")
    if "la liga" in l:
        candidates.append("soccer_spain_la_liga")

    if "serie a" in l and "italy" in c:
        candidates.append("soccer_italy_serie_a")
    if "serie b" in l and "italy" in c:
        candidates.append("soccer_italy_serie_b")

    if "primeira liga" in l:
        candidates.append("soccer_portugal_primeira_liga")

    if "league of ireland" in l:
        candidates.append("soccer_league_of_ireland")

    if "eliteserien" in l:
        candidates.append("soccer_norway_eliteserien")

    if "allsvenskan" in l:
        candidates.append("soccer_sweden_allsvenskan")
    if "superettan" in l:
        candidates.append("soccer_sweden_superettan")

    if "j league" in l:
        candidates.append("soccer_japan_j_league")

    if "k league 1" in l:
        candidates.append("soccer_korea_kleague1")

    if "eredivisie" in l:
        candidates.append("soccer_netherlands_eredivisie")

    if "premiership" in l and "scotland" in c:
        candidates.append("soccer_spl")

    if "super league" in l and "turkey" in c:
        candidates.append("soccer_turkey_super_league")

    if "saudi pro league" in l:
        candidates.append("soccer_saudi_arabia_pro_league")

    if "champions league women" in l:
        candidates.append("soccer_uefa_champs_league_women")
    if "champions league qualification" in l:
        candidates.append("soccer_uefa_champs_league_qualification")
    if "champions league" in l:
        candidates.append("soccer_uefa_champs_league")
    if "europa conference" in l:
        candidates.append("soccer_uefa_europa_conference_league")
    if "europa league" in l:
        candidates.append("soccer_uefa_europa_league")
    if "nations league" in l:
        candidates.append("soccer_uefa_nations_league")
    if "euro qualification" in l:
        candidates.append("soccer_uefa_euro_qualification")
    if "euro" in l:
        candidates.append("soccer_uefa_european_championship")
    if "copa america" in l:
        candidates.append("soccer_conmebol_copa_america")
    if "copa libertadores" in l:
        candidates.append("soccer_conmebol_copa_libertadores")
    if "sudamericana" in l:
        candidates.append("soccer_conmebol_copa_sudamericana")
    if "leagues cup" in l:
        candidates.append("soccer_concacaf_leagues_cup")
    if "gold cup" in l:
        candidates.append("soccer_concacaf_gold_cup")

    seen = set()
    out: List[str] = []
    for item in candidates:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _score_sport_match(sport: Dict[str, Any], league: str, country: str) -> int:
    key = _normalize_text(sport.get("key", ""))
    title = _normalize_text(sport.get("title", ""))
    desc = _normalize_text(sport.get("description", ""))
    league_n = _normalize_text(league)
    country_n = _normalize_text(country)

    haystack = f"{key} {title} {desc}"
    score = 0

    if "soccer" not in key:
        return 0

    league_tokens = set(league_n.split())
    country_tokens = set(country_n.split())

    for tok in league_tokens:
        if len(tok) >= 3 and tok in haystack:
            score += 12

    for tok in country_tokens:
        if len(tok) >= 3 and tok in haystack:
            score += 10

    if league_n and league_n in haystack:
        score += 35

    if country_n and country_n in haystack:
        score += 20

    return score


# =========================================================
# DESCUBRIR SPORTS DISPONIBLES
# =========================================================
def _get_active_sports(api_key: str) -> List[Dict[str, Any]]:
    try:
        data = _request_json(
            SPORTS_URL,
            params={"apiKey": api_key},
            timeout=15,
        )
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def _resolve_candidate_sport_keys(api_key: str, league: str, country: str = "") -> List[str]:
    sports = _get_active_sports(api_key)
    if not sports:
        return []

    active_keys = {
        _safe_text(item.get("key"))
        for item in sports
        if bool(item.get("active", False))
    }

    candidates: List[str] = []

    for key in _league_mapping_candidates(league, country):
        if key in active_keys:
            candidates.append(key)

    scored: List[Tuple[int, str]] = []
    for sport in sports:
        key = _safe_text(sport.get("key"))
        if key not in active_keys:
            continue
        if not key.startswith("soccer_"):
            continue

        score = _score_sport_match(sport, league, country)
        if score > 0:
            scored.append((score, key))

    scored.sort(reverse=True)

    for _, key in scored[:6]:
        if key not in candidates:
            candidates.append(key)

    return candidates


# =========================================================
# EXTRAER MERCADOS TOTALS
# =========================================================
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

                if over_price <= 0 and under_price <= 0:
                    continue

                results.append({
                    "bookmaker": bookmaker_title,
                    "line": point,
                    "over_price": over_price,
                    "under_price": under_price,
                })

    return results


# =========================================================
# ELEGIR MEJOR EVENTO
# =========================================================
def _choose_best_event(events: List[Dict[str, Any]], local: str, visitante: str) -> Tuple[Optional[Dict[str, Any]], int]:
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
        return None, 0

    if best_score < 90:
        return None, best_score

    return best_event, best_score


# =========================================================
# CONSULTAR ODDS POR SPORT KEY
# =========================================================
def _fetch_odds_for_sport(api_key: str, sport_key: str) -> List[Dict[str, Any]]:
    url = SPORT_ODDS_URL_TEMPLATE.format(sport_key=sport_key)
    params = {
        "apiKey": api_key,
        "regions": "eu",
        "markets": "totals",
        "oddsFormat": "decimal",
        "bookmakers": "bet365,pinnacle,williamhill,unibet",
    }

    try:
        data = _request_json(url, params=params, timeout=15)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


# =========================================================
# API PRINCIPAL
# =========================================================
def obtener_odds_partido(local: str, visitante: str, league: str = "", country: str = "") -> Dict[str, Any]:
    api_key = os.getenv("THE_ODDS_API_KEY", "").strip()

    base_response = {
        "ok": False,
        "error": "",
        "odds_source": "the_odds_api",
        "odds_data_available": False,
        "home_team": "",
        "away_team": "",
        "commence_time": "",
        "sport_key": "",
        "matched_event_id": "",
        "match_score": 0,
        "searched_sport_keys": [],
        "bookmakers_found": 0,
        "markets": [],
    }

    if not api_key:
        base_response["error"] = "THE_ODDS_API_KEY no configurada"
        return base_response

    sport_candidates = _resolve_candidate_sport_keys(api_key, league=league, country=country)
    base_response["searched_sport_keys"] = sport_candidates

    if not sport_candidates:
        base_response["error"] = "no se encontró sport_key compatible en The Odds API"
        return base_response

    best_event = None
    best_sport_key = ""
    best_match_score = -1

    for sport_key in sport_candidates:
        events = _fetch_odds_for_sport(api_key, sport_key)
        if not events:
            continue

        candidate_event, candidate_score = _choose_best_event(events, local, visitante)
        if not candidate_event:
            continue

        if candidate_score > best_match_score:
            best_match_score = candidate_score
            best_event = candidate_event
            best_sport_key = sport_key

        if candidate_score >= 180:
            break

    if not best_event:
        base_response["error"] = "no se encontró partido compatible en The Odds API"
        return base_response

    home_team = _safe_text(best_event.get("home_team"))
    away_team = _extract_away_team(best_event)
    commence_time = _safe_text(best_event.get("commence_time"))
    bookmakers = best_event.get("bookmakers") or []
    markets = _extract_totals_market(bookmakers)

    return {
        "ok": True,
        "error": "" if markets else "partido encontrado pero sin mercado totals disponible",
        "odds_source": "the_odds_api",
        "odds_data_available": len(markets) > 0,
        "home_team": home_team,
        "away_team": away_team,
        "commence_time": commence_time,
        "sport_key": best_sport_key,
        "matched_event_id": _safe_text(best_event.get("id")),
        "match_score": best_match_score,
        "searched_sport_keys": sport_candidates,
        "bookmakers_found": len(bookmakers),
        "markets": markets,
               }
