from cx_Freeze import setup, Executable
import sys
import os

# Opciones de construcción para incluir archivos adicionales (como el icono)
build_exe_options = {
    "packages": [],  # Puedes agregar aquí paquetes adicionales si es necesario
    "include_files": [
        # Se incluye el icono en la ruta destino 'static/icons/icon.ico'
        (r"C:\Users\RF\ffmpeg-gui\static\icons\icon.ico", os.path.join("static", "icons", "icon.ico"))
    ]
}

# Para aplicaciones Windows sin consola (windowed)
base = None
if sys.platform == "win32":
    base = "Win32GUI"  # Esto evita que se abra la consola al ejecutar el ejecutable

# Definición del ejecutable
executables = [
    Executable(
        script="main.py",
        base=base,
        target_name="FFmpeg-GUI-2.8.exe",  # Usamos target_name en lugar de targetName
        icon=r"C:\Users\RF\ffmpeg-gui\static\icons\icon.ico"
    )
]

# Configuración de cx_Freeze
setup(
    name="FFmpeg-GUI-2.8",
    version="2.8",
    description="Aplicación GUI para FFmpeg",
    options={"build_exe": build_exe_options},
    executables=executables
)
