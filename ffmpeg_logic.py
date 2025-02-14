# ffmpeg_logic.py

import os
import re

def detect_image_prefix(folder_path):
    """
    Detecta un prefijo del tipo 'algo_0001.png'.
    Retorna (prefix, True) si lo encuentra, (None, False) si no.
    """
    files = sorted(os.listdir(folder_path))
    if not files:
        return None, False

    match = re.match(r"(.+_)(\d{4})", files[0])
    if not match:
        return None, False

    prefix = match.group(1)
    return prefix, True


def convert_images_to_video_command(folder_path, fps, audio_path=None, output_format="mp4"):
    """
    Construye el comando ffmpeg (en forma de lista) para generar un video
    desde una secuencia de imágenes (prefijo%04d.png). Devuelve:
      - command: lista con los parámetros para subprocess
      - output_file: ruta final del video
    NO ejecuta ffmpeg, solo prepara el comando.
    """
    # Detectar prefijo
    prefix, is_valid = detect_image_prefix(folder_path)
    if not is_valid:
        # Si no se detectó patrón, devolvemos listas vacías
        return [], ""

    # Nombre de salida
    output_file = os.path.join(folder_path, f"video_output.{output_format}")

    # Construcción del comando
    command = [
        "ffmpeg",
        "-y",                # -y para sobrescribir sin preguntar
        "-framerate", str(fps),
        "-i", os.path.join(folder_path, f"{prefix}%04d.png"),
    ]

    # Si hay audio, lo añadimos como otra entrada
    if audio_path:
        command.extend(["-i", audio_path])

    # Ajustes de video
    command.extend([
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p"
    ])

    # Ajustes de audio (si se incluyó)
    if audio_path:
        command.extend([
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest"  # Recorta el audio a la duración del video
        ])

    command.append(output_file)

    return command, output_file
