import os

def open_application(app_name):
    try:
        if app_name == "opera":
            os.startfile("opera.exe")
            return "Abrindo o navegador Opera GX."
        elif app_name == "steam":
            os.startfile("steam://open/main")
            return "Iniciando a Steam."
        elif app_name == "downloads":
            os.startfile(r"D:\Download")
            return "Abrindo a pasta de Downloads no disco D."
        elif app_name == "spotify":
            os.startfile("spotify:") # Protocolo oficial do Windows
            return "Abrindo o Spotify."
        elif app_name == "whatsapp":
            os.startfile("whatsapp:") # Protocolo oficial do Windows
            return "Abrindo o WhatsApp."
        elif app_name == "discord":
            # Tenta abrir pelo caminho padrão de instalação, ou via comando do sistema
            caminho_discord = os.path.expanduser("~\\AppData\\Local\\Discord\\Discord.exe")
            if os.path.exists(caminho_discord):
                os.startfile(caminho_discord)
            else:
                os.system("start discord")
            return "Abrindo o Discord."
        else:
            return f"Ainda não sei como abrir {app_name}."
    except Exception:
        return f"Falha ao abrir {app_name}. Verifique se o aplicativo está instalado corretamente."