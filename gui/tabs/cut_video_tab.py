# gui/tabs/cut_video_tab.py
"""
CutVideoTab: Pestaña para cortar un video.
Permite seleccionar un video, definir el tiempo de inicio, duración o tiempo final,
y luego ejecutar el corte mediante FFmpeg.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QPushButton, QLabel, QLineEdit,
    QScrollArea, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

# Importa la función que construye el comando para cortar el video
from logic.ffmpeg_logic import cut_video_command
# Importa el worker para ejecutar FFmpeg
from logic.ffmpeg_worker import FFmpegWorker
# Importa el widget de tarea (usado para mostrar cada corte)
from gui.task_widget import ConversionTaskWidget

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
        group_process.setLayout(process_layout)
        layout.addWidget(group_process)

        # --- Grupo: Tareas de Corte ---
        group_tasks = QGroupBox("Tareas de Corte")
        self.tasks_layout = QVBoxLayout()
        # Alinea las tareas hacia la parte superior para que se vayan agregando de arriba hacia abajo
        self.tasks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        group_tasks.setLayout(self.tasks_layout)

        # Se usa un QScrollArea para que la lista de tareas sea desplazable
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        # Define un tamaño mínimo para el contenedor de tareas
        scroll_area.setMinimumHeight(100)
        scroll_content = QWidget()
        scroll_content.setLayout(self.tasks_layout)
        scroll_area.setWidget(scroll_content)

        layout.addWidget(group_tasks)
        layout.addWidget(scroll_area)

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
        construye el comando FFmpeg y arranca el worker, creando además un widget de tarea.
        """
        if not self.cut_video_file:
            error_widget = ConversionTaskWidget("Error: Sin video")
            error_widget.update_status("Selecciona un video primero.")
            self.tasks_layout.addWidget(error_widget)
            return

        start_time = self.cut_start_input.text().strip() or "0"
        duration = self.cut_duration_input.text().strip()
        end_time = self.cut_end_input.text().strip()

        # Genera el comando FFmpeg y obtiene la ruta de salida
        command, output_file = cut_video_command(
            self.cut_video_file,
            start_time,
            duration=duration or None,
            end_time=end_time or None
        )
        if not command:
            error_widget = ConversionTaskWidget("Error: Comando inválido")
            error_widget.update_status("Error al construir el comando FFmpeg.")
            self.tasks_layout.addWidget(error_widget)
            return

        # Crea el widget de tarea para mostrar el corte
        task_name = f"Corte: {os.path.basename(output_file)}"
        task_widget = ConversionTaskWidget(task_name)
        self.tasks_layout.addWidget(task_widget)

        # Crea y arranca el worker para ejecutar FFmpeg
        worker = FFmpegWorker(command, total_frames=100, output_file=output_file, enable_logs=False)
        worker.progressChanged.connect(lambda value: task_widget.update_progress(value))
        worker.finishedSignal.connect(lambda success, message: self.handle_cut_task_finished(task_widget, success, message))
        # Permite cancelar la tarea: se conecta la señal del widget a una función que llama a terminate()
        task_widget.cancelRequested.connect(lambda: self.cancel_cut_task(worker, task_widget))
        worker.start()

    def handle_cut_task_finished(self, task_widget, success, message):
        """Actualiza el widget de la tarea según el resultado del corte."""
        if success:
            task_widget.update_status("Completado")
            task_widget.update_progress(100)
            if message and os.path.exists(message):
                normalized_path = os.path.abspath(message).replace("\\", "/")
                # Se actualiza el texto para mostrar un enlace clicable con el nombre del archivo
                task_widget.name_label.setText(
                    f"<a style='color:blue; text-decoration:underline;' href='#'>{os.path.basename(message)}</a>"
                )
                task_widget.name_label.setToolTip(message)
                task_widget.name_label.linkActivated.connect(
                    lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(normalized_path))
                )
            else:
                task_widget.update_status("Corte completado, pero no se encontró la ruta.")
        elif message.lower() == "cancelado":
            task_widget.update_status(message)  # Sin "Error: ", solo muestra el mensaje
            task_widget.update_progress(0)
        else:
            task_widget.update_status(f"Error: {message}")  # Solo agrega "Error:" en errores reales
            task_widget.update_progress(0)

    def cancel_cut_task(self, worker, task_widget):
        """Cancela la tarea forzando la terminación del worker y actualizando el widget."""
        worker.cancel()  
        task_widget.update_status("Cancelado")
        task_widget.update_progress(0)
