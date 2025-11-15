# logic/ffmpeg_worker.py
"""
Módulo que contiene la clase FFmpegWorker.
Esta clase extiende QThread para ejecutar comandos FFmpeg en un hilo separado,
manteniendo la interfaz gráfica responsiva durante procesos largos.
Además, permite cancelar el proceso FFmpeg de forma segura, de modo que si se 
cancela la operación, se elimine el archivo de salida incompleto para evitar confusiones.
"""

import os
import subprocess
import re
import sys
from PyQt6.QtCore import QThread, pyqtSignal

class FFmpegWorker(QThread):
    """
    Worker que ejecuta un comando FFmpeg y emite señales para actualizar el progreso 
    y notificar la finalización. Permite cancelar la ejecución del proceso FFmpeg de forma segura,
    eliminando el archivo de salida incompleto en caso de cancelación.
    """
    progressChanged = pyqtSignal(int)  # Señal para actualizar el progreso (en porcentaje)
    finishedSignal = pyqtSignal(bool, str)  # Señal que indica la finalización: (éxito, mensaje o ruta de salida)

    # En Windows se usa un flag para evitar que aparezca la consola al iniciar el proceso
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
            enable_logs: Si True, guarda logs del proceso FFmpeg en un archivo.
        """
        super().__init__()
        self.command = command
        self.total_frames = total_frames
        self.output_file = output_file
        self.enable_logs = enable_logs
        self.proc = None       # Almacena la instancia del proceso FFmpeg para permitir su cancelación
        self.cancelled = False # Bandera para indicar si se ha solicitado la cancelación

    def run(self):
        """
        Ejecuta el comando FFmpeg y emite señales según el progreso y al finalizar.
        Se almacena la instancia del proceso en self.proc para permitir su cancelación.
        Si se cancela, se elimina el archivo de salida incompleto.
        """
        self.proc = subprocess.Popen(
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
            if self.cancelled and self.proc:
                # si ya se ha pedido cancelar, salimos del bucle
                break

            line = self.proc.stderr.readline()
            if not line:
                break

            if self.enable_logs:
                log_file.write(line)

            match = re.search(r"frame=\s*(\d+)", line)
            if match and self.total_frames and self.total_frames > 0:
                current_frame = int(match.group(1))
                progress = int(current_frame / self.total_frames * 100)
                if progress > 100:
                    progress = 100
                self.progressChanged.emit(progress)

        # Espera a que el proceso FFmpeg finalice y obtiene el código de retorno
        self.proc.wait()
        retcode = self.proc.returncode

        # Si se canceló la operación, consideramos el resultado como fallido
        success = (retcode == 0) and not self.cancelled

        # Si se canceló, se elimina el archivo de salida incompleto, si existe
        if self.cancelled and os.path.exists(self.output_file):
            try:
                os.remove(self.output_file)
            except Exception as e:
                if self.enable_logs:
                    log_file.write(f"Error al eliminar archivo cancelado: {e}\n")

        if not success:
            error_output = self.proc.stderr.read()
            if self.enable_logs and error_output:
                log_file.write(error_output)
        else:
            error_output = ""

        if self.enable_logs:
            log_file.write(f"=== Proceso finalizado. Return code: {retcode} ===\n\n")
            log_file.close()

        # Emite la señal de finalización con el estado y mensaje (o ruta de salida en caso de éxito)
        if self.cancelled:
            self.finishedSignal.emit(False, "Cancelado")
        elif success:
            self.finishedSignal.emit(True, self.output_file)
        else:
            self.finishedSignal.emit(False, error_output or "Error en FFmpeg.")
            
    def cancel(self):
        """
        Cancela la ejecución del proceso FFmpeg de forma segura.
        Se establece la bandera de cancelación y se fuerza la terminación del proceso.
        """
        self.cancelled = True
        if self.proc:
            try:
                self.proc.kill()  # Fuerza la finalización del proceso FFmpeg
            except Exception as e:
                print("Error al cancelar el proceso FFmpeg:", e)
