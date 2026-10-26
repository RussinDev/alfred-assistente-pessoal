import time
from audio_handler import start_listening, hear, find_wakeword, speak, prewarm, r
from command_handler import handle_command

# Ajuste equilibrado: dá-lhe tempo para respirar entre dois comandos sem cortar a sua voz
r.pause_threshold = 0.7
r.non_speaking_duration = 0.4

def start_alfred_logic():
    def log(mensagem, origem="SISTEMA"):
        print(f"[{origem}]: {mensagem}")

    log("Carregando módulos centrais...", "SISTEMA")
    prewarm([])
    stop_listening = start_listening()
    log("Microfone online. ALFRED na escuta.", "SISTEMA")
    
    speak("Sistemas ativos, mestre Eric. Aguardando palavra de ativação.")

    escuta_ativa = False
    tempo_limite_escuta = 0

    try:
        while True:
            frase = hear(timeout=0.1)
            
            if frase:
                if escuta_ativa:
                    is_wake = True
                    comando = frase
                else:
                    is_wake, comando = find_wakeword(frase)
                
                if is_wake:
                    if not comando:
                        escuta_ativa = True
                        # Tempo de espera estendido para 15 segundos no modo atenção
                        tempo_limite_escuta = time.time() + 15 
                        
                        log("Sim, mestre.", "ALFRED")
                        speak("Sim, mestre.")
                        continue 
                    else:
                        escuta_ativa = False 
                        log(comando, "VOCÊ")
                        
                        resposta, encerrar = handle_command(comando)
                        
                        if resposta:  # Evita tentar falar respostas vazias
                            log(resposta, "ALFRED")
                            speak(resposta)
                            
                            # NOVIDADE: Se ele fizer uma pergunta, o microfone continua aberto!
                            if "?" in resposta or "Diga" in resposta:
                                escuta_ativa = True
                                tempo_limite_escuta = time.time() + 15
                                log("Modo Atenção estendido. Aguardando sua resposta...", "SISTEMA")
                        
                        if encerrar:
                            log("Sistemas offline.", "SISTEMA")
                            break
                        
                        if not escuta_ativa:
                            log("Aguardando novas instruções.", "SISTEMA")

            if escuta_ativa and time.time() > tempo_limite_escuta:
                escuta_ativa = False
                log("Tempo de espera esgotado. Retornando ao modo de fundo.", "SISTEMA")

    except KeyboardInterrupt:
        pass
    finally:
        stop_listening(wait_for_stop=False)
        log("Desligado.", "SISTEMA")

if __name__ == "__main__":
    start_alfred_logic()