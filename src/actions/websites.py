import webbrowser

def open_website(site_name):
    if site_name == "youtube":
        webbrowser.open("https://www.youtube.com")
        return "Abrindo o YouTube."
    elif site_name == "uva":
        webbrowser.open("https://portalaluno.uva.br/Login")
        return "Acessando o portal da Universidade Veiga de Almeida."
    elif site_name == "twitch":
        webbrowser.open("https://www.twitch.tv")
        return "Abrindo a Twitch."
    elif site_name == "disney":
        webbrowser.open("https://www.disneyplus.com")
        return "Abrindo o Disney Plus."
    elif site_name == "hbo":
        webbrowser.open("https://www.max.com") 
        return "Abrindo o HBO Max."
    elif site_name == "netflix":
        webbrowser.open("https://www.netflix.com")
        return "Abrindo a Netflix."
    elif site_name == "prime":
        webbrowser.open("https://www.primevideo.com")
        return "Abrindo o Prime Video."
    elif site_name == "gmail":
        webbrowser.open("https://mail.google.com")
        return "Abrindo o Gmail."
    elif site_name == "instagram":
        webbrowser.open("https://www.instagram.com")
        return "Abrindo o Instagram."
    elif site_name == "twitter":
        webbrowser.open("https://x.com")
        return "Abrindo o Twitter."
    elif site_name == "gemini":
        webbrowser.open("https://gemini.google.com")
        return "Abrindo o Google Gemini."
    elif site_name == "chatgpt":
        webbrowser.open("https://chatgpt.com")
        return "Abrindo o ChatGPT."
    else:
        return "Desculpe, este site não está na minha lista."