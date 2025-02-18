# FFmpeg GUI

Una **Interfaz Gráfica para FFmpeg** desarrollada en Python utilizando PyQt6.  
Esta aplicación permite:
- **Convertir secuencias de imágenes a video**, configurando parámetros como FPS, CRF, fundidos (fade in/out), audio opcional y formato de salida.
- **Agregar audio a un video** (por ejemplo, a un video sin sonido).
- **Cortar videos** especificando tiempos de inicio y duración o tiempo final.

La aplicación ejecuta los procesos de FFmpeg en hilos separados para mantener la interfaz responsiva y, si se intenta generar un video con un nombre de archivo ya existente, se genera un nombre único automáticamente para evitar conflictos.

---

## Características

- **Interfaz intuitiva:** Organizada en pestañas para cada funcionalidad (Imágenes, Video y Cortar Video).
- **Procesamiento en segundo plano:** Utiliza hilos (QThread) para ejecutar FFmpeg sin bloquear la UI.
- **Gestión automática de archivos de salida:** Se renombra el archivo de salida si ya existe (se añade un timestamp).
- **Modularidad:** El código está organizado en módulos para facilitar el mantenimiento y la escalabilidad.

---

## Estructura del Proyecto

```
project/
│
├── main.py                # Punto de entrada de la aplicación.
│
├── gui/
│   ├── __init__.py
│   ├── main_window.py     # Ventana principal que organiza las pestañas.
│   ├── widgets.py         # Widgets personalizados (ej. ClickableLabel).
│   └── tabs/
│       ├── __init__.py
│       ├── images_tab.py  # Pestaña para convertir imágenes a video.
│       ├── video_tab.py   # Pestaña para agregar audio a un video.
│       └── cut_video_tab.py  # Pestaña para cortar un video.
│
└── logic/
    ├── __init__.py
    ├── ffmpeg_logic.py    # Funciones para construir comandos FFmpeg.
    └── ffmpeg_worker.py   # Worker que ejecuta FFmpeg en un hilo separado.
```

---

## Requisitos

- **Python 3.x**
- **PyQt6** (se puede instalar vía pip)
- **FFmpeg** instalado y disponible en el PATH del sistema  
  (Descarga FFmpeg desde [ffmpeg.org](https://ffmpeg.org/) y sigue las instrucciones de instalación para tu sistema operativo).

---

## Instalación

1. **Clonar el repositorio:**

   ```bash
   git clone https://github.com/tu_usuario/ffmpeg-gui.git
   cd ffmpeg-gui
   ```

2. **Instalar las dependencias:**

   ```bash
   pip install PyQt6
   ```

3. **Verificar FFmpeg:**  
   Asegúrate de que FFmpeg esté instalado y accesible desde la línea de comandos.

---

## Uso

1. **Ejecutar la aplicación:**

   ```bash
   python main.py
   ```

2. **Interfaz de usuario:**  
   - **Pestaña Imágenes:** Selecciona una carpeta con imágenes, define los parámetros (FPS, CRF, fundidos, audio, formato) y convierte la secuencia en un video.
   - **Pestaña Video:** Selecciona un video sin audio y un archivo de audio para combinarlos.
   - **Pestaña Cortar Video:** Selecciona un video, define los parámetros de corte (tiempo de inicio, duración o tiempo final) y corta el video.

3. **Salida:**  
   Los archivos de salida se generarán en la misma carpeta de las imágenes o junto al video de entrada. Si ya existe un archivo con el mismo nombre, se le añadirá un timestamp para evitar sobrescrituras.

---

## Personalización

- **Parámetros FFmpeg:**  
  Puedes modificar las funciones en `logic/ffmpeg_logic.py` para ajustar los parámetros de FFmpeg según tus necesidades.

- **Interfaz:**  
  La UI se encuentra modularizada en `gui/`, permitiendo personalizar o extender la funcionalidad fácilmente.

---

## Licencia

Este proyecto se distribuye bajo la licencia **Non Comercial License**. Consulta el archivo [LICENSE](LICENSE) para más detalles.

---

## Créditos

- **Desarrollador:** Roberto Fernández Barrios
- Inspirado en diversas herramientas y proyectos que integran FFmpeg con interfaces gráficas.

---

¡Gracias por utilizar FFmpeg GUI!