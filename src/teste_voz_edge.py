
import asyncio
import edge_tts
import pygame
import os

VOZ = "pt-BR-AntonioNeural"
ARQUIVO = "teste_alfred.mp3"

async def gerar_audio():
    texto = (
        "Olá! Eu sou o Alfred, seu assistente pessoal. "
        "Sistemas iniciados. Estou pronto para ajudar."
    )

    comunicacao = edge_tts.Communicate(
        texto,
        VOZ,
        rate="-5%",
        pitch="-5Hz"
    )

    await comunicacao.save(ARQUIVO)

async def main():
    try:
        print("Gerando voz masculina brasileira...")
        await gerar_audio()

        pygame.mixer.init()
        pygame.mixer.music.load(ARQUIVO)
        pygame.mixer.music.play()

        print("Reproduzindo áudio...")

        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)

        pygame.mixer.quit()
        print("Teste concluído!")

    except Exception as erro:
        print(f"Erro no teste de voz: {erro}")

if __name__ == "__main__":
    asyncio.run(main())
