import psutil
import subprocess
import os
import tempfile
import shutil

def run_diagnostics():
    relatorio = "Iniciando diagnóstico completo do sistema. "
    
    # 1. Analisa CPU e Memória
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent
    
    relatorio += f"O processador está operando a {cpu_usage} por cento da capacidade. A memória RAM está com {ram_usage} por cento de uso. "
    
    if cpu_usage > 85:
        relatorio += "Atenção: A CPU está sobrecarregada, recomendo fechar aplicativos pesados. "
    if ram_usage > 85:
        relatorio += "Atenção: O consumo de memória está próximo do limite. "
        
    # 2. Teste de Rede (Ping)
    try:
        # Envia 1 pacote de dados para o Google para testar a rede
        output = subprocess.run(["ping", "-n", "1", "8.8.8.8"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if "Tempo limite esgotado" in output.stdout or "Falha" in output.stdout:
            relatorio += "Detectei instabilidade na conexão de rede. "
        else:
            relatorio += "A sua conexão com a internet está estável. "
    except Exception:
        pass
        
    # 3. Limpeza Silenciosa de Arquivos Temporários (%TEMP%)
    temp_path = tempfile.gettempdir()
    arquivos_limpos = 0
    
    for item in os.listdir(temp_path):
        item_path = os.path.join(temp_path, item)
        try:
            if os.path.isfile(item_path):
                os.unlink(item_path)
                arquivos_limpos += 1
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
                arquivos_limpos += 1
        except Exception:
            # Ignora arquivos que estão em uso no momento pelo Windows
            continue
            
    if arquivos_limpos > 0:
        relatorio += "Fiz uma limpeza nos arquivos temporários para liberar espaço. "
        
    relatorio += "Diagnóstico concluído."
    return relatorio