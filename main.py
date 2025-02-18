# main.py
"""
Punto de entrada de la aplicación FFmpeg GUI.
Este script inicializa la aplicación Qt, crea la ventana principal y
arranca el loop de eventos.
"""

import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import FFmpegGUI  # Importa la ventana principal

def main():
    app = QApplication(sys.argv)
    window = FFmpegGUI()  # Crea la instancia de la ventana principal
    window.show()         # Muestra la ventana
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
