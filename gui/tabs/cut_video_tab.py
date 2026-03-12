# gui/tabs/cut_video_tab.py
"""
CutVideoTab: Pestaña para cortar un video.
Permite seleccionar un video, definir el inicio y la duración del corte
ya sea por tiempo (segundos o hh:mm:ss) o por frames (en cuyo caso se debe indicar FPS).
También permite añadir fundido a negro al principio y/o al final.
Luego ejecuta el corte mediante FFmpeg.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QPushButton, QLabel, QLineEdit,
    QScrollArea, QFileDialog, QComboBox
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFontMetrics

from logic.ffmpeg_logic import cut_video_command
from logic.ffmpeg_worker import FFmpegWorker
from gui.task_widget import ConversionTaskWidget


class CutVideoTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.cut_video_file = None
        self.active_workers = []
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

        self.cut_mode_label = QLabel("Modo de corte:")
        params_layout.addWidget(self.cut_mode_label)

        self.cut_mode_combo = QComboBox()
        self.cut_mode_combo.addItems(["Frames", "Tiempo"])
        self.cut_mode_combo.currentTextChanged.connect(self.update_mode_visibility)
        params_layout.addWidget(self.cut_mode_combo)

        self.cut_start_label = QLabel("Tiempo de inicio (segundos o hh:mm:ss):")
        params_layout.addWidget(self.cut_start_label)

        self.cut_start_input = QLineEdit("0")
        params_layout.addWidget(self.cut_start_input)

        self.fps_frame_label = QLabel("FPS (Del video de entrada):")
        params_layout.addWidget(self.fps_frame_label)

        self.fps_frame_input = QLineEdit("30")
        params_layout.addWidget(self.fps_frame_input)

        self.cut_duration_label = QLabel("Duración (segundos):")
        params_layout.addWidget(self.cut_duration_label)

        self.cut_duration_input = QLineEdit("")
        params_layout.addWidget(self.cut_duration_input)

        self.cut_end_label = QLabel("Tiempo final (segundos o hh:mm:ss, opcional):")
        params_layout.addWidget(self.cut_end_label)

        self.cut_end_input = QLineEdit("")
        params_layout.addWidget(self.cut_end_input)

        group_params.setLayout(params_layout)
        layout.addWidget(group_params)

        # --- Grupo: Fundidos ---
        group_fades = QGroupBox("Fundidos a Negro")
        fades_layout = QVBoxLayout()

        self.fade_in_label = QLabel("Fade in al inicio (segundos):")
        fades_layout.addWidget(self.fade_in_label)

        self.fade_in_input = QLineEdit("0")
        fades_layout.addWidget(self.fade_in_input)

        self.fade_out_label = QLabel("Fade out al final (segundos):")
        fades_layout.addWidget(self.fade_out_label)

        self.fade_out_input = QLineEdit("0")
        fades_layout.addWidget(self.fade_out_input)

        group_fades.setLayout(fades_layout)
        layout.addWidget(group_fades)

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
        self.update_mode_visibility(self.cut_mode_combo.currentText())

    def update_mode_visibility(self, mode):
        """Actualiza la visibilidad y el texto de los campos según el modo de corte."""
        if mode == "Tiempo":
            self.cut_start_label.setText("Tiempo de inicio (segundos o hh:mm:ss):")
            self.cut_end_label.show()
            self.cut_end_input.show()
            self.cut_duration_label.setText("Duración (segundos):")
            self.fps_frame_label.hide()
            self.fps_frame_input.hide()
        else:
            self.cut_start_label.setText("Inicio (frames):")
            self.cut_end_label.hide()
            self.cut_end_input.hide()
            self.cut_duration_label.setText("Cantidad de frames:")
            self.fps_frame_label.show()
            self.fps_frame_input.show()

    def select_cut_video_file(self):
        """Abre un diálogo para seleccionar el video que se desea cortar."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Video",
            "",
            "Videos (*.mp4 *.avi *.mkv *.mov)"
        )
        if file_path:
            self.cut_video_file_label.setText(
                f"Video: <span style='color:blue;'>{os.path.basename(file_path)}</span>"
            )
            self.cut_video_file = file_path

    def dragEnterEvent(self, event):
        """
        Se llama cuando se arrastra un objeto sobre el widget.
        Si el objeto contiene URLs (archivos), se acepta la acción.
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """
        Se llama cuando se suelta un objeto sobre el widget.
        Si el archivo soltado es un video, se asigna a self.cut_video_file.
        """
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                video_exts = [".mp4", ".avi", ".mkv", ".mov"]
                ext = os.path.splitext(file_path)[1].lower()
                if ext in video_exts:
                    self.cut_video_file = file_path
                    self.cut_video_file_label.setText(
                        f"Video: <span style='color:blue;'>{os.path.basename(file_path)}</span>"
                    )
            event.acceptProposedAction()
        else:
            event.ignore()

    def cut_video(self):
        """
        Inicia el proceso de corte de video.
        Recoge los parámetros según el modo seleccionado, construye el comando FFmpeg
        y arranca el worker, creando además un widget de tarea.
        """
        if not self.cut_video_file:
            error_widget = ConversionTaskWidget("Error: Sin video")
            error_widget.update_status("Selecciona un video primero.")
            self.tasks_layout.addWidget(error_widget)
            return

        mode = self.cut_mode_combo.currentText()
        cut_mode = "time" if mode == "Tiempo" else "frames"

        if cut_mode == "time":
            start_time = self.cut_start_input.text().strip() or "0"
            duration = self.cut_duration_input.text().strip() or None
            end_time = self.cut_end_input.text().strip() or None

        else:
            try:
                fps_value = float(self.fps_frame_input.text().strip())
                if fps_value <= 0:
                    raise ValueError
            except ValueError:
                error_widget = ConversionTaskWidget("Error: FPS inválido")
                error_widget.update_status("El valor de FPS debe ser un número mayor que 0.")
                self.tasks_layout.addWidget(error_widget)
                return

            try:
                start_frames = int(self.cut_start_input.text().strip())
            except ValueError:
                error_widget = ConversionTaskWidget("Error: Inicio inválido")
                error_widget.update_status("El inicio debe ser un número entero de frames.")
                self.tasks_layout.addWidget(error_widget)
                return

            start_time = str(start_frames / fps_value)

            raw_duration_frames = self.cut_duration_input.text().strip() or None
            if raw_duration_frames is not None:
                try:
                    duration_frames = int(raw_duration_frames)
                    if duration_frames <= 0:
                        raise ValueError
                except ValueError:
                    error_widget = ConversionTaskWidget("Error: Duración inválida")
                    error_widget.update_status("La cantidad de frames debe ser un entero mayor que 0.")
                    self.tasks_layout.addWidget(error_widget)
                    return

                # Para el cálculo correcto del fade en la lógica,
                # pasamos la duración convertida a segundos.
                duration = str(duration_frames / fps_value)
            else:
                duration = None

            end_time = None

        try:
            fade_in_duration = float(self.fade_in_input.text().strip() or "0")
            fade_out_duration = float(self.fade_out_input.text().strip() or "0")
        except ValueError:
            error_widget = ConversionTaskWidget("Error: Fundidos inválidos")
            error_widget.update_status("Los valores de fundido deben ser números.")
            self.tasks_layout.addWidget(error_widget)
            return

        if fade_in_duration < 0 or fade_out_duration < 0:
            error_widget = ConversionTaskWidget("Error: Fundidos inválidos")
            error_widget.update_status("Los fundidos no pueden ser negativos.")
            self.tasks_layout.addWidget(error_widget)
            return

        command, output_file = cut_video_command(
            self.cut_video_file,
            start_time,
            duration=duration,
            end_time=end_time,
            output_format="mp4",
            cut_mode="time",  # ya convertimos todo a tiempo real
            fade_in_duration=fade_in_duration,
            fade_out_duration=fade_out_duration
        )

        if not command:
            error_widget = ConversionTaskWidget("Error: Comando inválido")
            error_widget.update_status("Error al construir el comando FFmpeg.")
            self.tasks_layout.addWidget(error_widget)
            return

        task_name = f"Corte: {os.path.basename(output_file)}"
        task_widget = ConversionTaskWidget(task_name)
        self.tasks_layout.addWidget(task_widget)

        worker = FFmpegWorker(command, total_frames=100, output_file=output_file, enable_logs=False)
        self.active_workers.append(worker)

        worker.progressChanged.connect(lambda value: task_widget.update_progress(value))
        worker.finishedSignal.connect(
            lambda success, message: self.handle_cut_task_finished(task_widget, success, message, worker)
        )
        task_widget.cancelRequested.connect(lambda: self.cancel_cut_task(worker, task_widget))
        worker.start()

    def handle_cut_task_finished(self, task_widget, success, message, worker):
        """Actualiza el widget de la tarea según el resultado del corte."""
        self.remove_worker_reference(worker)

        if success:
            task_widget.update_status("Completado")
            task_widget.update_progress(100)

            if message and os.path.exists(message):
                normalized_path = os.path.abspath(message).replace("\\", "/")
                full_name = os.path.basename(message)
                prefix = "Corte: "
                full_text = prefix + full_name

                metrics = QFontMetrics(task_widget.name_label.font())
                elided = metrics.elidedText(full_text, Qt.TextElideMode.ElideMiddle, 200)
                link_html = f"<a style='color:blue; text-decoration:underline;' href='#'>{elided}</a>"

                task_widget.name_label.setText(link_html)
                task_widget.name_label.setToolTip(full_text)
                task_widget.name_label.linkActivated.connect(
                    lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(normalized_path))
                )
            else:
                task_widget.update_status("Corte completado, pero no se encontró la ruta.")

        elif str(message).lower() == "cancelado":
            task_widget.update_status("Cancelado")
            task_widget.update_progress(0)
        else:
            task_widget.update_status(f"Error: {message}")
            task_widget.update_progress(0)

    def cancel_cut_task(self, worker, task_widget):
        """Cancela la tarea forzando la terminación del worker y actualizando el widget."""
        worker.cancel()
        task_widget.update_status("Cancelado")
        task_widget.update_progress(0)
        self.remove_worker_reference(worker)

    def remove_worker_reference(self, worker):
        """Elimina la referencia al worker cuando finaliza o se cancela."""
        try:
            if worker in self.active_workers:
                self.active_workers.remove(worker)
        except Exception:
            pass