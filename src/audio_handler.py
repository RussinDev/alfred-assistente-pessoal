import asyncio
import hashlib
import os
import queue
import re
import shutil
import tempfile
import threading
import time
import unicodedata
from difflib import SequenceMatcher

import edge_tts
import pygame
import speech_recognition as sr

DEBUG = True
VOZ = "pt-BR-AntonioNeural"
VELOCIDADE = "+15%"
TOM = "-5Hz"
TEMPO_LIMITE_FRASE = 10

r = sr.Recognizer()
r.pause_threshold = 0.5
r.non_speaking_duration = 0.3

# DESLIGAMOS A SENSIBILIDADE DINÂMICA. 
# Assim, um barulho alto não vai deixar o microfone "surdo" depois.
r.dynamic_energy_threshold = False 
# Forçamos uma sensibilidade alta (capta sons baixos)
r.energy_threshold = 300 

_mic = None
_audio_queue = queue.Queue()
_fala_queue = queue.Queue()

_is_speaking = threading.Event()
_speech_lock = threading.Lock()

_loop_voz = None
_thread_voz = None
_mixer_inicializado = False
_audio_cache = {}

# ==================================================
# CACHE DE VOZ EM DISCO (frases fixas tocam instantaneamente)
# ==================================================
PASTA_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cache_voz")

FRASES_FIXAS = [
    "Sim, mestre.",
    "Sistemas ativos, mestre Eric. Aguardando palavra de ativação.",
    "Até logo, mestre Eric!",
    "Desculpe, essa instrução ainda não consta no meu sistema.",
    "Não consegui compreender. Pode repetir?",
    "Diga o volume desejado, de zero a cem.",
    "Desculpe, mestre Eric, não entendi essa combinação de ordens.",
]
_FIXAS = set(FRASES_FIXAS)

def _caminho_cache(texto):
    chave = hashlib.sha1(f"{VOZ}|{VELOCIDADE}|{TOM}|{texto}".encode("utf-8")).hexdigest()[:16]
    return os.path.join(PASTA_CACHE, chave + ".mp3")

def normalize(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9\s]", " ", texto).strip()

def _flush_queue():
    while not _audio_queue.empty():
        try:
            _audio_queue.get_nowait()
        except queue.Empty:
            break

async def _gerar_audio(texto, caminho):
    texto_limpo = texto.strip().lower()
    
    if texto_limpo in _audio_cache and os.path.exists(_audio_cache[texto_limpo]):
        shutil.copyfile(_audio_cache[texto_limpo], caminho)
        return

    comunicacao = edge_tts.Communicate(texto, VOZ, rate=VELOCIDADE, pitch=TOM)
    await comunicacao.save(caminho)
    
    cache_path = os.path.join(tempfile.gettempdir(), f"alfred_cache_{hash(texto_limpo)}.mp3")
    shutil.copyfile(caminho, cache_path)
    _audio_cache[texto_limpo] = cache_path

def _inicializar_audio():
    global _mixer_inicializado
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    _mixer_inicializado = True

def prewarm(frases):
    global _loop_voz, _thread_voz
    try:
        _inicializar_audio()
    except Exception as erro:
        print(f"[AVISO AUDIO]: {erro}")

    if _thread_voz is None or not _thread_voz.is_alive():
        _thread_voz = threading.Thread(target=_worker_voz, daemon=True)
        _thread_voz.start()

    threading.Thread(target=_pre_gerar, args=(list(FRASES_FIXAS) + list(frases or []),), daemon=True).start()

def _pre_gerar(frases):
    loop = asyncio.new_event_loop()
    try:
        os.makedirs(PASTA_CACHE, exist_ok=True)
        for texto in frases:
            caminho = _caminho_cache(texto)
            if os.path.exists(caminho) and os.path.getsize(caminho) > 0:
                continue
            tmp = f"{caminho}.{threading.get_ident()}.tmp"
            try:
                loop.run_until_complete(
                    edge_tts.Communicate(texto, VOZ, rate=VELOCIDADE, pitch=TOM).save(tmp)
                )
                os.replace(tmp, caminho)
            except Exception:
                if os.path.exists(tmp):
                    os.remove(tmp)
    finally:
        loop.close()

def _worker_voz():
    global _loop_voz
    while True:
        item = _fala_queue.get()
        if item is None:
            _fala_queue.task_done()
            break
        texto, concluido = item
        try:
            _reproduzir_texto(texto)
        except Exception as erro:
            print(f"[ERRO DE VOZ]: {erro}")
        finally:
            if concluido is not None:
                concluido.set()
            _fala_queue.task_done()

def _reproduzir_texto(texto):
    caminho = None
    apagar = True
    with _speech_lock:
        _is_speaking.set()
        try:
            global _loop_voz
            if _loop_voz is None or _loop_voz.is_closed():
                _loop_voz = asyncio.new_event_loop()
            asyncio.set_event_loop(_loop_voz)

            fixa = texto in _FIXAS
            caminho_fixo = _caminho_cache(texto) if fixa else None
            if fixa and os.path.exists(caminho_fixo) and os.path.getsize(caminho_fixo) > 0:
                caminho = caminho_fixo  # instantâneo, sem internet
                apagar = False
            else:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as arquivo:
                    caminho = arquivo.name
                _loop_voz.run_until_complete(_gerar_audio(texto, caminho))
                apagar = True

            _inicializar_audio()
            pygame.mixer.music.load(caminho)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                time.sleep(0.01)
        finally:
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
            except Exception:
                pass
            if apagar and caminho and os.path.exists(caminho):
                try:
                    os.remove(caminho)
                except OSError:
                    pass

            _flush_queue()
            _is_speaking.clear()

def speak(texto):
    if not texto or not texto.strip():
        return
    print(f"ALFRED: {texto}")
    if _thread_voz is None or not _thread_voz.is_alive():
        prewarm([])
    concluido = threading.Event()
    _fala_queue.put((texto.strip(), concluido))
    concluido.wait()

def start_listening():
    global _mic
    _mic = sr.Microphone()

    with _mic as source:
        print("[SISTEMA]: Calibrando ruido ambiente por 1 segundo... (Fique em silêncio)")
        r.adjust_for_ambient_noise(source, duration=1.0)
        
        # Garante que o microfone se mantém super sensível mesmo após a calibração
        if r.energy_threshold > 500:
            r.energy_threshold = 400

    def _callback(recognizer, audio):
        if not _is_speaking.is_set():
            _audio_queue.put(audio)

    print("[SISTEMA]: Microfone ativo e com sensibilidade travada no máximo.")

    return r.listen_in_background(_mic, _callback, phrase_time_limit=TEMPO_LIMITE_FRASE)

def hear(timeout=None):
    try:
        audio = _audio_queue.get(timeout=timeout)
    except queue.Empty:
        return None

    try:
        texto = r.recognize_google(audio, language="pt-BR")
        if DEBUG:
            print(f"-> Ouvido: '{texto}'")
        return texto
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as erro:
        print(f"[ERRO Google STT]: {erro}")
        return ""


# ==================================================
# PALAVRA DE ATIVACAO (MEGA FLEXÍVEL)
# ==================================================

WAKE_WORDS = {
    "alfred", "aufred", "alfrade", "alfre", "alfired", "fred", "frede", "phred", 
    "alfie", "alfy", "alfi", "alvi", "alfredj", "aufredj", "alfrede", "aufrede", 
    "aufré", "alfré", "alfrê", "aufrê", "aufréd", "ófred", "ofred", "orfred", 
    "al", "au", "alfredo", "alvaro", "álvaro", "alface", "iphone", "ifood", "alfa"
}

def _is_wake(palavra):
    if palavra in WAKE_WORDS: return True
    # Reduzida a exigência de perfeição matemática de 0.75 para 0.65
    return SequenceMatcher(None, palavra, "alfred").ratio() >= 0.65

def find_wakeword(texto):
    texto_norm = normalize(texto)
    palavras = texto_norm.split()
    
    for i, palavra in enumerate(palavras):
        if _is_wake(palavra):
            return True, " ".join(palavras[i + 1:])
        if i + 1 < len(palavras):
            combinada = palavra + palavras[i + 1]
            if _is_wake(combinada):
                return True, " ".join(palavras[i + 2:])
                
    # Super-gatilho: se o Google comer o espaço, mas o começo bater (ex: "alfredquehorassao")
    for wake in WAKE_WORDS:
        if texto_norm.startswith(wake):
            comando = texto_norm[len(wake):].strip()
            return True, comando
            
    return False, ""