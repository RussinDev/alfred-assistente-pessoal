import os
import time
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

load_dotenv()  # lê o arquivo .env
TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

API_URL = "https://api.football-data.org/v4/competitions/BSA/matches"

BRT = timezone(timedelta(hours=-3))  # horário de Brasília
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
        "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]

_cache = {"quando": 0, "partidas": []}
CACHE_SEGUNDOS = 1800  # 30 min: resposta mais rápida e não estoura o limite da API


def _buscar_partidas():
    if time.time() - _cache["quando"] < CACHE_SEGUNDOS and _cache["partidas"]:
        return _cache["partidas"]

    resp = requests.get(API_URL, headers={"X-Auth-Token": TOKEN}, timeout=8)
    resp.raise_for_status()
    partidas = resp.json().get("matches", [])
    _cache.update(quando=time.time(), partidas=partidas)
    return partidas


def _nome(time_info):
    return time_info.get("shortName") or time_info.get("name") or ""


def _quando(dt):
    dias = (dt.date() - datetime.now(BRT).date()).days
    if dias == 0:
        dia = "hoje"
    elif dias == 1:
        dia = "amanhã"
    else:
        dia = f"{DIAS[dt.weekday()]}, dia {dt.day} de {MESES[dt.month - 1]}"
    hora = f"{dt.hour} horas"
    if dt.minute:
        hora += f" e {dt.minute} minutos"
    return f"{dia}, às {hora}"


def get_vasco_game():
    if not TOKEN:
        return "Mestre, falta configurar o token da API de futebol no arquivo ponto env."

    try:
        partidas = _buscar_partidas()
    except requests.HTTPError as e:
        codigo = e.response.status_code
        print(f"[vasco_tracker] HTTP {codigo}: {e.response.text[:200]}")
        if codigo == 429:
            return "A API de futebol limitou as consultas. Tente de novo em um minuto."
        return "Não consegui acessar a API de futebol. Verifique o token."
    except Exception as e:
        print(f"[vasco_tracker] erro: {e}")
        return "Não consegui consultar a agenda do Vasco agora."

    agora = datetime.now(timezone.utc)
    proximos = []
    for p in partidas:
        if p.get("status") not in ("SCHEDULED", "TIMED"):
            continue
        casa, fora = _nome(p["homeTeam"]), _nome(p["awayTeam"])
        if "vasco" not in (casa + fora).lower():
            continue
        dt = datetime.fromisoformat(p["utcDate"].replace("Z", "+00:00"))
        if dt >= agora:
            proximos.append((dt, casa, fora))

    if not proximos:
        return "Não encontrei próximos jogos do Vasco no Brasileirão."

    dt, casa, fora = min(proximos)
    dt = dt.astimezone(BRT)
    if "vasco" in casa.lower():
        return f"O próximo jogo do Vasco é contra o {fora}, em casa, {_quando(dt)}."
    return f"O próximo jogo do Vasco é contra o {casa}, fora de casa, {_quando(dt)}."