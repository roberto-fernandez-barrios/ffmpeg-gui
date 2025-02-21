# gui/tabs/audio_editing_tab.py
"""
AudioEditingTab: Pestaña para la edición de audio de un video.
Permite seleccionar un video y, mediante un desplegable, elegir entre:
  - Añadir audio
  - Quitar audio
  - Sustituir audio

Según la operación, se habilita o se oculta la selección de un archivo de audio.
Se procesa la operación usando FFmpeg y se muestra el progreso en un widget de tarea.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QPushButton, QLabel, QFileDialog,
    QComboBox, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDesktopServices, QFontMetrics
from PyQt6.QtCore import QUrl
from logic.ffmpeg_worker import FFmpegWorker
from gui.task_widget import ConversionTaskWidget

# Asegúrate de tener estas funciones implementadas en logic/ffmpeg_logic.py
from logic.ffmpeg_logic import add_audio_to_video_command, remove_audio_command, replace_audio_command

class AudioEditingTab(QWidget):
    def __init__(self):
        super().__init__()
        self.video_file = None    # Video a editar
        self.audio_file = None    # Archivo de audio para añadir/sustituir
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Grupo: Selección de Video
        group_video = QGroupBox("Seleccionar Video")
        video_layout = QVBoxLayout()
        self.video_label = QLabel("Video:")
        video_layout.addWidget(self.video_label)
        self.btn_select_video = QPushButton("Seleccionar Video")
        self.btn_select_video.clicked.connect(self.select_video_file)
        video_layout.addWidget(self.btn_select_video)
        group_video.setLayout(video_layout)
        layout.addWidget(group_video)

        # Grupo: Selección de Operación
        group_operation = QGroupBox("Operación de Edición de Audio")
        op_layout = QVBoxLayout()
        op_layout.addWidget(QLabel("Selecciona la operación:"))
        self.operation_combo = QComboBox()
        self.operation_combo.addItems(["Añadir audio", "Quitar audio", "Sustituir audio"])
        self.operation_combo.currentIndexChanged.connect(self.operation_changed)
        op_layout.addWidget(self.operation_combo)
        group_operation.setLayout(op_layout)
        layout.addWidget(group_operation)

        # Grupo: Selección de Audio (visible solo para "Añadir audio" o "Sustituir audio")
        self.group_audio = QGroupBox("Seleccionar Audio")
        audio_layout = QVBoxLayout()
        self.audio_label = QLabel("Audio:")
        audio_layout.addWidget(self.audio_label)
        self.btn_select_audio = QPushButton("Seleccionar Archivo de Audio")
        self.btn_select_audio.clicked.connect(self.select_audio_file)
        audio_layout.addWidget(self.btn_select_audio)
        self.group_audio.setLayout(audio_layout)
        layout.addWidget(self.group_audio)

        # Botón para iniciar la operación
        self.btn_process = QPushButton("Procesar")
        self.btn_process.clicked.connect(self.process_audio_edit)
        layout.addWidget(self.btn_process)

        # Grupo: Tareas de Edición de Audio (área para mostrar tareas activas)
        group_tasks = QGroupBox("Tareas de Edición de Audio")
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
        # Actualiza la visibilidad del grupo de audio según la operación seleccionada
        self.operation_changed()

    def select_video_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Video", "", "Videos (*.mp4 *.avi *.mkv *.mov)"
        )
        if file_path:
            video_name = os.path.basename(file_path)
            self.video_label.setText(f"Video seleccionado: <span style='color:blue;'>{video_name}</span>")
            self.video_file = file_path

    def select_audio_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Archivo de Audio", "", "Audio (*.mp3 *.wav *.aac)"
        )
        if file_path:
            audio_name = os.path.basename(file_path)
            self.audio_label.setText(f"Audio seleccionado: <span style='color:blue;'>{audio_name}</span>")
            self.audio_file = file_path

    def operation_changed(self):
        """Actualiza la visibilidad del grupo de audio según la operación seleccionada."""
        op = self.operation_combo.currentText()
        if op == "Quitar audio":
            self.group_audio.hide()
        else:
            self.group_audio.show()

    def process_audio_edit(self):
        """Inicia la operación de edición de audio según la opción seleccionada."""
        if not self.video_file:
            error_widget = ConversionTaskWidget("Error: Sin video")
            error_widget.update_status("Selecciona un video primero.")
            self.tasks_layout.addWidget(error_widget)
            return

        op = self.operation_combo.currentText()
        if op in ["Añadir audio", "Sustituir audio"]:
            if not self.audio_file:
                error_widget = ConversionTaskWidget("Error: Sin audio")
                error_widget.update_status("Selecciona un archivo de audio.")
                self.tasks_layout.addWidget(error_widget)
                return

        # Selecciona el comando FFmpeg según la operación
        if op == "Añadir audio":
            command, output_file = add_audio_to_video_command(self.video_file, self.audio_file)
            task_prefix = "Añadir audio: "
        elif op == "Sustituir audio":
            command, output_file = replace_audio_command(self.video_file, self.audio_file)
            task_prefix = "Sustituir audio: "
        elif op == "Quitar audio":
            command, output_file = remove_audio_command(self.video_file)
            task_prefix = "Quitar audio: "
        else:
            return

        if not command:
            error_widget = ConversionTaskWidget("Error: Comando inválido")
            error_widget.update_status("Error al construir el comando FFmpeg.")
            self.tasks_layout.addWidget(error_widget)
            return

        task_name = task_prefix + os.path.basename(output_file)
        task_widget = ConversionTaskWidget(task_name)
        self.tasks_layout.addWidget(task_widget)
        # Usamos un valor de referencia para total_frames (por ejemplo, 100) ya que estas operaciones suelen ser rápidas.
        worker = FFmpegWorker(command, total_frames=100, output_file=output_file, enable_logs=False)
        worker.progressChanged.connect(lambda value: task_widget.update_progress(value))
        worker.finishedSignal.connect(lambda success, message: self.handle_audio_edit_finished(task_widget, success, message))
        task_widget.cancelRequested.connect(lambda: self.cancel_audio_edit(worker, task_widget))
        worker.start()

    def handle_audio_edit_finished(self, task_widget, success, message):
        """Actualiza el widget de la tarea según el resultado de la operación de edición de audio."""
        if success:
            task_widget.update_status("Completado")
            task_widget.update_progress(100)
            if message and os.path.exists(message):
                normalized_path = os.path.abspath(message).replace("\\", "/")
                full_name = os.path.basename(message)
                # Define el prefijo según la operación seleccionada
                op = self.operation_combo.currentText()
                prefix = ""
                if op == "Añadir audio":
                    prefix = "Añadir audio: "
                elif op == "Sustituir audio":
                    prefix = "Sustituir audio: "
                elif op == "Quitar audio":
                    prefix = "Quitar audio: "
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

    def cancel_audio_edit(self, worker, task_widget):
        worker.cancel()
        task_widget.update_status("Cancelado")
        task_widget.update_progress(0)
