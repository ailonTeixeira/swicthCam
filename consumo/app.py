from flask import Flask, render_template, jsonify
import sqlite3

app = Flask(__name__)

# Função para obter os dados do banco de dados
def get_data_from_db():
    conn = sqlite3.connect('dados_corrente.db')
    cursor = conn.cursor()
    cursor.execute("SELECT data_hora, corrente, consumo_kwh FROM dados_corrente ORDER BY id DESC LIMIT 100")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Função para obter métricas principais
def get_total_consumo_e_potencia():
    conn = sqlite3.connect('dados_corrente.db')
    cursor = conn.cursor()
    
    # Total consumo acumulado e potência máxima
    cursor.execute("SELECT SUM(consumo_kwh), MAX(potencia) FROM dados_corrente")
    result = cursor.fetchone()
    total_consumo = result[0] if result[0] else 0
    ultima_potencia = result[1] if result[1] else 0

    # Data e hora da última potência
    cursor.execute("SELECT data_hora FROM dados_corrente WHERE potencia = ? ORDER BY id DESC LIMIT 1", (ultima_potencia,))
    ultima_potencia_horario = cursor.fetchone()
    ultima_potencia_horario = ultima_potencia_horario[0] if ultima_potencia_horario else "N/A"

    # Data e hora do intervalo de consumo total
    cursor.execute("SELECT MIN(data_hora), MAX(data_hora) FROM dados_corrente")
    intervalo_consumo = cursor.fetchone()
    inicio_consumo = intervalo_consumo[0] if intervalo_consumo[0] else "N/A"
    fim_consumo = intervalo_consumo[1] if intervalo_consumo[1] else "N/A"

    # �^zltima leitura de corrente
    cursor.execute("SELECT corrente, data_hora FROM dados_corrente ORDER BY id DESC LIMIT 1")
    ultima_corrente = cursor.fetchone()
    ultima_corrente_valor = ultima_corrente[0] if ultima_corrente else 0
    ultima_corrente_horario = ultima_corrente[1] if ultima_corrente else "N/A"

    # Cálculo do custo em reais
    custo_kwh = total_consumo * 0.85

    conn.close()

    return {
        "total_consumo": total_consumo,
        "ultima_potencia": ultima_potencia,
        "ultima_potencia_horario": ultima_potencia_horario,
        "inicio_consumo": inicio_consumo,
        "fim_consumo": fim_consumo,
        "ultima_corrente": ultima_corrente_valor,
        "ultima_corrente_horario": ultima_corrente_horario,
        "custo_reais": custo_kwh
    }

@app.route('/')
def index():
    # Obtém os dados principais
    dados_totais = get_total_consumo_e_potencia()
    return render_template('index.html', dados_totais=dados_totais)

@app.route('/data')
def data():
    rows = get_data_from_db()
    data = {
        "labels": [row[0] for row in rows],  # Data/Hora
        "corrente": [row[1] for row in rows],  # Corrente (A)
        "consumo": [row[2] for row in rows]   # Consumo (kWh/min)
    }
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)


