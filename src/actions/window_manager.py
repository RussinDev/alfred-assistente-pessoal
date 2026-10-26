import pyautogui
import time

def minimize_all():
    try:
        pyautogui.hotkey('win', 'd')
        return "Tudo minimizado, mestre."
    except Exception as erro:
        print(f"[ERRO JANELAS]: {erro}")
        return "Desculpe mestre, não consegui minimizar as janelas."