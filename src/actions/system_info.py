import datetime

def get_time():
    agora = datetime.datetime.now()
    return f"Agora são {agora.strftime('%H:%M')}."

def get_date():
    hoje = datetime.date.today()
    return f"Hoje é dia {hoje.strftime('%d/%m/%Y')}."