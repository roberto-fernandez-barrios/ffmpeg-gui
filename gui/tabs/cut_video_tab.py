# gui/tabs/cut_video_tab.py
"""
CutVideoTab: Pestaña para cortar un video.
Permite seleccionar un video, definir el tiempo de inicio, duración o tiempo final,
y luego ejecutar el corte mediante FFmpeg.
"""

import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QPushButton, QLabel, QLineEdit, QProgressBar, QFileDialog
from PyQt6.QtCore import Qt
from gui.widgets import ClickableLabel  # Widget para etiquetas clicables
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

# Importa la función que construye el comando para cortar el video
from logic.ffmpeg_logic import cut_video_command
# Importa el worker para ejecutar FFmpeg
from logic.ffmpeg_worker import FFmpegWorker

class CutVideoTab(QWidget):
    def __init__(self):
        super().__init__()
        self.cut_video_file = None  # Archivo de video a cortar
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # --- Grupo: Selección de Video ---
        group_video = QGroupBox("Seleccionar Video")
        video_layout = QVBoxLayout()
        self.cut_video_file_label = QLabel("Video:")
        video_layout.addWidget(self.cut_video_file_label)
        self.btn_select_cut_video = QPushButton("Seleccionar Video")
        self.btn_select_cut_video.clicked.connect(self.select_cut_video_file)
        video_layout.addWidget(self.btn_select_cut_video)
        group_video.setLayout(video_layout)
        layout.addWidget(group_video)

        # --- Grupo: Parámetros de Corte ---
        group_params = QGroupBox("Parámetros de Corte")
        params_layout = QVBoxLayout()

        # Tiempo de inicio (-ss)
        self.cut_start_input = QLineEdit("0")
        params_layout.addWidget(QLabel("Tiempo de inicio (segundos o hh:mm:ss):"))
        params_layout.addWidget(self.cut_start_input)

        # Duración (-t)
        self.cut_duration_input = QLineEdit("")
        params_layout.addWidget(QLabel("Duración (segundos, opcional):"))
        params_layout.addWidget(self.cut_duration_input)

        # Tiempo final (-to)
        self.cut_end_input = QLineEdit("")
        params_layout.addWidget(QLabel("Tiempo final (segundos o hh:mm:ss, opcional):"))
        params_layout.addWidget(self.cut_end_input)

        group_params.setLayout(params_layout)
        layout.addWidget(group_params)

        # --- Grupo: Procesamiento ---
        group_process = QGroupBox("Procesar Corte de Video")
        process_layout = QVBoxLayout()
        self.btn_cut_video = QPushButton("Cortar Video")
        self.btn_cut_video.clicked.connect(self.cut_video)
        process_layout.addWidget(self.btn_cut_video)

        self.cut_progress_bar = QProgressBar()
        self.cut_progress_bar.setValue(0)
        self.cut_progress_bar.setVisible(False)
        process_layout.addWidget(self.cut_progress_bar)

        self.cut_status_label = QLabel("")
        process_layout.addWidget(self.cut_status_label)

        self.cut_video_link_label = ClickableLabel("")
        self.cut_video_link_label.setTextFormat(Qt.TextFormat.RichText)
        self.cut_video_link_label.setVisible(False)
        process_layout.addWidget(self.cut_video_link_label)

        group_process.setLayout(process_layout)
        layout.addWidget(group_process)

        self.setLayout(layout)

    def select_cut_video_file(self):
        """Abre un diálogo para seleccionar el video que se desea cortar."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Video",
            "",
            "Videos (*.mp4 *.avi *.mkv *.mov)"
        )
        if file_path:
            self.cut_video_file_label.setText(f"Video: <span style='color:blue;'>{os.path.basename(file_path)}</span>")
            self.cut_video_file = file_path

    def cut_video(self):
        """
        Inicia el proceso de corte de video.
        Recoge los parámetros (tiempo de inicio, duración o tiempo final),
        construye el comando FFmpeg y arranca el worker.
        """
        if not self.cut_video_file:
            self.cut_status_label.setText("Selecciona un video primero.")
            return

        start_time = self.cut_start_input.text().strip() or "0"
        duration = self.cut_duration_input.text().strip()
        end_time = self.cut_end_input.text().strip()

        # Genera el comando FFmpeg y obtiene la ruta de salida
        command, output_file = cut_video_command(self.cut_video_file, start_time, duration=duration or None, end_time=end_time or None)
        if not command:
            self.cut_status_label.setText("Error al construir el comando FFmpeg.")
            return

        # Crea y arranca el worker
        self.cut_worker = FFmpegWorker(command, total_frames=100, output_file=output_file, enable_logs=False)
        self.cut_worker.progressChanged.connect(self.on_cut_video_progress_changed)
        self.cut_worker.finishedSignal.connect(self.on_cut_video_finished)

        self.cut_progress_bar.setVisible(True)
        self.cut_progress_bar.setValue(0)
        self.cut_status_label.setText("Cortando video...")
        self.btn_cut_video.setEnabled(False)
        self.cut_worker.start()

    def on_cut_video_progress_changed(self, value):
        """Actualiza la barra de progreso durante el corte del video."""
        self.cut_progress_bar.setValue(value)

    def on_cut_video_finished(self, success, message):
        """
        Maneja el final del proceso de corte.
        Si es exitoso, muestra un enlace clicable para abrir el video cortado.
        """
        self.btn_cut_video.setEnabled(True)
        if success:
            self.cut_status_label.setText("Corte completado.")
            if message and os.path.exists(message):
                normalized_path = os.path.abspath(message).replace("\\", "/")
                self.cut_video_link_label.setText(
                    f"<a style='color:blue; text-decoration:underline;' href='#'>Abrir video cortado: {os.path.basename(message)}</a>"
                )
                self.cut_video_link_label.setVisible(True)
                try:
                    self.cut_video_link_label.clicked.disconnect()
                except Exception:
                    pass
                self.cut_video_link_label.clicked.connect(
                    lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(normalized_path))
                )
            else:
                self.cut_video_link_label.setText("Video cortado, pero no se encontró la ruta.")
                self.cut_video_link_label.setVisible(True)
        else:
            self.cut_status_label.setText(f"Error: {message}")
            self.cut_video_link_label.setVisible(False)
        self.cut_progress_bar.setValue(100 if success else 0)
