# gui/tabs/scale_video_tab.py
"""
ScaleVideoTab: Pestaña para reescalar un video.
Permite seleccionar un video y configurar las dimensiones (ancho y alto),
así como los parámetros de codificación (preset y CRF), para reescalar el video.
El video se reescala sin recortar, lo que puede deformarlo si las proporciones cambian.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QPushButton, QLabel, QLineEdit,
    QFileDialog, QScrollArea, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

# Importa la función de lógica para escalar videos
from logic.ffmpeg_logic import scale_video_command
# Importa el worker para ejecutar FFmpeg
from logic.ffmpeg_worker import FFmpegWorker
# Importa el widget de tarea para mostrar el progreso
from gui.task_widget import ConversionTaskWidget

class ScaleVideoTab(QWidget):
    def __init__(self):
        super().__init__()
        self.input_video = None  # Ruta del video de entrada
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # --- Grupo: Selección de Video ---
        group_video = QGroupBox("Seleccionar Video")
        video_layout = QVBoxLayout()
        self.video_file_label = QLabel("Video de entrada:")
        video_layout.addWidget(self.video_file_label)
        self.btn_select_video = QPushButton("Seleccionar Video")
        self.btn_select_video.clicked.connect(self.select_video_file)
        video_layout.addWidget(self.btn_select_video)
        group_video.setLayout(video_layout)
        layout.addWidget(group_video)

        # --- Grupo: Parámetros de Escalado ---
        group_params = QGroupBox("Parámetros de Escalado")
        params_layout = QVBoxLayout()

        # Ancho deseado
        self.width_label = QLabel("Ancho deseado (px):")
        params_layout.addWidget(self.width_label)
        self.width_input = QLineEdit("2520")
        params_layout.addWidget(self.width_input)

        # Alto deseado
        self.height_label = QLabel("Alto deseado (px):")
        params_layout.addWidget(self.height_label)
        self.height_input = QLineEdit("5376")
        params_layout.addWidget(self.height_input)

        # Preset de codificación (usando QComboBox)
        self.preset_label = QLabel("Preset:")
        params_layout.addWidget(self.preset_label)
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "ultrafast", "superfast", "veryfast", "faster",
            "fast", "medium", "slow", "slower", "veryslow"
        ])
        # Selecciona por defecto "slow"
        self.preset_combo.setCurrentText("slow")
        params_layout.addWidget(self.preset_combo)


        # CRF
        self.crf_label = QLabel("CRF:")
        params_layout.addWidget(self.crf_label)
        self.crf_input = QLineEdit("19")
        params_layout.addWidget(self.crf_input)

        group_params.setLayout(params_layout)
        layout.addWidget(group_params)

        # --- Botón para iniciar el escalado ---
        self.btn_scale_video = QPushButton("Reescalar Video")
        self.btn_scale_video.clicked.connect(self.scale_video)
        layout.addWidget(self.btn_scale_video)

        # --- Grupo: Tareas de Escalado ---
        group_tasks = QGroupBox("Tareas de Escalado")
        self.tasks_layout = QVBoxLayout()
        self.tasks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Alinea los widgets desde arriba
        group_tasks.setLayout(self.tasks_layout)

        # QScrollArea para que la lista de tareas sea desplazable
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

    def scale_video(self):
        """
        Inicia el proceso de escalado del video.
        Recoge los parámetros configurados, construye el comando FFmpeg y lanza un worker,
        creando un widget de tarea para mostrar el progreso.
        """
        if not self.input_video:
            error_widget = ConversionTaskWidget("Error: Sin video")
            error_widget.update_status("Selecciona un video primero.")
            self.tasks_layout.addWidget(error_widget)
            return

        scale_width = self.width_input.text().strip()
        scale_height = self.height_input.text().strip()
        preset = self.preset_combo.currentText().strip()
        crf = self.crf_input.text().strip()

        # Validar que ancho y alto sean números
        if not scale_width.isdigit() or not scale_height.isdigit():
            error_widget = ConversionTaskWidget("Error: Parámetros inválidos")
            error_widget.update_status("El ancho y el alto deben ser números.")
            self.tasks_layout.addWidget(error_widget)
            return

        # Construye el comando FFmpeg para reescalar el video
        command, output_file = scale_video_command(
            self.input_video, scale_width, scale_height, preset, crf
        )
        if not command:
            error_widget = ConversionTaskWidget("Error: Comando inválido")
            error_widget.update_status("Error al construir el comando FFmpeg.")
            self.tasks_layout.addWidget(error_widget)
            return

        task_name = f"Reescalado: {os.path.basename(output_file)}"
        task_widget = ConversionTaskWidget(task_name)
        self.tasks_layout.addWidget(task_widget)

        # Usamos un valor de referencia para total_frames (p.ej. 100) ya que el escalado suele ser rápido.
        worker = FFmpegWorker(command, total_frames=100, output_file=output_file, enable_logs=False)
        worker.progressChanged.connect(lambda value: task_widget.update_progress(value))
        worker.finishedSignal.connect(lambda success, message: self.handle_scale_task_finished(task_widget, success, message))
        task_widget.cancelRequested.connect(lambda: self.cancel_scale_task(worker, task_widget))
        worker.start()

    def handle_scale_task_finished(self, task_widget, success, message):
        """Actualiza el widget de la tarea según el resultado del escalado."""
        if success:
            task_widget.update_status("Completado")
            task_widget.update_progress(100)
            if message and os.path.exists(message):
                normalized_path = os.path.abspath(message).replace("\\", "/")
                task_widget.name_label.setText(
                    f"<a style='color:blue; text-decoration:underline;' href='#'>{os.path.basename(message)}</a>"
                )
                task_widget.name_label.setToolTip(message)
                task_widget.name_label.linkActivated.connect(
                    lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(normalized_path))
                )
        elif message.lower() == "cancelado":
            task_widget.update_status(message)
            task_widget.update_progress(0)
        else:
            task_widget.update_status(f"Error: {message}")
            task_widget.update_progress(0)

    def cancel_scale_task(self, worker, task_widget):
        """Cancela la tarea de escalado forzando la terminación del proceso."""
        worker.cancel()
        task_widget.update_status("Proceso cancelado por el usuario.")
        task_widget.update_progress(0)
