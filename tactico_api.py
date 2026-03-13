from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import random
import time

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# =========================================================
# CACHE GLOBAL DEL SISTEMA
# =========================================================

cache_partidos = []
cache_senales = []
cache_historial = []
last_scan_ts = None


# =========================================================
# DATOS DEMO
# =========================================================

def generar_partidos_demo():
    partidos_base = [
        ("Arsenal", "Chelsea", "Premier League", "England"),
        ("Barcelona", "Valencia", "La Liga", "Spain"),
        ("Juventus", "Milan", "Serie A", "Italy"),
        ("River Plate", "Boca Juniors", "Liga Profesional Argentina", "Argentina"),
        ("Flamengo", "Palmeiras", "Brasileirao", "Brazil"),
        ("Toluca W", "Pumas UNAM W", "Liga MX Femenil", "Mexico"),
        ("Al Shorta", "Al Quwa Al Jawiya", "Iraqi League", "Iraq"),
        ("Andorra", "Betis", "UEFA Conference League", "World"),
    ]

    estados_posibles = ["EN_JUEGO", "FINALIZADO", "PROXIMO"]

    partidos = []

    for idx, (home, away, league, country) in enumerate(partidos_base, start=1):
        estado = random.choices(
            population=estados_posibles,
            weights=[70, 10, 20],
            k=1
        )[0]

        minuto = random.randint(5, 87) if estado == "EN_JUEGO" else 0
        if estado == "FINALIZADO":
            minuto = 90

        marcador_local = random.randint(0, 3) if estado != "PROXIMO" else 0
        marcador_visitante = random.randint(0, 3) if estado != "PROXIMO" else 0

        possession_home = random.randint(40, 60)
        possession_away = 100 - possession_home

        partido = {
            "id": idx,
            "local": home,
            "visitante": away,
            "liga": league,
            "pais": country,
            "minuto": minuto,
            "estado_partido": estado,
            "hora_inicio": f"{random.randint(12,23):02d}:{random.choice([0,15,30,45]):02d}",
            "marcador_local": marcador_local,
            "marcador_visitante": marcador_visitante,
            "xG": round(random.uniform(0.2, 3.5), 2),
            "shots": random.randint(4, 18),
            "shots_on_target": random.randint(1, 8),
            "dangerous_attacks": random.randint(10, 65),
            "momentum": random.choice(["BAJO", "MEDIO", "ALTO", "MUY ALTO"]),
            "goal_pressure": {
                "pressure_score": random.randint(20, 95)
            },
            "goal_predictor": {
                "goal_next_5_prob": round(random.uniform(0.10, 0.85), 2),
                "goal_next_10_prob": round(random.uniform(0.15, 0.90), 2),
            },
            "chaos": {
                "chaos_score": random.randint(10, 90)
            },
            "possession_home": possession_home,
            "possession_away": possession_away,
            "fouls_home": random.randint(4, 18),
            "fouls_away": random.randint(4, 18),
            "yellow_cards_home": random.randint(0, 4),
            "yellow_cards_away": random.randint(0, 4),
            "red_cards_home": random.randint(0, 1),
            "red_cards_away": random.randint(0, 1),
            "relevance": random.randint(50, 100),
            "popularity": random.randint(50, 100),
        }

        partidos.append(partido)

    return partidos


def generar_senales_demo(partidos):
    senales = []

    for p in partidos:
        if p["estado_partido"] != "EN_JUEGO":
            continue

        confianza = random.randint(65, 94)
        value = round(random.uniform(3, 22), 2)
        signal_score = round(random.uniform(150, 285), 2)
        tactical_score = round(random.uniform(8, 28), 2)
        goal_inminente_score = round(random.uniform(1, 8), 2)
        value_score = round(random.uniform(2, 10), 2)
        risk_score = round(random.uniform(1, 7), 2)
        ai_score = round(random.uniform(25, 100), 2)
        ai_decision_score = round(random.uniform(40, 150), 2)

        rank = "NORMAL"
        if signal_score >= 250:
            rank = "ELITE"
        elif signal_score >= 210:
            rank = "TOP"
        elif signal_score >= 170:
            rank = "ALTA"

        senal = {
            "match_id": p["id"],
            "home": p["local"],
            "away": p["visitante"],
            "league": p["liga"],
            "country": p["pais"],
            "minute": p["minuto"],
            "score": f"{p['marcador_local']}-{p['marcador_visitante']}",
            "market": random.choice([
                "RESULT_HOLDS_NEXT_15",
                "OVER_NEXT_15_DYNAMIC",
                "OVER_MATCH_DYNAMIC",
            ]),
            "selection": random.choice([
                "Se mantiene resultado próximos 15 min",
                "Over próximos 15 min",
                "Over partido",
            ]),
            "line": random.choice([None, 1.5, 2.5, 3.5]),
            "odd": round(random.uniform(1.55, 2.65), 2),
            "prob": round(random.uniform(0.52, 0.87), 2),
            "value": value,
            "confidence": confianza,
            "reason": "Presión ofensiva + lectura táctica favorable",
            "tier": random.choice(["PREMIUM", "FUERTE", "NORMAL"]),
            "estado_partido": {
                "estado": random.choice(["FRIO", "CONTROLADO", "CALIENTE", "EXPLOSIVO", "CAOS"])
            },
            "gol_inminente": {
                "gol_inminente": random.choice([True, False])
            },
            "signal_status": "OPEN",
            "goal_prob_5": round(random.uniform(20, 85), 2),
            "goal_prob_10": round(random.uniform(25, 90), 2),
            "goal_prob_15": round(random.uniform(30, 95), 2),
            "resultado_probable": random.choice(["1-0", "2-1", "2-0", "1-1", "3-1"]),
            "ganador_probable": random.choice([p["local"], p["visitante"], "EMPATE"]),
            "doble_oportunidad_probable": random.choice([
                "LOCAL_O_EMPATE", "EMPATE_O_VISITANTE", "LOCAL_O_VISITANTE"
            ]),
            "total_goles_estimado": round(random.uniform(1.5, 4.5), 2),
            "linea_goles_probable": random.choice(["OVER_1_5", "OVER_2_5", "UNDER_3_5"]),
            "over_under_probable": random.choice(["OVER 2.5", "UNDER 3.5", "OVER 1.5"]),
            "confianza_prediccion": random.randint(65, 91),
            "recomendacion_final": random.choice(["APOSTAR", "OBSERVAR"]),
            "riesgo_operativo": random.choice(["BAJO", "MEDIO", "ALTO"]),
            "all_signals": [],
            "tactical_score": tactical_score,
            "goal_inminente_score": goal_inminente_score,
            "signal_score": signal_score,
            "signal_rank": rank,
            "prob_implicita_calculada": round(random.uniform(0.35, 0.62), 2),
            "value_pct": value,
            "edge_pct": round(random.uniform(1, 18), 2),
            "value_score": value_score,
            "value_categoria": random.choice(["VALUE_ELITE", "VALUE_ALTO", "VALUE_MEDIO"]),
            "recomendacion_value": random.choice(["APOSTAR_FUERTE", "APOSTAR", "APOSTAR_SUAVE"]),
            "razon_value": "La cuota ofrece ventaja positiva frente al mercado",
            "risk_score": risk_score,
            "risk_level": random.choice(["APTO", "RIESGO_MEDIO", "RIESGO_ALTO"]),
            "apto_para_entrar": True,
            "motivos_riesgo": [
                "Volatilidad moderada",
                "Ritmo cambiante"
            ],
            "ai_state": random.choice([
                "CONTROL_REAL",
                "CAOS_UTIL",
                "PRESION_FALSA",
                "CIERRE_TACTICO",
                "NEUTRO"
            ]),
            "ai_score": ai_score,
            "ai_reason": "La IA detecta ventaja situacional del equipo dominante",
            "ai_fit": random.choice(["ALINEADA", "NEUTRO", "DESALINEADA"]),
            "ai_fit_reason": "La lectura táctica y la señal mantienen coherencia",
            "ai_confidence_adjustment": round(random.uniform(-6, 8), 2),
            "ai_confidence_final": round(random.uniform(60, 95), 2),
            "ai_decision_score": ai_decision_score,
            "ai_recommendation": random.choice([
                "APOSTAR_FUERTE", "APOSTAR", "APOSTAR_SUAVE", "OBSERVAR"
            ]),
            "handicap_probable": random.choice(["Local -0.5", "Visitante +0.5", "Sin definir"]),
        }

        senales.append(senal)

    senales.sort(key=lambda s: float(s.get("ai_decision_score", 0)), reverse=True)
    return senales


def generar_historial_demo():
    return [
        {
            "home": "Flamengo",
            "away": "Palmeiras",
            "league": "Brasileirao",
            "country": "Brazil",
            "market": "Over partido",
            "minute": 72,
            "odd": 1.87,
            "value": 11.2,
            "estado_resultado": "ganada"
        },
        {
            "home": "River Plate",
            "away": "Boca Juniors",
            "league": "Liga Profesional Argentina",
            "country": "Argentina",
            "market": "Se mantiene resultado próximos 15 min",
            "minute": 64,
            "odd": 1.74,
            "value": 8.4,
            "estado_resultado": "pendiente"
        }
    ]


def refresh_cache():
    global cache_partidos, cache_senales, cache_historial, last_scan_ts
    cache_partidos = generar_partidos_demo()
    cache_senales = generar_senales_demo(cache_partidos)
    cache_historial = generar_historial_demo()
    last_scan_ts = int(time.time())


# =========================================================
# PÁGINAS HTML
# =========================================================

@app.route("/")
def home():
    return render_template("dashboard.html")


@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")


@app.route("/leagues")
def leagues_page():
    return render_template("leagues.html")


@app.route("/matches/<league_name>")
def matches_page(league_name):
    return render_template("matches.html")


@app.route("/match/<match_id>")
def match_page(match_id):
    return render_template("match_detail.html")


# =========================================================
# APIS GENERALES
# =========================================================

@app.route("/status")
def status():
    return jsonify({
        "status": "ok",
        "service": "JHONNY_ELITE_BACKEND",
        "version": "V15_MODULAR"
    })


@app.route("/scan")
def scan():
    global cache_partidos, last_scan_ts
    if not cache_partidos:
        refresh_cache()

    return jsonify({
        "partidos_analizados": len(cache_partidos),
        "total_partidos": len(cache_partidos),
        "partidos": cache_partidos,
        "last_scan": last_scan_ts
    })


@app.route("/signals")
def signals():
    global cache_senales, cache_partidos, last_scan_ts
    if not cache_partidos or not cache_senales:
        refresh_cache()

    return jsonify({
        "total_senales": len(cache_senales),
        "signals": cache_senales,
        "last_scan": last_scan_ts
    })


@app.route("/history")
def history():
    global cache_historial
    if not cache_historial:
        refresh_cache()
    return jsonify(cache_historial)


@app.route("/learning-stats")
def learning_stats():
    global cache_senales, cache_historial
    if not cache_senales:
        refresh_cache()

    ganadas = sum(1 for h in cache_historial if str(h.get("estado_resultado", "")).lower() == "ganada")
    perdidas = sum(1 for h in cache_historial if str(h.get("estado_resultado", "")).lower() == "perdida")
    total_resueltas = ganadas + perdidas
    win_rate = round((ganadas / total_resueltas) * 100, 2) if total_resueltas else 0

    elite = sum(1 for s in cache_senales if str(s.get("signal_rank", "")).upper() == "ELITE")
    top = sum(1 for s in cache_senales if str(s.get("signal_rank", "")).upper() == "TOP")

    value_promedio = round(
        sum(float(s.get("value", 0) or 0) for s in cache_senales) / len(cache_senales),
        2
    ) if cache_senales else 0

    riesgo_medio = round(
        sum(float(s.get("risk_score", 0) or 0) for s in cache_senales) / len(cache_senales),
        2
    ) if cache_senales else 0

    return jsonify({
        "ganadas": ganadas,
        "perdidas": perdidas,
        "win_rate": win_rate,
        "roi_percent": round(random.uniform(2, 16), 2),
        "signals_elite": elite,
        "signals_top": top,
        "value_promedio": value_promedio,
        "riesgo_medio": riesgo_medio
    })


@app.route("/auto-scan/status")
def auto_scan_status():
    global cache_partidos, cache_senales, last_scan_ts
    if not cache_partidos:
        refresh_cache()

    return jsonify({
        "status": "ok",
        "auto_scan_activo": True,
        "intervalo_segundos": 60,
        "ultimo_scan": last_scan_ts,
        "partidos_cache": len(cache_partidos),
        "senales_cache": len(cache_senales)
    })


# =========================================================
# API NIVEL 1 - LIGAS
# =========================================================

@app.route("/api/leagues")
def api_leagues():
    global cache_partidos
    if not cache_partidos:
        refresh_cache()

    date = request.args.get("date", "today")
    state = request.args.get("state", "live")

    # date se deja listo para futura lógica real
    _ = date

    leagues_map = {}

    for p in cache_partidos:
        league = p.get("liga", "Liga desconocida")
        country = p.get("pais", "Otros")
        estado_raw = str(p.get("estado_partido", "EN_JUEGO")).upper()

        if state == "live":
            allowed = estado_raw in ["EN_JUEGO", "LIVE", "ACTIVO"]
        elif state == "finished":
            allowed = estado_raw in ["FINALIZADO", "FINISHED", "FT"]
        elif state == "upcoming":
            allowed = estado_raw in ["PROXIMO", "UPCOMING", "SCHEDULED"]
        else:
            allowed = True

        key = (league, country)
        if key not in leagues_map:
            leagues_map[key] = {
                "league": league,
                "country": country,
                "matches_live": 0,
                "matches_total": 0
            }

        leagues_map[key]["matches_total"] += 1
        if allowed:
            leagues_map[key]["matches_live"] += 1

    data = list(leagues_map.values())
    data.sort(key=lambda x: (x["matches_live"], x["matches_total"]), reverse=True)
    return jsonify(data)


# =========================================================
# API NIVEL 2 - PARTIDOS POR LIGA
# =========================================================

@app.route("/api/matches/<league_name>")
def api_matches(league_name):
    global cache_partidos
    if not cache_partidos:
        refresh_cache()

    league_name = league_name.strip().lower()
    matches = []

    for p in cache_partidos:
        if str(p.get("liga", "")).strip().lower() == league_name:
            estado_raw = str(p.get("estado_partido", "EN_JUEGO")).upper()

            if estado_raw in ["EN_JUEGO", "LIVE", "ACTIVO"]:
                status = "LIVE"
            elif estado_raw in ["FINALIZADO", "FINISHED", "FT"]:
                status = "FINISHED"
            else:
                status = "UPCOMING"

            matches.append({
                "id": p.get("id"),
                "home": p.get("local"),
                "away": p.get("visitante"),
                "minute": p.get("minuto", 0),
                "score": f"{p.get('marcador_local', 0)}-{p.get('marcador_visitante', 0)}",
                "status": status,
                "start_time": p.get("hora_inicio", "-"),
                "relevance": p.get("relevance", 50),
                "popularity": p.get("popularity", 50)
            })

    return jsonify(matches)


# =========================================================
# API NIVEL 3 - DETALLE DEL PARTIDO
# =========================================================

@app.route("/api/match-details/<match_id>")
def api_match_details(match_id):
    global cache_partidos, cache_senales
    if not cache_partidos:
        refresh_cache()

    partido = next((p for p in cache_partidos if str(p.get("id")) == str(match_id)), None)
    if not partido:
        return jsonify({"error": "Partido no encontrado"}), 404

    senal = next((s for s in cache_senales if str(s.get("match_id")) == str(match_id)), None)

    return jsonify({
        "match_id": partido.get("id"),
        "home": partido.get("local"),
        "away": partido.get("visitante"),
        "league": partido.get("liga"),
        "country": partido.get("pais"),
        "minute": partido.get("minuto", 0),
        "status": partido.get("estado_partido", "LIVE"),
        "score": f"{partido.get('marcador_local', 0)}-{partido.get('marcador_visitante', 0)}",
        "marcador_local": partido.get("marcador_local", 0),
        "marcador_visitante": partido.get("marcador_visitante", 0),
        "xg": partido.get("xG", 0),
        "shots": partido.get("shots", 0),
        "shots_on_target": partido.get("shots_on_target", 0),
        "dangerous_attacks": partido.get("dangerous_attacks", 0),
        "possession_home": partido.get("possession_home", 50),
        "possession_away": partido.get("possession_away", 50),
        "fouls_home": partido.get("fouls_home", 0),
        "fouls_away": partido.get("fouls_away", 0),
        "yellow_cards_home": partido.get("yellow_cards_home", 0),
        "yellow_cards_away": partido.get("yellow_cards_away", 0),
        "red_cards_home": partido.get("red_cards_home", 0),
        "red_cards_away": partido.get("red_cards_away", 0),
        "momentum": partido.get("momentum", "MEDIO"),
        "goal_pressure": partido.get("goal_pressure", {}),
        "goal_predictor": partido.get("goal_predictor", {}),
        "chaos": partido.get("chaos", {}),
        "signal": senal or None
    })


# =========================================================
# API AUXILIARES DEL DASHBOARD ACTUAL
# =========================================================

@app.route("/league-explorer")
def league_explorer():
    global cache_partidos, cache_senales
    if not cache_partidos:
        refresh_cache()

    grouped = {}

    for p in cache_partidos:
        country = p.get("pais", "Otros")
        region = "Otros"

        if country in ["England", "Spain", "Italy", "Germany", "France", "Portugal", "Belgium"]:
            region = "Europe"
        elif country in ["Argentina", "Brazil"]:
            region = "South America"
        elif country in ["Mexico"]:
            region = "North America"
        elif country in ["Iraq", "Iran", "Saudi-Arabia", "Qatar", "UAE"]:
            region = "Asia"

        if region not in grouped:
            grouped[region] = []

        league = p.get("liga", "Liga desconocida")
        existing = next((x for x in grouped[region] if x["league"] == league and x["country"] == country), None)

        elite = 0
        top = 0
        league_signals = [
            s for s in cache_senales
            if str(s.get("league", "")) == str(league) and str(s.get("country", "")) == str(country)
        ]
        elite = sum(1 for s in league_signals if str(s.get("signal_rank", "")).upper() == "ELITE")
        top = sum(1 for s in league_signals if str(s.get("signal_rank", "")).upper() == "TOP")

        if existing:
            existing["matches"] += 1
            existing["signals"] = len(league_signals)
            existing["elite"] = elite
            existing["top"] = top
        else:
            grouped[region].append({
                "league": league,
                "country": country,
                "matches": 1,
                "signals": len(league_signals),
                "elite": elite,
                "top": top
            })

    return jsonify({"league_explorer": grouped})


@app.route("/hot-matches")
def hot_matches():
    global cache_partidos, cache_senales
    if not cache_partidos:
        refresh_cache()

    hot = []
    for p in cache_partidos:
        if str(p.get("estado_partido", "")).upper() != "EN_JUEGO":
            continue

        signal = next((s for s in cache_senales if str(s.get("match_id")) == str(p.get("id"))), None)
        if signal:
            hot.append(p)

    return jsonify({"hot_matches": hot[:6]})


# =========================================================
# INICIO
# =========================================================

refresh_cache()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
