# gui/tabs/limit_kps_tab.py
"""
LimitKpsTab: Pestaña para limitar los kps (bitrate) de un video.
Permite seleccionar un video, configurar el bitrate y la tasa máxima, y generar
el video limitado mediante FFmpeg.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QPushButton, QLabel, QLineEdit,
    QScrollArea, QFileDialog
)
from PyQt6.QtCore import Qt

# Importa la función que genera el comando FFmpeg para limitar kps
from logic.ffmpeg_logic import limit_kps_command
# Importa el widget de tarea para gestionar el progreso de cada operación
from gui.task_widget import ConversionTaskWidget
from gui.tab_mixins import FfmpegTaskMixin

class LimitKpsTab(FfmpegTaskMixin, QWidget):
    def __init__(self):
        super().__init__()
        # Habilitar drag & drop para la selección de video
        self.setAcceptDrops(True)
        self.input_video = None
        self.active_workers = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # --- Grupo: Seleccionar Video ---
        group_video = QGroupBox("Seleccionar Video")
        video_layout = QVBoxLayout()
        self.video_file_label = QLabel("Video de entrada:")
        video_layout.addWidget(self.video_file_label)
        self.btn_select_video = QPushButton("Seleccionar Video")
        self.btn_select_video.clicked.connect(self.select_video_file)
        video_layout.addWidget(self.btn_select_video)
        group_video.setLayout(video_layout)
        layout.addWidget(group_video)

        # --- Grupo: Parámetros de Limitación ---
        group_params = QGroupBox("Parámetros de Limitación")
        params_layout = QVBoxLayout()
        # Bitrate de video
        self.bit_rate_label = QLabel("Bitrate de video (k = kbps, M = Mbps, G = Gbps):")
        params_layout.addWidget(self.bit_rate_label)
        self.bit_rate_input = QLineEdit("57M")
        params_layout.addWidget(self.bit_rate_input)
        # Maxrate
        self.max_rate_label = QLabel("Maxrate (k = kbps, M = Mbps, G = Gbps):")
        params_layout.addWidget(self.max_rate_label)
        self.max_rate_input = QLineEdit("60M")
        params_layout.addWidget(self.max_rate_input)
        group_params.setLayout(params_layout)
        layout.addWidget(group_params)

        # --- Botón para iniciar el proceso ---
        self.btn_limit_kps = QPushButton("Limitar Kps")
        self.btn_limit_kps.clicked.connect(self.limit_kps)
        layout.addWidget(self.btn_limit_kps)

        # --- Grupo: Tareas de Limitación ---
        group_tasks = QGroupBox("Tareas de Limitación")
        self.tasks_layout = QVBoxLayout()
        # Alinea las tareas hacia arriba para que se vayan apilando de arriba hacia abajo
        self.tasks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        group_tasks.setLayout(self.tasks_layout)

        # QScrollArea para soportar múltiples tareas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(100)
        scroll_content = QWidget()
        scroll_content.setLayout(self.tasks_layout)
        scroll_area.setWidget(scroll_content)

        layout.addWidget(group_tasks)
        layout.addWidget(scroll_area)

        self.setLayout(layout)

    def select_video_file(self):
        """Abre un diálogo para seleccionar el video de entrada."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Video",
            "",
            "Videos (*.mp4 *.avi *.mkv *.mov)"
        )
        if file_path:
            video_name = os.path.basename(file_path)
            self.video_file_label.setText(f"Video de entrada: <span style='color:blue;'>{video_name}</span>")
            self.input_video = file_path

    def dragEnterEvent(self, event):
        """
        Se llama cuando se arrastra un objeto sobre el widget.
        Si el objeto contiene URLs (archivos), se acepta la acción.
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """
        Se llama cuando se suelta un objeto sobre el widget.
        Si el archivo soltado es un video (extensiones .mp4, .avi, .mkv, .mov),
        se asigna a self.input_video y se actualiza el label correspondiente.
        """
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                video_exts = [".mp4", ".avi", ".mkv", ".mov"]
                ext = os.path.splitext(file_path)[1].lower()
                if ext in video_exts:
                    self.input_video = file_path
                    video_name = os.path.basename(file_path)
                    self.video_file_label.setText(f"Video de entrada: <span style='color:blue;'>{video_name}</span>")
            event.acceptProposedAction()
        else:
            event.ignore()

    def limit_kps(self):
        """
        Inicia el proceso para limitar los kps (bitrate) del video.
        Construye el comando FFmpeg y arranca un worker, creando un widget de tarea
        para mostrar el progreso.
        """
        if not self.input_video:
            error_widget = ConversionTaskWidget("Error: Sin video")
            error_widget.update_status("Selecciona un video primero.")
            self.tasks_layout.addWidget(error_widget)
            return

        bitrate = self.bit_rate_input.text().strip() or "57M"
        maxrate = self.max_rate_input.text().strip() or "60M"

        command, output_file = limit_kps_command(self.input_video, video_bitrate=bitrate, maxrate=maxrate)
        if not command:
            error_widget = ConversionTaskWidget("Error: Comando inválido")
            error_widget.update_status("Error al construir el comando FFmpeg.")
            self.tasks_layout.addWidget(error_widget)
            return

        task_name = f"Limitación: {os.path.basename(output_file)}"
        task_widget = ConversionTaskWidget(task_name)
        self.tasks_layout.addWidget(task_widget)

        # total_frames=100 es un valor de referencia para el progreso.
        self.start_ffmpeg_task(task_widget, command, output_file, total_frames=100, task_prefix="Limitación: ")
