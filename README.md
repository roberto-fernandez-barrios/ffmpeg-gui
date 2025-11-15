# FFmpeg Backend

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11-green.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.x-blue.svg)

---

## 🎬 Descripción

**FFmpeg Backend** es una aplicación de escritorio multiplataforma (Windows) desarrollada con **PyQt6** que ofrece una interfaz gráfica amigable para ejecutar tareas comunes de FFmpeg sin necesidad de línea de comandos. Permite:

* 🚀 **Convertir secuencias de imágenes** (PNG) a video con ajustes de FPS, CRF, fundidos (fade-in/out) y pista de audio opcional.
* 🎵 **Editar audio** en videos: añadir, quitar o sustituir pistas de audio.
* ✂️ **Cortar videos** por tiempo o número de frames.
* 🔒 **Limitar bitrate** (kps) de un video.
* 📏 **Escalar videos** a dimensiones personalizadas con presets de codificación y CRF.
* 🖼️ **Recortar (crop)** videos especificando píxeles a eliminar por cada lado.
* 🖱️ **Drag & Drop** de archivos/carpeta para una experiencia más ágil.
* 🛑 **Cola de tareas** con barras de progreso, cancelación segura y limpieza de salidas incompletas.

---

## 📸 Captura de Pantalla
![Interfaz Principal](https://github.com/user-attachments/assets/798409d4-9c40-4bf0-be3b-e0c519d5d141)

---

## ⚙️ Instalación

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

Para generar un `.exe` ejecutable:

```bash
pyinstaller --onefile --windowed \
    --name "FFmpeg-GUI-<versión>" \
    --icon="static/icons/icon.ico" \
    --add-data "static/icons/icon.ico;static/icons/" \
    main.py
```

El ejecutable se ubicará en `dist/FFmpeg-GUI-<versión>.exe`. Puedes limpiar la carpeta `build/` y el archivo `.spec` si sólo deseas distribuir el EXE.

---

## 🚀 Uso

1. **Convertir imágenes**: arrastra o selecciona una carpeta con secuencia `PNG`. Ajusta **FPS**, **CRF**, **fade**, formato y pista de audio (opcional). Pulsa **Convertir**.
2. **Editar audio**: selecciona un video; elige operación (Añadir, Quitar, Sustituir). Si aplica, arrastra o selecciona la pista de audio. Pulsa **Procesar**.
3. **Cortar video**: selecciona un video; indica inicio y duración (o frames+FPS). Pulsa **Cortar Video**.
4. **Limitar bitrate**: selecciona un video; ajusta **bitrate** y **maxrate**. Pulsa **Limitar Kps**.
5. **Escalar video**: selecciona un video; define **ancho/alto**, **preset** y **CRF**. Pulsa **Reescalar Video**.
6. **Recortar video**: selecciona un video; define píxeles a recortar por cada lado. Pulsa **Recortar Video**.

Todas las operaciones se muestran en una cola de tareas con progreso y opción de cancelar.

---

## 📂 Estructura del Proyecto

```
ffmpeg-gui/
├─ gui/
│  ├─ tabs/           # Pestañas: conversion, audio_editing, cut, limit, scale, crop
│  └─ task_widget.py  # Widget para mostrar tareas
├─ logic/
│  ├─ ffmpeg_logic.py # Construcción de comandos FFmpeg
│  └─ ffmpeg_worker.py# QThread para ejecutar FFmpeg y notificar progreso
├─ static/
│  └─ icons/          # Iconos de la aplicación
├─ main.py            # Punto de entrada de la aplicación
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
