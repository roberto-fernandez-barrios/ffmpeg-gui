# main.py
"""
Punto de entrada de la aplicación FFmpeg GUI.
Este script inicializa la aplicación Qt, crea la ventana principal y
arranca el loop de eventos.
"""
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from gui.main_window import FFmpegGUI  # Tu ventana principal

def resource_path(relative_path):
    """
    Obtiene la ruta absoluta a un recurso, funciona para desarrollo y para el ejecutable empaquetado.
    """
    try:
        # PyInstaller crea un atributo _MEIPASS temporal
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def main():
    app = QApplication(sys.argv)
    
    # Utiliza la función resource_path para obtener la ruta correcta al icono
    icon_path = resource_path("static\icons\icon.ico")
    app.setWindowIcon(QIcon(icon_path))
    
    window = FFmpegGUI() # Crea la instancia de la ventana principal
    window.show() # Muestra la ventana
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
