# gui/tabs/images_tab.py

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QPushButton, QLabel, QLineEdit,
    QComboBox, QFileDialog, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from gui.widgets import ClickableLabel  # Widget personalizado (si lo necesitas en otra parte)
from gui.task_widget import ConversionTaskWidget  # Nuestra nueva clase de tarea
from logic.ffmpeg_logic import convert_images_to_video_command
from logic.ffmpeg_worker import FFmpegWorker

class ImagesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.image_folder = None  # Ruta a la carpeta con imágenes
        self.audio_path = None    # Ruta opcional al archivo de audio
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Grupo: Selección de Imágenes
        group_folder = QGroupBox("Selección de Imágenes")
        folder_layout = QVBoxLayout()
        self.img_seq_label = QLabel("Carpeta con imágenes:")
        folder_layout.addWidget(self.img_seq_label)
        self.btn_select_images = QPushButton("Seleccionar carpeta de imágenes")
        self.btn_select_images.clicked.connect(self.select_image_folder)
        folder_layout.addWidget(self.btn_select_images)
        group_folder.setLayout(folder_layout)
        layout.addWidget(group_folder)

        # Grupo: Configuración de Conversión
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
        self.fade_in_input = QLineEdit("0")
        config_layout.addWidget(self.fade_in_input)

        # Configuración de fundido de salida (fade out)
        self.fade_out_label = QLabel("Fade Out (segundos):")
        config_layout.addWidget(self.fade_out_label)
        self.fade_out_input = QLineEdit("0")
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
            "mp4 (H.264 16-bit)",
            "mp4 (H.265 16-bit)",    
            "mp4 (H.265 10-bit)",
            "mp4 (H.264 10-bit)",
            "mp4 (H.264 8-bit)",
            "mp4 (H.265 8-bit)",
            "avi",
            "mkv",
            "mov"
        ])
        config_layout.addWidget(self.img_format_combo)

        # NUEVO: Selección del formato YUV
        self.yuv_label = QLabel("Formato YUV:")
        config_layout.addWidget(self.yuv_label)
        self.yuv_combo = QComboBox()
        self.yuv_combo.addItems(["yuv420p", "yuv422p", "yuv444p"])
        config_layout.addWidget(self.yuv_combo)

        group_config.setLayout(config_layout)
        layout.addWidget(group_config)

        # Botón para iniciar la conversión
        self.btn_convert_images = QPushButton("Convertir imágenes a video")
        self.btn_convert_images.clicked.connect(self.convert_images_to_video)
        layout.addWidget(self.btn_convert_images)

        # Área para mostrar las tareas de conversión activas
        group_tasks = QGroupBox("Tareas de Conversión")
        self.tasks_layout = QVBoxLayout()
        self.tasks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Alinea las tareas hacia arriba
        group_tasks.setLayout(self.tasks_layout)

        # Se usa un QScrollArea para que la lista sea desplazable en caso de muchas tareas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Establece un tamaño mínimo para que el cuadro sea más grande
        scroll_area.setMinimumHeight(100)

        scroll_content = QWidget()
        scroll_content.setLayout(self.tasks_layout)
        scroll_area.setWidget(scroll_content)

        layout.addWidget(group_tasks)
        layout.addWidget(scroll_area)

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
        Inicia la conversión de imágenes a video y crea una nueva tarea en la interfaz para mostrar su progreso.
        """
        if not self.image_folder:
            self.status_label.setText("Selecciona una carpeta de imágenes primero.")
            return

        fps = self.fps_input.text()
        audio_path = self.audio_path  # Puede ser None si no se seleccionó audio
        user_format = self.img_format_combo.currentText()
        
        # Se obtiene la selección del formato YUV
        selected_yuv = self.yuv_combo.currentText()

        # Resto del código de validación...
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

        # Construye el comando FFmpeg, pasando la selección de formato YUV
        command, output_file = convert_images_to_video_command(
            self.image_folder, fps, audio_path, user_format, crf, fade_in, fade_out, selected_yuv
        )
        if not command:
            self.status_label.setText("No se detectó el patrón correcto en las imágenes.")
            return

        # Se crea un widget de tarea para esta conversión
        task_name = f"Conversión: {os.path.basename(output_file)}"
        task_widget = ConversionTaskWidget(task_name)
        self.tasks_layout.addWidget(task_widget)

        # Se crea el worker que ejecutará FFmpeg para esta conversión
        worker = FFmpegWorker(command, total_images, output_file, enable_logs=False)
        # Conectamos la señal de progreso para actualizar la barra del widget de tarea
        worker.progressChanged.connect(lambda value: task_widget.update_progress(value))
        # Conectamos la señal de finalización para actualizar el estado del widget
        worker.finishedSignal.connect(lambda success, message: self.handle_task_finished(task_widget, success, message))
        # Permite cancelar la tarea: en este ejemplo se llama a terminate() (nota: no es lo ideal en producción)
        task_widget.cancelRequested.connect(lambda: self.cancel_conversion(worker, task_widget))

        worker.start()

    def handle_task_finished(self, task_widget, success, message):
        """Actualiza el widget de la tarea según el resultado de la conversión."""
        if success:
            task_widget.update_status("Completado")
            task_widget.update_progress(100)
        elif message.lower() == "cancelado":
            task_widget.update_status(message)  # Solo muestra "Proceso cancelado por el usuario."
            task_widget.update_progress(0)
        else:
            task_widget.update_status(f"Error: {message}")  # Mantiene "Error:" en otros casos
            task_widget.update_progress(0)

    def cancel_conversion(self, worker, task_widget):
        """
        Cancela la conversión forzando la terminación del worker y actualizando el widget de la tarea.
        """
        worker.cancel()  
        task_widget.update_status("Cancelado")
        task_widget.update_progress(0)
