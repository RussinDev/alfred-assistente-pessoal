"""
Motor do ALFRED para a interface gráfica.

Replica o loop do main.py (palavra de ativação, modo atenção, comandos),
mas em vez de imprimir no terminal avisa a interface por callbacks.
Não depende de Qt, então também pode ser testado sozinho.

Estados enviados em on_state:
    iniciando, aguardando, ouvindo, processando, falando,
    mudo, sem_microfone, offline
Papéis enviados em on_message:
    user, alfred, erro, system
"""
import queue
import threading
import time

ATENCAO_SEGUNDOS = 15


class AlfredEngine:
    def __init__(self, on_state, on_message, on_mic, on_command, on_shutdown):
        self._on_state = on_state
        self._on_message = on_message
        self._on_mic = on_mic
        self._on_command = on_command
        self._on_shutdown = on_shutdown

        self._typed = queue.Queue()
        self._rodando = False
        self._thread = None

        self._mic_ligado = True
        self._mic_ok = False
        self._atencao = False
        self._atencao_ate = 0.0
        self._parar_escuta = None

        self._ah = None  # audio_handler
        self._ch = None  # command_handler

    # ------------------------------------------------------------------
    # API chamada pela interface
    # ------------------------------------------------------------------
    def start(self):
        self._rodando = True
        self._thread = threading.Thread(target=self._run, name="alfred-engine", daemon=True)
        self._thread.start()

    def stop(self):
        self._rodando = False
        self.silence()
        if self._parar_escuta:
            try:
                self._parar_escuta(wait_for_stop=False)
            except Exception:
                pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def submit(self, texto):
        """Comando digitado (ou clicado em uma ação rápida)."""
        texto = (texto or "").strip()
        if not texto:
            return
        self._on_message("user", texto)
        self._typed.put(texto)

    def set_mic(self, ligado):
        self._mic_ligado = bool(ligado)
        if not self._mic_ligado:
            self._atencao = False
        self._on_state(self._estado_ocioso())

    def mic_ligado(self):
        return self._mic_ligado

    def listen_now(self):
        """Entra no modo atenção sem precisar dizer 'Alfred'."""
        if not self._mic_ok or not self._mic_ligado:
            return
        self._entrar_atencao()
        self._on_state("ouvindo")

    def silence(self):
        """Interrompe a fala em andamento."""
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------
    def _entrar_atencao(self):
        self._atencao = True
        self._atencao_ate = time.time() + ATENCAO_SEGUNDOS

    def _estado_ocioso(self):
        if not self._mic_ok:
            return "sem_microfone"
        if not self._mic_ligado:
            return "mudo"
        if self._atencao:
            return "ouvindo"
        return "aguardando"

    def _falar(self, texto):
        """Substitui o speak() para a interface mostrar a fala e o estado."""
        if not texto or not texto.strip():
            return
        texto = texto.strip()
        self._on_message("alfred", texto)
        self._on_state("falando")
        try:
            self._ah.speak(texto)
        except Exception as erro:
            self._on_message("erro", f"Falha ao falar: {erro}")
        finally:
            self._on_state(self._estado_ocioso())

    def _executar(self, comando):
        self._on_state("processando")
        try:
            resposta, encerrar = self._ch.handle_command(comando)
        except Exception as erro:
            self._on_message("erro", f"Falha ao executar o comando: {erro}")
            self._on_state(self._estado_ocioso())
            return

        if resposta and "não consta no meu sistema" not in resposta.lower():
            self._on_command()
        elif not resposta:
            # handle_command já falou cada parte de um comando composto
            self._on_command()

        if resposta:
            if "?" in resposta or "Diga" in resposta:
                self._entrar_atencao()  # antes de falar, para o estado não oscilar
            self._falar(resposta)

        if encerrar:
            self._rodando = False
            self._on_shutdown()
            return

        self._on_state(self._estado_ocioso())

    def _descartar_audio(self):
        try:
            self._ah._flush_queue()
        except Exception:
            pass

    def _run(self):
        try:
            import audio_handler as ah
            import command_handler as ch
        except Exception as erro:
            self._on_message("erro", f"Não foi possível carregar os módulos do ALFRED: {erro}")
            self._on_state("offline")
            return

        self._ah, self._ch = ah, ch
        ch.speak = self._falar  # comandos compostos também passam pela interface

        self._on_state("iniciando")
        try:
            ah.prewarm([])
        except Exception as erro:
            self._on_message("erro", f"Áudio indisponível: {erro}")

        try:
            self._parar_escuta = ah.start_listening()
            self._mic_ok = True
            self._on_mic(True, "")
        except Exception as erro:
            self._mic_ok = False
            self._on_mic(False, str(erro))
            self._on_message(
                "erro",
                "Não encontrei um microfone utilizável. Você ainda pode digitar comandos.",
            )

        self._on_state(self._estado_ocioso())
        self._falar("Sistemas ativos, mestre Eric. Aguardando palavra de ativação.")

        while self._rodando:
            try:
                self._passo()
            except Exception as erro:
                self._on_message("erro", f"Erro inesperado: {erro}")
                self._on_state(self._estado_ocioso())
                time.sleep(0.5)

    def _passo(self):
        ah = self._ah

        # 1) comandos digitados têm prioridade
        try:
            digitado = self._typed.get_nowait()
        except queue.Empty:
            digitado = None
        if digitado:
            self._executar(digitado)
            return

        # 2) voz
        frase = ah.hear(timeout=0.1)

        if not self._mic_ligado:
            self._descartar_audio()
            frase = None

        if frase:
            if self._atencao:
                eh_ativacao, comando = True, frase
            else:
                eh_ativacao, comando = ah.find_wakeword(frase)

            if eh_ativacao:
                if not comando:
                    self._entrar_atencao()
                    self._falar("Sim, mestre.")
                    return
                self._atencao = False
                self._on_message("user", comando)
                self._executar(comando)
                return

        # 3) fim do modo atenção
        if self._atencao and time.time() > self._atencao_ate:
            self._atencao = False
            self._on_state(self._estado_ocioso())