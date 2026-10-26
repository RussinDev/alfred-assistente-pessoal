class StateManager:
    def __init__(self):
        self.current_state = "IDLE"

    def set_state(self, new_state):
        self.current_state = new_state
        # Imprime o estado atual no terminal para acompanharmos o cérebro dele
        print(f"\n[ESTADO DO SISTEMA: {self.current_state}]")

    def get_state(self):
        return self.current_state

# Instância global que será importada pelos outros arquivos
state = StateManager()