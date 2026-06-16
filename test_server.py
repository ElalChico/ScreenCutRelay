import win32gui
from mss import mss
from PIL import Image
import io
import time
import subprocess
import threading
from flask import Flask, Response

app = Flask(__name__)

def run():
    subprocess.run(["./scrcpy.exe", "--window-title", "ScrcpyWebCrop"])

def find_scrcpy_window():
    scrcpy_hwnd = 0
    def callback(hwnd, extra):
        nonlocal scrcpy_hwnd
        title = win32gui.GetWindowText(hwnd)
        if win32gui.IsWindowVisible(hwnd) and "scrcpywebcrop" in title.lower():
            rect = win32gui.GetWindowRect(hwnd)
            w = rect[2] - rect[0]
            h = rect[3] - rect[1]
            if w > 0 and h > 0:
                scrcpy_hwnd = hwnd

    win32gui.EnumWindows(callback, None)
    return scrcpy_hwnd

def generate_frames():
    black_img = Image.new('RGB', (800, 600), color='red') # red to notice
    buf_black = io.BytesIO()
    black_img.save(buf_black, format="JPEG", quality=50)
    black_frame = buf_black.getvalue()

    with mss() as sct:
        while True:
            hwnd = find_scrcpy_window()
            frame_to_yield = black_frame
            if hwnd != 0:
                rect = win32gui.GetWindowRect(hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                if width > 0 and height > 0:
                    monitor = {"top": rect[1], "left": rect[0], "width": width, "height": height}
                    try:
                        sct_img = sct.grab(monitor)
                        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG", quality=80)
                        frame_to_yield = buf.getvalue()
                    except Exception as e:
                        print("Error grabbing:", e)
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_to_yield + b"\r\n")
            time.sleep(0.05)

@app.route("/")
def index():
    return '<img src="/video_feed">'

@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == '__main__':
    threading.Thread(target=run, daemon=True).start()
    app.run(port=5001)

