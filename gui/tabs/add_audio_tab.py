# gui/tabs/video_tab.py
"""
VideoTab: Pestaña para agregar audio a un video.
Permite seleccionar un video sin audio y un archivo de audio, y luego
combinar ambos mediante FFmpeg.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QPushButton, QLabel, QFileDialog,
    QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDesktopServices, QFontMetrics
from PyQt6.QtCore import QUrl

# Función que genera el comando para agregar audio
from logic.ffmpeg_logic import add_audio_to_video_command
# Worker para ejecutar FFmpeg
from logic.ffmpeg_worker import FFmpegWorker
# Widget de tarea (ya implementado en gui/task_widget.py)
from gui.task_widget import ConversionTaskWidget

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

        # --- Botón para iniciar el proceso ---
        self.btn_add_audio = QPushButton("Agregar audio al video")
        self.btn_add_audio.clicked.connect(self.add_audio_to_video)
        layout.addWidget(self.btn_add_audio)

        # --- Grupo: Tareas de Conversión ---
        group_tasks = QGroupBox("Tareas de Conversión")
        self.tasks_layout = QVBoxLayout()
        self.tasks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Alinea las tareas hacia arriba
        group_tasks.setLayout(self.tasks_layout)

        # QScrollArea para soportar múltiples tareas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        # Ajusta el tamaño mínimo del cuadro donde se muestran las tareas
        scroll_area.setMinimumHeight(100)

        scroll_content = QWidget()
        scroll_content.setLayout(self.tasks_layout)
        scroll_area.setWidget(scroll_content)

        layout.addWidget(group_tasks)
        layout.addWidget(scroll_area)

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
        Construye el comando FFmpeg y arranca un worker para ejecutar la tarea,
        creando además un widget de tarea que se añade al área de tareas.
        """
        if not self.video_file:
            error_widget = ConversionTaskWidget("Error: Sin video")
            error_widget.update_status("Selecciona un video primero.")
            self.tasks_layout.addWidget(error_widget)
            return
        if not self.video_audio_file:
            error_widget = ConversionTaskWidget("Error: Sin audio")
            error_widget.update_status("Selecciona un archivo de audio.")
            self.tasks_layout.addWidget(error_widget)
            return

        # Genera el comando FFmpeg y obtiene el archivo de salida
        command, output_file = add_audio_to_video_command(self.video_file, self.video_audio_file)
        if not command:
            error_widget = ConversionTaskWidget("Error: Comando inválido")
            error_widget.update_status("Error al construir el comando FFmpeg.")
            self.tasks_layout.addWidget(error_widget)
            return

        # Crea el widget de tarea para mostrar la conversión
        task_name = f"Video: {os.path.basename(output_file)}"
        task_widget = ConversionTaskWidget(task_name)
        self.tasks_layout.addWidget(task_widget)

        # Crea y configura el worker para ejecutar FFmpeg
        # En este caso, asignamos un total de 100 "frames" de referencia, ya que agregar audio suele ser un proceso rápido
        worker = FFmpegWorker(command, total_frames=100, output_file=output_file, enable_logs=False)
        worker.progressChanged.connect(lambda value: task_widget.update_progress(value))
        worker.finishedSignal.connect(lambda success, message: self.handle_video_task_finished(task_widget, success, message))
        # Permite cancelar la tarea mediante el botón del widget (advertencia: terminate() fuerza la terminación)
        task_widget.cancelRequested.connect(lambda: self.cancel_video_task(worker, task_widget))

        worker.start()

    def handle_video_task_finished(self, task_widget, success, message):
        """
        Actualiza el widget de la tarea según el resultado del proceso.
        Si es exitoso, actualiza el nombre para incluir un enlace clicable.
        """
        if success:
            task_widget.update_status("Completado")
            task_widget.update_progress(100)
            if message and os.path.exists(message):
                normalized_path = os.path.abspath(message).replace("\\", "/")
                full_name = os.path.basename(message)
                prefix = "Video: "  # Prefijo para tareas de video (adición de audio, etc.)
                full_text = prefix + full_name
                metrics = QFontMetrics(task_widget.name_label.font())
                elided = metrics.elidedText(full_text, Qt.TextElideMode.ElideMiddle, 200)
                link_html = f"<a style='color:blue; text-decoration:underline;' href='#'>{elided}</a>"
                task_widget.name_label.setText(link_html)
                task_widget.name_label.setToolTip(full_text)
                task_widget.name_label.linkActivated.connect(
                    lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(normalized_path))
                )
        elif message.lower() == "cancelado":
            task_widget.update_status(message)
            task_widget.update_progress(0)
        else:
            task_widget.update_status(f"Error: {message}")
            task_widget.update_progress(0)


    def cancel_video_task(self, worker, task_widget):
        """Cancela la tarea de conversión forzando la terminación del worker."""
        worker.cancel()
        task_widget.update_status("Cancelado")
        task_widget.update_progress(0)
