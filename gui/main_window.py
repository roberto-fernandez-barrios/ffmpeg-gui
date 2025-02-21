# gui/main_window.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from gui.tabs.convert_images_tab import ImagesTab
from gui.tabs.add_audio_tab import VideoTab
from gui.tabs.cut_video_tab import CutVideoTab
from gui.tabs.limit_kps_tab import LimitKpsTab
from gui.tabs.scale_video_tab import ScaleVideoTab
from gui.tabs.crop_video_tab import CropVideoTab

class FFmpegGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.workers = []  # Lista para almacenar los workers activos
        self.setWindowTitle("FFmpeg GUI")
        self.setGeometry(100, 100, 650, 500)  # Ajusta el tamaño de la ventana según lo necesites
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.images_tab = ImagesTab()
        self.tabs.addTab(self.images_tab, "Imágenes a Video")

        self.video_tab = VideoTab()
        self.tabs.addTab(self.video_tab, "Añadir Audio")

        self.cut_video_tab = CutVideoTab()
        self.tabs.addTab(self.cut_video_tab, "Cortar Video")
        
        self.limit_kps_tab = LimitKpsTab()
        self.tabs.addTab(self.limit_kps_tab, "Limitar Kps")

        self.scale_video_tab = ScaleVideoTab()
        self.tabs.addTab(self.scale_video_tab, "Escalar Video")

        self.crop_video_tab = CropVideoTab()
        self.tabs.addTab(self.crop_video_tab, "Recortar Video")

        self.setLayout(main_layout)
