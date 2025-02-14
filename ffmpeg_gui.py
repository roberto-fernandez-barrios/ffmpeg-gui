# ffmpeg_gui.py

import os
import re
import subprocess

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QLabel, QComboBox, QLineEdit, QProgressBar
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt

from ffmpeg_logic import convert_images_to_video_command

class FFmpegGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("FFmpeg GUI")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        # Selección de carpeta de imágenes
        self.img_seq_label = QLabel("Carpeta con imágenes:")
        layout.addWidget(self.img_seq_label)

        self.btn_select_images = QPushButton("Seleccionar carpeta de imágenes")
        self.btn_select_images.clicked.connect(self.select_image_folder)
        layout.addWidget(self.btn_select_images)

        # FPS
        self.fps_label = QLabel("FPS (Frames por segundo):")
        layout.addWidget(self.fps_label)

        self.fps_input = QLineEdit("30")
        layout.addWidget(self.fps_input)

        # Audio opcional
        self.audio_label = QLabel("Archivo de audio (opcional):")
        layout.addWidget(self.audio_label)

        self.btn_select_audio = QPushButton("Seleccionar archivo de audio")
        self.btn_select_audio.clicked.connect(self.select_audio_file)
        layout.addWidget(self.btn_select_audio)

        # Formato de salida
        self.img_format_label = QLabel("Formato de salida:")
        layout.addWidget(self.img_format_label)

        self.img_format_combo = QComboBox()
        self.img_format_combo.clear()
        self.img_format_combo.addItems([
            "mp4 (H.264 8-bit)",
            "mp4 (H.265)",
            "mp4 (H.264 10-bit)",
            "avi",
            "mkv",
            "mov"
        ])
        layout.addWidget(self.img_format_combo)

        # Botón para iniciar la conversión
        self.btn_convert_images = QPushButton("Convertir imágenes a video")
        self.btn_convert_images.clicked.connect(self.convert_images_to_video)
        layout.addWidget(self.btn_convert_images)

        # Barra de progreso (oculta hasta que inicie la conversión)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Label de estado
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # Label para el enlace al video final (oculto por defecto)
        self.video_link_label = QLabel("")
        self.video_link_label.setOpenExternalLinks(True)
        self.video_link_label.setTextFormat(Qt.TextFormat.RichText)
        self.video_link_label.setVisible(False)
        layout.addWidget(self.video_link_label)

        self.setLayout(layout)

    def select_image_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de imágenes")
        if folder_path:
            self.img_seq_label.setText(f"Carpeta seleccionada: {folder_path}")
            self.image_folder = folder_path

    def select_audio_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Archivo de Audio",
            "",
            "Audio (*.mp3 *.wav *.aac)"
        )
        if file_path:
            self.audio_label.setText(f"Audio seleccionado: {file_path}")
            self.audio_path = file_path

    def convert_images_to_video(self):
        """
        Inicia el proceso de conversión en un hilo para no bloquear la interfaz.
        """
        if not hasattr(self, 'image_folder'):
            self.status_label.setText("Selecciona una carpeta de imágenes primero.")
            return

        # Leemos FPS y audio
        fps = self.fps_input.text()
        audio_path = getattr(self, 'audio_path', None)
        output_format = self.img_format_combo.currentText()

        # Contamos cuántas imágenes (asumiendo .png)
        images = sorted(os.listdir(self.image_folder))
        total_images = len([img for img in images if img.lower().endswith('.png')])
        if total_images == 0:
            self.status_label.setText("No se encontraron imágenes .png en la carpeta.")
            return

        # Construimos el comando ffmpeg
        command, output_file = convert_images_to_video_command(
            self.image_folder, fps, audio_path, output_format
        )
        if not command:
            self.status_label.setText("No se detectó el prefijo correcto en los archivos.")
            return

        # Creamos un hilo (Worker) para ejecutar ffmpeg y leer el progreso
        self.worker = FFmpegWorker(command, total_images, output_file)

        # Conectamos señales
        self.worker.progressChanged.connect(self.on_progress_changed)
        self.worker.finishedSignal.connect(self.on_conversion_finished)

        # Reiniciamos la barra y estado
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.video_link_label.setVisible(False)
        self.status_label.setText("Convirtiendo...")
        self.worker.start()

    def on_progress_changed(self, value):
        """Recibe la señal de progreso y actualiza la barra."""
        self.progress_bar.setValue(value)

    def on_conversion_finished(self, success, message):
        """
        Señal emitida cuando FFmpeg termina.
        'message' es la ruta del archivo de salida si success=True,
        o el texto del error si success=False.
        """
        if success:
            self.status_label.setText("Conversión completada.")
            self.progress_bar.setValue(100)

            # Mostramos enlace al video
            self.video_link_label.setText(
                f"<a href='file:///{message}'>Abrir video: {os.path.basename(message)}</a>"
            )
            self.video_link_label.setVisible(True)
        else:
            self.status_label.setText(f"Error: {message}")
            self.progress_bar.setValue(0)
            self.video_link_label.setVisible(False)

# -----------------------------------------------------------------
# CLASE QThread PARA EJECUTAR Y PARSEAR FFmpeg EN BACKGROUND (stderr)
# -----------------------------------------------------------------
class FFmpegWorker(QThread):
    progressChanged = pyqtSignal(int)
    finishedSignal = pyqtSignal(bool, str)

    def __init__(self, command, total_frames, output_file):
        """
        command: Lista de parámetros para subprocess (ffmpeg).
        total_frames: número total de frames/imágenes a procesar.
        output_file: ruta del archivo de salida final.
        """
        super().__init__()
        self.command = command
        self.total_frames = total_frames
        self.output_file = output_file

    def run(self):
        """
        Ejecuta FFmpeg y parsea su salida (stderr) en tiempo real
        para capturar "frame=   XXX" y así calcular el progreso.
        """
        proc = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            shell=False
            # En Windows, para evitar ventana CMD: 
            # creationflags=subprocess.CREATE_NO_WINDOW 
        )

        while True:
            line = proc.stderr.readline()
            if not line:
                break

            # Buscar "frame=    12"
            match = re.search(r"frame=\s*(\d+)", line)
            if match:
                current_frame = int(match.group(1))
                # Calculamos porcentaje en base a total_frames
                progress = int(current_frame / self.total_frames * 100)
                self.progressChanged.emit(progress)

        proc.wait()
        retcode = proc.returncode
        success = (retcode == 0)

        if success:
            # Si todo fue bien, emitimos la ruta del archivo final
            self.finishedSignal.emit(True, self.output_file)
        else:
            # Leemos el resto de stderr como error
            error_output = proc.stderr.read()
            self.finishedSignal.emit(False, error_output or "Error en FFmpeg.")
