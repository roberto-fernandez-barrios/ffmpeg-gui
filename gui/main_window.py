# gui/main_window.py
"""
Ventana principal de la aplicación FFmpeg GUI.
Se organiza en un QTabWidget que contiene tres pestañas:
- Imágenes (para convertir secuencias de imágenes a video)
- Video (para agregar audio a videos)
- Cortar Video (para cortar un video)
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from gui.tabs.images_tab import ImagesTab
from gui.tabs.video_tab import VideoTab
from gui.tabs.cut_video_tab import CutVideoTab

class FFmpegGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FFmpeg GUI")
        self.setGeometry(100, 100, 500, 400)
        self.init_ui()

    def init_ui(self):
        # Se crea el layout principal y el QTabWidget
        main_layout = QVBoxLayout()
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Se instancia y añade cada pestaña al QTabWidget
        self.images_tab = ImagesTab()
        self.tabs.addTab(self.images_tab, "Imágenes")

        self.video_tab = VideoTab()
        self.tabs.addTab(self.video_tab, "Video")

        self.cut_video_tab = CutVideoTab()
        self.tabs.addTab(self.cut_video_tab, "Cortar Video")

        self.setLayout(main_layout)
