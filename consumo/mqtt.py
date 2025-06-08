import paho.mqtt.client as mqtt
import sqlite3
from datetime import datetime

# Configurações do banco de dados
db_name = "dados_corrente.db"
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

# Criação da tabela se ela ainda não existir
cursor.execute('''
    CREATE TABLE IF NOT EXISTS dados_corrente (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_hora TEXT,
        corrente REAL,
        potencia REAL,
        consumo_kwh REAL
    )
''')
conn.commit()

# Função para calcular potência e consumo
def calcular_potencia_e_consumo(corrente):
    if 0 <= corrente <= 1.0:  # Considera corrente entre 0.5 e 1 A como 0
        corrente = 0
    corrente_ajustada = corrente * 2 
    tensao = 220  # Tensão fixa de 220V
    potencia = corrente_ajustada * tensao  # Potência em Watts
    consumo_kwh = potencia / 1000 / 60  # Consumo em kWh/minuto
    return corrente, potencia, consumo_kwh

# Funções de callback do MQTT
def on_connect(client, userdata, flags, rc):
    print("Conectado ao broker MQTT com código de retorno " + str(rc))
    client.subscribe("corrente/dados")

def on_message(client, userdata, msg):
    corrente = float(msg.payload.decode())
    corrente, potencia, consumo_kwh = calcular_potencia_e_consumo(corrente)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Recebido: {corrente} A em {timestamp}, Potência: {potencia} W, Cons umo: {consumo_kwh} kWh/min")
    
    # Insere os dados no banco de dados
    cursor.execute('''
        INSERT INTO dados_corrente (data_hora, corrente, potencia, consumo_kwh)
        VALUES (?, ?, ?, ?)
    ''', (timestamp, corrente, potencia, consumo_kwh))
    conn.commit()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)  # Conecta ao broker no Raspberry Pi

client.loop_forever()

