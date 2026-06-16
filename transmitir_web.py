import io
import json
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox

import requests
import win32gui
import ctypes
from PIL import Image, ImageTk

# -- Imports para servidor web y camara --
try:
    from flask import Flask, Response, render_template_string, request
except ImportError:
    subprocess.run(["pip", "install", "flask"])
    from flask import Flask, Response, render_template_string, request

try:
    import cv2
except ImportError:
    subprocess.run(["pip", "install", "opencv-python"])
    import cv2


# --- VARIABLES GLOBALES ---
player_top_name = "Jugador 1"
player_bottom_name = "Jugador 2"
pos_top = {"top": "5%", "left": "5%"}
pos_bottom = {"top": "85%", "left": "70%"}
font_size = 32

VIDEO_MODE = "mobile"  # Puede ser "mobile" o "webcam"
CROP_COORDS = None  # (w, h, x, y)


def get_screenshot_adb():
    result = subprocess.run(
        ["./adb.exe", "exec-out", "screencap", "-p"], capture_output=True
    )
    if result.returncode != 0:
        return None
    return Image.open(io.BytesIO(result.stdout))


def get_screenshot_webcam():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None
    # Convertir BGR a RGB para PIL
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame)


class StartupDialog:
    def __init__(self, master):
        self.master = master
        self.choice = None
        self.master.title("Origen de Video")

        # Centrar la ventana
        w, h = 350, 150
        ws = master.winfo_screenwidth()
        hs = master.winfo_screenheight()
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)
        master.geometry("%dx%d+%d+%d" % (w, h, x, y))

        tk.Label(
            master,
            text="¿Qué dispositivo vas a usar para transmitir?",
            font=("Arial", 11, "bold"),
        ).pack(pady=15)

        tk.Button(
            master,
            text="Teléfono Móvil (idChess / Android)",
            width=30,
            command=self.choose_mobile,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
        ).pack(pady=5)
        tk.Button(
            master,
            text="Cámara Web PC (USB)",
            width=30,
            command=self.choose_webcam,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
        ).pack(pady=5)

    def choose_mobile(self):
        self.choice = "mobile"
        self.master.destroy()

    def choose_webcam(self):
        self.choice = "webcam"
        self.master.destroy()


class CropSelector:
    def __init__(self, master, image):
        self.master = master
        self.master.title("Selecciona la zona a transmitir")

        self.original_image = image
        self.orig_width, self.orig_height = image.size

        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()

        max_height = screen_height - 150
        max_width = screen_width - 150

        self.scale = min(
            max_width / self.orig_width, max_height / self.orig_height, 1.0
        )

        self.disp_width = int(self.orig_width * self.scale)
        self.disp_height = int(self.orig_height * self.scale)

        self.display_image = self.original_image.resize(
            (self.disp_width, self.disp_height), Image.Resampling.LANCZOS
        )
        self.tk_image = ImageTk.PhotoImage(self.display_image)

        self.canvas = tk.Canvas(
            master, width=self.disp_width, height=self.disp_height, cursor="cross"
        )
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

        self.rect = None
        self.start_x = None
        self.start_y = None
        self.crop_coords = None

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        # Interfaz extra para configurar los nombres de los jugadores
        self.frame_config = tk.Frame(master)
        self.frame_config.pack(pady=10, fill=tk.X)

        inner_frame = tk.Frame(self.frame_config)
        inner_frame.pack(anchor="center")

        tk.Label(
            inner_frame, text="Jugador Superior (Arriba):", font=("Arial", 10, "bold")
        ).grid(row=0, column=0, padx=5, pady=2)
        self.entry_top = tk.Entry(inner_frame, font=("Arial", 10))
        self.entry_top.insert(0, "Blancas")
        self.entry_top.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(
            inner_frame, text="Jugador Inferior (Abajo):", font=("Arial", 10, "bold")
        ).grid(row=1, column=0, padx=5, pady=2)
        self.entry_bottom = tk.Entry(inner_frame, font=("Arial", 10))
        self.entry_bottom.insert(0, "Negras")
        self.entry_bottom.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(
            master,
            text="Paso 1: Escribe los nombres.\nPaso 2: Haz clic y arrastra en la imagen para recortar.\nAl soltar, iniciará la transmisión.",
            font=("Arial", 10, "bold"),
            fg="blue",
        ).pack(pady=5)

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.start_x,
            self.start_y,
            outline="red",
            width=3,
        )

    def on_move_press(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        if (x2 - x1) < 10 or (y2 - y1) < 10:
            self.canvas.delete(self.rect)
            self.rect = None
            return

        x1 = max(0, min(x1, self.disp_width))
        y1 = max(0, min(y1, self.disp_height))
        x2 = max(0, min(x2, self.disp_width))
        y2 = max(0, min(y2, self.disp_height))

        orig_x1 = int(x1 / self.scale)
        orig_y1 = int(y1 / self.scale)
        orig_x2 = int(x2 / self.scale)
        orig_y2 = int(y2 / self.scale)

        width = orig_x2 - orig_x1
        height = orig_y2 - orig_y1

        self.crop_coords = (width, height, orig_x1, orig_y1)
        self.p_top = self.entry_top.get()
        self.p_bottom = self.entry_bottom.get()
        self.master.destroy()


# === SERVIDOR WEB FLASK ===
app = Flask(__name__)


def _make_waiting_frame():
    img = Image.new("RGB", (800, 600), color=(20, 20, 20))
    try:
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), "Conectando al telefono...", font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((800 - tw) / 2, (600 - th) / 2), "Conectando al telefono...", fill=(255, 80, 80), font=font)
    except ImportError:
        pass
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=60)
    return buf.getvalue()


def generate_frames():
    global VIDEO_MODE, CROP_COORDS

    waiting_frame = _make_waiting_frame()

    if VIDEO_MODE == "mobile":
        w, h, x, y = CROP_COORDS
        print(f"[VIDEO] Iniciando captura ADB directa. Recorte: {w}x{h} en ({x},{y})")
        sys.stdout.flush()
        consecutive_errors = 0
        while True:
            try:
                result = subprocess.run(
                    ["./adb.exe", "exec-out", "screencap", "-p"],
                    capture_output=True, timeout=10
                )
                if result.returncode != 0:
                    consecutive_errors += 1
                    if consecutive_errors == 1 or consecutive_errors % 30 == 0:
                        print(f"[VIDEO] ADB error (codigo {result.returncode}, intento {consecutive_errors})")
                        sys.stdout.flush()
                    yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + waiting_frame + b"\r\n")
                    time.sleep(0.5)
                    continue

                img = Image.open(io.BytesIO(result.stdout)).convert("RGB")
                cropped = img.crop((x, y, x + w, y + h))
                buf = io.BytesIO()
                cropped.save(buf, format="JPEG", quality=80)
                frame = buf.getvalue()

                if consecutive_errors > 0:
                    print(f"[VIDEO] ADB recuperado tras {consecutive_errors} fallos")
                    sys.stdout.flush()
                consecutive_errors = 0

                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

            except subprocess.TimeoutExpired:
                consecutive_errors += 1
                if consecutive_errors == 1 or consecutive_errors % 30 == 0:
                    print(f"[VIDEO] Timeout ADB (intento {consecutive_errors})")
                    sys.stdout.flush()
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + waiting_frame + b"\r\n")

            except Exception as e:
                consecutive_errors += 1
                if consecutive_errors == 1 or consecutive_errors % 30 == 0:
                    print(f"[VIDEO] Error captura ADB: {e} (intento {consecutive_errors})")
                    sys.stdout.flush()
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + waiting_frame + b"\r\n")
                time.sleep(0.5)

    elif VIDEO_MODE == "webcam":
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        w, h, x, y = CROP_COORDS
        while True:
            ret, frame = cap.read()
            if not ret:
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + waiting_frame + b"\r\n")
                time.sleep(0.1)
                continue
            cropped = frame[y : y + h, x : x + w]
            ret_jpg, buffer = cv2.imencode(".jpg", cropped, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ret_jpg:
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
            time.sleep(0.05)


@app.route("/")
def index():
    return render_template_string(
        get_html_template(), p1=player_top_name, p2=player_bottom_name, is_control=False, font_size=font_size
    )


@app.route("/control")
def control():
    return render_template_string(
        get_html_template(), p1=player_top_name, p2=player_bottom_name, is_control=True, font_size=font_size
    )


def get_html_template():
    return """
    <html>
      <head>
        <title>idChess - {% if is_control %}Panel de Control{% else %}Espectador{% endif %}</title>
        <style>
          * { margin: 0; padding: 0; box-sizing: border-box; }
          body { background-color: #111; color: white; display: flex; flex-direction: column; height: 100vh; font-family: sans-serif; overflow: hidden; }
          .board-container { position: relative; flex: 1; width: 100vw; overflow: hidden; background: #000; display: flex; justify-content: center; align-items: center; }
          img { width: 100%; height: 100%; object-fit: contain; display: block; }
          .player {
            position: absolute;
            color: #ffffff;
            font-size: {{ font_size }}px;
            font-weight: 900;
            text-shadow: 2px 2px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000;
            z-index: 10;
            white-space: nowrap;
            letter-spacing: 2px;
            {% if is_control %}
            cursor: move;
            {% else %}
            cursor: default;
            {% endif %}
            user-select: none;
          }
          #player1 { top: 5%; left: 5%; }
          #player2 { top: 85%; left: 70%; }
          .toolbar {
            position: fixed; top: 10px; right: 10px; z-index: 100;
            display: flex; gap: 6px; align-items: center;
            background: rgba(0,0,0,0.75); border-radius: 8px; padding: 6px 10px;
          }
          .toolbar button {
            background: #333; color: white; border: 1px solid #555;
            border-radius: 4px; padding: 4px 10px; cursor: pointer;
            font-size: 0.85rem; font-weight: bold; transition: background 0.15s;
          }
          .toolbar button:hover { background: #555; }
          .toolbar button.swap { background: #7B1FA2; border-color: #9C27B0; }
          .toolbar button.swap:hover { background: #9C27B0; }
          .toolbar button.edit { background: #00695C; border-color: #00897B; }
          .toolbar button.edit:hover { background: #00897B; }
          .toolbar .font-label { color: #aaa; font-size: 0.75rem; margin: 0 2px; }
          .toolbar button.font { background: #1A237E; border-color: #283593; }
          .toolbar button.font:hover { background: #283593; }
          .status-bar {
            position: fixed; bottom: 0; left: 0; right: 0;
            background: rgba(0,0,0,0.7); color: #aaa; text-align: center;
            padding: 6px; font-size: 0.8rem; z-index: 100;
          }
          .status-bar.ok { color: #4CAF50; }
        </style>
      </head>
      <body>
        <div class="board-container">
            <div id="player1" class="player">{{ p1 }}</div>
            <img id="video" src="/video_feed">
            <div id="player2" class="player">{{ p2 }}</div>
        </div>
        <div id="status" class="status-bar">Conectando al video...</div>
        {% if is_control %}
        <div class="toolbar">
            <button class="font" id="font-down" title="Reducir texto">A−</button>
            <span class="font-label" id="font-label">{{ font_size }}px</span>
            <button class="font" id="font-up" title="Aumentar texto">A+</button>
            <button class="edit" id="edit-btn" title="Editar nombres de jugadores">✏</button>
            <button class="swap" id="swap-btn" title="Intercambiar arriba/abajo">↕</button>
        </div>
        {% endif %}
        <script>
            let is_control = {% if is_control %}true{% else %}false{% endif %};
            let isDragging1 = false;
            let isDragging2 = false;
            let videoImg = document.getElementById('video');
            let statusEl = document.getElementById('status');
            let videoOk = false;
            videoImg.onload = function() {
                if (!videoOk) {
                    videoOk = true;
                    statusEl.className = 'status-bar ok';
                    statusEl.textContent = 'Transmision activa';
                    setTimeout(() => { statusEl.style.display = 'none'; }, 3000);
                }
            };
            videoImg.onerror = function() {
                videoOk = false;
                statusEl.className = 'status-bar';
                statusEl.textContent = 'Error: No se pudo cargar el video. Verifica la conexion ADB.';
                statusEl.style.display = 'block';
            };

            if (is_control) {
                function dragElement(elmnt, playerId) {
                    var pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
                    elmnt.onmousedown = dragMouseDown;

                    function dragMouseDown(e) {
                        e.preventDefault();
                        if(playerId === 'player1') isDragging1 = true;
                        if(playerId === 'player2') isDragging2 = true;
                        pos3 = e.clientX;
                        pos4 = e.clientY;
                        document.onmouseup = closeDragElement;
                        document.onmousemove = elementDrag;
                    }

                    function elementDrag(e) {
                        e.preventDefault();
                        pos1 = pos3 - e.clientX;
                        pos2 = pos4 - e.clientY;
                        pos3 = e.clientX;
                        pos4 = e.clientY;
                        elmnt.style.top = (elmnt.offsetTop - pos2) + "px";
                        elmnt.style.left = (elmnt.offsetLeft - pos1) + "px";
                    }

                    function closeDragElement() {
                        document.onmouseup = null;
                        document.onmousemove = null;
                        if(playerId === 'player1') isDragging1 = false;
                        if(playerId === 'player2') isDragging2 = false;
                        let parentH = elmnt.offsetParent.offsetHeight || window.innerHeight;
                        let parentW = elmnt.offsetParent.offsetWidth || window.innerWidth;
                        let pctTop = (elmnt.offsetTop / parentH * 100).toFixed(2) + "%";
                        let pctLeft = (elmnt.offsetLeft / parentW * 100).toFixed(2) + "%";
                        fetch('/update_pos', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ player: playerId, top: pctTop, left: pctLeft })
                        });
                    }
                }

                dragElement(document.getElementById("player1"), "player1");
                dragElement(document.getElementById("player2"), "player2");

                // Boton editar nombres
                document.getElementById('edit-btn').addEventListener('click', function() {
                    let p1 = document.getElementById('player1');
                    let p2 = document.getElementById('player2');
                    let topName = prompt('Nombre del jugador SUPERIOR (arriba):', p1.innerText);
                    if (!topName) return;
                    topName = topName.trim();
                    if (!topName) return;
                    let bottomName = prompt('Nombre del jugador INFERIOR (abajo):', p2.innerText);
                    if (!bottomName) return;
                    bottomName = bottomName.trim();
                    if (!bottomName) return;
                    fetch('/update_names', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ top: topName, bottom: bottomName })
                    }).then(r => r.json()).then(d => {
                        if (d.status === 'ok') {
                            p1.innerText = topName;
                            p2.innerText = bottomName;
                        }
                    }).catch(e => console.error('edit error', e));
                });

                // Boton swap
                document.getElementById('swap-btn').addEventListener('click', function() {
                    let p1 = document.getElementById('player1');
                    let p2 = document.getElementById('player2');
                    [p1.innerText, p2.innerText] = [p2.innerText, p1.innerText];
                    fetch('/swap_names', { method: 'POST' })
                    .then(r => r.json())
                    .then(d => {
                        if (d.status === 'ok') {
                            p1.style.top = d.pos_top.top;
                            p1.style.left = d.pos_top.left;
                            p2.style.top = d.pos_bottom.top;
                            p2.style.left = d.pos_bottom.left;
                        }
                    })
                    .catch(e => console.error('swap error', e));
                });

                // Botones A+ / A-
                document.getElementById('font-up').addEventListener('click', function() {
                    fetch('/set_font_size', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ delta: 2 })
                    });
                });
                document.getElementById('font-down').addEventListener('click', function() {
                    fetch('/set_font_size', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ delta: -2 })
                    });
                });
            }

            setInterval(() => {
                fetch('/get_data')
                .then(response => response.json())
                .then(data => {
                    let p1 = document.getElementById('player1');
                    let p2 = document.getElementById('player2');

                    if (!isDragging1) p1.innerText = data.top_name;
                    if (!isDragging2) p2.innerText = data.bottom_name;

                    if(!isDragging1) {
                        p1.style.top = data.pos_top.top;
                        p1.style.left = data.pos_top.left;
                    }
                    if(!isDragging2) {
                        p2.style.top = data.pos_bottom.top;
                        p2.style.left = data.pos_bottom.left;
                    }

                    // Actualizar tamaño de fuente y label
                    let label = document.getElementById('font-label');
                    if (label) {
                        label.textContent = data.font_size + 'px';
                        p1.style.fontSize = data.font_size + 'px';
                        p2.style.fontSize = data.font_size + 'px';
                    }
                });
            }, 1000);
        </script>
      </body>
    </html>
    """


@app.route("/get_data")
def get_data():
    global player_top_name, player_bottom_name, pos_top, pos_bottom, font_size
    return Response(
        json.dumps(
            {
                "top_name": player_top_name,
                "bottom_name": player_bottom_name,
                "pos_top": pos_top,
                "pos_bottom": pos_bottom,
                "font_size": font_size,
            }
        ),
        mimetype="application/json",
    )


@app.route("/update_pos", methods=["POST"])
def update_pos():
    global pos_top, pos_bottom
    data = request.json
    if data.get("player") == "player1":
        pos_top["top"] = data.get("top")
        pos_top["left"] = data.get("left")
    elif data.get("player") == "player2":
        pos_bottom["top"] = data.get("top")
        pos_bottom["left"] = data.get("left")
    return Response(json.dumps({"status": "ok"}), mimetype="application/json")


@app.route("/swap_names", methods=["POST"])
def swap_names():
    global player_top_name, player_bottom_name, pos_top, pos_bottom
    player_top_name, player_bottom_name = player_bottom_name, player_top_name
    pos_top, pos_bottom = pos_bottom, pos_top
    print(f"[SWAP] Nombres intercambiados: '{player_top_name}' arriba, '{player_bottom_name}' abajo")
    sys.stdout.flush()
    return Response(json.dumps({
        "status": "ok",
        "pos_top": pos_top,
        "pos_bottom": pos_bottom,
    }), mimetype="application/json")


@app.route("/set_font_size", methods=["POST"])
def set_font_size():
    global font_size
    data = request.json
    delta = data.get("delta", 0)
    new_size = data.get("size", font_size + delta)
    font_size = max(12, min(120, new_size))
    return Response(json.dumps({"status": "ok", "font_size": font_size}), mimetype="application/json")


@app.route("/update_names", methods=["POST"])
def update_names():
    global player_top_name, player_bottom_name
    data = request.json
    if "top" in data:
        player_top_name = data["top"]
    if "bottom" in data:
        player_bottom_name = data["bottom"]
    print(f"[NAMES] Actualizados: '{player_top_name}' / '{player_bottom_name}'")
    sys.stdout.flush()
    return Response(json.dumps({"status": "ok"}), mimetype="application/json")


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


def run_web_server(initial_top, initial_bottom):
    global player_top_name, player_bottom_name
    player_top_name = initial_top
    player_bottom_name = initial_bottom

    import logging
    import socket
    import webbrowser

    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    print(f"\n========================================================")
    print(f" SERVIDOR WEB INICIADO ")
    print(f"========================================================")
    print(f" ENLACE DE ESPECTADOR -> http://{local_ip}:5000")
    print(f" ENLACE DE CONTROL   -> http://127.0.0.1:5000/control")
    print(f"========================================================")
    print(f" El video se captura directo del telefono via ADB.")
    sys.stdout.flush()

    webbrowser.open("http://127.0.0.1:5000/control")

    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


def main():
    global VIDEO_MODE, CROP_COORDS

    # 1. Dialogo inicial para elegir modo (Móvil vs Webcam)
    root_dialog = tk.Tk()
    dialog = StartupDialog(root_dialog)
    root_dialog.mainloop()

    VIDEO_MODE = dialog.choice
    if not VIDEO_MODE:
        print("Operacion cancelada en el menu de origen.")
        return

    # 2. Captura de pantalla para el recorte segun el modo elegido
    print(f"Iniciando modo: {VIDEO_MODE}")
    sys.stdout.flush()
    if VIDEO_MODE == "mobile":
        print("Obteniendo captura de pantalla del movil...")
        sys.stdout.flush()
        img = get_screenshot_adb()
        if img is None:
            print(
                "ERROR: No se detecta el celular. Revisa la conexion (cable o Wi-Fi)."
            )
            sys.stdout.flush()
            return
    elif VIDEO_MODE == "webcam":
        print("Iniciando la Camara Web de tu PC. Sonrie!...")
        sys.stdout.flush()
        img = get_screenshot_webcam()
        if img is None:
            print("ERROR: No se detecto ninguna Camara Web conectada a la PC.")
            sys.stdout.flush()
            return

    # 3. Interfaz de Recorte
    root = tk.Tk()
    selector = CropSelector(root, img)
    root.lift()
    root.attributes("-topmost", True)
    root.after_idle(root.attributes, "-topmost", False)
    root.mainloop()

    if selector.crop_coords:
        CROP_COORDS = selector.crop_coords
        w, h, x, y = CROP_COORDS
        print(f"Iniciando transmision en zona: {w}x{h} en ({x}, {y})")
        sys.stdout.flush()

        if VIDEO_MODE == "mobile":
            crop_arg = f"{w}:{h}:{x}:{y}"
            cmd = ["./scrcpy.exe", "--crop", crop_arg, "--window-title", "ScrcpyWebCrop"]
            print(f"[SCRPCY] scrcpy para vista local: {' '.join(cmd)}")
            sys.stdout.flush()

            def run_scrcpy():
                while True:
                    proc = subprocess.Popen(cmd)
                    print(f"[SCRPCY] scrcpy iniciado (PID: {proc.pid})")
                    sys.stdout.flush()
                    time.sleep(1)
                    try:
                        hwnd = win32gui.FindWindow(None, "ScrcpyWebCrop")
                        if hwnd:
                            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                            value = ctypes.c_int(1)
                            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value)
                            )
                            print("[SCRPCY] Barra de titulo oscura aplicada")
                            sys.stdout.flush()
                    except Exception as e:
                        print(f"[SCRPCY] Error al aplicar barra oscura: {e}")
                        sys.stdout.flush()
                    proc.wait()
                    print("[SCRPCY] scrcpy cerrado, reiniciando en 3s...")
                    sys.stdout.flush()
                    time.sleep(3)

            threading.Thread(target=run_scrcpy, daemon=True).start()

            time.sleep(1)
            run_web_server(selector.p_top, selector.p_bottom)

        elif VIDEO_MODE == "webcam":
            # Para Webcam, Flask bloqueara el hilo principal y es el encargado de proveer el video
            run_web_server(selector.p_top, selector.p_bottom)

    else:
        print("Operacion cancelada en el menu de recorte.")


if __name__ == "__main__":
    main()
