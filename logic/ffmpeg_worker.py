# logic/ffmpeg_worker.py
"""
Módulo que contiene la clase FFmpegWorker.
Esta clase extiende QThread para ejecutar comandos FFmpeg en un hilo separado,
manteniendo la interfaz gráfica responsiva durante procesos largos.
"""

import subprocess
import re
import sys
from PyQt6.QtCore import QThread, pyqtSignal

class FFmpegWorker(QThread):
    """
    Worker que ejecuta un comando FFmpeg y emite señales para actualizar el progreso y notificar la finalización.
    """
    progressChanged = pyqtSignal(int)  # Señal para actualizar el progreso (en porcentaje)
    finishedSignal = pyqtSignal(bool, str)  # Señal que indica la finalización: (éxito, mensaje o ruta de salida)

    # En Windows se usa un flag para evitar que aparezca la consola
    if sys.platform.startswith("win"):
        CREATE_NO_WINDOW = 0x08000000
    else:
        CREATE_NO_WINDOW = 0

    def __init__(self, command, total_frames, output_file, enable_logs=False):
        """
        Inicializa el worker.
        
        Parámetros:
            command: Lista de argumentos para FFmpeg.
            total_frames: Estimación de frames totales para calcular el progreso.
            output_file: Ruta del archivo de salida.
            enable_logs: Si True, guarda logs del proceso FFmpeg.
        """
        super().__init__()
        self.command = command
        self.total_frames = total_frames
        self.output_file = output_file
        self.enable_logs = enable_logs

    def run(self):
        """
        Ejecuta el comando FFmpeg y emite señales según el progreso y al finalizar.
        """
        proc = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            shell=False,
            creationflags=self.CREATE_NO_WINDOW
        )

        # Si se habilitan logs, abre un archivo para escribir la salida de FFmpeg
        if self.enable_logs:
            log_file = open("ffmpeg.log", "a", encoding="utf-8")
            log_file.write("\n=== Iniciando FFmpeg Worker ===\n")
            log_file.write("Comando: " + " ".join(self.command) + "\n\n")

        # Lee la salida de stderr línea por línea para capturar el progreso
        while True:
            line = proc.stderr.readline()
            if not line:
                break

            if self.enable_logs:
                log_file.write(line)

            # Busca en la salida la información del frame actual
            match = re.search(r"frame=\s*(\d+)", line)
            if match:
                current_frame = int(match.group(1))
                progress = int(current_frame / self.total_frames * 100)
                self.progressChanged.emit(progress)

        proc.wait()
        retcode = proc.returncode
        success = (retcode == 0)

        if not success:
            error_output = proc.stderr.read()
            if self.enable_logs and error_output:
                log_file.write(error_output)
        else:
            error_output = ""

        if self.enable_logs:
            log_file.write(f"=== Proceso finalizado. Return code: {retcode} ===\n\n")
            log_file.close()

        # Emite la señal de finalización con el estado y mensaje (o ruta de salida en caso de éxito)
        if success:
            self.finishedSignal.emit(True, self.output_file)
        else:
            self.finishedSignal.emit(False, error_output or "Error en FFmpeg.")
