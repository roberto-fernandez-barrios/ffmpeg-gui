# gui/tabs/video_tab.py
"""
VideoTab: Pestaña para agregar audio a un video.
Permite seleccionar un video sin audio y un archivo de audio, y luego
combinar ambos mediante FFmpeg.
"""

import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QPushButton, QLabel, QFileDialog, QProgressBar
from PyQt6.QtCore import Qt
from gui.widgets import ClickableLabel  # Widget para enlaces clicables
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

# Importa la función que genera el comando para agregar audio
from logic.ffmpeg_logic import add_audio_to_video_command
# Importa el worker para ejecutar FFmpeg
from logic.ffmpeg_worker import FFmpegWorker

class VideoTab(QWidget):
    def __init__(self):
        super().__init__()
        self.video_file = None        # Video sin audio seleccionado
        self.video_audio_file = None  # Archivo de audio a agregar
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # --- Grupo: Selección de Video (sin audio) ---
        group_video = QGroupBox("Seleccionar video sin audio")
        video_layout = QVBoxLayout()
        self.video_file_label = QLabel("Video sin audio:")
        video_layout.addWidget(self.video_file_label)
        self.btn_select_video = QPushButton("Seleccionar video")
        self.btn_select_video.clicked.connect(self.select_video_file)
        video_layout.addWidget(self.btn_select_video)
        group_video.setLayout(video_layout)
        layout.addWidget(group_video)

        # --- Grupo: Selección de Audio ---
        group_audio = QGroupBox("Seleccionar audio para agregar")
        audio_layout = QVBoxLayout()
        self.video_audio_label = QLabel("Archivo de audio:")
        audio_layout.addWidget(self.video_audio_label)
        self.btn_select_video_audio = QPushButton("Seleccionar audio")
        self.btn_select_video_audio.clicked.connect(self.select_video_audio_file)
        audio_layout.addWidget(self.btn_select_video_audio)
        group_audio.setLayout(audio_layout)
        layout.addWidget(group_audio)

        # --- Grupo: Procesamiento ---
        group_process = QGroupBox("Procesar adición de audio")
        process_layout = QVBoxLayout()
        self.btn_add_audio = QPushButton("Agregar audio al video")
        self.btn_add_audio.clicked.connect(self.add_audio_to_video)
        process_layout.addWidget(self.btn_add_audio)

        self.video_progress_bar = QProgressBar()
        self.video_progress_bar.setValue(0)
        self.video_progress_bar.setVisible(False)
        process_layout.addWidget(self.video_progress_bar)

        self.video_status_label = QLabel("")
        process_layout.addWidget(self.video_status_label)

        self.video_link_label = ClickableLabel("")
        self.video_link_label.setTextFormat(Qt.TextFormat.RichText)
        self.video_link_label.setVisible(False)
        process_layout.addWidget(self.video_link_label)

        group_process.setLayout(process_layout)
        layout.addWidget(group_process)

        self.setLayout(layout)

    def select_video_file(self):
        """Abre un diálogo para seleccionar un video (sin audio)."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Video (sin audio)",
            "",
            "Videos (*.mp4 *.avi *.mkv *.mov)"
        )
        if file_path:
            video_name = os.path.basename(file_path)
            self.video_file_label.setText(f"Video seleccionado: <span style='color:blue;'>{video_name}</span>")
            self.video_file = file_path

    def select_video_audio_file(self):
        """Abre un diálogo para seleccionar un archivo de audio."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Archivo de Audio",
            "",
            "Audio (*.mp3 *.wav *.aac)"
        )
        if file_path:
            audio_name = os.path.basename(file_path)
            self.video_audio_label.setText(f"Audio seleccionado: <span style='color:blue;'>{audio_name}</span>")
            self.video_audio_file = file_path

    def add_audio_to_video(self):
        """
        Inicia el proceso para agregar audio a un video.
        Construye el comando FFmpeg y arranca un worker para ejecutar la tarea.
        """
        if not self.video_file:
            self.video_status_label.setText("Selecciona un video primero.")
            return
        if not self.video_audio_file:
            self.video_status_label.setText("Selecciona un archivo de audio.")
            return

        # Genera el comando FFmpeg y obtiene el archivo de salida
        command, output_file = add_audio_to_video_command(self.video_file, self.video_audio_file)
        if not command:
            self.video_status_label.setText("Error al construir el comando FFmpeg.")
            return

        # Crea y arranca el worker
        self.video_worker = FFmpegWorker(command, total_frames=100, output_file=output_file, enable_logs=False)
        self.video_worker.progressChanged.connect(self.on_video_progress_changed)
        self.video_worker.finishedSignal.connect(self.on_video_conversion_finished)

        self.video_progress_bar.setVisible(True)
        self.video_progress_bar.setValue(0)
        self.video_status_label.setText("Agregando audio al video...")
        self.video_worker.start()

    def on_video_progress_changed(self, value):
        """Actualiza la barra de progreso durante la adición de audio."""
        self.video_progress_bar.setValue(value)

    def on_video_conversion_finished(self, success, message):
        """
        Maneja el final del proceso de adición de audio.
        Si es exitoso, muestra un enlace clicable para abrir el video generado.
        """
        if success:
            self.video_status_label.setText("Audio agregado con éxito.")
            if message and os.path.exists(message):
                normalized_path = os.path.abspath(message).replace("\\", "/")
                self.video_link_label.setText(
                    f"<a style='color:blue; text-decoration:underline;' href='#'>Abrir video: {os.path.basename(message)}</a>"
                )
                self.video_link_label.setVisible(True)
                try:
                    self.video_link_label.clicked.disconnect()
                except Exception:
                    pass
                self.video_link_label.clicked.connect(
                    lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(normalized_path))
                )
            else:
                self.video_link_label.setText("Video generado, pero no se encontró la ruta.")
                self.video_link_label.setVisible(True)
        else:
            self.video_status_label.setText(f"Error: {message}")
            self.video_link_label.setVisible(False)
        self.video_progress_bar.setValue(100 if success else 0)
