import os
import unicodedata
from difflib import SequenceMatcher
from typing import Dict, Any, List, Optional, Tuple

import requests
from requests.exceptions import SSLError, Timeout, ConnectionError, HTTPError, RequestException


SPORTS_URL = "https://api.the-odds-api.com/v4/sports"
SPORT_ODDS_URL_TEMPLATE = "https://api.the-odds-api.com/v4/sports/{sport_key}/odds"

ODDS_API_IO_BASE_URL = "https://api.odds-api.io/v3"
REQUEST_TIMEOUT = 15


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


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", _safe_text(text))
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _normalize_text(text: str) -> str:
    t = _strip_accents(_safe_text(text)).lower()

    for ch in [".", ",", "-", "_", "/", "(", ")", ":", ";", "'", '"', "&"]:
        t = t.replace(ch, " ")

    t = " ".join(t.split())
    return t


def _apply_aliases(text: str) -> str:
    aliases = {
        "argentinos jrs": "argentinos juniors",
        "argentinos jr": "argentinos juniors",
        "arg jrs": "argentinos juniors",
        "hungria": "hungary",
        "grecia": "greece",
        "rusia": "russia",
        "jordania": "jordan",
        "espana": "spain",
        "mirandes": "mirandes",
        "aldosivi": "aldosivi",
        "nigeria": "nigeria",
        "mali": "mali",
        "turkiye": "turkey",
        "bosnia herzegovina": "bosnia and herzegovina",
        "rep of ireland": "republic of ireland",
        "fyr macedonia": "north macedonia",
    }
    return aliases.get(text, text)


def _normalize_team_name(name: str) -> str:
    text = _normalize_text(name)
    text = _apply_aliases(text)

    replacements = {
        "fc": "",
        "cf": "",
        "sc": "",
        "ac": "",
        "cd": "",
        "club": "",
        "deportivo": "depor",
        "deportes": "depor",
        "athletic": "ath",
        "atletico": "atl",
        "sporting": "sport",
        "association": "",
        "fk": "",
        "bk": "",
        "if": "",
        "ik": "",
        "sk": "",
        "nk": "",
        "us": "",
        "ud": "",
        "ca": "",
        "rc": "",
        "sv": "",
        "ss": "",
        "afc": "",
        "cfc": "",
        "women": "",
        "woman": "",
        "femenino": "",
        "femenina": "",
        "ladies": "",
        "reserves": "",
        "reserve": "",
        "b": "",
        "ii": "",
        "iii": "",
        "iv": "",
        "u17": "",
        "u18": "",
        "u19": "",
        "u20": "",
        "u21": "",
        "u22": "",
        "u23": "",
        "sub17": "",
        "sub18": "",
        "sub19": "",
        "sub20": "",
        "sub21": "",
        "sub22": "",
        "sub23": "",
        "w": "",
    }

    tokens = text.split()
    out: List[str] = []

    for tok in tokens:
        mapped = replacements.get(tok, tok)
        if mapped:
            out.append(mapped)

    cleaned = " ".join(out).strip()
    return " ".join(cleaned.split())


def _tokenize_team_name(name: str) -> List[str]:
    text = _normalize_team_name(name)
    return [tok for tok in text.split() if tok]


def _sequence_ratio_score(name_a: str, name_b: str) -> int:
    a = _normalize_team_name(name_a)
    b = _normalize_team_name(name_b)

    if not a or not b:
        return 0

    ratio = SequenceMatcher(None, a, b).ratio()
    return int(round(ratio * 100))


def _similar_team_score(name_a: str, name_b: str) -> int:
    a = _normalize_team_name(name_a)
    b = _normalize_team_name(name_b)

    if not a or not b:
        return 0

    if a == b:
        return 100

    if a in b or b in a:
        return 86

    tokens_a = set(_tokenize_team_name(a))
    tokens_b = set(_tokenize_team_name(b))

    token_score = 0
    if tokens_a and tokens_b:
        common = tokens_a.intersection(tokens_b)
        if common:
            token_score = len(common) * 22

            if len(common) >= 2:
                token_score += 12

            if len(common) == len(tokens_a) or len(common) == len(tokens_b):
                token_score += 10

    seq_score = _sequence_ratio_score(a, b)

    return min(max(token_score, seq_score), 100)


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


def _request_json(
    url: str,
    params: Dict[str, Any],
    timeout: int = REQUEST_TIMEOUT,
    headers: Optional[Dict[str, str]] = None,
) -> Any:
    response = requests.get(
        url,
        params=params,
        headers=headers or {},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def _get_provider_mode() -> str:
    return _safe_text(os.getenv("ODDS_PROVIDER", "auto"), "auto").lower()


def _empty_response(source: str, error: str = "") -> Dict[str, Any]:
    return {
        "ok": False,
        "error": error,
        "odds_source": source,
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
        "debug_candidates": [],
        "searched_match": {},
    }


def _error_label(exc: Exception) -> str:
    if isinstance(exc, SSLError):
        return f"SSL_ERROR: {exc}"
    if isinstance(exc, Timeout):
        return f"TIMEOUT: {exc}"
    if isinstance(exc, ConnectionError):
        return f"CONNECTION_ERROR: {exc}"
    if isinstance(exc, HTTPError):
        return f"HTTP_ERROR: {exc}"
    if isinstance(exc, RequestException):
        return f"REQUEST_ERROR: {exc}"
    return f"UNEXPECTED_ERROR: {exc}"


def _build_searched_match(local: str, visitante: str, league: str, country: str) -> Dict[str, Any]:
    return {
        "local": local,
        "visitante": visitante,
        "league": league,
        "country": country,
        "local_normalized": _normalize_team_name(local),
        "visitante_normalized": _normalize_team_name(visitante),
    }


def _league_country_bonus(event_text: str, league: str, country: str) -> int:
    score = 0
    league_n = _normalize_text(league)
    country_n = _normalize_text(country)
    haystack = _normalize_text(event_text)

    if league_n and league_n in haystack:
        score += 20

    if country_n and country_n in haystack:
        score += 12

    return score


# =========================================================
# FILTRO DE COMPETENCIAS
# =========================================================
def _is_excluded_competition(league: str) -> bool:
    l = _normalize_text(league)

    excluded_terms = [
        "u17", "u18", "u19", "u20", "u21", "u22", "u23",
        "sub17", "sub18", "sub19", "sub20", "sub21", "sub22", "sub23",
        "reserve", "reserves", "reservas",
        "women", "femenino", "femenina", "ladies",
        "youth", "juvenil", "junior",
        "development", "development league",
        "serie c", "serie d",
        "segunda rfef", "tercera",
        "primera b", "segunda b",
        "regional", "amateur", "amateure",
    ]

    return any(term in l for term in excluded_terms)


def _is_allowed_major_competition(league: str, country: str = "") -> bool:
    l = _normalize_text(league)
    c = _normalize_text(country)

    if _is_excluded_competition(l):
        return False

    major_terms = [
        "premier league",
        "la liga",
        "bundesliga",
        "serie a",
        "ligue 1",
        "eredivisie",
        "primeira liga",
        "mls",
        "champions league",
        "europa league",
        "conference league",
        "copa libertadores",
        "copa sudamericana",
        "copa america",
        "nations league",
        "world cup",
        "world cup qualification",
        "qualification europe",
        "euro",
        "mundial",
        "concacaf",
        "asian cup",
        "africa cup",
        "friendlies",
        "friendly",
        "amistosos",
        "amistoso",
        "fa cup",
        "copa del rey",
        "coppa italia",
        "dfb pokal",
        "coupe de france",
        "super cup",
        "supercopa",
        "league cup",
        "liga mx",
        "campeonato brasileiro",
        "brasileirao",
        "liga profesional argentina",
        "primera division",
        "primera a",
        "campeonato",
        "national league",
        "national league north",
        "national league south",
        "non league",
        "vanarama",
    ]

    if any(term in l for term in major_terms):
        return True

    if "world" in c and ("friendly" in l or "friendlies" in l or "amistoso" in l or "amistosos" in l):
        return True

    return False


# =========================================================
# MAPEO DE LIGAS
# =========================================================
def _league_mapping_candidates(league: str, country: str = "") -> List[str]:
    l = _normalize_text(league)
    c = _normalize_text(country)

    candidates: List[str] = []

    if "liga mx" in l:
        candidates.append("soccer_mexico_ligamx")
    if "mls" in l:
        candidates.append("soccer_usa_mls")
    if "la liga" in l:
        candidates.append("soccer_spain_la_liga")
    if "serie a" in l and "italy" in c:
        candidates.append("soccer_italy_serie_a")
    if "primeira liga" in l:
        candidates.append("soccer_portugal_primeira_liga")
    if "eredivisie" in l:
        candidates.append("soccer_netherlands_eredivisie")
    if "champions league" in l:
        candidates.append("soccer_uefa_champs_league")
    if "europa league" in l:
        candidates.append("soccer_uefa_europa_league")
    if "conference league" in l:
        candidates.append("soccer_uefa_europa_conference_league")
    if "copa libertadores" in l:
        candidates.append("soccer_conmebol_copa_libertadores")
    if "sudamericana" in l:
        candidates.append("soccer_conmebol_copa_sudamericana")
    if "premier league" in l and "england" in c:
        candidates.append("soccer_epl")
    if "bundesliga" in l:
        candidates.append("soccer_germany_bundesliga")
    if "ligue 1" in l:
        candidates.append("soccer_france_ligue_one")
    if "argentina" in c and ("liga profesional" in l or "primera division" in l):
        candidates.append("soccer_argentina_primera_division")
    if "brazil" in c or "brasil" in c:
        candidates.append("soccer_brazil_campeonato")
    if "nations league" in l:
        candidates.append("soccer_uefa_nations_league")

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
# THE ODDS API
# =========================================================
def _get_active_sports(api_key: str) -> List[Dict[str, Any]]:
    try:
        data = _request_json(
            SPORTS_URL,
            params={"apiKey": api_key},
            timeout=REQUEST_TIMEOUT,
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

    for _, key in scored[:8]:
        if key not in candidates:
            candidates.append(key)

    return candidates


def _extract_totals_market_the_odds(bookmakers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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


def _choose_best_event(
    events: List[Dict[str, Any]],
    local: str,
    visitante: str,
    league: str = "",
    country: str = "",
) -> Tuple[Optional[Dict[str, Any]], int, List[Dict[str, Any]]]:
    best_event = None
    best_score = -1
    debug_candidates: List[Dict[str, Any]] = []

    for event in events or []:
        home_team = _safe_text(event.get("home_team"))
        away_team = _extract_away_team(event)

        score = _match_score(local, visitante, home_team, away_team)

        event_text = " ".join([
            _safe_text(event.get("sport_key")),
            _safe_text(event.get("commence_time")),
            home_team,
            away_team,
        ])
        score += _league_country_bonus(event_text, league, country)

        candidate = {
            "home_team": home_team,
            "away_team": away_team,
            "event_id": _safe_text(event.get("id")),
            "score": score,
        }
        debug_candidates.append(candidate)

        if score > best_score:
            best_score = score
            best_event = event

    debug_candidates.sort(key=lambda x: _safe_int(x.get("score")), reverse=True)
    debug_candidates = debug_candidates[:5]

    if best_event is None:
        return None, 0, debug_candidates

    if best_score < 80:
        return None, best_score, debug_candidates

    return best_event, best_score, debug_candidates


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
        data = _request_json(url, params=params, timeout=REQUEST_TIMEOUT)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def _obtener_odds_the_odds_api(local: str, visitante: str, league: str = "", country: str = "") -> Dict[str, Any]:
    api_key = os.getenv("THE_ODDS_API_KEY", "").strip()
    base_response = _empty_response("the_odds_api")
    base_response["searched_match"] = _build_searched_match(local, visitante, league, country)

    if not api_key:
        base_response["error"] = "THE_ODDS_API_KEY no configurada"
        return base_response

    if not _is_allowed_major_competition(league, country):
        base_response["error"] = "competencia descartada por filtro de calidad"
        return base_response

    sport_candidates = _resolve_candidate_sport_keys(api_key, league=league, country=country)
    base_response["searched_sport_keys"] = sport_candidates

    if not sport_candidates:
        base_response["error"] = "no se encontró sport_key compatible en The Odds API"
        return base_response

    best_event = None
    best_sport_key = ""
    best_match_score = -1
    best_debug_candidates: List[Dict[str, Any]] = []

    for sport_key in sport_candidates:
        events = _fetch_odds_for_sport(api_key, sport_key)
        if not events:
            continue

        candidate_event, candidate_score, debug_candidates = _choose_best_event(
            events,
            local,
            visitante,
            league=league,
            country=country,
        )

        if debug_candidates and not best_debug_candidates:
            best_debug_candidates = debug_candidates

        if not candidate_event:
            if candidate_score > best_match_score:
                best_match_score = candidate_score
                best_debug_candidates = debug_candidates
            continue

        if candidate_score > best_match_score:
            best_match_score = candidate_score
            best_event = candidate_event
            best_sport_key = sport_key
            best_debug_candidates = debug_candidates

        if candidate_score >= 180:
            break

    base_response["debug_candidates"] = best_debug_candidates

    if not best_event:
        base_response["match_score"] = max(best_match_score, 0)
        base_response["error"] = "no se encontró partido compatible en The Odds API"
        return base_response

    home_team = _safe_text(best_event.get("home_team"))
    away_team = _extract_away_team(best_event)
    commence_time = _safe_text(best_event.get("commence_time"))
    bookmakers = best_event.get("bookmakers") or []
    markets = _extract_totals_market_the_odds(bookmakers)

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
        "debug_candidates": best_debug_candidates,
        "searched_match": _build_searched_match(local, visitante, league, country),
    }


# =========================================================
# ODDS-API.IO
# =========================================================
def _extract_totals_market_odds_api_io(data: Any) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    if isinstance(data, dict):
        if isinstance(data.get("data"), list):
            data = data.get("data")
        elif isinstance(data.get("matches"), list):
            data = data.get("matches")
        elif isinstance(data.get("response"), list):
            data = data.get("response")
        else:
            data = [data]

    if not isinstance(data, list):
        return results

    for event in data:
        bookmakers = event.get("bookmakers") or event.get("sites") or []
        for bookmaker in bookmakers:
            bookmaker_name = _safe_text(
                bookmaker.get("title") or bookmaker.get("name") or bookmaker.get("key"),
                "bookmaker_desconocido"
            )

            markets = bookmaker.get("markets") or bookmaker.get("odds") or []
            for market in markets:
                market_name = _safe_text(
                    market.get("key") or market.get("name") or market.get("market"),
                    ""
                ).lower()

                if "total" not in market_name:
                    continue

                outcomes = market.get("outcomes") or market.get("values") or []
                grouped: Dict[float, Dict[str, float]] = {}

                for outcome in outcomes:
                    outcome_name = _safe_text(
                        outcome.get("name") or outcome.get("label") or outcome.get("side"),
                        ""
                    ).upper()

                    point = _safe_float(
                        outcome.get("point") or outcome.get("line") or outcome.get("total"),
                        0.0
                    )

                    price = _safe_float(
                        outcome.get("price") or outcome.get("odd") or outcome.get("odds"),
                        0.0
                    )

                    if point <= 0 or price <= 0:
                        continue

                    normalized_name = outcome_name
                    if "OVER" in normalized_name:
                        normalized_name = "OVER"
                    elif "UNDER" in normalized_name:
                        normalized_name = "UNDER"

                    if normalized_name not in {"OVER", "UNDER"}:
                        continue

                    grouped.setdefault(point, {})
                    grouped[point][normalized_name] = price

                for point, prices in grouped.items():
                    over_price = _safe_float(prices.get("OVER"), 0.0)
                    under_price = _safe_float(prices.get("UNDER"), 0.0)

                    if over_price <= 0 and under_price <= 0:
                        continue

                    results.append({
                        "bookmaker": bookmaker_name,
                        "line": point,
                        "over_price": over_price,
                        "under_price": under_price,
                    })

    return results


def _extract_event_teams_odds_api_io(event: Dict[str, Any]) -> Tuple[str, str]:
    home_team = _safe_text(
        event.get("home_team") or event.get("home") or event.get("team_home")
    )
    away_team = _safe_text(
        event.get("away_team") or event.get("away") or event.get("team_away")
    )

    teams = event.get("teams") or []
    if (not home_team or not away_team) and isinstance(teams, list) and len(teams) >= 2:
        if not home_team:
            home_team = _safe_text(teams[0])
        if not away_team:
            away_team = _safe_text(teams[1])

    return home_team, away_team


def _choose_best_event_odds_api_io(
    events: List[Dict[str, Any]],
    local: str,
    visitante: str,
    league: str = "",
    country: str = "",
) -> Tuple[Optional[Dict[str, Any]], int, List[Dict[str, Any]]]:
    best_event = None
    best_score = -1
    debug_candidates: List[Dict[str, Any]] = []

    for event in events or []:
        home_team, away_team = _extract_event_teams_odds_api_io(event)
        score = _match_score(local, visitante, home_team, away_team)

        event_text = " ".join([
            _safe_text(event.get("league")),
            _safe_text(event.get("country")),
            home_team,
            away_team,
        ])
        score += _league_country_bonus(event_text, league, country)

        candidate = {
            "home_team": home_team,
            "away_team": away_team,
            "event_id": _safe_text(event.get("id") or event.get("event_id")),
            "score": score,
        }
        debug_candidates.append(candidate)

        if score > best_score:
            best_score = score
            best_event = event

    debug_candidates.sort(key=lambda x: _safe_int(x.get("score")), reverse=True)
    debug_candidates = debug_candidates[:5]

    if best_event is None:
        return None, 0, debug_candidates

    if best_score < 80:
        return None, best_score, debug_candidates

    return best_event, best_score, debug_candidates


def _fetch_odds_api_io_events(api_key: str, league: str = "", country: str = "") -> List[Dict[str, Any]]:
    base_url = _safe_text(os.getenv("ODDS_API_IO_BASE_URL"), ODDS_API_IO_BASE_URL)
    url = f"{base_url.rstrip('/')}/odds"

    params: Dict[str, Any] = {
        "apiKey": api_key,
        "sport": "soccer",
    }

    if league:
        params["league"] = league
    if country:
        params["country"] = country

    try:
        data = _request_json(url, params=params, timeout=REQUEST_TIMEOUT)

        if isinstance(data, dict):
            if isinstance(data.get("data"), list):
                return data.get("data")
            if isinstance(data.get("matches"), list):
                return data.get("matches")
            if isinstance(data.get("response"), list):
                return data.get("response")

        if isinstance(data, list):
            return data

    except Exception:
        pass

    try:
        data = _request_json(
            url,
            params={"apiKey": api_key, "sport": "soccer"},
            timeout=REQUEST_TIMEOUT,
        )

        if isinstance(data, dict):
            if isinstance(data.get("data"), list):
                return data.get("data")
            if isinstance(data.get("matches"), list):
                return data.get("matches")
            if isinstance(data.get("response"), list):
                return data.get("response")

        if isinstance(data, list):
            return data

    except Exception:
        return []

    return []


def _obtener_odds_odds_api_io(local: str, visitante: str, league: str = "", country: str = "") -> Dict[str, Any]:
    api_key = os.getenv("ODDS_API_IO_KEY", "").strip()
    base_response = _empty_response("odds_api_io")
    base_response["searched_match"] = _build_searched_match(local, visitante, league, country)

    if not api_key:
        base_response["error"] = "ODDS_API_IO_KEY no configurada"
        return base_response

    events = _fetch_odds_api_io_events(api_key, league=league, country=country)
    base_response["searched_sport_keys"] = ["soccer"]

    if not events:
        base_response["error"] = "odds-api.io no devolvió eventos utilizables"
        return base_response

    best_event, best_score, debug_candidates = _choose_best_event_odds_api_io(
        events,
        local,
        visitante,
        league=league,
        country=country,
    )
    base_response["debug_candidates"] = debug_candidates

    if not best_event:
        base_response["match_score"] = best_score
        base_response["error"] = "no se encontró partido compatible en odds-api.io"
        return base_response

    home_team, away_team = _extract_event_teams_odds_api_io(best_event)
    commence_time = _safe_text(
        best_event.get("commence_time") or best_event.get("start_time") or best_event.get("kickoff")
    )

    markets = _extract_totals_market_odds_api_io([best_event])
    bookmakers = best_event.get("bookmakers") or best_event.get("sites") or []

    return {
        "ok": True,
        "error": "" if markets else "partido encontrado pero sin mercado totals disponible",
        "odds_source": "odds_api_io",
        "odds_data_available": len(markets) > 0,
        "home_team": home_team,
        "away_team": away_team,
        "commence_time": commence_time,
        "sport_key": "soccer",
        "matched_event_id": _safe_text(best_event.get("id") or best_event.get("event_id")),
        "match_score": best_score,
        "searched_sport_keys": ["soccer"],
        "bookmakers_found": len(bookmakers),
        "markets": markets,
        "debug_candidates": debug_candidates,
        "searched_match": _build_searched_match(local, visitante, league, country),
    }


# =========================================================
# WRAPPERS SEGUROS
# =========================================================
def _safe_provider_odds_api_io(local: str, visitante: str, league: str = "", country: str = "") -> Dict[str, Any]:
    try:
        return _obtener_odds_odds_api_io(local, visitante, league=league, country=country)
    except Exception as exc:
        return _empty_response("odds_api_io", _error_label(exc))


def _safe_provider_the_odds_api(local: str, visitante: str, league: str = "", country: str = "") -> Dict[str, Any]:
    try:
        return _obtener_odds_the_odds_api(local, visitante, league=league, country=country)
    except Exception as exc:
        return _empty_response("the_odds_api", _error_label(exc))


# =========================================================
# API PRINCIPAL
# =========================================================
def obtener_odds_partido(local: str, visitante: str, league: str = "", country: str = "") -> Dict[str, Any]:
    provider = _get_provider_mode()

    if provider == "odds_api_io":
        return _safe_provider_odds_api_io(local, visitante, league=league, country=country)

    if provider == "the_odds_api":
        return _safe_provider_the_odds_api(local, visitante, league=league, country=country)

    primary = _safe_provider_the_odds_api(local, visitante, league=league, country=country)
    if primary.get("odds_data_available", False):
        return primary

    fallback = _safe_provider_odds_api_io(local, visitante, league=league, country=country)
    if fallback.get("odds_data_available", False):
        return fallback

    primary_error = _safe_text(primary.get("error"))
    fallback_error = _safe_text(fallback.get("error"))

    return {
        "ok": False,
        "error": f"the_odds_api: {primary_error or 'sin datos'} | odds_api_io: {fallback_error or 'sin datos'}",
        "odds_source": "auto",
        "odds_data_available": False,
        "home_team": "",
        "away_team": "",
        "commence_time": "",
        "sport_key": "",
        "matched_event_id": "",
        "match_score": max(_safe_int(primary.get("match_score")), _safe_int(fallback.get("match_score"))),
        "searched_sport_keys": list({
            *primary.get("searched_sport_keys", []),
            *fallback.get("searched_sport_keys", []),
        }),
        "bookmakers_found": max(
            _safe_int(primary.get("bookmakers_found")),
            _safe_int(fallback.get("bookmakers_found"))
        ),
        "markets": [],
        "debug_candidates": primary.get("debug_candidates", []) or fallback.get("debug_candidates", []),
        "searched_match": primary.get("searched_match", {}) or fallback.get("searched_match", {}),
        }
