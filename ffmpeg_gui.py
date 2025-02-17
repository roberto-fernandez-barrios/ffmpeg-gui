# ffmpeg_gui.py

import os
import re
import subprocess

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QLabel, QComboBox, QLineEdit, QProgressBar, QTabWidget, QGroupBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt

from ffmpeg_logic import convert_images_to_video_command

class FFmpegGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("FFmpeg GUI")
        self.setGeometry(100, 100, 500, 400)

        main_layout = QVBoxLayout()

        # Creamos el QTabWidget para organizar las secciones
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- Pestaña "Imágenes" ---
        self.tab_images = QWidget()
        self.init_tab_images()
        self.tabs.addTab(self.tab_images, "Imágenes")

        # --- Pestaña "Video" ---
        self.tab_video = QWidget()
        self.init_tab_video()  # Nueva función para inicializar la pestaña Video
        self.tabs.addTab(self.tab_video, "Video")

        self.setLayout(main_layout)

    def init_tab_images(self):
        layout = QVBoxLayout()

        # Grupo para seleccionar la carpeta de imágenes
        group_folder = QGroupBox("Selección de Imágenes")
        folder_layout = QVBoxLayout()
        self.img_seq_label = QLabel("Carpeta con imágenes:")
        folder_layout.addWidget(self.img_seq_label)
        self.btn_select_images = QPushButton("Seleccionar carpeta de imágenes")
        self.btn_select_images.clicked.connect(self.select_image_folder)
        folder_layout.addWidget(self.btn_select_images)
        group_folder.setLayout(folder_layout)
        layout.addWidget(group_folder)

        # Grupo para configurar parámetros (FPS, Audio, Formato)
        group_config = QGroupBox("Configuración de Conversión")
        config_layout = QVBoxLayout()
        
        # FPS
        self.fps_label = QLabel("FPS (Frames por segundo):")
        config_layout.addWidget(self.fps_label)
        self.fps_input = QLineEdit("30")
        config_layout.addWidget(self.fps_input)

        # CRF Editable (valor por defecto 19)
        self.crf_label = QLabel("CRF:")
        config_layout.addWidget(self.crf_label)
        self.crf_input = QLineEdit("19")
        config_layout.addWidget(self.crf_input)
        
        # Audio opcional
        self.audio_label = QLabel("Archivo de audio (opcional):")
        config_layout.addWidget(self.audio_label)
        self.btn_select_audio = QPushButton("Seleccionar archivo de audio")
        self.btn_select_audio.clicked.connect(self.select_audio_file)
        config_layout.addWidget(self.btn_select_audio)
        
        # Formato de salida
        self.img_format_label = QLabel("Formato de salida:")
        config_layout.addWidget(self.img_format_label)
        self.img_format_combo = QComboBox()
        self.img_format_combo.clear()
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
        
        # Grupo para el procesamiento y resultados
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
        
        self.image_video_link_label = QLabel("")
        self.image_video_link_label.setOpenExternalLinks(True)
        self.image_video_link_label.setTextFormat(Qt.TextFormat.RichText)
        self.image_video_link_label.setVisible(False)
        process_layout.addWidget(self.image_video_link_label)
        
        group_process.setLayout(process_layout)
        layout.addWidget(group_process)

        self.tab_images.setLayout(layout)

    def init_tab_video(self):
        layout = QVBoxLayout()

        # Grupo para seleccionar el video sin audio
        group_video = QGroupBox("Seleccionar video sin audio")
        video_layout = QVBoxLayout()
        self.video_file_label = QLabel("Video sin audio:")
        video_layout.addWidget(self.video_file_label)
        self.btn_select_video = QPushButton("Seleccionar video")
        self.btn_select_video.clicked.connect(self.select_video_file)
        video_layout.addWidget(self.btn_select_video)
        group_video.setLayout(video_layout)
        layout.addWidget(group_video)

        # Grupo para seleccionar el audio
        group_audio = QGroupBox("Seleccionar audio para agregar")
        audio_layout = QVBoxLayout()
        self.video_audio_label = QLabel("Archivo de audio:")
        audio_layout.addWidget(self.video_audio_label)
        self.btn_select_video_audio = QPushButton("Seleccionar audio")
        self.btn_select_video_audio.clicked.connect(self.select_video_audio_file)
        audio_layout.addWidget(self.btn_select_video_audio)
        group_audio.setLayout(audio_layout)
        layout.addWidget(group_audio)

        # Grupo para procesar la adición y mostrar resultados
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
        
        self.video_link_label = QLabel("")
        self.video_link_label.setOpenExternalLinks(True)
        self.video_link_label.setTextFormat(Qt.TextFormat.RichText)
        self.video_link_label.setVisible(False)
        process_layout.addWidget(self.video_link_label)
        
        group_process.setLayout(process_layout)
        layout.addWidget(group_process)

        self.tab_video.setLayout(layout)


    def show_video_tab(self):
        """Agrega la pestaña de Video si aún no existe y cambia a ella."""
        if self.tab_video is None:
            self.tab_video = QWidget()
            layout = QVBoxLayout()
            # Aquí puedes agregar los widgets que necesites para la sección Video
            lbl = QLabel("Aquí va la sección para trabajar con videos.")
            layout.addWidget(lbl)
            self.tab_video.setLayout(layout)
            self.tabs.addTab(self.tab_video, "Video")
        # Cambia a la pestaña Video
        index = self.tabs.indexOf(self.tab_video)
        self.tabs.setCurrentIndex(index)


    def select_video_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Video (sin audio)",
            "",
            "Videos (*.mp4 *.avi *.mkv *.mov)"
        )
        if file_path:
            self.video_file_label.setText(f"Video seleccionado: {file_path}")
            self.video_file = file_path

    def select_video_audio_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Archivo de Audio",
            "",
            "Audio (*.mp3 *.wav *.aac)"
        )
        if file_path:
            self.video_audio_label.setText(f"Audio seleccionado: {file_path}")
            self.video_audio_file = file_path

    def add_audio_to_video(self):
        """
        Inicia el proceso para agregar audio a un video sin audio.
        """
        if not hasattr(self, 'video_file'):
            self.video_status_label.setText("Selecciona un video primero.")
            return
        if not hasattr(self, 'video_audio_file'):
            self.video_status_label.setText("Selecciona un archivo de audio.")
            return

        # Construir el comando usando la nueva función de ffmpeg_logic
        from ffmpeg_logic import add_audio_to_video_command  # Asegúrate de importarlo
        command, output_file = add_audio_to_video_command(self.video_file, self.video_audio_file)
        if not command:
            self.video_status_label.setText("Error al construir el comando FFmpeg.")
            return

        # Usamos el mismo worker para ejecutar FFmpeg (puedes reutilizar FFmpegWorker)
        self.video_worker = FFmpegWorker(command, total_frames=100, output_file=output_file, enable_logs=False)
        # Nota: total_frames se usa solo para mostrar progreso; si no puedes estimarlo, puedes omitir el progreso o poner un valor fijo.
        self.video_worker.progressChanged.connect(self.on_video_progress_changed)
        self.video_worker.finishedSignal.connect(self.on_video_conversion_finished)

        self.video_progress_bar.setVisible(True)
        self.video_progress_bar.setValue(0)
        self.video_status_label.setText("Agregando audio al video...")
        self.video_worker.start()

    def on_video_progress_changed(self, value):
        self.video_progress_bar.setValue(value)

    def on_video_conversion_finished(self, success, message):
        if success:
            self.video_status_label.setText("Audio agregado con éxito.")
        else:
            self.video_status_label.setText(f"Error: {message}")
        self.video_progress_bar.setValue(100 if success else 0)


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

        fps = self.fps_input.text()
        audio_path = getattr(self, 'audio_path', None)
        user_format = self.img_format_combo.currentText()

        images = sorted(os.listdir(self.image_folder))
        total_images = len([img for img in images if img.lower().endswith('.png')])
        if total_images == 0:
            self.status_label.setText("No se encontraron imágenes .png en la carpeta.")
            return

        crf = self.crf_input.text()
        command, output_file = convert_images_to_video_command(
            self.image_folder, fps, audio_path, user_format, crf
        )
        if not command:
            self.status_label.setText("No se detectó el patrón correcto en las imágenes.")
            return

        self.worker = FFmpegWorker(command, total_images, output_file, enable_logs=False)
        self.worker.progressChanged.connect(self.on_progress_changed)
        self.worker.finishedSignal.connect(self.on_conversion_finished)

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.image_video_link_label.setVisible(False)
        self.status_label.setText("Convirtiendo...")
        self.worker.start()

    def on_progress_changed(self, value):
        self.progress_bar.setValue(value)

    def on_conversion_finished(self, success, message):
        if success:
            self.status_label.setText("Conversión completada.")
            self.progress_bar.setValue(100)
            # Verifica que 'message' contenga la ruta correcta del video generado
            if message and os.path.exists(message):
                self.image_video_link_label.setText(
                    f"<a href='file:///{message}'>Abrir video: {os.path.basename(message)}</a>"
                )
                self.image_video_link_label.setVisible(True)
            else:
                self.image_video_link_label.setText("Video generado, pero no se encontró la ruta.")
                self.image_video_link_label.setVisible(True)
        else:
            self.status_label.setText(f"Error: {message}")
            self.progress_bar.setValue(0)
            self.image_video_link_label.setVisible(False)


    def on_video_conversion_finished(self, success, message):
        if success:
            self.video_status_label.setText("Audio agregado con éxito.")
            self.video_link_label.setText(
                f"<a href='file:///{message}'>Abrir video: {os.path.basename(message)}</a>"
            )
            self.video_link_label.setVisible(True)
        else:
            self.video_status_label.setText(f"Error: {message}")
            self.video_link_label.setVisible(False)
        self.video_progress_bar.setValue(100 if success else 0)

# -----------------------------------------------------------------
# Clase Worker para ejecutar FFmpeg (con opción de log)
# -----------------------------------------------------------------
class FFmpegWorker(QThread):
    progressChanged = pyqtSignal(int)
    finishedSignal = pyqtSignal(bool, str)

    if __import__('sys').platform.startswith("win"):
        CREATE_NO_WINDOW = 0x08000000
    else:
        CREATE_NO_WINDOW = 0

    def __init__(self, command, total_frames, output_file, enable_logs=False):
        super().__init__()
        self.command = command
        self.total_frames = total_frames
        self.output_file = output_file
        self.enable_logs = enable_logs

    def run(self):
        proc = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            shell=False,
            creationflags=self.CREATE_NO_WINDOW
        )

        if self.enable_logs:
            log_file = open("ffmpeg.log", "a", encoding="utf-8")
            log_file.write("\n=== Iniciando FFmpeg Worker ===\n")
            log_file.write("Comando: " + " ".join(self.command) + "\n\n")

        while True:
            line = proc.stderr.readline()
            if not line:
                break

            if self.enable_logs:
                log_file.write(line)

            match = re.search(r"frame=\s*(\d+)", line)
            if match:
                current_frame = int(match.group(1))
                progress = int(current_frame / self.total_frames * 100)
                self.progressChanged.emit(progress)

        proc.wait()
        retcode = proc.returncode
        success = (retcode == 0)

        if not success:
            error_output = proc.stderr.read()
            if self.enable_logs and error_output:
                log_file.write(error_output)
        else:
            error_output = ""

        if self.enable_logs:
            log_file.write(f"=== Proceso finalizado. Return code: {retcode} ===\n\n")
            log_file.close()

        if success:
            self.finishedSignal.emit(True, self.output_file)
        else:
            self.finishedSignal.emit(False, error_output or "Error en FFmpeg.")
