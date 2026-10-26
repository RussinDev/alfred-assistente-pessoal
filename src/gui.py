"""
Interface gráfica do ALFRED (PySide6).

Executar:  python src\\gui.py
Usa o mesmo cérebro do main.py (audio_handler + command_handler),
através do alfred_engine.py.
"""
import datetime
import math
import os
import sys
import time
from collections import deque

# Com pythonw não existe console; evita erro nos print() dos outros módulos.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

# Quando empacotado em .exe, trabalha a partir da pasta do executável
# (o .env com as chaves fica ao lado do ALFRED.exe).
if getattr(sys, "frozen", False):
    _base = os.path.dirname(sys.executable)
    os.chdir(_base)
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(_base, ".env"))
    except Exception:
        pass

from PySide6.QtCore import QObject, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen,
    QIcon, QRadialGradient,
)
from PySide6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSizeGrip, QSizePolicy, QVBoxLayout, QWidget,
)

try:
    import psutil
except ImportError:  # a interface continua funcionando sem os gráficos
    psutil = None

from alfred_engine import AlfredEngine
from config_manager import config, save_config

# ======================================================================
# TEMAS
# ======================================================================
THEMES = {
    "escuro": {
        "bg0": "#0b0912", "bg1": "#18112b", "glow": "#7c3aed",
        "card": "rgba(255,255,255,0.05)", "border": "rgba(255,255,255,0.10)",
        "text": "#f1eefb", "muted": "#9a93b5",
        "accent": "#8b5cf6", "accent2": "#b79cff", "accent_soft": "rgba(139,92,246,0.22)",
        "chip": "rgba(255,255,255,0.06)", "chip_hover": "rgba(255,255,255,0.12)",
        "input": "rgba(0,0,0,0.30)", "bubble": "rgba(255,255,255,0.08)",
        "scroll": "rgba(255,255,255,0.18)", "orb_dark": "#2a1466",
        "ok": "#4ade80", "warn": "#fbbf24", "err": "#f87171",
    },
    "claro": {
        "bg0": "#f6f4fc", "bg1": "#e8e2f8", "glow": "#a78bfa",
        "card": "rgba(255,255,255,0.72)", "border": "rgba(70,40,150,0.12)",
        "text": "#1c1533", "muted": "#6b6485",
        "accent": "#6d3df0", "accent2": "#8b66ff", "accent_soft": "rgba(109,61,240,0.14)",
        "chip": "rgba(109,61,240,0.07)", "chip_hover": "rgba(109,61,240,0.14)",
        "input": "rgba(255,255,255,0.85)", "bubble": "rgba(255,255,255,0.85)",
        "scroll": "rgba(70,40,150,0.25)", "orb_dark": "#3b1a99",
        "ok": "#16a34a", "warn": "#d97706", "err": "#dc2626",
    },
}
T = {}


def set_theme(nome):
    T.clear()
    T.update(THEMES.get(nome, THEMES["escuro"]))


def qcolor(chave_ou_hex, alpha=None):
    c = QColor(T.get(chave_ou_hex, chave_ou_hex))
    if alpha is not None:
        c.setAlpha(alpha)
    return c


def with_alpha(cor, alpha):
    c = QColor(cor)
    c.setAlpha(alpha)
    return c


QSS = """
QLabel { color: @text@; font-family: "Segoe UI"; font-size: 13px; background: transparent; }
QLabel#muted { color: @muted@; }
QLabel#brand { font-size: 17px; font-weight: 700; }
QLabel#greeting { font-size: 26px; font-weight: 600; }
QLabel#cardTitle { font-size: 14px; font-weight: 600; }
QLabel#statLabel { color: @muted@; font-size: 12px; }
QLabel#statValue { font-size: 28px; font-weight: 600; }
QLabel#statSub { color: @muted@; font-size: 11px; }
QLabel#stateTitle { font-size: 20px; font-weight: 600; }
QLabel#statusText { color: @muted@; font-size: 12px; }
QLabel#systemNote { color: @muted@; font-size: 12px; }
QLabel#bubbleUser { background: @accent@; color: #ffffff; border-radius: 16px;
                    padding: 10px 14px; font-size: 14px; }
QLabel#bubbleAlfred { background: @bubble@; border: 1px solid @border@; border-radius: 16px;
                      padding: 10px 14px; font-size: 14px; }
QLabel#bubbleErro { background: rgba(248,113,113,0.14); border: 1px solid rgba(248,113,113,0.45);
                    border-radius: 16px; padding: 10px 14px; font-size: 14px; }

QFrame#card { background: @card@; border: 1px solid @border@; border-radius: 18px; }

QPushButton { font-family: "Segoe UI"; font-size: 13px; color: @text@; background: @chip@;
              border: 1px solid @border@; border-radius: 12px; padding: 9px 14px; }
QPushButton:hover { background: @chip_hover@; }
QPushButton:pressed { background: @accent_soft@; }
QPushButton#primary { background: @accent@; color: #ffffff; border: none; font-weight: 600; }
QPushButton#primary:hover { background: @accent2@; }
QPushButton[on="true"] { background: @accent_soft@; border: 1px solid @accent@; }
QPushButton#winBtn { background: transparent; border: none; border-radius: 8px;
                     padding: 4px 11px; font-size: 15px; }
QPushButton#winBtn:hover { background: @chip_hover@; }
QPushButton#closeBtn { background: transparent; border: none; border-radius: 8px;
                       padding: 4px 11px; font-size: 15px; }
QPushButton#closeBtn:hover { background: rgba(248,113,113,0.85); color: #ffffff; }

QLineEdit { background: @input@; border: 1px solid @border@; border-radius: 14px;
            padding: 11px 16px; color: @text@; font-family: "Segoe UI"; font-size: 14px;
            selection-background-color: @accent@; }
QLineEdit:focus { border: 1px solid @accent@; }

#chatScroll { background: transparent; border: none; }
#chatScroll > QWidget > QWidget { background: transparent; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 4px 0; }
QScrollBar::handle:vertical { background: @scroll@; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
"""


def build_qss():
    qss = QSS
    for chave, valor in T.items():
        qss = qss.replace(f"@{chave}@", valor)
    return qss


# ======================================================================
# TEXTOS DE ESTADO
# ======================================================================
ESTADOS = {
    "iniciando":     ("Iniciando…", "Calibrando o microfone, fique em silêncio."),
    "aguardando":    ("Aguardando comando", "Diga “Alfred” ou digite abaixo."),
    "ouvindo":       ("Ouvindo você", "Pode falar o comando."),
    "processando":   ("Interpretando…", "Executando sua solicitação."),
    "falando":       ("Falando", "Use “Calar” para interromper."),
    "mudo":          ("Microfone desligado", "Você ainda pode digitar comandos."),
    "sem_microfone": ("Microfone indisponível", "Você ainda pode digitar comandos."),
    "offline":       ("Offline", "Os módulos do ALFRED não carregaram."),
}
STATUS_CABECALHO = {
    "iniciando": ("warn", "Iniciando"),
    "aguardando": ("ok", "Disponível"),
    "ouvindo": ("ok", "Disponível"),
    "processando": ("accent", "Ocupado"),
    "falando": ("accent", "Ocupado"),
    "mudo": ("warn", "Sem escuta"),
    "sem_microfone": ("warn", "Sem escuta"),
    "offline": ("err", "Offline"),
}
DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def repolish(widget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)


# ======================================================================
# WIDGETS PERSONALIZADOS
# ======================================================================
class Bridge(QObject):
    """Leva os eventos da thread do motor para a thread da interface."""
    state = Signal(str)
    message = Signal(str, str)
    mic = Signal(bool, str)
    command = Signal()
    shutdown = Signal()


class Orb(QWidget):
    """O elemento central: um orbe que muda de comportamento com o estado."""

    def __init__(self):
        super().__init__()
        self.state = "iniciando"
        self._t0 = time.monotonic()
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(33)

    def set_state(self, estado):
        self.state = estado
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        R = min(w, h) * 0.27
        t = time.monotonic() - self._t0
        st = self.state
        ativo = st in ("iniciando", "aguardando", "ouvindo", "processando", "falando")
        base = qcolor("accent") if ativo else qcolor("muted")
        centro = QPointF(cx, cy)

        escala = 1.0
        if st == "aguardando":
            escala = 1 + 0.025 * math.sin(t * 1.4)
        elif st == "iniciando":
            escala = 1 + 0.05 * math.sin(t * 3)
        elif st == "falando":
            escala = 1 + 0.03 * math.sin(t * 7)
        r = R * escala

        # halo
        halo = QRadialGradient(centro, R * 2.2)
        c0 = QColor(base); c0.setAlpha(120 if ativo else 35)
        c1 = QColor(base); c1.setAlpha(0)
        halo.setColorAt(0.0, c0)
        halo.setColorAt(0.4, c0)
        halo.setColorAt(1.0, c1)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(halo))
        p.drawEllipse(centro, R * 2.2, R * 2.2)

        # anel fixo e discreto
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(with_alpha(base, 55), 1.2))
        p.drawEllipse(centro, R * 1.3, R * 1.3)

        if st == "ouvindo":
            for k in range(3):
                ph = (t * 0.7 + k / 3) % 1.0
                rr = R * (1.1 + 0.9 * ph)
                p.setPen(QPen(qcolor("accent2", int(160 * (1 - ph))), 2))
                p.drawEllipse(centro, rr, rr)

        elif st in ("processando", "iniciando"):
            pen = QPen(qcolor("accent2"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            rect = QRectF(cx - R * 1.3, cy - R * 1.3, R * 2.6, R * 2.6)
            inicio = int(-t * 240 * 16) % (360 * 16)
            p.drawArc(rect, inicio, 110 * 16)

        elif st == "falando":
            n = 56
            pen = QPen(qcolor("accent2", 210), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            for i in range(n):
                ang = 2 * math.pi * i / n
                amp = abs(math.sin(t * 5 + i * 0.9)) * (0.55 + 0.45 * math.sin(t * 1.7 + i * 0.23))
                r1 = R * 1.22
                r2 = r1 + R * (0.10 + 0.34 * abs(amp))
                p.drawLine(
                    QPointF(cx + math.cos(ang) * r1, cy + math.sin(ang) * r1),
                    QPointF(cx + math.cos(ang) * r2, cy + math.sin(ang) * r2),
                )

        # núcleo
        luz = qcolor("accent2") if ativo else qcolor("muted").lighter(125)
        nucleo = QRadialGradient(QPointF(cx - r * 0.3, cy - r * 0.35), r * 1.5)
        nucleo.setColorAt(0.0, luz)
        nucleo.setColorAt(0.5, base)
        nucleo.setColorAt(1.0, qcolor("orb_dark"))
        p.setBrush(QBrush(nucleo))
        p.setPen(QPen(qcolor("accent2", 120), 1.2))
        p.drawEllipse(centro, r, r)

        # reflexo de vidro
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 70))
        p.drawEllipse(QPointF(cx - r * 0.32, cy - r * 0.42), r * 0.30, r * 0.15)


class Sparkline(QWidget):
    def __init__(self, n=40):
        super().__init__()
        self.values = deque([0.0] * n, maxlen=n)
        self.setFixedHeight(34)

    def push(self, valor):
        self.values.append(float(valor))
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        n = len(self.values)
        if n < 2 or w < 4:
            return
        passo = w / (n - 1)
        pontos = [
            QPointF(i * passo, h - 3 - (min(max(v, 0.0), 100.0) / 100.0) * (h - 6))
            for i, v in enumerate(self.values)
        ]
        linha = QPainterPath(pontos[0])
        for pt in pontos[1:]:
            linha.lineTo(pt)

        area = QPainterPath(linha)
        area.lineTo(QPointF(w, h))
        area.lineTo(QPointF(0, h))
        area.closeSubpath()
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, qcolor("accent", 110))
        grad.setColorAt(1.0, qcolor("accent", 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawPath(area)

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(qcolor("accent2"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawPath(linha)


class StatCard(QFrame):
    def __init__(self, titulo, com_grafico=False):
        super().__init__()
        self.setObjectName("card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 12)
        lay.setSpacing(2)

        self.label = QLabel(titulo)
        self.label.setObjectName("statLabel")
        self.value = QLabel("–")
        self.value.setObjectName("statValue")
        self.sub = QLabel("")
        self.sub.setObjectName("statSub")
        lay.addWidget(self.label)
        lay.addWidget(self.value)
        self.spark = None
        if com_grafico:
            self.spark = Sparkline()
            lay.addWidget(self.spark)
        else:
            lay.addWidget(self.sub)
            lay.addStretch()

    def set_value(self, texto, sub=None):
        self.value.setText(texto)
        if sub is not None:
            self.sub.setText(sub)


class HeaderBar(QWidget):
    """Barra superior arrastável (a janela não tem moldura do Windows)."""

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.window().windowHandle()
            if handle is not None:
                handle.startSystemMove()


# ======================================================================
# JANELA PRINCIPAL
# ======================================================================
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ALFRED")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.resize(1180, 780)
        self.setMinimumSize(980, 700)

        self.tema = config.get("tema_interface", "escuro")
        if self.tema not in THEMES:
            self.tema = "escuro"
        set_theme(self.tema)
        self.nome = config.get("nome_utilizador", "Eric")
        self.comandos = 0
        self.estado = "iniciando"

        self._montar()

        # motor de voz e comandos
        self.bridge = Bridge()
        self.bridge.state.connect(self.on_state)
        self.bridge.message.connect(self.add_message)
        self.bridge.mic.connect(self.on_mic)
        self.bridge.command.connect(self.on_command)
        self.bridge.shutdown.connect(self.on_shutdown)
        self.engine = AlfredEngine(
            on_state=self.bridge.state.emit,
            on_message=self.bridge.message.emit,
            on_mic=self.bridge.mic.emit,
            on_command=self.bridge.command.emit,
            on_shutdown=self.bridge.shutdown.emit,
        )

        # relógio e métricas
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)
        self.tick()

        self.apply_theme(self.tema)
        self.on_state("iniciando")
        self.add_message("system", "ALFRED iniciado.")
        QTimer.singleShot(150, self.engine.start)

    # ------------------------------------------------------------------
    # Construção da tela
    # ------------------------------------------------------------------
    def _montar(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(26, 8, 26, 18)
        raiz.setSpacing(14)

        raiz.addWidget(self._cabecalho())
        raiz.addLayout(self._saudacao())
        raiz.addLayout(self._estatisticas())

        corpo = QHBoxLayout()
        corpo.setSpacing(14)
        corpo.addLayout(self._coluna_esquerda(), 0)
        corpo.addWidget(self._painel_conversa(), 1)
        raiz.addLayout(corpo, 1)

        grip = QSizeGrip(self)
        raiz.addWidget(grip, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        grip.setFixedSize(14, 14)

    def _cabecalho(self):
        barra = HeaderBar()
        barra.setFixedHeight(48)
        lay = QHBoxLayout(barra)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        marca = QLabel("ALFRED")
        marca.setObjectName("brand")
        fonte = marca.font()
        fonte.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3)
        marca.setFont(fonte)

        self.dot = QLabel()
        self.dot.setFixedSize(10, 10)
        self.status_txt = QLabel("Iniciando")
        self.status_txt.setObjectName("statusText")

        self.btn_tema = QPushButton()
        self.btn_tema.setObjectName("winBtn")
        self.btn_tema.setToolTip("Alternar entre modo claro e escuro")
        self.btn_tema.clicked.connect(self.alternar_tema)
        btn_min = QPushButton("–")
        btn_min.setObjectName("winBtn")
        btn_min.clicked.connect(self.showMinimized)
        btn_fechar = QPushButton("✕")
        btn_fechar.setObjectName("closeBtn")
        btn_fechar.clicked.connect(self.close)

        lay.addWidget(marca)
        lay.addSpacing(8)
        lay.addWidget(self.dot)
        lay.addWidget(self.status_txt)
        lay.addStretch()
        lay.addWidget(self.btn_tema)
        lay.addWidget(btn_min)
        lay.addWidget(btn_fechar)
        return barra

    def _saudacao(self):
        lay = QVBoxLayout()
        lay.setSpacing(2)
        self.lbl_saudacao = QLabel()
        self.lbl_saudacao.setObjectName("greeting")
        sub = QLabel("Estou à disposição. Diga “Alfred” ou digite um comando.")
        sub.setObjectName("muted")
        lay.addWidget(self.lbl_saudacao)
        lay.addWidget(sub)
        return lay

    def _estatisticas(self):
        lay = QHBoxLayout()
        lay.setSpacing(14)
        self.card_cpu = StatCard("Processador", com_grafico=True)
        self.card_ram = StatCard("Memória", com_grafico=True)
        self.card_cmd = StatCard("Comandos executados")
        self.card_hora = StatCard("Agora")
        self.card_cmd.set_value("0", "nesta sessão")
        for c in (self.card_cpu, self.card_ram, self.card_cmd, self.card_hora):
            c.setMinimumHeight(112)
            lay.addWidget(c, 1)
        return lay

    def _coluna_esquerda(self):
        col = QVBoxLayout()
        col.setSpacing(14)

        # --- orbe de estado ---
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(360)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 14, 18, 18)
        lay.setSpacing(4)

        self.orb = Orb()
        self.lbl_estado = QLabel()
        self.lbl_estado.setObjectName("stateTitle")
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado_sub = QLabel()
        self.lbl_estado_sub.setObjectName("muted")
        self.lbl_estado_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado_sub.setWordWrap(True)

        botoes = QHBoxLayout()
        botoes.setSpacing(8)
        self.btn_mic = QPushButton("Mic ligado")
        self.btn_mic.setProperty("on", True)
        self.btn_mic.clicked.connect(self.alternar_mic)
        self.btn_falar = QPushButton("Falar agora")
        self.btn_falar.setObjectName("primary")
        self.btn_falar.clicked.connect(lambda: self.engine.listen_now())
        self.btn_calar = QPushButton("Calar")
        self.btn_calar.clicked.connect(lambda: self.engine.silence())
        for b in (self.btn_mic, self.btn_falar, self.btn_calar):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            botoes.addWidget(b, 1)

        lay.addWidget(self.orb, 1)
        lay.addWidget(self.lbl_estado)
        lay.addWidget(self.lbl_estado_sub)
        lay.addSpacing(10)
        lay.addLayout(botoes)
        col.addWidget(card, 1)

        # --- ações rápidas ---
        acoes = QFrame()
        acoes.setObjectName("card")
        acoes.setFixedWidth(360)
        a_lay = QVBoxLayout(acoes)
        a_lay.setContentsMargins(18, 14, 18, 16)
        a_lay.setSpacing(10)
        titulo = QLabel("Ações rápidas")
        titulo.setObjectName("cardTitle")
        a_lay.addWidget(titulo)

        grade = QGridLayout()
        grade.setSpacing(8)
        atalhos = [
            ("Que horas são?", "que horas são"),
            ("Clima agora", "clima"),
            ("Jogo do Vasco", "jogo do vasco"),
            ("Diagnóstico", "diagnóstico"),
            ("Modo gamer", "modo gamer"),
            ("Minimizar tudo", "minimizar tudo"),
        ]
        for i, (rotulo, comando) in enumerate(atalhos):
            b = QPushButton(rotulo)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _=False, c=comando: self.engine.submit(c))
            grade.addWidget(b, i // 2, i % 2)
        a_lay.addLayout(grade)
        col.addWidget(acoes, 0)
        return col

    def _painel_conversa(self):
        card = QFrame()
        card.setObjectName("card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 16, 20, 18)
        lay.setSpacing(12)

        topo = QHBoxLayout()
        titulo = QLabel("Conversa")
        titulo.setObjectName("cardTitle")
        limpar = QPushButton("Limpar")
        limpar.setCursor(Qt.CursorShape.PointingHandCursor)
        limpar.clicked.connect(self.limpar_conversa)
        topo.addWidget(titulo)
        topo.addStretch()
        topo.addWidget(limpar)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("chatScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat = QWidget()
        self.chat_lay = QVBoxLayout(self.chat)
        self.chat_lay.setContentsMargins(0, 0, 8, 0)
        self.chat_lay.setSpacing(10)
        self.chat_lay.addStretch()
        self.scroll.setWidget(self.chat)
        barra = self.scroll.verticalScrollBar()
        barra.rangeChanged.connect(lambda _mn, mx: barra.setValue(mx))

        entrada = QHBoxLayout()
        entrada.setSpacing(8)
        self.campo = QLineEdit()
        self.campo.setPlaceholderText("Digite um comando para o ALFRED…")
        self.campo.returnPressed.connect(self.enviar)
        enviar = QPushButton("Enviar")
        enviar.setObjectName("primary")
        enviar.setCursor(Qt.CursorShape.PointingHandCursor)
        enviar.setMinimumHeight(42)
        enviar.clicked.connect(self.enviar)
        entrada.addWidget(self.campo, 1)
        entrada.addWidget(enviar)

        lay.addLayout(topo)
        lay.addWidget(self.scroll, 1)
        lay.addLayout(entrada)
        return card

    # ------------------------------------------------------------------
    # Fundo
    # ------------------------------------------------------------------
    def paintEvent(self, _event):
        p = QPainter(self)
        w, h = self.width(), self.height()
        fundo = QLinearGradient(0, 0, 0, h)
        fundo.setColorAt(0.0, qcolor("bg0"))
        fundo.setColorAt(1.0, qcolor("bg1"))
        p.fillRect(self.rect(), QBrush(fundo))
        for fx, fy, raio, alfa in ((0.10, 0.0, 0.55, 80), (0.95, 1.0, 0.60, 60)):
            g = QRadialGradient(QPointF(w * fx, h * fy), max(w, h) * raio)
            g.setColorAt(0.0, qcolor("glow", alfa))
            g.setColorAt(1.0, qcolor("glow", 0))
            p.fillRect(self.rect(), QBrush(g))
        p.setPen(QPen(QColor(255, 255, 255, 26) if self.tema == "escuro" else QColor(70, 40, 150, 40), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------
    def apply_theme(self, nome):
        self.tema = nome
        set_theme(nome)
        self.setStyleSheet(build_qss())
        self.btn_tema.setText("☀" if nome == "escuro" else "☾")
        self.orb.update()
        self.card_cpu.spark.update()
        self.card_ram.spark.update()
        self.on_state(self.estado)
        self.update()

    def alternar_tema(self):
        novo = "claro" if self.tema == "escuro" else "escuro"
        self.apply_theme(novo)
        try:
            config["tema_interface"] = novo
            save_config(config)
        except Exception:
            pass

    def alternar_mic(self):
        ligar = not self.engine.mic_ligado()
        self.engine.set_mic(ligar)
        self.btn_mic.setText("Mic ligado" if ligar else "Mic desligado")
        self.btn_mic.setProperty("on", ligar)
        repolish(self.btn_mic)

    def enviar(self):
        texto = self.campo.text().strip()
        if texto:
            self.engine.submit(texto)
            self.campo.clear()

    def limpar_conversa(self):
        while self.chat_lay.count() > 1:
            item = self.chat_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def tick(self):
        agora = datetime.datetime.now()
        self.card_hora.set_value(
            agora.strftime("%H:%M"),
            f"{DIAS[agora.weekday()]}, {agora.day} de {MESES[agora.month - 1]}",
        )
        h = agora.hour
        saudacao = "Bom dia" if h < 12 else ("Boa tarde" if h < 18 else "Boa noite")
        self.lbl_saudacao.setText(f"{saudacao}, {self.nome}")
        if psutil:
            try:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent
                self.card_cpu.spark.push(cpu)
                self.card_ram.spark.push(ram)
                self.card_cpu.set_value(f"{cpu:.0f}%")
                self.card_ram.set_value(f"{ram:.0f}%")
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Eventos vindos do motor
    # ------------------------------------------------------------------
    def on_state(self, estado):
        self.estado = estado
        titulo, sub = ESTADOS.get(estado, (estado, ""))
        self.lbl_estado.setText(titulo)
        self.lbl_estado_sub.setText(sub)
        self.orb.set_state(estado)
        cor, texto = STATUS_CABECALHO.get(estado, ("warn", estado))
        self.status_txt.setText(texto)
        self.dot.setStyleSheet(f"background: {T[cor]}; border-radius: 5px;")

    def on_mic(self, ok, _detalhe):
        if not ok:
            self.btn_mic.setEnabled(False)
            self.btn_falar.setEnabled(False)
            self.btn_mic.setText("Sem mic")

    def on_command(self):
        self.comandos += 1
        self.card_cmd.set_value(str(self.comandos), "nesta sessão")

    def on_shutdown(self):
        QTimer.singleShot(900, self.close)

    def add_message(self, papel, texto):
        if papel == "alfred":
            baixo = texto.lower()
            if any(k in baixo for k in ("desculpe", "lamento", "falha")):
                papel = "erro"

        linha = QWidget()
        lay = QHBoxLayout(linha)
        lay.setContentsMargins(0, 0, 0, 0)

        rotulo = QLabel(texto)
        rotulo.setWordWrap(True)
        rotulo.setTextFormat(Qt.TextFormat.PlainText)
        rotulo.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        if papel == "system":
            rotulo.setObjectName("systemNote")
            rotulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(rotulo)
        else:
            rotulo.setObjectName({"user": "bubbleUser", "erro": "bubbleErro"}.get(papel, "bubbleAlfred"))
            rotulo.setMaximumWidth(520)
            rotulo.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
            if papel == "user":
                lay.addStretch()
                lay.addWidget(rotulo)
            else:
                lay.addWidget(rotulo)
                lay.addStretch()

        self.chat_lay.insertWidget(self.chat_lay.count() - 1, linha)

    def closeEvent(self, event):
        try:
            self.engine.stop()
        except Exception:
            pass
        event.accept()
        QApplication.quit()


def caminho_icone():
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets", "alfred.ico")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ALFRED")
    icone = caminho_icone()
    if os.path.exists(icone):
        app.setWindowIcon(QIcon(icone))
    janela = MainWindow()
    janela.show()
    code = app.exec()
    os._exit(code)  # garante que threads de áudio não segurem o processo


if __name__ == "__main__":
    main()