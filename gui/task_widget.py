# gui/task_widget.py

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QProgressBar, QPushButton, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFontMetrics

class ConversionTaskWidget(QWidget):
    cancelRequested = pyqtSignal()

    def __init__(self, task_name: str, parent=None):
        super().__init__(parent)
        self.full_task_name = task_name  # Guarda el nombre completo
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()

        # Etiqueta para el nombre de la tarea
        self.name_label = QLabel()
        # Permite que la etiqueta se expanda y use el espacio disponible
        self.name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.update_task_name()  # Establece el texto inicial con elidado
        layout.addWidget(self.name_label)

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Etiqueta de estado
        self.status_label = QLabel("En progreso")
        layout.addWidget(self.status_label)

        # Botón de cancelar
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.cancelRequested.emit)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

    def update_task_name(self):
        """Actualiza el nombre mostrado con texto elidido y configura el tooltip con el nombre completo."""
        self.name_label.setToolTip(self.full_task_name)
        # Se calcula el texto elidido en función de un ancho máximo.
        metrics = QFontMetrics(self.name_label.font())
        elided = metrics.elidedText(self.full_task_name, Qt.TextElideMode.ElideMiddle, 200)
        self.name_label.setText(elided)

    def update_progress(self, value: int):
        self.progress_bar.setValue(value)

    def update_status(self, text: str):
        self.status_label.setText(text)

    def resizeEvent(self, event):
        """Recalcula el texto elidido al redimensionar el widget para adaptarse al nuevo ancho."""
        self.update_task_name()
        super().resizeEvent(event)
