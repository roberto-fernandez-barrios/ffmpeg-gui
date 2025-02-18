# gui/tabs/images_tab.py
"""
ImagesTab: Pestaña para convertir una secuencia de imágenes en un video.
Proporciona la interfaz para seleccionar la carpeta de imágenes, definir parámetros
(de FPS, CRF, fundidos, audio, formato) y ejecutar la conversión mediante FFmpeg.
"""

import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QPushButton, QLabel, QLineEdit, QComboBox, QProgressBar, QFileDialog
from PyQt6.QtCore import Qt
from gui.widgets import ClickableLabel  # Widget personalizado para etiquetas clicables
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

# Importa la función que construye el comando FFmpeg para conversión
from logic.ffmpeg_logic import convert_images_to_video_command
# Importa el worker que ejecuta FFmpeg en un hilo
from logic.ffmpeg_worker import FFmpegWorker

class ImagesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.image_folder = None  # Ruta a la carpeta con imágenes
        self.audio_path = None    # Ruta opcional al archivo de audio
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # --- Grupo: Selección de Imágenes ---
        group_folder = QGroupBox("Selección de Imágenes")
        folder_layout = QVBoxLayout()
        self.img_seq_label = QLabel("Carpeta con imágenes:")
        folder_layout.addWidget(self.img_seq_label)
        self.btn_select_images = QPushButton("Seleccionar carpeta de imágenes")
        self.btn_select_images.clicked.connect(self.select_image_folder)
        folder_layout.addWidget(self.btn_select_images)
        group_folder.setLayout(folder_layout)
        layout.addWidget(group_folder)

        # --- Grupo: Configuración de Conversión ---
        group_config = QGroupBox("Configuración de Conversión")
        config_layout = QVBoxLayout()

        # Configuración de FPS
        self.fps_label = QLabel("FPS (Frames por segundo):")
        config_layout.addWidget(self.fps_label)
        self.fps_input = QLineEdit("30")
        config_layout.addWidget(self.fps_input)

        # Configuración de CRF
        self.crf_label = QLabel("CRF:")
        config_layout.addWidget(self.crf_label)
        self.crf_input = QLineEdit("19")
        config_layout.addWidget(self.crf_input)

        # Configuración de fundido de entrada (fade in)
        self.fade_in_label = QLabel("Fade In (segundos):")
        config_layout.addWidget(self.fade_in_label)
        self.fade_in_input = QLineEdit("1")
        config_layout.addWidget(self.fade_in_input)

        # Configuración de fundido de salida (fade out)
        self.fade_out_label = QLabel("Fade Out (segundos):")
        config_layout.addWidget(self.fade_out_label)
        self.fade_out_input = QLineEdit("1")
        config_layout.addWidget(self.fade_out_input)

        # Selección opcional de archivo de audio
        self.audio_label = QLabel("Archivo de audio (opcional):")
        config_layout.addWidget(self.audio_label)
        self.btn_select_audio = QPushButton("Seleccionar archivo de audio")
        self.btn_select_audio.clicked.connect(self.select_audio_file)
        config_layout.addWidget(self.btn_select_audio)

        # Selección del formato de salida
        self.img_format_label = QLabel("Formato de salida:")
        config_layout.addWidget(self.img_format_label)
        self.img_format_combo = QComboBox()
        self.img_format_combo.addItems([
            "mp4 (H.264 8-bit)",
            "mp4 (H.265 8-bit)",
            "mp4 (H.265 10-bit)",
            "mp4 (H.264 10-bit)",
            "avi",
            "mkv",
            "mov"
        ])
        config_layout.addWidget(self.img_format_combo)

        group_config.setLayout(config_layout)
        layout.addWidget(group_config)

        # --- Grupo: Procesamiento de Conversión ---
        group_process = QGroupBox("Procesar Conversión")
        process_layout = QVBoxLayout()
        self.btn_convert_images = QPushButton("Convertir imágenes a video")
        self.btn_convert_images.clicked.connect(self.convert_images_to_video)
        process_layout.addWidget(self.btn_convert_images)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        process_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        process_layout.addWidget(self.status_label)

        self.image_video_link_label = ClickableLabel("")
        self.image_video_link_label.setTextFormat(Qt.TextFormat.RichText)
        self.image_video_link_label.setVisible(False)
        process_layout.addWidget(self.image_video_link_label)

        group_process.setLayout(process_layout)
        layout.addWidget(group_process)

        self.setLayout(layout)

    def select_image_folder(self):
        """Abre un diálogo para seleccionar la carpeta de imágenes."""
        folder_path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de imágenes")
        if folder_path:
            folder_name = os.path.basename(folder_path)
            self.img_seq_label.setText(f"Carpeta seleccionada: <span style='color:blue;'>{folder_name}</span>")
            self.image_folder = folder_path

    def select_audio_file(self):
        """Abre un diálogo para seleccionar un archivo de audio."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Archivo de Audio",
            "",
            "Audio (*.mp3 *.wav *.aac)"
        )
        if file_path:
            audio_name = os.path.basename(file_path)
            self.audio_label.setText(f"Audio seleccionado: <span style='color:blue;'>{audio_name}</span>")
            self.audio_path = file_path

    def convert_images_to_video(self):
        """
        Inicia la conversión de imágenes a video.
        Recoge los parámetros definidos por el usuario, construye el comando FFmpeg
        y arranca un hilo (worker) para ejecutar la conversión.
        """
        if not self.image_folder:
            self.status_label.setText("Selecciona una carpeta de imágenes primero.")
            return

        fps = self.fps_input.text()
        audio_path = self.audio_path  # Puede ser None si no se seleccionó audio
        user_format = self.img_format_combo.currentText()

        # Verifica que existan imágenes .png en la carpeta
        images = sorted(os.listdir(self.image_folder))
        total_images = len([img for img in images if img.lower().endswith('.png')])
        if total_images == 0:
            self.status_label.setText("No se encontraron imágenes .png en la carpeta.")
            return

        crf = self.crf_input.text()
        try:
            fade_in = float(self.fade_in_input.text())
        except ValueError:
            fade_in = 1
        try:
            fade_out = float(self.fade_out_input.text())
        except ValueError:
            fade_out = 1

        # Construye el comando FFmpeg y obtiene la ruta del archivo de salida
        command, output_file = convert_images_to_video_command(
            self.image_folder, fps, audio_path, user_format, crf, fade_in, fade_out
        )
        if not command:
            self.status_label.setText("No se detectó el patrón correcto en las imágenes.")
            return

        # Crea y arranca el worker para ejecutar FFmpeg
        self.worker = FFmpegWorker(command, total_images, output_file, enable_logs=False)
        self.worker.progressChanged.connect(self.on_progress_changed)
        self.worker.finishedSignal.connect(self.on_conversion_finished)

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.image_video_link_label.setVisible(False)
        self.status_label.setText("Convirtiendo...")
        self.worker.start()

    def on_progress_changed(self, value):
        """Actualiza la barra de progreso."""
        self.progress_bar.setValue(value)

    def on_conversion_finished(self, success, message):
        """
        Maneja el final del proceso de conversión.
        Si es exitoso, muestra un enlace clicable para abrir el video generado.
        """
        if success:
            self.status_label.setText("Conversión completada.")
            self.progress_bar.setValue(100)
            if message and os.path.exists(message):
                normalized_path = os.path.abspath(message).replace("\\", "/")
                self.image_video_link_label.setText(
                    f"<a style='color:blue; text-decoration:underline;' href='#'>Abrir video: {os.path.basename(message)}</a>"
                )
                self.image_video_link_label.setVisible(True)
                try:
                    self.image_video_link_label.clicked.disconnect()
                except Exception:
                    pass
                self.image_video_link_label.clicked.connect(
                    lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(normalized_path))
                )
            else:
                self.image_video_link_label.setText("Video generado, pero no se encontró la ruta.")
                self.image_video_link_label.setVisible(True)
        else:
            self.status_label.setText(f"Error: {message}")
            self.progress_bar.setValue(0)
            self.image_video_link_label.setVisible(False)
