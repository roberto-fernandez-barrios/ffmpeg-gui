# gui/tabs/crop_video_tab.py
"""
CropVideoTab: Pestaña para recortar un video.
Permite seleccionar un video y definir los valores de recorte (en píxeles) para la parte superior, inferior, izquierda y derecha,
generando un video recortado.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QPushButton, QLabel, QLineEdit, QFileDialog, QScrollArea
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFontMetrics

# Importa la función para construir el comando de recorte
from logic.ffmpeg_logic import crop_video_command
# Importa el worker para ejecutar FFmpeg
from logic.ffmpeg_worker import FFmpegWorker
# Importa el widget de tarea para mostrar el progreso
from gui.task_widget import ConversionTaskWidget

class CropVideoTab(QWidget):
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
        
        # --- Grupo: Parámetros de Recorte ---
        group_params = QGroupBox("Parámetros de Recorte")
        params_layout = QVBoxLayout()
        
        self.top_label = QLabel("Recortar arriba (px):")
        params_layout.addWidget(self.top_label)
        self.top_input = QLineEdit("0")
        params_layout.addWidget(self.top_input)
        
        self.bottom_label = QLabel("Recortar abajo (px):")
        params_layout.addWidget(self.bottom_label)
        self.bottom_input = QLineEdit("0")
        params_layout.addWidget(self.bottom_input)
        
        self.left_label = QLabel("Recortar izquierda (px):")
        params_layout.addWidget(self.left_label)
        self.left_input = QLineEdit("0")
        params_layout.addWidget(self.left_input)
        
        self.right_label = QLabel("Recortar derecha (px):")
        params_layout.addWidget(self.right_label)
        self.right_input = QLineEdit("0")
        params_layout.addWidget(self.right_input)
        
        group_params.setLayout(params_layout)
        layout.addWidget(group_params)
        
        # --- Botón para iniciar el recorte ---
        self.btn_crop_video = QPushButton("Recortar Video")
        self.btn_crop_video.clicked.connect(self.crop_video)
        layout.addWidget(self.btn_crop_video)
        
        # --- Grupo: Tareas de Recorte ---
        group_tasks = QGroupBox("Tareas de Recorte")
        self.tasks_layout = QVBoxLayout()
        self.tasks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        group_tasks.setLayout(self.tasks_layout)
        
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
            
    def crop_video(self):
        """Inicia el proceso de recorte del video según los parámetros indicados."""
        if not self.input_video:
            error_widget = ConversionTaskWidget("Error: Sin video")
            error_widget.update_status("Selecciona un video primero.")
            self.tasks_layout.addWidget(error_widget)
            return
        
        try:
            crop_top = int(self.top_input.text().strip())
            crop_bottom = int(self.bottom_input.text().strip())
            crop_left = int(self.left_input.text().strip())
            crop_right = int(self.right_input.text().strip())
        except ValueError:
            error_widget = ConversionTaskWidget("Error: Parámetros inválidos")
            error_widget.update_status("Los valores de recorte deben ser números.")
            self.tasks_layout.addWidget(error_widget)
            return
        
        command, output_file = crop_video_command(
            self.input_video,
            crop_top=crop_top,
            crop_bottom=crop_bottom,
            crop_left=crop_left,
            crop_right=crop_right
        )
        if not command:
            error_widget = ConversionTaskWidget("Error: Comando inválido")
            error_widget.update_status("Error al construir el comando FFmpeg.")
            self.tasks_layout.addWidget(error_widget)
            return
        
        task_name = f"Recorte: {os.path.basename(output_file)}"
        task_widget = ConversionTaskWidget(task_name)
        self.tasks_layout.addWidget(task_widget)
        
        worker = FFmpegWorker(command, total_frames=100, output_file=output_file, enable_logs=False)
        worker.progressChanged.connect(lambda value: task_widget.update_progress(value))
        worker.finishedSignal.connect(lambda success, message: self.handle_crop_task_finished(task_widget, success, message))
        task_widget.cancelRequested.connect(lambda: self.cancel_crop_task(worker, task_widget))
        worker.start()
        
    def handle_crop_task_finished(self, task_widget, success, message):
        """Actualiza el widget de la tarea según el resultado del recorte."""
        if success:
            task_widget.update_status("Completado")
            task_widget.update_progress(100)
            if message and os.path.exists(message):
                normalized_path = os.path.abspath(message).replace("\\", "/")
                full_name = os.path.basename(message)
                prefix = "Recorte: "
                full_text = prefix + full_name  # Texto completo con el prefijo
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
        
    def cancel_crop_task(self, worker, task_widget):
        """Cancela la tarea de recorte forzando la terminación del proceso."""
        worker.cancel()
        task_widget.update_status("Cancelado")
        task_widget.update_progress(0)
