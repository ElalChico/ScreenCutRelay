# ScreenCutRelay

Stream any screen (mobile device via ADB or PC webcam) to the web in real‑time.

## What it does

- Captures the screen of an Android device using `scrcpy`/ADB, **or** captures a webcam.
- Lets you select the region of the screen you want to broadcast.
- Streams the video as MJPEG over HTTP (compatible with browsers, OBS, smart‑TVs, etc.).
- Provides a control panel (http://127.0.0.1:5000/control) to:
  * Edit the names of the two labels (or any two texts you want).
  * Move the labels on‑screen (drag‑and‑drop).
  * Change the font size.
  * Swap the top/bottom labels.
- The viewer page (http://<IP>:5000) shows the video with the floating labels.

## Why "ScreenCutRelay"?

- **Screen** – we capture the screen of a device.
- **Cut** – you can cut (crop) the region you want to show.
- **Relay** – the video is relayed to any client on the same network.

## Prerequisites

- **Python 3.8+** (required packages are installed automatically on first run):
  - `flask`
  - `opencv-python`
  - `pillow`
  - `pywin32`
- **scrcpy** – download the latest release from https://github.com/Genymobile/scrcpy/releases and extract `scrcpy.exe`, `adb.exe` and the required DLLs somewhere on your `PATH` or next to the scripts.
- (Optional) If you want to use the mobile mode, enable **ADB over Wi‑Fi** on your Android device.

## Quick start

```bat
rem 1️⃣ Start the web streamer (mobile or webcam)
transmitir_web.bat

rem 2️⃣ Choose the source (Mobile / Webcam) → a dialog appears.
rem 3️⃣ Write the two names you want to display (they can be anything:
rem    "Camera 1", "Monitor", …).
rem 4️⃣ Click‑drag on the captured screenshot to select the region that will be
rem    streamed.
rem 5️⃣ The control panel opens automatically in your default browser.
```

### Command line only (if you prefer)

```bash
python transmitir_web.py
```

## Control panel actions

- **Edit names** – click the ✏ button.
- **Swap names** – click the ↕ button.
- **Increase / decrease font** – A+ / A‑ buttons.
- **Drag the labels** – click on a label and move it; the new position is
  sent to all viewers in real‑time.

## FAQ

**Q: My viewer page only shows a black screen.**
A: Verify the mobile device is connected (run `adb devices`). If using Wi‑Fi,
make sure the device is on the same network and that the ADB port is open
(`abrir_puerto_firewall.bat` can help on Windows).

**Q: How can I change the video quality?**
A: The script uses JPEG quality 80 for the stream. You can edit the
`quality` parameter in `transmitir_web.py` inside `generate_frames()`.

**Q: Can I broadcast more than one source at the same time?**
A: The current version supports a single source per instance. Run multiple
instances on different ports if you need parallel streams.

## License

Your own scripts are MIT‑licensed (you can change this if you prefer).
scrcpy itself is Apache‑2.0; see its repository for the full license.

## Credits

- **scrcpy** – © Genymobile, Apache‑2.0 – the core tool that captures the Android screen.
- **Flask**, **OpenCV**, **Pillow**, **pywin32** – open‑source Python libraries.
