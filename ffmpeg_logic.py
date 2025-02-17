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


def convert_images_to_video_command(folder_path, fps, audio_path=None, user_format="mp4 (H.264 8-bit)", crf="19"):
    """
    Construye el comando (lista) para generar un video a partir de una secuencia de imágenes
    usando FFmpeg.

    Parámetros:
      - folder_path: Carpeta que contiene las imágenes (ej. prefijo_0001.png, prefijo_0002.png, ...)
      - fps: Frames por segundo para el video.
      - audio_path: (Opcional) Ruta a un archivo de audio.
      - user_format: Opción de formato/códec, que puede ser:
          * "mp4 (H.264 8-bit)"
          * "mp4 (H.264 10-bit)"
          * "mp4 (H.265 8-bit)"
          * "mp4 (H.265 10-bit)"
          * "avi", "mkv", "mov", etc.
      - crf: Valor CRF a utilizar (por defecto "19").

    Retorna:
      - command: Lista de argumentos para FFmpeg.
      - output_file: Ruta al video generado.
    """
    import os
    import re

    # Detectar el prefijo basado en el primer archivo
    files = sorted(os.listdir(folder_path))
    if not files:
        return [], ""
    match = re.match(r"(.+_)(\d{4})", files[0])
    if not match:
        return [], ""
    prefix = match.group(1)

    # Determinar la extensión de salida
    if user_format.lower().startswith("mp4"):
        extension = "mp4"
    elif user_format.lower() == "avi":
        extension = "avi"
    elif user_format.lower() == "mkv":
        extension = "mkv"
    elif user_format.lower() == "mov":
        extension = "mov"
    else:
        extension = "mp4"  # Valor por defecto

    output_file = os.path.join(folder_path, f"video_output.{extension}")

    # Construir la base del comando
    command = [
        "ffmpeg",
        "-y",  # Sobrescribir sin preguntar
        "-framerate", str(fps),
        "-i", os.path.join(folder_path, f"{prefix}%04d.png")
    ]

    # Si se proporciona audio, añadirlo como segunda entrada
    if audio_path:
        command.extend(["-i", audio_path])

    # Seleccionar códec y pix_fmt en función de la opción seleccionada
    if user_format == "mp4 (H.265 8-bit)":
        command.extend(["-c:v", "libx265", "-pix_fmt", "yuv420p", "-crf", crf])
    elif user_format == "mp4 (H.265 10-bit)":
        command.extend(["-c:v", "libx265", "-pix_fmt", "yuv420p10le", "-crf", crf])
    elif user_format == "mp4 (H.264 10-bit)":
        command.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p10le", "-crf", crf])
    elif user_format == "mp4 (H.264 8-bit)" or user_format.lower().startswith("mp4"):
        # Aquí se asume por defecto H.264 8-bit si se especifica "mp4 (H.264 8-bit)"
        command.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", crf])
    else:
        # Para otros contenedores, asumimos H.264 8-bit
        command.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", crf])

    # Si se proporciona audio, agregar opciones de audio y cortar el audio a la duración del video
    if audio_path:
        command.extend([
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest"
        ])

    command.append(output_file)

    return command, output_file


# Agrega esta función en ffmpeg_logic.py

def add_audio_to_video_command(video_path, audio_path, output_format="mp4"):
    """
    Construye el comando para añadir audio a un video sin audio.
    El video de salida se guardará con el sufijo "_con_audio".
    """
    output_file = video_path.rsplit('.', 1)[0] + "_con_audio." + output_format
    command = [
        "ffmpeg",
        "-y",              # Sobrescribir sin preguntar
        "-i", video_path,  # Video sin audio
        "-i", audio_path,  # Audio a agregar
        "-c", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_file
    ]
    return command, output_file
