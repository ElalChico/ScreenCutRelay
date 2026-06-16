import win32gui
from mss import mss
from PIL import Image
import time
import subprocess
import threading

def run():
    subprocess.run(["./scrcpy.exe", "--window-title", "ScrcpyWebCrop"])

threading.Thread(target=run, daemon=True).start()
time.sleep(5)

hwnd = 0
def cb(h, e):
    global hwnd
    if win32gui.GetWindowText(h) == "ScrcpyWebCrop":
        hwnd = h
win32gui.EnumWindows(cb, None)

if hwnd:
    rect = win32gui.GetWindowRect(hwnd)
    print("Rect:", rect)
    w = rect[2] - rect[0]
    h = rect[3] - rect[1]
    monitor = {"top": rect[1], "left": rect[0], "width": w, "height": h}
    with mss() as sct:
        img = sct.grab(monitor)
        print("Captured:", img.size)
        Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX").save("test_out.jpg")
else:
    print("Not found")

