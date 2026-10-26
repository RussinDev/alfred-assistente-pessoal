import pyautogui

def play_music():
    """Retoma a reprodução de mídia."""
    try:
        pyautogui.press("playpause")
        return "Música retomada."
    except Exception as e:
        return f"Erro ao controlar o Spotify: {e}"

def pause_music():
    """Pausa a reprodução de mídia."""
    try:
        pyautogui.press("playpause")
        return "Música pausada."
    except Exception as e:
        return f"Erro ao controlar o Spotify: {e}"

def next_track():
    """Pula para a próxima faixa."""
    try:
        pyautogui.press("nexttrack")
        return "Avançando para a próxima faixa."
    except Exception as e:
        return f"Erro ao controlar o Spotify: {e}"

def set_volume(level):
    """Ajusta o volume do sistema/mídia."""
    try:
        # Garante que o volume está entre 0 e 100
        level = max(0, min(100, int(level)))
        # Ajuste aproximado baseado em etapas de volume
        steps = level // 5
        for _ in range(steps):
            pyautogui.press("volumeup")
        return f"Volume ajustado para {level} por cento."
    except Exception as e:
        return f"Erro ao ajustar o volume: {e}"

def play_specific_song(song_name):
    """Função de compatibilidade caso queira pesquisar por música, ou apenas abre o atalho."""
    try:
        pyautogui.hotkey('ctrl', 'k') # Atalho comum de busca em muitos players
        return f"Procurando por {song_name}."
    except Exception as e:
        return f"Não foi possível tocar a música: {e}"