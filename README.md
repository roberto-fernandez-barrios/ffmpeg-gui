# FFmpeg GUI

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11-green.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.x-blue.svg)
![Electron](https://img.shields.io/badge/Electron-React%2FTS-9cf.svg)

---

## 🎬 Descripción

Este repositorio contiene dos interfaces para el mismo backend de FFmpeg:

* **`gui/` + `main.py`** — la aplicación de escritorio original en **PyQt6**.
* **`frontend/`** — una interfaz alternativa en **Electron + React + TypeScript**, con la misma cobertura de funciones que la PyQt6, que llama al mismo backend Python a través de `logic/cli.py` (ver `frontend/README.md` para el detalle de la integración).

Ambas interfaces comparten la lógica de construcción de comandos FFmpeg en `logic/ffmpeg_logic.py`, que ofrece:

* 🚀 **Convertir secuencias de imágenes** (PNG) a video con ajustes de FPS, CRF, fundidos (fade-in/out) y pista de audio opcional.
* 🎵 **Editar audio** en videos: añadir, quitar o sustituir pistas de audio.
* ✂️ **Cortar videos** por tiempo o número de frames.
* 🔒 **Limitar bitrate** (kps) de un video.
* 📏 **Escalar videos** a dimensiones personalizadas con presets de codificación y CRF.
* 🖼️ **Recortar (crop)** videos especificando píxeles a eliminar por cada lado.
* 🔗 **Unir videos**, manualmente o emparejando automáticamente por resolución entre dos carpetas.
* 🖱️ **Drag & Drop** de archivos/carpeta para una experiencia más ágil (en ambas interfaces).
* 🛑 **Cola de tareas** con barras de progreso, cancelación segura y limpieza de salidas incompletas.

---

## 📸 Capturas de pantalla

### Frontend Electron

| Imágenes a video | Editar audio | Unir videos |
|---|---|---|
| ![Imágenes a video](docs/screenshots/frontend-img2vid.png) | ![Editar audio](docs/screenshots/frontend-audio.png) | ![Unir videos](docs/screenshots/frontend-merge.png) |

### GUI PyQt6

![Interfaz Principal](https://github.com/user-attachments/assets/798409d4-9c40-4bf0-be3b-e0c519d5d141)

---

## ⚙️ Instalación (GUI PyQt6)

1. Clona el repositorio:

   ```bash
   git clone https://github.com/usuario/ffmpeg-gui.git
   cd ffmpeg-gui
   ```

2. Crea y activa un entorno virtual:

   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```

3. Instala dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Ejecuta la aplicación:

   ```bash
   python main.py
   ```

---

## 📦 Empaquetado (Windows)

### GUI PyQt6

```bash
pyinstaller --onefile --windowed \
    --name "FFmpeg-GUI-<versión>" \
    --icon="static/icons/icon.ico" \
    --add-data "static/icons/icon.ico;static/icons/" \
    main.py
```

El ejecutable se ubicará en `dist/FFmpeg-GUI-<versión>.exe`. Puedes limpiar la carpeta `build/` y el archivo `.spec` si sólo deseas distribuir el EXE.

### Frontend Electron

```bash
cd frontend
npm run build
```

Genera un instalador NSIS en `frontend/release/<versión>/` que **no necesita Python instalado** en la máquina de destino (empaqueta `logic/cli.py` como ejecutable independiente vía PyInstaller — ver `frontend/README.md`). Solo hace falta `ffmpeg`/`ffprobe` en el `PATH` del sistema, igual que la GUI PyQt6.

---

## 🖥️ Frontend Electron (alternativa)

```bash
cd frontend
npm install
npm run dev    # desarrollo, necesita python en el PATH
npm run build  # instalador .exe, ver sección de empaquetado arriba
```

Al arrancar, la app comprueba que `ffmpeg`/`ffprobe` estén en el `PATH` y muestra un aviso en la interfaz si faltan, en vez de fallar en silencio en cada conversión. Más detalles en `frontend/README.md`.

---

## ✅ Pruebas

```bash
node tests/test_cli_bridge.cjs
```

Prueba de regresión end-to-end del puente `logic/cli.py`: genera sus propios ficheros con `ffmpeg` en una carpeta temporal, ejercita las 8 operaciones (incluyendo cancelación a mitad de proceso) por el mismo mecanismo de `spawn` que usa el frontend Electron, y limpia todo al terminar. No requiere nada más que lo que ya necesita la propia app (Python, ffmpeg/ffprobe en el PATH).

---

## 🚀 Uso

Ambas interfaces cubren las mismas siete operaciones, con formularios equivalentes:

1. **Convertir imágenes**: arrastra o selecciona una carpeta con secuencia `PNG`/`JPG`. Ajusta **FPS**, **CRF**, **fade**, formato, formato YUV y pista de audio (opcional). Pulsa **Convertir**.
2. **Editar audio**: selecciona un video; elige operación (Añadir, Quitar, Sustituir). Si aplica, arrastra o selecciona la pista de audio. Pulsa **Procesar**.
3. **Cortar video**: selecciona un video; indica inicio y duración por tiempo o por frames. Pulsa **Cortar Video**.
4. **Limitar bitrate**: selecciona un video; ajusta **bitrate** y **maxrate**. Pulsa **Limitar Kps**.
5. **Escalar video**: selecciona un video; define **ancho/alto**, **preset** y **CRF**. Pulsa **Reescalar Video**.
6. **Recortar video**: selecciona un video; define píxeles a recortar por cada lado, con fundidos opcionales. Pulsa **Recortar Video**.
7. **Unir videos**: añade una lista manual de videos (reordenable) o empareja automáticamente dos carpetas por resolución. Elige modo rápido (sin recodificar) o compatible.

Todas las operaciones se muestran en una cola de tareas con progreso en tiempo real y opción de cancelar; los botones de envío se deshabilitan hasta que los campos obligatorios estén completos.

---

## 📂 Estructura del Proyecto

```
ffmpeg-gui/
├─ gui/
│  ├─ tabs/           # Pestañas PyQt6: conversion, audio_editing, cut, limit, scale, crop, merge
│  └─ task_widget.py  # Widget para mostrar tareas
├─ logic/
│  ├─ ffmpeg_logic.py # Construcción de comandos FFmpeg (sin dependencias de PyQt)
│  ├─ ffmpeg_worker.py# QThread para ejecutar FFmpeg y notificar progreso (usado por gui/)
│  └─ cli.py          # Puente headless usado por el frontend Electron (stdin/stdout JSON)
├─ frontend/          # Interfaz alternativa Electron + React + TypeScript (ver su README)
├─ tests/
│  └─ test_cli_bridge.cjs # Prueba de regresión end-to-end del puente logic/cli.py
├─ docs/
│  └─ screenshots/    # Capturas usadas en este README
├─ static/
│  └─ icons/          # Iconos de la aplicación
├─ main.py            # Punto de entrada de la aplicación PyQt6
├─ requirements.txt
└─ README.md
```

---

## 🤝 Contribuir

1. Haz **fork** del repositorio.
2. Crea una rama (`git checkout -b feature/nueva-funcion`).
3. Realiza tus cambios y haz **commit** (`git commit -m 'Añade nueva función'`).
4. Empuja tu rama (`git push origin feature/nueva-funcion`).
5. Abre un **Pull Request**.

---

## 📝 Licencia

Este proyecto está licenciado bajo la [MIT License](LICENSE).
