# -*- coding: utf-8 -*-
import cv2
import time
import threading
import requests
import numpy as np
from flask import Flask, render_template, Response, request, redirect, url_for, session, flash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Substitua por uma chave secreta real

# URL para capturar uma única imagem do ESP32CAM
ESP32_CAPTURE_URL = 'http://10.42.0.65/capture'

# URL para controlar a saída digital
ESP32_CONTROL_URL = 'http://10.42.0.11/control'

# Variáveis globais
last_frames = []
motion_detected = False
control_state = "ON"
frame_reference = None  # Frame de referência inicial

# Credenciais de login (substitua por credenciais seguras)
USERNAME = ''
PASSWORD = ''

# Função para exigir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Rota para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('Nome de usuario ou senha incorretos')
    return render_template('login.html')

# Rota para logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# Rota principal da interface web (requer login)
@app.route('/')
@login_required
def index():
    return render_template('index.html', control_state=control_state)

# Rota para obter a imagem atual (requer login)
@app.route('/video_feed')
@login_required
def video_feed():
    def generate():
        while True:
            if last_frames:
                frame = last_frames[-1]
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(1)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Rota para controlar a saída digital manualmente (requer login)
@app.route('/control', methods=['POST'])
@login_required
def control():
    global control_state
    command = request.form.get('command')
    if command in ["ON", "OFF"]:
        send_control_command(command)
        control_state = command  # Atualiza o estado de controle
    return '', 204  # Retorna uma resposta vazia com status 204 (No Content)

# Função para capturar frames a cada 1 segundo
def capture_frames():
    global motion_detected, last_frames, frame_reference
    no_motion_count = 0
    motion_frames = 0
    motion_frames_threshold = 3  # Número de frames consecutivos com movimento necessários para acionar

    # Inicializar o subtrator de fundo
    fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=True)

    while True:
        try:
            # Solicita a imagem do endpoint /capture
            response = requests.get(ESP32_CAPTURE_URL, timeout=5)
            if response.status_code == 200:
                image_bytes = np.asarray(bytearray(response.content), dtype=np.uint8)
                frame = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
            else:
                print("Falha ao obter a imagem do ESP32CAM")
                time.sleep(10)
                continue
        except Exception as e:
            print(f"Erro ao conectar ao ESP32CAM: {e}")
            time.sleep(10)
            continue

        # Redimensiona para processamento mais rápido (opcional)
        frame_resized = frame

        # Converter para escala de cinza
        gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # Aplicar o subtrator de fundo
        fgmask = fgbg.apply(gray)

        # Opcional: aplicar limiarização para eliminar sombras
        _, fgmask = cv2.threshold(fgmask, 250, 255, cv2.THRESH_BINARY)

        # Dilatar a máscara para preencher buracos
        fgmask = cv2.dilate(fgmask, None, iterations=2)

        # Encontrar contornos na máscara
        contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected_current = False

        for contour in contours:
            if cv2.contourArea(contour) < 100:
                continue  # Ignora áreas pequenas
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame_resized, (x, y), (x + w, y + h), (0, 255, 0), 2)
            motion_detected_current = True

        # Atualiza o frame de referência apenas quando não há movimento
        if not motion_detected_current:
            frame_reference = gray

        # Verifica se o movimento foi detectado
        if motion_detected_current:
            motion_frames += 1
            no_motion_count = 0
            if motion_frames >= motion_frames_threshold:
                if not motion_detected:
                    motion_detected = True
                    send_control_command("ON")
        else:
            motion_frames = 0
            no_motion_count += 1
            if no_motion_count >= 60:
                if motion_detected:
                    motion_detected = False
                    send_control_command("OFF")

        # Armazena o frame para exibição na interface web
        _, jpeg = cv2.imencode('.jpg', frame_resized)
        last_frames.append(jpeg.tobytes())
        if len(last_frames) > 1:
            last_frames.pop(0)

        time.sleep(0.20)

# Função para enviar comando ao ESP32
def send_control_command(command):
    global control_state
    try:
        response = requests.post(ESP32_CONTROL_URL, data=command)
        if response.status_code == 200:
            control_state = command
            print(f"Saida digital definida para: {command}")
        else:
            print("Falha ao enviar o comando ao ESP32")
    except Exception as e:
        print(f"Erro ao conectar ao ESP32: {e}")

if __name__ == '__main__':
    # Inicia a thread de captura de frames
    t = threading.Thread(target=capture_frames)
    t.daemon = True
    t.start()
    # Executa o servidor Flask na porta 5001
    app.run(host='0.0.0.0', port=5001)
