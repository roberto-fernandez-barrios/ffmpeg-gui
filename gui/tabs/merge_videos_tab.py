# gui/tabs/merge_videos_tab.py
"""
MergeVideosTab: Pestaña para unir varios videos en uno solo.

Pensada para campañas con muchos clips (20-30 o más), permitiendo:
- Seleccionar múltiples vídeos.
- Reordenarlos.
- Arrastrarlos y soltarlos.
- Elegir entre:
    1) Unión rápida sin recodificar (muy rápida, requiere compatibilidad entre clips).
    2) Unión compatible recodificando (más lenta, más robusta).
"""

import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QPushButton, QLabel, QFileDialog,
    QScrollArea, QListWidget, QListWidgetItem, QHBoxLayout, QComboBox, QLineEdit
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFontMetrics

from logic.ffmpeg_worker import FFmpegWorker
from gui.task_widget import ConversionTaskWidget
from logic.ffmpeg_logic import merge_videos_command


class MergeVideosTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.input_videos = []   # Lista de rutas absolutas
        self.active_workers = [] # Referencias para evitar GC prematuro
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # --- Grupo: Selección de vídeos ---
        group_videos = QGroupBox("Seleccionar Videos")
        videos_layout = QVBoxLayout()

        self.videos_label = QLabel("Videos seleccionados: 0")
        videos_layout.addWidget(self.videos_label)

        self.btn_add_videos = QPushButton("Añadir Videos")
        self.btn_add_videos.clicked.connect(self.select_video_files)
        videos_layout.addWidget(self.btn_add_videos)

        self.video_list_widget = QListWidget()
        self.video_list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.video_list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.video_list_widget.model().rowsMoved.connect(self.sync_input_videos_from_widget)
        videos_layout.addWidget(self.video_list_widget)

        row_buttons = QHBoxLayout()

        self.btn_remove_selected = QPushButton("Quitar Seleccionados")
        self.btn_remove_selected.clicked.connect(self.remove_selected_videos)
        row_buttons.addWidget(self.btn_remove_selected)

        self.btn_move_up = QPushButton("Subir")
        self.btn_move_up.clicked.connect(self.move_selected_up)
        row_buttons.addWidget(self.btn_move_up)

        self.btn_move_down = QPushButton("Bajar")
        self.btn_move_down.clicked.connect(self.move_selected_down)
        row_buttons.addWidget(self.btn_move_down)

        self.btn_clear_videos = QPushButton("Limpiar Lista")
        self.btn_clear_videos.clicked.connect(self.clear_videos)
        row_buttons.addWidget(self.btn_clear_videos)

        videos_layout.addLayout(row_buttons)
        group_videos.setLayout(videos_layout)
        layout.addWidget(group_videos)

        # --- Grupo: Configuración de unión ---
        group_config = QGroupBox("Configuración de Unión")
        config_layout = QVBoxLayout()

        self.mode_label = QLabel("Modo de unión:")
        config_layout.addWidget(self.mode_label)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Rápido (sin recodificar)",
            "Compatible (recodificar)"
        ])
        self.mode_combo.currentTextChanged.connect(self.update_mode_visibility)
        config_layout.addWidget(self.mode_combo)

        self.output_name_label = QLabel("Nombre de salida (sin extensión, opcional):")
        config_layout.addWidget(self.output_name_label)

        self.output_name_input = QLineEdit("")
        config_layout.addWidget(self.output_name_input)

        self.preset_label = QLabel("Preset (solo modo compatible):")
        config_layout.addWidget(self.preset_label)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "ultrafast", "superfast", "veryfast", "faster",
            "fast", "medium", "slow", "slower", "veryslow"
        ])
        self.preset_combo.setCurrentText("slow")
        config_layout.addWidget(self.preset_combo)

        self.crf_label = QLabel("CRF (solo modo compatible):")
        config_layout.addWidget(self.crf_label)

        self.crf_input = QLineEdit("19")
        config_layout.addWidget(self.crf_input)

        group_config.setLayout(config_layout)
        layout.addWidget(group_config)

        # --- Botón de procesado ---
        self.btn_merge_videos = QPushButton("Unir Videos")
        self.btn_merge_videos.clicked.connect(self.merge_videos)
        layout.addWidget(self.btn_merge_videos)

        # --- Grupo: Tareas ---
        group_tasks = QGroupBox("Tareas de Unión")
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
        self.update_mode_visibility(self.mode_combo.currentText())

    # =========================================================
    # Selección y gestión de vídeos
    # =========================================================
    def select_video_files(self):
        """Abre un diálogo para seleccionar múltiples vídeos."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar Videos",
            "",
            "Videos (*.mp4 *.avi *.mkv *.mov)"
        )
        if file_paths:
            self.add_videos(file_paths)

    def add_videos(self, file_paths):
        """Añade vídeos a la lista, evitando duplicados exactos."""
        valid_exts = {".mp4", ".avi", ".mkv", ".mov"}
        existing = set(os.path.normcase(os.path.abspath(p)) for p in self.input_videos)

        for path in file_paths:
            abs_path = os.path.abspath(path)
            ext = os.path.splitext(abs_path)[1].lower()
            norm = os.path.normcase(abs_path)

            if ext not in valid_exts:
                continue
            if norm in existing:
                continue

            self.input_videos.append(abs_path)
            item = QListWidgetItem(os.path.basename(abs_path))
            item.setToolTip(abs_path)
            item.setData(Qt.ItemDataRole.UserRole, abs_path)
            self.video_list_widget.addItem(item)
            existing.add(norm)

        self.update_videos_label()

    def remove_selected_videos(self):
        """Elimina los vídeos seleccionados de la lista."""
        selected_items = self.video_list_widget.selectedItems()
        if not selected_items:
            return

        selected_paths = {
            item.data(Qt.ItemDataRole.UserRole)
            for item in selected_items
        }

        for item in selected_items:
            row = self.video_list_widget.row(item)
            self.video_list_widget.takeItem(row)

        self.input_videos = [p for p in self.input_videos if p not in selected_paths]
        self.update_videos_label()

    def clear_videos(self):
        """Limpia completamente la lista de vídeos."""
        self.input_videos = []
        self.video_list_widget.clear()
        self.update_videos_label()

    def move_selected_up(self):
        """Mueve hacia arriba el bloque de elementos seleccionados."""
        selected_rows = sorted(set(self.video_list_widget.row(item) for item in self.video_list_widget.selectedItems()))
        if not selected_rows or selected_rows[0] == 0:
            return

        for row in selected_rows:
            item = self.video_list_widget.takeItem(row)
            self.video_list_widget.insertItem(row - 1, item)
            item.setSelected(True)

        self.sync_input_videos_from_widget()

    def move_selected_down(self):
        """Mueve hacia abajo el bloque de elementos seleccionados."""
        selected_rows = sorted(
            set(self.video_list_widget.row(item) for item in self.video_list_widget.selectedItems()),
            reverse=True
        )
        if not selected_rows or selected_rows[0] == self.video_list_widget.count() - 1:
            return

        for row in selected_rows:
            item = self.video_list_widget.takeItem(row)
            self.video_list_widget.insertItem(row + 1, item)
            item.setSelected(True)

        self.sync_input_videos_from_widget()

    def sync_input_videos_from_widget(self, *args):
        """Sincroniza self.input_videos con el orden actual del QListWidget."""
        ordered_paths = []
        for i in range(self.video_list_widget.count()):
            item = self.video_list_widget.item(i)
            path = item.data(Qt.ItemDataRole.UserRole)
            if path:
                ordered_paths.append(path)
        self.input_videos = ordered_paths
        self.update_videos_label()

    def update_videos_label(self):
        """Actualiza el contador de vídeos seleccionados."""
        self.videos_label.setText(f"Videos seleccionados: {len(self.input_videos)}")

    # =========================================================
    # Drag & drop
    # =========================================================
    def dragEnterEvent(self, event):
        """
        Se llama cuando se arrastra un objeto sobre el widget.
        Si contiene archivos, se acepta la acción.
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """
        Se llama cuando se suelta un objeto sobre el widget.
        Añade a la lista los archivos de vídeo válidos.
        """
        if event.mimeData().hasUrls():
            paths = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    paths.append(file_path)
            self.add_videos(paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    # =========================================================
    # Configuración visual
    # =========================================================
    def update_mode_visibility(self, mode_text):
        """Muestra u oculta parámetros según el modo seleccionado."""
        compatible_mode = (mode_text == "Compatible (recodificar)")
        self.preset_label.setVisible(compatible_mode)
        self.preset_combo.setVisible(compatible_mode)
        self.crf_label.setVisible(compatible_mode)
        self.crf_input.setVisible(compatible_mode)

    # =========================================================
    # Procesado
    # =========================================================
    def merge_videos(self):
        """
        Inicia el proceso de unión de vídeos:
        - valida entrada
        - construye comando
        - crea tarea visual
        - lanza worker
        """
        if len(self.input_videos) < 2:
            error_widget = ConversionTaskWidget("Error: Vídeos insuficientes")
            error_widget.update_status("Selecciona al menos 2 vídeos.")
            self.tasks_layout.addWidget(error_widget)
            return

        mode_text = self.mode_combo.currentText()

        if mode_text == "Compatible (recodificar)":
            crf = self.crf_input.text().strip()
            if not crf.isdigit():
                error_widget = ConversionTaskWidget("Error: CRF inválido")
                error_widget.update_status("El CRF debe ser un número entero.")
                self.tasks_layout.addWidget(error_widget)
                return

        try:
            mode = "fast" if mode_text == "Rápido (sin recodificar)" else "compatible"

            command, output_file, concat_file, error_message = merge_videos_command(
                self.input_videos,
                mode=mode,
                output_name=self.output_name_input.text().strip(),
                preset=self.preset_combo.currentText(),
                crf=self.crf_input.text().strip(),
                output_format="mp4"
            )

            if not command:
                error_widget = ConversionTaskWidget("Error: Preparación de unión")
                error_widget.update_status(error_message or "No se pudo construir el comando FFmpeg.")
                self.tasks_layout.addWidget(error_widget)
                return

        except Exception as e:
            error_widget = ConversionTaskWidget("Error: Preparación de unión")
            error_widget.update_status(str(e))
            self.tasks_layout.addWidget(error_widget)
            return

        task_prefix = "Unión rápida: " if mode_text == "Rápido (sin recodificar)" else "Unión compatible: "
        task_name = task_prefix + os.path.basename(output_file)
        task_widget = ConversionTaskWidget(task_name)
        self.tasks_layout.addWidget(task_widget)

        # Progreso aproximado, siguiendo el patrón actual del proyecto
        worker = FFmpegWorker(command, total_frames=100, output_file=output_file, enable_logs=False)
        self.active_workers.append(worker)

        worker.progressChanged.connect(lambda value: task_widget.update_progress(value))
        worker.finishedSignal.connect(
            lambda success, message: self.handle_merge_task_finished(
                task_widget, success, message, concat_file, worker, task_prefix
            )
        )
        task_widget.cancelRequested.connect(
            lambda: self.cancel_merge_task(worker, task_widget, concat_file)
        )

        worker.start()

    def handle_merge_task_finished(self, task_widget, success, message, concat_file, worker, task_prefix):
        """
        Actualiza el widget de tarea al finalizar y limpia archivo temporal.
        """
        self.safe_remove_file(concat_file)
        self.remove_worker_reference(worker)

        if success:
            task_widget.update_status("Completado")
            task_widget.update_progress(100)

            if message and os.path.exists(message):
                normalized_path = os.path.abspath(message).replace("\\", "/")
                full_name = os.path.basename(message)
                full_text = task_prefix + full_name

                metrics = QFontMetrics(task_widget.name_label.font())
                elided = metrics.elidedText(full_text, Qt.TextElideMode.ElideMiddle, 200)
                link_html = f"<a style='color:blue; text-decoration:underline;' href='#'>{elided}</a>"

                task_widget.name_label.setText(link_html)
                task_widget.name_label.setToolTip(full_text)
                task_widget.name_label.linkActivated.connect(
                    lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(normalized_path))
                )

        elif str(message).lower() == "cancelado":
            task_widget.update_status("Cancelado")
            task_widget.update_progress(0)
        else:
            task_widget.update_status(f"Error: {message}")
            task_widget.update_progress(0)

    def cancel_merge_task(self, worker, task_widget, concat_file):
        """
        Cancela la tarea de unión.
        """
        worker.cancel()
        self.safe_remove_file(concat_file)
        task_widget.update_status("Cancelado")
        task_widget.update_progress(0)
        self.remove_worker_reference(worker)

    # =========================================================
    # Utilidades
    # =========================================================
    def safe_remove_file(self, file_path):
        """Elimina un archivo si existe, ignorando errores."""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

    def remove_worker_reference(self, worker):
        """Elimina la referencia al worker cuando finaliza."""
        try:
            if worker in self.active_workers:
                self.active_workers.remove(worker)
        except Exception:
            pass