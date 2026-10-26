# ALFRED — assistente pessoal por voz para Windows

Assistente de desktop inspirado no mordomo de Bruce Wayne. Escuta uma palavra de ativação, entende comandos em português, responde por voz e executa tarefas no computador, com uma interface gráfica em tema escuro.

<!-- Coloque aqui um print da interface: ![ALFRED](docs/interface.png) -->

## O que ele faz

- Reconhece voz em português (palavra de ativação: "Alfred") e responde falando
- Abre aplicativos e sites (Discord, WhatsApp, YouTube, Netflix, portal da faculdade e outros)
- Informa hora, data, clima e chance de chuva no Rio de Janeiro
- Mostra o próximo jogo do Vasco (API football-data.org)
- Controla a música (tocar, pausar, próxima faixa, volume)
- Modo gamer, diagnóstico do sistema e minimizar todas as janelas
- Interface com orbe de estado animado, histórico da conversa, ações rápidas e tema claro/escuro

## Tecnologias

Python · PySide6 (interface) · SpeechRecognition · edge-tts · pygame · psutil · requests

## Como rodar

1. Instale o Python 3.11 e clone o repositório
2. Crie e ative um ambiente virtual e instale as dependências:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Copie `.env.example` para `src/actions/.env` e coloque seu token da football-data.org
4. Execute:
   ```
   python src\gui.py     # com interface
   python src\main.py    # só terminal
   ```

## Estrutura

```
src/
  gui.py              interface gráfica
  alfred_engine.py    loop de voz e comandos usado pela interface
  audio_handler.py    microfone, reconhecimento e voz
  command_handler.py  interpretação dos comandos
  actions/            ações (apps, sites, clima, Spotify, Vasco...)
```

## Autor

Eric Nascimento de Oliveira — estudante de Ciência da Computação (UVA)
