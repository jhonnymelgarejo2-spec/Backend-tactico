from flask import Flask, jsonify
from flask_cors import CORS
import random
import time

app = Flask(__name__)
CORS(app)

# =========================================
# CACHE DEL SISTEMA
# =========================================

cache_partidos = []
cache_senales = []
cache_historial = []

# =========================================
# GENERADOR DEMO DE PARTIDOS
# =========================================

def generar_partidos_demo():

    partidos = []

    equipos = [
        ("Arsenal","Chelsea","Premier League","England"),
        ("Barcelona","Valencia","La Liga","Spain"),
        ("Juventus","Milan","Serie A","Italy"),
        ("River Plate","Boca Juniors","Liga Profesional Argentina","Argentina"),
        ("Flamengo","Palmeiras","Brasileirao","Brazil"),
        ("Toluca W","Pumas UNAM W","Liga MX Femenil","Mexico"),
        ("Guapore","Rondoniense","Rondoniense","Brazil")
    ]

    for i,(home,away,league,country) in enumerate(equipos):

        marcador_local=random.randint(0,3)
        marcador_visitante=random.randint(0,3)

        partidos.append({

            "id":i+1,
            "local":home,
            "visitante":away,
            "liga":league,
            "pais":country,
            "minuto":random.randint(10,85),
            "estado_partido":"EN_JUEGO",

            "marcador_local":marcador_local,
            "marcador_visitante":marcador_visitante,

            "xG":round(random.uniform(0.2,3.2),2),

            "shots":random.randint(3,15),
            "shots_on_target":random.randint(1,7),
            "dangerous_attacks":random.randint(10,60),

            "momentum":random.choice(["BAJO","MEDIO","ALTO"]),

            "goal_pressure":{
                "pressure":random.randint(0,100)
            },

            "goal_predictor":{
                "prob_10":random.randint(0,100)
            },

            "chaos":{
                "chaos_level":random.randint(0,100)
            }

        })

    return partidos

# =========================================
# GENERADOR DE SEÑALES DEMO
# =========================================

def generar_senales_demo(partidos):

    senales=[]

    for p in partidos:

        confianza=random.randint(60,95)
        value=random.randint(3,25)

        senales.append({

            "match_id":p["id"],
            "home":p["local"],
            "away":p["visitante"],
            "league":p["liga"],
            "country":p["pais"],
            "minute":p["minuto"],
            "score":f"{p['marcador_local']}-{p['marcador_visitante']}",

            "market":"RESULT_HOLDS_NEXT_15",
            "selection":"Se mantiene resultado próximos 15 min",

            "odd":round(random.uniform(1.6,2.3),2),

            "confidence":confianza,
            "value":value,

            "signal_score":round(random.uniform(150,260),2),
            "tactical_score":round(random.uniform(5,25),2),
            "goal_inminente_score":round(random.uniform(1,5),2),

            "value_score":random.randint(1,10),
            "risk_score":random.randint(1,6),

            "signal_rank":random.choice(["ELITE","TOP","ALTA"]),
            "risk_level":random.choice(["APTO","RIESGO_MEDIO"]),

            "ai_state":random.choice([
                "CONTROL_REAL",
                "CIERRE_TACTICO",
                "CAOS_UTIL",
                "NEUTRO"
            ]),

            "ai_score":random.randint(20,100),
            "ai_decision_score":random.randint(30,140),

            "ai_recommendation":random.choice([
                "APOSTAR_FUERTE",
                "APOSTAR",
                "APOSTAR_SUAVE",
                "OBSERVAR"
            ]),

            "reason":"Ritmo controlado + ventaja táctica local",
            "razon_value":"Cuota inflada por mercado",
            "ai_reason":"IA detecta control territorial",

            "resultado_probable":"2-1",
            "ganador_probable":p["local"],
            "over_under_probable":"OVER 2.5",

            "gol_inminente":{
                "gol_inminente":random.choice([True,False])
            }

        })

    return senales

# =========================================
# STATUS
# =========================================

@app.route("/status")
def status():

    return jsonify({

        "status":"ok",
        "service":"JHONNY_ELITE_BACKEND"

    })

# =========================================
# SCAN PARTIDOS
# =========================================

@app.route("/scan")
def scan():

    global cache_partidos

    cache_partidos=generar_partidos_demo()

    return jsonify({

        "partidos_analizados":len(cache_partidos),
        "partidos":cache_partidos

    })

# =========================================
# SIGNALS
# =========================================

@app.route("/signals")
def signals():

    global cache_senales

    if not cache_partidos:
        cache_partidos.extend(generar_partidos_demo())

    cache_senales=generar_senales_demo(cache_partidos)

    return jsonify({

        "total_senales":len(cache_senales),
        "signals":cache_senales

    })

# =========================================
# EXPLORADOR DE LIGAS
# =========================================

@app.route("/league-explorer")
def league_explorer():

    ligas={}

    for p in cache_partidos:

        region="Europe"

        if p["pais"] in ["Brazil","Argentina"]:
            region="South America"

        if p["pais"]=="Mexico":
            region="North America"

        if region not in ligas:
            ligas[region]=[]

        ligas[region].append({

            "league":p["liga"],
            "country":p["pais"],
            "matches":1,
            "signals":1,
            "elite":0,
            "top":1

        })

    return jsonify({

        "league_explorer":ligas

    })

# =========================================
# HISTORIAL
# =========================================

@app.route("/history")
def history():

    return jsonify(cache_historial)

# =========================================
# STATS DEL SISTEMA
# =========================================

@app.route("/learning-stats")
def learning_stats():

    return jsonify({

        "ganadas":0,
        "perdidas":0,
        "win_rate":0,
        "roi_percent":0,
        "signals_elite":0,
        "signals_top":len(cache_senales),
        "value_promedio":21,
        "riesgo_medio":4.6

    })

# =========================================
# DETALLE DEL PARTIDO
# =========================================

@app.route("/match-details/<match_id>")
def match_details(match_id):

    global cache_partidos, cache_senales

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
        "minute": partido.get("minuto"),
        "status": partido.get("estado_partido"),

        "score": f"{partido.get('marcador_local',0)}-{partido.get('marcador_visitante',0)}",

        "marcador_local": partido.get("marcador_local",0),
        "marcador_visitante": partido.get("marcador_visitante",0),

        "xg": partido.get("xG",0),

        "shots": partido.get("shots",0),
        "shots_on_target": partido.get("shots_on_target",0),
        "dangerous_attacks": partido.get("dangerous_attacks",0),

        "momentum": partido.get("momentum","MEDIO"),

        "goal_pressure": partido.get("goal_pressure",{}),
        "goal_predictor": partido.get("goal_predictor",{}),
        "chaos": partido.get("chaos",{}),

        "signal": senal or None

    })

# =========================================
# RUN SERVER
# =========================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
