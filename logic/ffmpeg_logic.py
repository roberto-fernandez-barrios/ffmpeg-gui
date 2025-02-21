# logic/ffmpeg_logic.py
"""
Módulo que contiene funciones para construir comandos FFmpeg para diversas operaciones:
- Convertir una secuencia de imágenes en un video.
- Agregar audio a un video.
- Cortar un video.
"""

import os
import re
import time

def get_unique_filename(file_path):
    """
    Si el archivo 'file_path' ya existe, genera un nombre único añadiendo un timestamp.
    Retorna el nombre de archivo único.
    """
    if not os.path.exists(file_path):
        return file_path
    base, ext = os.path.splitext(file_path)
    # Agregamos un timestamp para crear un nombre único
    timestamp = int(time.time())
    new_file_path = f"{base}_{timestamp}{ext}"
    # En caso de que por alguna razón el nombre siga existiendo, se repite el proceso.
    while os.path.exists(new_file_path):
        timestamp = int(time.time())
        new_file_path = f"{base}_{timestamp}{ext}"
    return new_file_path

def detect_image_prefix(folder_path):
    """
    Detecta un prefijo común en los nombres de archivos de imagen (por ejemplo, 'algo_0001.png').
    Retorna (prefix, True) si lo encuentra, o (None, False) si no.
    """
    files = sorted(os.listdir(folder_path))
    if not files:
        return None, False

    match = re.match(r"(.+_)(\d{4})", files[0])
    if not match:
        return None, False

    prefix = match.group(1)
    return prefix, True

def convert_images_to_video_command(folder_path, fps, audio_path=None, user_format="mp4 (H.264 8-bit)",
                                    crf="19", fade_in_duration=1, fade_out_duration=1, pix_fmt=None):
    """
    Construye un comando FFmpeg para convertir una secuencia de imágenes en un video.
    
    Parámetros:
        folder_path: Carpeta que contiene la secuencia de imágenes.
        fps: Frames por segundo para el video de salida.
        audio_path: Ruta opcional a un archivo de audio.
        user_format: Formato y códec de salida (por ejemplo, "mp4 (H.264 8-bit)", "mp4 (H.265 10-bit)", etc).
        crf: Factor de tasa constante para la calidad del video.
        fade_in_duration: Duración del fundido de entrada.
        fade_out_duration: Duración del fundido de salida.
        pix_fmt: (Opcional) Formato de pixel YUV deseado, ej. "yuv420p", "yuv422p" o "yuv444p". 
                 Si se especifica, se usará para la opción -pix_fmt, independientemente del bit depth.
    
    Retorna:
        (command, output_file) donde command es una lista de argumentos FFmpeg y
        output_file es la ruta del video generado.
    """
    import os, re, time
    files = sorted(os.listdir(folder_path))
    if not files:
        return [], ""
    match = re.match(r"(.+_)(\d+)", files[0])
    if not match:
        return [], ""
    prefix = match.group(1)
    width = len(match.group(2))  # Número de dígitos en la numeración

    # Filtra solo imágenes .png que inicien con el prefijo detectado
    images = [f for f in os.listdir(folder_path)
              if f.lower().endswith('.png') and f.startswith(prefix)]
    num_images = len(images)

    try:
        fps_val = float(fps)
    except ValueError:
        fps_val = 30.0
    duration = num_images / fps_val if fps_val > 0 else 0

    # Determina la extensión de salida según el formato seleccionado
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

    # Construye la ruta del archivo de salida y genera un nombre único si es necesario
    output_file = os.path.join(folder_path, f"{prefix}video.{extension}")
    output_file = get_unique_filename(output_file)

    # Construye el patrón de entrada para las imágenes
    image_pattern = os.path.join(folder_path, f"{prefix}%0{width}d.png")
    command = [
        "ffmpeg",
        "-y",  # Sobrescribe sin preguntar
        "-framerate", str(fps),
        "-i", image_pattern
    ]

    if audio_path:
        command.extend(["-i", audio_path])

    # Selección del códec y pixel format. Si pix_fmt está definido, se usa ese valor;
    # de lo contrario, se asigna un valor por defecto según el user_format y bit depth.
    if user_format == "mp4 (H.265 8-bit)":
        default_fmt = "yuv420p"
        chosen_fmt = pix_fmt if pix_fmt else default_fmt
        command.extend(["-c:v", "libx265", "-pix_fmt", chosen_fmt, "-crf", crf])
    elif user_format == "mp4 (H.265 10-bit)":
        default_fmt = "yuv420p10le"
        chosen_fmt = pix_fmt if pix_fmt else default_fmt
        command.extend(["-c:v", "libx265", "-pix_fmt", chosen_fmt, "-crf", crf])
    elif user_format == "mp4 (H.265 16-bit)":
        default_fmt = "yuv420p16le"
        chosen_fmt = pix_fmt if pix_fmt else default_fmt
        command.extend(["-c:v", "libx265", "-pix_fmt", chosen_fmt, "-crf", crf])
    elif user_format == "mp4 (H.264 10-bit)":
        default_fmt = "yuv420p10le"
        chosen_fmt = pix_fmt if pix_fmt else default_fmt
        command.extend(["-c:v", "libx264", "-pix_fmt", chosen_fmt, "-crf", crf])
    elif user_format == "mp4 (H.264 16-bit)":
        default_fmt = "yuv420p16le"
        chosen_fmt = pix_fmt if pix_fmt else default_fmt
        command.extend(["-c:v", "libx264", "-pix_fmt", chosen_fmt, "-crf", crf])
    elif user_format == "mp4 (H.264 8-bit)" or user_format.lower().startswith("mp4"):
        default_fmt = "yuv420p"
        chosen_fmt = pix_fmt if pix_fmt else default_fmt
        command.extend(["-c:v", "libx264", "-pix_fmt", chosen_fmt, "-crf", crf])
    else:
        default_fmt = "yuv420p"
        chosen_fmt = pix_fmt if pix_fmt else default_fmt
        command.extend(["-c:v", "libx264", "-pix_fmt", chosen_fmt, "-crf", crf])

    # Agrega filtros de fundido si la duración lo permite
    if duration > (fade_in_duration + fade_out_duration):
        fade_filter = f"fade=t=in:st=0:d={fade_in_duration},fade=t=out:st={duration - fade_out_duration}:d={fade_out_duration}"
        command.extend(["-vf", fade_filter])

    if audio_path:
        command.extend(["-c:a", "aac", "-b:a", "192k", "-shortest"])

    command.append(output_file)

    # Para debugging: muestra en consola el comando construido
    print(" ".join(command))

    return command, output_file



def add_audio_to_video_command(video_path, audio_path, output_format="mp4"):
    """
    Construye un comando FFmpeg para agregar audio a un video sin sonido.
    
    Parámetros:
        video_path: Ruta al video sin audio.
        audio_path: Ruta al archivo de audio.
        output_format: Formato de salida deseado.
    
    Retorna:
        (command, output_file) con el comando FFmpeg y la ruta del video de salida.
    """
    output_file = video_path.rsplit('.', 1)[0] + "_CON_AUDIO." + output_format
    # Renombra si ya existe
    output_file = get_unique_filename(output_file)
    command = [
        "ffmpeg",
        "-y",               # Sobrescribe sin preguntar
        "-i", video_path,   # Video sin audio
        "-i", audio_path,   # Audio a agregar
        "-c:v", "copy",     # Copia el video sin reencodear
        "-c:a", "aac",      # Reencodea el audio a AAC
        "-b:a", "192k",     # Bitrate del audio
        "-shortest",
        output_file
    ]
    return command, output_file

def cut_video_command(video_path, start_time, duration=None, end_time=None, output_format="mp4"):
    """
    Construye un comando FFmpeg para cortar un segmento de un video.
    
    Parámetros:
        video_path: Ruta al video de entrada.
        start_time: Tiempo de inicio para el corte (segundos o hh:mm:ss).
        duration: Duración del segmento a cortar (opcional).
        end_time: Tiempo final del corte (opcional; si se usa, se calcula la duración).
        output_format: Formato de salida del video cortado.
    
    Retorna:
        (command, output_file) con el comando FFmpeg y la ruta del video cortado.
    """
    base = os.path.splitext(video_path)[0]
    output_file = f"{base}_cut.mp4"
    # Renombra el archivo de salida si ya existe
    output_file = get_unique_filename(output_file)

    command = ["ffmpeg", "-y", "-ss", str(start_time), "-i", video_path]

    if end_time:
        # Convierte start_time y end_time a segundos y calcula la duración real
        start_seconds = parse_time_to_seconds(start_time)
        end_seconds = parse_time_to_seconds(end_time)
        real_duration = max(0, end_seconds - start_seconds)  # Asegura duración positiva
        command.extend(["-t", str(real_duration)])
    elif duration:
        command.extend(["-t", str(duration)])

    command.extend(["-c", "copy", output_file])
    return command, output_file

def parse_time_to_seconds(time_str):
    """
    Convierte una cadena de tiempo en formato 'hh:mm:ss' o segundos en un entero de segundos.
    """
    if ":" in time_str:
        parts = list(map(int, time_str.split(":")))
        return sum(x * 60 ** i for i, x in enumerate(reversed(parts)))
    return int(time_str)


def limit_kps_command(input_file, video_bitrate="57M", maxrate="60M", output_format="mp4"):
    """
    Construye un comando FFmpeg para limitar los kps (bitrate de video).

    Parámetros:
        input_file: Ruta del video de entrada.
        video_bitrate: Bitrate de video deseado (ej. '57M').
        maxrate: Tasa máxima de bits (ej. '60M').
        output_format: Formato de salida del video.

    Retorna:
        (command, output_file) donde command es una lista de argumentos para FFmpeg
        y output_file es la ruta del video generado.
    """
    import os
    # Se obtiene la ruta base y se genera un nombre único para el video de salida
    base = os.path.splitext(input_file)[0]
    output_file = f"{base}_limited.{output_format}"
    output_file = get_unique_filename(output_file)

    command = [
        "ffmpeg",
        "-y",              # Sobrescribe sin preguntar
        "-i", input_file,
        "-c:v", "libx264",
        "-b:v", video_bitrate,
        "-maxrate", maxrate,
        output_file
    ]
    print(" ".join(command))
    return command, output_file

def scale_video_command(input_file, scale_width, scale_height, preset="slow", crf="18", output_format="mp4"):
    """
    Construye un comando FFmpeg para reescalar un video sin recortar, lo que implica que se deforme si es necesario.
    
    Parámetros:
        input_file: Ruta del video de entrada.
        scale_width: Ancho deseado para el video escalado.
        scale_height: Altura deseada para el video escalado.
        preset: Preset de FFmpeg para la codificación (por defecto "slow").
        crf: Factor de tasa constante para la calidad (por defecto "18").
        output_format: Formato de salida del video (por defecto "mp4").
        
    Retorna:
        (command, output_file) donde command es la lista de argumentos FFmpeg y 
        output_file es la ruta del video generado.
    """
    import os
    # Construye el nombre de salida basado en el video de entrada y agrega un sufijo
    base = os.path.splitext(input_file)[0]
    output_file = f"{base}_scaled.{output_format}"
    output_file = get_unique_filename(output_file)
    
    # Construye la lista de argumentos para FFmpeg
    command = [
        "ffmpeg",
        "-y",                          # Sobrescribe sin preguntar
        "-i", input_file,              # Video de entrada
        "-vf", f"scale={scale_width}:{scale_height}",  # Filtro de escalado sin mantener aspecto
        "-preset", preset,             # Preset de codificación
        "-crf", crf,                   # Calidad de compresión
        output_file
    ]
    
    # Muestra el comando construido en la consola (útil para debugging)
    print(" ".join(command))
    
    return command, output_file

def crop_video_command(input_file, crop_top=0, crop_bottom=0, crop_left=0, crop_right=0, output_format="mp4"):
    """
    Construye un comando FFmpeg para recortar un video, eliminando partes de sus bordes.
    
    Parámetros:
      input_file: Ruta del video de entrada.
      crop_top: Píxeles a recortar desde la parte superior.
      crop_bottom: Píxeles a recortar desde la parte inferior.
      crop_left: Píxeles a recortar desde la parte izquierda.
      crop_right: Píxeles a recortar desde la parte derecha.
      output_format: Formato de salida del video (por defecto "mp4").
    
    Retorna:
      (command, output_file) donde command es la lista de argumentos FFmpeg y 
      output_file es la ruta del video recortado.
      
    Ejemplo:
      Si el video tiene una altura de 100 y se quiere recortar 20 píxeles de arriba y 10 de abajo,
      se llamaría: crop_video_command("input.mp4", crop_top=20, crop_bottom=10)
      Esto generará un video con altura = ih - (20+10).
    """
    import os
    # Construye el nombre de salida
    base = os.path.splitext(input_file)[0]
    output_file = f"{base}_cropped.{output_format}"
    output_file = get_unique_filename(output_file)
    
    # Construye el filtro de recorte:
    # El ancho resultante: iw - (crop_left + crop_right)
    # La altura resultante: ih - (crop_top + crop_bottom)
    # El offset x = crop_left y el offset y = crop_top
    crop_filter = f"crop=iw-{crop_left + crop_right}:ih-{crop_top + crop_bottom}:{crop_left}:{crop_top}"
    
    command = [
        "ffmpeg",
        "-y",  # Sobrescribe sin preguntar
        "-i", input_file,
        "-vf", crop_filter,
        output_file
    ]
    
    print(" ".join(command))
    return command, output_file

def remove_audio_command(video_path, output_format="mp4"):
    """
    Construye un comando FFmpeg para quitar el audio de un video.
    
    Parámetros:
        video_path: Ruta al video de entrada (con audio).
        output_format: Formato de salida del video (por defecto "mp4").
        
    Retorna:
        (command, output_file) donde command es la lista de argumentos FFmpeg y
        output_file es la ruta del video resultante sin audio.
        
    Comando de referencia:
        ffmpeg -y -i video_path -c:v copy -an output_file
    """
    import os
    base = os.path.splitext(video_path)[0]
    output_file = f"{base}_SIN_AUDIO.{output_format}"
    output_file = get_unique_filename(output_file)
    command = [
        "ffmpeg",
        "-y",                   # Sobrescribe sin preguntar
        "-i", video_path,       # Video de entrada
        "-c:v", "copy",         # Copia el video sin recodificar
        "-an",                  # Elimina el audio
        output_file
    ]
    print(" ".join(command))
    return command, output_file


def replace_audio_command(video_path, new_audio_path, output_format="mp4"):
    """
    Construye un comando FFmpeg para sustituir la pista de audio de un video por una nueva.
    
    Parámetros:
        video_path: Ruta al video original (con o sin audio).
        new_audio_path: Ruta al nuevo archivo de audio.
        output_format: Formato de salida del video (por defecto "mp4").
        
    Retorna:
        (command, output_file) donde command es la lista de argumentos FFmpeg y
        output_file es la ruta del video resultante con el nuevo audio.
        
    Comando de referencia:
        ffmpeg -y -i video_path -i new_audio_path -c:v copy -c:a aac -b:a 192k -map 0:v:0 -map 1:a:0 -shortest output_file
    """
    import os
    base = os.path.splitext(video_path)[0]
    output_file = f"{base}_REPLACE_AUDIO.{output_format}"
    output_file = get_unique_filename(output_file)
    command = [
        "ffmpeg",
        "-y",                   # Sobrescribe sin preguntar
        "-i", video_path,       # Video de entrada
        "-i", new_audio_path,   # Nuevo audio a incorporar
        "-c:v", "copy",         # Copia el video sin recodificar
        "-c:a", "aac",          # Codifica el audio a AAC
        "-b:a", "192k",         # Bitrate del audio
        "-map", "0:v:0",        # Selecciona el stream de video del primer input
        "-map", "1:a:0",        # Selecciona el stream de audio del segundo input
        "-shortest",            # Finaliza cuando el audio o video termine, el que ocurra primero
        output_file
    ]
    print(" ".join(command))
    return command, output_file
