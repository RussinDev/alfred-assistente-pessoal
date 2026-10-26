import requests

# Coordenadas do Rio de Janeiro
LAT = "-22.9068"
LON = "-43.1729"

def get_weather():
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current_weather=true&timezone=America/Sao_Paulo"
    
    try:
        resposta = requests.get(url, timeout=5)
        dados = resposta.json()
        
        clima_atual = dados.get("current_weather", {})
        temperatura = round(clima_atual.get("temperature", 0)) 
        codigo_clima = clima_atual.get("weathercode", -1)
        
        descricao = _traduzir_codigo(codigo_clima)
        
        return f"A temperatura atual no Rio de Janeiro é de {temperatura} graus, com {descricao}."
        
    except Exception as erro:
        print(f"[ERRO CLIMA]: {erro}")
        return "Desculpe mestre, ocorreu uma falha ao consultar os satélites de meteorologia."

def get_rain_chance():
    # Nova URL buscando a probabilidade máxima de precipitação (chuva) do dia
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&daily=precipitation_probability_max&timezone=America/Sao_Paulo"
    
    try:
        resposta = requests.get(url, timeout=5)
        dados = resposta.json()
        
        # Pega a probabilidade de chuva do primeiro dia da lista (hoje)
        chance = dados.get("daily", {}).get("precipitation_probability_max", [0])[0]
        
        if chance == 0:
            return "Mestre, os radares indicam que não há nenhuma chance de chuva para hoje no Rio de Janeiro."
        elif chance < 30:
            return f"A chance de chuva para hoje é bem baixa, cerca de {chance} por cento. Pode sair tranquilo."
        elif chance < 70:
            return f"Há uma possibilidade moderada de chuva hoje, na casa dos {chance} por cento."
        else:
            return f"Recomendo levar um guarda-chuva, mestre. A probabilidade de chuva hoje é alta, chegando a {chance} por cento."
            
    except Exception as erro:
        print(f"[ERRO CHUVA]: {erro}")
        return "Desculpe mestre, não consegui aceder aos dados de precipitação no momento."

def _traduzir_codigo(codigo):
    tabela = {
        0: "céu limpo",
        1: "céu predominantemente limpo",
        2: "céu parcialmente nublado",
        3: "tempo nublado",
        45: "nevoeiro",
        48: "nevoeiro",
        51: "chuvisco leve",
        53: "chuvisco moderado",
        55: "chuvisco forte",
        61: "chuva leve",
        63: "chuva moderada",
        65: "chuva forte",
        80: "pancadas de chuva",
        81: "chuva forte e passageira",
        82: "tempestade forte",
        95: "tempestade",
        96: "tempestade com granizo",
        99: "tempestade severa"
    }
    return tabela.get(codigo, "condições mistas")