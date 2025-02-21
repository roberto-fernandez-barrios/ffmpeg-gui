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
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

# Importa la función que genera el comando FFmpeg para limitar kps
from logic.ffmpeg_logic import limit_kps_command
# Importa el worker para ejecutar FFmpeg
from logic.ffmpeg_worker import FFmpegWorker
# Importa el widget de tarea para gestionar el progreso de cada operación
from gui.task_widget import ConversionTaskWidget

class LimitKpsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.input_video = None
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

        # En este caso se usa total_frames=100 como referencia para el progreso
        worker = FFmpegWorker(command, total_frames=100, output_file=output_file, enable_logs=False)
        worker.progressChanged.connect(lambda value: task_widget.update_progress(value))
        worker.finishedSignal.connect(lambda success, message: self.handle_task_finished(task_widget, success, message))
        task_widget.cancelRequested.connect(lambda: self.cancel_task(worker, task_widget))
        worker.start()

    def handle_task_finished(self, task_widget, success, message):
        """Actualiza el widget de la tarea según el resultado del proceso."""
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
            task_widget.update_status(message)  # Evita agregar "Error: "
            task_widget.update_progress(0)
        else:
            task_widget.update_status(f"Error: {message}")  # Mantiene "Error:" en otros casos
            task_widget.update_progress(0)

    def cancel_task(self, worker, task_widget):
        """Cancela la tarea forzando la terminación del worker."""
        worker.cancel()
        task_widget.update_status("Cancelado")
        task_widget.update_progress(0)
