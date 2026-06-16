import os
import subprocess
import tkinter as tk
from PIL import Image, ImageTk
import io

def get_screenshot():
    # Execute adb and get the screenshot in bytes
    result = subprocess.run(["./adb.exe", "exec-out", "screencap", "-p"], capture_output=True)
    if result.returncode != 0:
        print("Error getting screenshot from device.")
        return None
    return Image.open(io.BytesIO(result.stdout))

class CropSelector:
    def __init__(self, master, image):
        self.master = master
        self.master.title("Selecciona la zona a transmitir")

        self.original_image = image
        self.orig_width, self.orig_height = image.size

        # Calculate scale to fit screen
        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()

        max_height = screen_height - 100
        max_width = screen_width - 100

        self.scale = min(max_width / self.orig_width, max_height / self.orig_height, 1.0)

        self.disp_width = int(self.orig_width * self.scale)
        self.disp_height = int(self.orig_height * self.scale)

        self.display_image = self.original_image.resize((self.disp_width, self.disp_height), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(self.display_image)

        self.canvas = tk.Canvas(master, width=self.disp_width, height=self.disp_height, cursor="cross")
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

        self.rect = None
        self.start_x = None
        self.start_y = None

        self.crop_coords = None

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        # Instructions
        tk.Label(master, text="Haz clic y arrastra para seleccionar la zona. La transmisión comenzará al soltar el ratón.").pack()

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=3)

    def on_move_press(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)

        # ensure start is top-left
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        # Minimum selection size
        if (x2 - x1) < 10 or (y2 - y1) < 10:
            print("Selección muy pequeña, intenta de nuevo.")
            self.canvas.delete(self.rect)
            self.rect = None
            return

        # Clamp to bounds
        x1 = max(0, min(x1, self.disp_width))
        y1 = max(0, min(y1, self.disp_height))
        x2 = max(0, min(x2, self.disp_width))
        y2 = max(0, min(y2, self.disp_height))

        # Map back to original image size
        orig_x1 = int(x1 / self.scale)
        orig_y1 = int(y1 / self.scale)
        orig_x2 = int(x2 / self.scale)
        orig_y2 = int(y2 / self.scale)

        width = orig_x2 - orig_x1
        height = orig_y2 - orig_y1

        self.crop_coords = (width, height, orig_x1, orig_y1)
        self.master.destroy()

def main():
    print("Obteniendo captura de pantalla del móvil...")
    img = get_screenshot()
    if img is None:
        return

    root = tk.Tk()
    selector = CropSelector(root, img)
    # Bring window to front
    root.lift()
    root.attributes('-topmost',True)
    root.after_idle(root.attributes,'-topmost',False)

    root.mainloop()

    if selector.crop_coords:
        w, h, x, y = selector.crop_coords
        print(f"Iniciando scrcpy en zona: {w}x{h} en ({x}, {y})")
        crop_arg = f"{w}:{h}:{x}:{y}"
        # Start scrcpy
        subprocess.run(["./scrcpy.exe", "--crop", crop_arg])
    else:
        print("Operación cancelada.")

if __name__ == "__main__":
    main()
