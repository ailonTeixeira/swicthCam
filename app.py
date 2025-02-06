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

# URLs do ESP32CAM e ESP32
ESP32_CAPTURE_URL = 'http://10.42.0.132/capture'
ESP32_CONTROL_URL = 'http://10.42.0.11/control'

# Variáveis globais
last_frames = []
motion_detected = False
control_state = "ON"
frame_reference = None

# Credenciais de login
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

# Rota principal da interface web
@app.route('/')
@login_required
def index():
    return render_template('index.html', control_state=control_state)

# Rota para obter a imagem atual
@app.route('/video_feed')
@login_required
def video_feed():
    def generate():
        while True:
            if last_frames:
                frame = last_frames[-1]
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.1)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Rota para controlar a saída digital manualmente
@app.route('/control', methods=['POST'])
@login_required
def control():
    global control_state
    command = request.form.get('command')
    if command in ["ON", "OFF"]:
        send_control_command(command)
        control_state = command
    return '', 204

def capture_frames():
    global motion_detected, last_frames, frame_reference
    no_motion_count = 0

    while True:
        try:
            response = requests.get(ESP32_CAPTURE_URL, timeout=5)
            if response.status_code == 200:
                image_bytes = np.asarray(bytearray(response.content), dtype=np.uint8)
                frame = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)

                if np.mean(frame) < 8000 or np.std(frame) < 1:
                    continue

            else:
                print("Falha ao obter a imagem do ESP32CAM")
                time.sleep(10)
                continue
        except Exception as e:
            print(f"Erro ao conectar ao ESP32CAM: {e}")
            time.sleep(10)
            continue

        frame_resized = frame
        gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if frame_reference is None:
            frame_reference = gray
            continue

        frame_delta = cv2.absdiff(frame_reference, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected_current = False

        for contour in contours:
            if cv2.contourArea(contour) < 0.000000005:
                continue
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame_resized, (x, y), (x + w, y + h), (0, 255, 0), 2)
            motion_detected_current = True

        frame_reference = gray

        if motion_detected_current:
            no_motion_count = 0
            if not motion_detected:
                motion_detected = True
                send_control_command("ON")
        else:
            no_motion_count += 1
            if no_motion_count >= 60:
                if motion_detected:
                    motion_detected = False
                    send_control_command("OFF")

        _, jpeg = cv2.imencode('.jpg', frame_resized)
        last_frames.append(jpeg.tobytes())
        if len(last_frames) > 1:
            last_frames.pop(0)

        # Pausa de 0.5 segundos entre cada iteração
        time.sleep(0.1)

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
    t = threading.Thread(target=capture_frames)
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', port=5001)
