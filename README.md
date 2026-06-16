# ScreenCutRelay

Transmite cualquier pantalla (dispositivo móvil vía ADB o webcam de PC) a la web en tiempo real.

⚠️ **Nota:** Este proyecto no modifica scrcpy; es un complemento que lo usa para capturar la pantalla.

## Qué hace

- Captura la pantalla de un dispositivo Android usando `scrcpy`/ADB, **o** captura una webcam.
- Permite seleccionar la zona de la pantalla que quieres difundir.
- Transmite el video como MJPEG sobre HTTP (compatible con navegadores, OBS, smart‑TV, etc.).
- Provee un panel de control (`http://127.0.0.1:5000/control`) para:
  * Editar los nombres de las dos etiquetas (o cualquier texto que necesites).
  * Mover las etiquetas en la pantalla (arrastrar‑y‑soltar).
  * Cambiar el tamaño de la fuente.
  * Intercambiar la etiqueta superior/inferior.

- La página del visor (`http://YOUR_IP:5000`) muestra el video con las etiquetas flotantes.

## Por qué "ScreenCutRelay"

- **Screen** – capturamos la pantalla de un dispositivo.
- **Cut** – puedes recortar (crop) la región que deseas mostrar.
- **Relay** – el video se retransmite a cualquier cliente en la misma red.

## Prerrequisitos

- **Python 3.8+** (los paquetes requeridos se instalan automáticamente al primer uso):
  - `flask`
  - `opencv-python`
  - `pillow`
  - `pywin32`
- **scrcpy** – descarga la última versión desde https://github.com/Genymobile/scrcpy/releases, extrae `scrcpy.exe`, `adb.exe` y las DLL necesarias y colócalos en la **carpeta raíz** del proyecto (donde están los scripts `.py`).
- (Opcional) Si deseas usar el modo móvil, habilita **ADB sobre Wi‑Fi** en tu dispositivo Android.

## Guía rápida

```bat
rem 1️⃣ Inicia la transmisión (modo móvil o webcam)
transmitir_web.bat

rem 2️⃣ Elige la fuente (Mobile / Webcam) → aparece un diálogo.
rem 3️⃣ Escribe los dos nombres que quieres mostrar (pueden ser cualquier texto,
rem    por ejemplo "Cámara 1", "Monitor", etc.).
rem 4️⃣ Haz click‑drag sobre la captura de pantalla para seleccionar la zona que se
rem    transmitirá.
rem 5️⃣ El panel de control se abre automáticamente en tu navegador predeterminado.
```

### Sólo línea de comandos (si lo prefieres)

```bash
python transmitir_web.py
```

## Acciones del panel de control

- **Editar nombres** – pulsa el botón ✏.
- **Intercambiar nombres** – pulsa el botón ↕.
- **Aumentar / disminuir fuente** – botones A+ / A‑.
- **Arrastrar etiquetas** – haz click sobre una etiqueta y muévela; la nueva posición
  se envía a todos los espectadores en tiempo real.

## Preguntas frecuentes

**P: Mi página del visor solo muestra una pantalla negra.**
R: Verifica que el dispositivo móvil esté conectado (ejecuta `adb devices`).
Si usas Wi‑Fi, asegúrate de que esté en la misma red y que el puerto ADB esté abierto
(`abrir_puerto_firewall.bat` puede ayudar en Windows).

**P: ¿Cómo puedo cambiar la calidad del video?**
R: El script usa calidad JPEG 80 para la transmisión. Puedes modificar el parámetro
`quality` dentro de `transmitir_web.py`, en la función `generate_frames()`.

**P: ¿Puedo transmitir más de una fuente a la vez?**
R: La versión actual soporta una única fuente por instancia. Ejecuta varias
instancias en diferentes puertos si necesitas transmisiones paralelas.

## Licencia

Tus scripts están bajo licencia MIT (puedes cambiarla si lo prefieres).
scrcpy está bajo licencia Apache 2.0; consulta su repositorio para el texto completo.

## Créditos

- **scrcpy** – © Genymobile, Apache‑2.0 – la herramienta principal que captura la pantalla Android.
- **Flask**, **OpenCV**, **Pillow**, **pywin32** – bibliotecas de código abierto.