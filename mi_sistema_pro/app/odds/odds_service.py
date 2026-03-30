import os
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
        "club": "",
        "deportivo": "depor",
        "athletic": "ath",
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
    if "eredivisie" in l:
        candidates.append("soccer_netherlands_eredivisie")
    if "allsvenskan" in l:
        candidates.append("soccer_sweden_allsvenskan")
    if "superettan" in l:
        candidates.append("soccer_sweden_superettan")
    if "j league" in l:
        candidates.append("soccer_japan_j_league")
    if "k league 1" in l:
        candidates.append("soccer_korea_kleague1")
    if "champions league" in l:
        candidates.append("soccer_uefa_champs_league")
    if "europa league" in l:
        candidates.append("soccer_uefa_europa_league")
    if "copa libertadores" in l:
        candidates.append("soccer_conmebol_copa_libertadores")
    if "sudamericana" in l:
        candidates.append("soccer_conmebol_copa_sudamericana")

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

    for _, key in scored[:6]:
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


def _choose_best_event_odds_api_io(events: List[Dict[str, Any]], local: str, visitante: str) -> Tuple[Optional[Dict[str, Any]], int]:
    best_event = None
    best_score = -1

    for event in events or []:
        home_team, away_team = _extract_event_teams_odds_api_io(event)
        score = _match_score(local, visitante, home_team, away_team)

        if score > best_score:
            best_score = score
            best_event = event

    if best_event is None:
        return None, 0

    if best_score < 90:
        return None, best_score

    return best_event, best_score


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
        return []
    except Exception:
        return []


def _obtener_odds_odds_api_io(local: str, visitante: str, league: str = "", country: str = "") -> Dict[str, Any]:
    api_key = os.getenv("ODDS_API_IO_KEY", "").strip()
    base_response = _empty_response("odds_api_io")

    if not api_key:
        base_response["error"] = "ODDS_API_IO_KEY no configurada"
        return base_response

    events = _fetch_odds_api_io_events(api_key, league=league, country=country)
    base_response["searched_sport_keys"] = ["soccer"]

    if not events:
        base_response["error"] = "odds-api.io no devolvió eventos utilizables"
        return base_response

    best_event, best_score = _choose_best_event_odds_api_io(events, local, visitante)
    if not best_event:
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

    primary = _safe_provider_odds_api_io(local, visitante, league=league, country=country)
    if primary.get("odds_data_available", False):
        return primary

    fallback = _safe_provider_the_odds_api(local, visitante, league=league, country=country)
    if fallback.get("odds_data_available", False):
        return fallback

    primary_error = _safe_text(primary.get("error"))
    fallback_error = _safe_text(fallback.get("error"))

    return {
        "ok": False,
        "error": f"odds_api_io: {primary_error or 'sin datos'} | the_odds_api: {fallback_error or 'sin datos'}",
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
}
