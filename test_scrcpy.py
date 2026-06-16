import subprocess
import threading
import time
import win32gui

def run():
    subprocess.run(["./scrcpy.exe", "--window-title", "ScrcpyWebCrop"])

threading.Thread(target=run, daemon=True).start()
time.sleep(3)

def callback(hwnd, extra):
    title = win32gui.GetWindowText(hwnd)
    if "scrcpy" in title.lower(): print("Found:", title)

win32gui.EnumWindows(callback, None)
