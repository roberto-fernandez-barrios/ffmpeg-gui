# gui/tab_mixins.py
"""
Mixin compartido por las pestañas simples de gui/tabs/ (una única operación
FFmpeg por tarea, sin limpieza adicional de archivos temporales) para evitar
repetir en cada una: arranque del FFmpegWorker, callback de finalización con
enlace clicable al archivo de salida, y cancelación.

No lo usa merge_videos_tab.py: esa pestaña necesita borrar un archivo de
concat temporal al terminar/cancelar, y forzar ese caso en el mixin genérico
complicaría la lógica sin quitar apenas duplicación real.
"""

import os
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFontMetrics

from logic.ffmpeg_worker import FFmpegWorker


class FfmpegTaskMixin:
    """
    Requiere que la clase que la use tenga ya inicializado self.active_workers
    (lista) en su __init__.
    """

    def start_ffmpeg_task(self, task_widget, command, output_file, total_frames, task_prefix):
        """
        Crea el FFmpegWorker para `command`, lo registra en active_workers,
        conecta sus señales al task_widget (usando task_prefix para el
        nombre del enlace de salida) y lo arranca. Devuelve el worker.
        """
        worker = FFmpegWorker(command, total_frames=total_frames, output_file=output_file, enable_logs=False)
        self.active_workers.append(worker)

        worker.progressChanged.connect(lambda value: task_widget.update_progress(value))
        worker.finishedSignal.connect(
            lambda success, message: self.handle_ffmpeg_task_finished(
                task_widget, success, message, worker, task_prefix
            )
        )
        task_widget.cancelRequested.connect(lambda: self.cancel_ffmpeg_task(worker, task_widget))
        worker.start()
        return worker

    def handle_ffmpeg_task_finished(self, task_widget, success, message, worker, task_prefix):
        """Actualiza el widget de tarea según el resultado y libera la referencia al worker."""
        self.remove_worker_reference(worker)

        if success:
            task_widget.update_status("Completado")
            task_widget.update_progress(100)

            if message and os.path.exists(message):
                normalized_path = os.path.abspath(message).replace("\\", "/")
                full_text = task_prefix + os.path.basename(message)

                metrics = QFontMetrics(task_widget.name_label.font())
                elided = metrics.elidedText(full_text, Qt.TextElideMode.ElideMiddle, 200)
                link_html = f"<a style='color:blue; text-decoration:underline;' href='#'>{elided}</a>"

                task_widget.name_label.setText(link_html)
                task_widget.name_label.setToolTip(full_text)
                task_widget.name_label.linkActivated.connect(
                    lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(normalized_path))
                )
            else:
                task_widget.update_status("Completado, pero no se encontró la ruta.")
        elif str(message).lower() == "cancelado":
            task_widget.update_status("Cancelado")
            task_widget.update_progress(0)
        else:
            task_widget.update_status(f"Error: {message}")
            task_widget.update_progress(0)

    def cancel_ffmpeg_task(self, worker, task_widget):
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
