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


def convert_images_to_video_command(folder_path, fps, audio_path=None, user_format="mp4 (H.264 8-bit)"):
    """
    Construye el comando (en forma de lista) para generar un video
    desde una secuencia de imágenes (prefijo%04d.png) usando FFmpeg.

    Devuelve:
      - command: lista con los parámetros para subprocess.Popen
      - output_file: ruta final del video

    No ejecuta ffmpeg; solo retorna el comando.

    user_format puede ser:
      - "mp4 (H.264 8-bit)"
      - "mp4 (H.265)"
      - "mp4 (H.264 10-bit)"
      - "avi"
      - "mkv"
      - "mov"
    """
    # Detectar prefijo
    prefix, is_valid = detect_image_prefix(folder_path)
    if not is_valid:
        # Si no se detectó el patrón, devolvemos vacío
        return [], ""

    # Elegimos la extensión a partir del user_format.
    # (Si prefieres algo más sofisticado, puedes mapear cada caso)
    if user_format.startswith("mp4"):
        extension = "mp4"
    elif user_format == "avi":
        extension = "avi"
    elif user_format == "mkv":
        extension = "mkv"
    elif user_format == "mov":
        extension = "mov"
    else:
        extension = "mp4"  # valor por defecto

    output_file = os.path.join(folder_path, f"video_output.{extension}")

    command = [
        "ffmpeg",
        "-y",                # -y para sobrescribir sin preguntar
        "-framerate", str(fps),
        "-i", os.path.join(folder_path, f"{prefix}%04d.png"),
    ]

    # Si hay audio, lo añadimos
    if audio_path:
        command.extend(["-i", audio_path])

    # Ahora, definimos el códec según user_format
    if user_format == "mp4 (H.265)":
        # H.265 8 bits
        command.extend(["-c:v", "libx265", "-pix_fmt", "yuv420p"])
    elif user_format == "mp4 (H.264 10-bit)":
        # H.264 10 bits
        command.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p10le"])
    elif user_format.startswith("mp4 (H.264 8-bit)"):
        # MP4 H.264 8 bits
        command.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p"])
    else:
        # Formatos genéricos
        #s Asumimos H.264 8 bits
        command.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p"])

    # Ajustes de audio (si se incluyó)
    if audio_path:
        command.extend([
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest"  # recorta el audio a la duración del video
        ])

    command.append(output_file)

    return command, output_file
