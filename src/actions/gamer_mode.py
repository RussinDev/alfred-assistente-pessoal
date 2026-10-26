import os

def activate_gamer_mode():
    """Abre os programas necessários para jogar com o controle genérico."""
    paths = {
        "HidHide": r"D:\Aplicativos\Hidhide\x64\HidHideClient.exe",
        "DS4 Windows": r"D:\Aplicativos\Ds4\DS4Windows.exe",
    }

    erros = []

    for nome, caminho in paths.items():
        if not os.path.exists(caminho):
            erros.append(nome)
            continue
        try:
            os.startfile(caminho)
        except Exception as e:
            print(f"[gamer_mode] Erro ao abrir {nome}: {e}")
            erros.append(nome)

    resposta = "Modo gamer ativado, mestre. "

    if erros:
        resposta += f"Não consegui abrir: {', '.join(erros)}. Verifique os caminhos no código."

    return resposta