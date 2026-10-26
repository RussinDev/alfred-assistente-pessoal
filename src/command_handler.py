import re
from difflib import SequenceMatcher

from audio_handler import normalize, speak
from actions.system_info import get_time, get_date
from actions.applications import open_application
from actions.websites import open_website
from actions.gamer_mode import activate_gamer_mode
from actions.system_diagnostics import run_diagnostics
from actions.weather import get_weather, get_rain_chance
from actions.vasco_tracker import get_vasco_game
from actions.window_manager import minimize_all

from actions.spotify_handler import (
    play_music,
    pause_music,
    next_track,
    set_volume,
    play_specific_song,
)

# ==================================================
# COMANDOS FIXOS DO ALFRED
# ==================================================

COMMANDS = [
    (
        [
            "horas", "horário", "hora certa", "que horas",
            "qual é a hora", "me diz as horas", "hora",
        ],
        get_time,
    ),
    (
        [
            "dia é hoje", "data", "que dia", "qual a data",
            "dia de hoje", "que dia é", "qual o dia", "dia",
        ],
        get_date,
    ),
    (
        [
            "diagnóstico", "verificar o computador",
            "verificar sistema", "como está o pc",
            "como tá a máquina", "tá lento", "limpar o pc",
        ],
        run_diagnostics,
    ),
    (
        [
            "modo gamer", "modo game", "modo gamers",
            "modo gaming", "modo geimer", "modo gueimer",
            "modo gaymer", "ativar modo gamer",
            "ligar modo gamer", "modo jogo", "modo de jogo",
            "gamer", "preparar para jogar", "abrir jogos",
            "jogar", "bora jogar", "ligar os controles",
        ],
        activate_gamer_mode,
    ),
    (
        [
            "previsão", "tempo hoje", "clima", 
            "temperatura", "como tá o tempo", "privisao",
            "qual a temperatura", "tá calor", "tá frio",
        ],
        get_weather,
    ),
    (
        [
            "chances de chuva", "chance de chuva", "chance de chuver",
            "probabilidade de chuva", "qual a probabilidade de chuva",
            "qual a probabilidade de chuver", "qual a chance de chover", 
            "chove hoje", "vai chover hoje", "vai chover", 
            "tem previsão de chuva", "risco de chuva", 
            "preciso de guarda chuva", "preciso de guarda-chuva", 
            "levar guarda-chuva", "chove", "tá chovendo",
        ],
        get_rain_chance,
    ),
    (
        [
            "jogo do vasco", "o vasco joga", "próximo jogo",
            "tem jogo hoje", "vascão", "jogo do gigante",
            "quando o vasco", "futebol do vasco",
            "gigante da colina",
        ],
        get_vasco_game,
    ),
    (
        [
            "minimizar tudo", "esconder abas", "esconder janelas",
            "minimizar janelas", "mostrar área de trabalho",
            "minimiza tudo", "limpar tela",
        ],
        minimize_all,
    ),
    (
        [
            "abrir o opera", "abrir navegador",
            "abrir ópera", "opera gx",
        ],
        lambda: open_application("opera"),
    ),
    (
        [
            "abrir a steam", "abrir o steam",
            "istim", "estin", "steam",
        ],
        lambda: open_application("steam"),
    ),
    (
        [
            "abrir downloads", "minha pasta",
            "pasta de downloads", "baixados",
        ],
        lambda: open_application("downloads"),
    ),
    (
        [
            "abrir discord", "abrir o discord",
            "discorde", "discorge", "discórd", "discord",
        ],
        lambda: open_application("discord"),
    ),
    (
        [
            "abrir whatsapp", "abrir o zap",
            "zap zap", "uatsap", "watsap", "zap",
        ],
        lambda: open_application("whatsapp"),
    ),
    (
        [
            "abrir o youtube", "abrir youtube",
            "iutubi", "iutub", "yutubi", "youtube",
        ],
        lambda: open_website("youtube"),
    ),
    (
        [
            "portal da faculdade", "abrir uva",
            "abrir a uva", "u v a", "veiga",
            "veiga de almeida", "universidade veiga",
        ],
        lambda: open_website("uva"),
    ),
    (
        [
            "abrir twitch", "tuitchi", "tuíti",
            "twitchi", "twitch",
        ],
        lambda: open_website("twitch"),
    ),
    (
        [
            "abrir disney", "disnei", "diznei", "disney",
        ],
        lambda: open_website("disney"),
    ),
    (
        [
            "abrir hbo", "abrir max", "agabeó", "aga be ó",
            "h b o", "bota na hbo", "bota na max",
            "colocar na hbo", "ei dí bê ou", "ei di be ou",
            "max",
        ],
        lambda: open_website("hbo"),
    ),
    (
        [
            "abrir netflix", "net flix", "netfrix",
            "bota na netflix", "netflix",
        ],
        lambda: open_website("netflix"),
    ),
    (
        [
            "abrir prime", "praime", "praimi",
            "prime video", "amazon prime",
        ],
        lambda: open_website("prime"),
    ),
    (
        [
            "abrir gmail", "meu email", "gimeio",
            "jimeio", "gi meio", "gmail",
        ],
        lambda: open_website("gmail"),
    ),
    (
        [
            "abrir instagram", "insta", "istagram",
            "instangran", "instagram",
        ],
        lambda: open_website("instagram"),
    ),
    (
        [
            "abrir twitter", "abrir o x", "tuiter",
            "tuíter", "xis", "twitter",
        ],
        lambda: open_website("twitter"),
    ),
    (
        [
            "abrir gemini", "jemini", "jémini",
            "gemine", "gemini",
        ],
        lambda: open_website("gemini"),
    ),
    (
        [
            "abrir chatgpt", "abrir gpt", "chat gpt",
            "xat gpt", "chat jpt", "xat jpt",
            "chatgepete", "chatgpt",
        ],
        lambda: open_website("chatgpt"),
    ),
]

EXIT_WORDS = [
    "sair",
    "desligar",
    "encerrar",
    "dormir",
    "tchau",
    "até logo",
    "fechar o sistema",
]

# ==================================================
# PREPARAÇÃO DOS COMANDOS
# ==================================================

def _compile(words):
    alternatives = "|".join(
        re.escape(normalize(word))
        for word in words
    )
    return re.compile(rf"\b(?:{alternatives})\b")

_TABELA = [
    (_compile(words), function)
    for words, function in COMMANDS
]

_SAIR = _compile(EXIT_WORDS)

def _modo_gamer_aproximado(texto):
    palavras = texto.split()
    for i in range(len(palavras) - 1):
        if palavras[i] in ("modo", "mod", "moda"):
            if SequenceMatcher(None, palavras[i + 1], "gamer").ratio() >= 0.6:
                return True
    return False

# ==================================================
# PROCESSADOR DE COMANDOS DO SPOTIFY (SUPER FLEXÍVEL)
# ==================================================

def _process_spotify_command(texto):
    texto = normalize(texto).strip()

    # NOVIDADE: Entende se você responder apenas com o número (ex: "50", "no 50", "para 50")
    numero_direto = re.search(r"^(?:bota no |coloca no |no |para )?(\d{1,3})$", texto)
    if numero_direto:
        volume = max(0, min(100, int(numero_direto.group(1))))
        return set_volume(volume), False

    # A. ABRIR SPOTIFY
    if any(c in texto for c in ["abrir", "abre", "iniciar"]) and any(s in texto for s in ["spotify", "ispotifai", "spotifai"]):
        return open_application("spotify"), False

    # B. VOLUME (Comando completo: "volume 50")
    volume_match = re.search(r"\b(?:volume|vol|altura)\b.*?\b(\d{1,3})\b", texto)
    if volume_match:
        volume = max(0, min(100, int(volume_match.group(1))))
        return set_volume(volume), False

    # Se você der o comando incompleto, ele avisa para dizer o número
    if any(c in texto for c in ["aumentar volume", "diminuir volume", "abaixar volume", "mudar volume", "colocar volume"]):
        return "Diga o volume desejado, de zero a cem.", False

    # C. PAUSAR / PARAR
    if any(c in texto for c in ["pausa", "parar", "pause", "para a", "para o", "calar"]):
        return pause_music(), False

    # D. PRÓXIMA MÚSICA / PULAR
    if any(c in texto for c in ["proxima", "pula", "passa", "avanca", "seguinte", "mudar de musica"]):
        return next_track(), False

    # E. RETOMAR / DESPAUSAR
    if any(c in texto for c in ["retomar", "continuar", "dar play", "despausar"]):
        return play_music(), False

    # F. TOCAR MÚSICA ESPECÍFICA (Mais natural)
    music_prefixes = [
        "quero ouvir ", "quero escutar ", "toca pra mim ", 
        "bota pra tocar ", "coloca pra tocar ", "colocar pra tocar ", 
        "reproduzir a musica ", "reproduzir musica ", "reproduzir ", 
        "tocar a musica ", "toca a musica ", "tocar o som ", "toca o som ",
        "tocar ", "toca ", "bota "
    ]
    
    for prefix in music_prefixes:
        prefix = normalize(prefix)
        if texto.startswith(prefix):
            nome_musica = texto[len(prefix):].strip()
            
            # Se disser só "tocar" ou "toca música" sem especificar
            if not nome_musica or nome_musica in ["musica", "a musica", "som", "o som", "spotify", "ispotifai", "spotifai"]:
                return play_music(), False
                
            return play_specific_song(nome_musica), False

    return None

# ==================================================
# PROCESSADOR DE UM ÚNICO COMANDO
# ==================================================

def _process_single_command(texto):
    texto = normalize(texto).strip()
    if not texto:
        return "Não consegui compreender. Pode repetir?", False

    spotify_result = _process_spotify_command(texto)
    if spotify_result is not None:
        return spotify_result

    if _modo_gamer_aproximado(texto):
        return activate_gamer_mode(), False

    for padrao, funcao in _TABELA:
        if padrao.search(texto):
            return funcao(), False

    if _SAIR.search(texto):
        return "Até logo, mestre Eric!", True

    return "Desculpe, essa instrução ainda não consta no meu sistema.", False

# ==================================================
# PROCESSADOR DE MÚLTIPLOS COMANDOS
# ==================================================

def handle_command(comando):
    if not comando or not comando.strip():
        return "Não consegui compreender. Pode repetir?", False

    texto_bruto = comando.lower().strip()
    prefixos = ["alfred ", "alfréd ", "alfrede ", "aufred ", "aufré ", "al ", "au "]
    for p in prefixos:
        if texto_bruto.startswith(p):
            texto_bruto = texto_bruto[len(p):].strip()

    texto_bruto = texto_bruto.replace(" depois ", " e ")
    texto_norm = normalize(texto_bruto)
    music_starts = ("tocar ", "toca ", "quero ouvir ", "quero escutar ", "toca pra mim ", "bota pra tocar ", "coloca pra tocar ", "reproduzir ", "bota ")

    if " e " in texto_bruto and not texto_norm.startswith(music_starts):
        sub_comandos = texto_bruto.split(" e ")
        encerrar_total = False
        teve_resposta = False

        for sub in sub_comandos:
            if not sub.strip():
                continue

            resposta, encerrar = _process_single_command(sub)

            if resposta and "não consta no meu sistema" not in resposta.lower():
                speak(resposta)
                teve_resposta = True

            if encerrar:
                encerrar_total = True

        if not teve_resposta:
            return "Desculpe, mestre Eric, não entendi essa combinação de ordens.", False
        
        return "", encerrar_total

    resposta, encerrar = _process_single_command(texto_bruto)

    if "não consta no meu sistema" in resposta.lower():
        print(f"[NÃO RECONHECIDO] Ouvi: '{comando}'")

    return resposta, encerrar

def execute_command(comando):
    return handle_command(comando)