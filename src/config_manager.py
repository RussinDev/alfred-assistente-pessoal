import json
import os

# O ficheiro será guardado dentro da pasta src
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    """Carrega as configurações ou cria um ficheiro padrão se não existir."""
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "nome_utilizador": "Eric",
            "velocidade_voz": "+20%",
            "tema_interface": "escuro"
        }
        save_config(default_config)
        return default_config
        
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config_data):
    """Guarda as configurações no ficheiro JSON."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)

# Carrega as definições automaticamente quando o sistema inicia
config = load_config()