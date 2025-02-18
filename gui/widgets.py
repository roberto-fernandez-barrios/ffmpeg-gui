# gui/widgets.py
"""
Módulo para widgets personalizados utilizados en la aplicación FFmpeg GUI.
Por ejemplo, se define un QLabel que emite una señal al ser clicado.
"""

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import pyqtSignal, Qt

class ClickableLabel(QLabel):
    """
    Subclase de QLabel que emite la señal 'clicked' cuando se presiona el mouse.
    Útil para mostrar enlaces clicables en la interfaz.
    """
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        self.clicked.emit()  # Emite la señal cuando se hace clic
        super().mousePressEvent(event)
