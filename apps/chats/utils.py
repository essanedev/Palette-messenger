from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import os
import subprocess
import tempfile


def compress_image(image_file, max_size_mb=15, quality=85):
    max_size_bytes = max_size_mb * 1024 * 1024

    img = Image.open(image_file)

    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background

    current_size = image_file.size
    scale_factor = min(1, (max_size_bytes / current_size) ** 0.5)
    new_width = int(img.width * scale_factor * 0.9)
    new_height = int(img.height * scale_factor * 0.9)

    max_dimension = 2048
    if new_width > max_dimension or new_height > max_dimension:
        if new_width > new_height:
            ratio = max_dimension / new_width
            new_width = max_dimension
            new_height = int(new_height * ratio)
        else:
            ratio = max_dimension / new_height
            new_height = max_dimension
            new_width = int(new_width * ratio)

    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    output = BytesIO()

    current_quality = quality
    while current_quality > 20:
        output.seek(0)
        output.truncate()
        img.save(output, format='JPEG', quality=current_quality, optimize=True, progressive=True)

        if output.tell() <= max_size_bytes:
            break
        current_quality -= 5

    output.seek(0)

    compressed_file = InMemoryUploadedFile(
        output,
        'ImageField',
        f"{os.path.splitext(image_file.name)[0]}.jpg",
        'image/jpeg',
        output.getbuffer().nbytes,
        None
    )

    print(
        f"Сжатие изображения: {image_file.size / (1024 * 1024):.2f}MB -> {compressed_file.size / (1024 * 1024):.2f}MB")

    return compressed_file


def compress_video_preview(video_file, max_size_mb=10):
    max_size_bytes = max_size_mb * 1024 * 1024

    if video_file.size <= max_size_bytes:
        return video_file

    original_size = video_file.size / (1024 * 1024)

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(video_file.name)[1]) as temp_input:
        for chunk in video_file.chunks():
            temp_input.write(chunk)
        temp_input_path = temp_input.name

    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    temp_output.close()
    temp_output_path = temp_output.name

    try:
        command = [
            'ffmpeg',
            '-i', temp_input_path,
            '-vcodec', 'libx264',
            '-acodec', 'aac',
            '-crf', '35',
            '-preset', 'fast',
            '-b:a', '128k',
            '-y', temp_output_path
        ]
        subprocess.run(command, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr.decode()}")
        os.unlink(temp_input_path)
        os.unlink(temp_output_path)
        return video_file
    except FileNotFoundError:
        print("FFmpeg не найден. Пожалуйста, установите FFmpeg и убедитесь, что он доступен в PATH.")
        os.unlink(temp_input_path)
        os.unlink(temp_output_path)
        return video_file

    with open(temp_output_path, 'rb') as f:
        compressed_data = f.read()

    compressed_size = len(compressed_data) / (1024 * 1024)

    os.unlink(temp_input_path)
    os.unlink(temp_output_path)

    output = BytesIO(compressed_data)
    compressed_file = InMemoryUploadedFile(
        output,
        'FileField',
        f"{os.path.splitext(video_file.name)[0]}.mp4",
        'video/mp4',
        len(compressed_data),
        None
    )

    print(f"Сжатие видео: {original_size:.2f}MB -> {compressed_size:.2f}MB")

    return compressed_file


def validate_file_size(file, max_size_mb):
    max_size_bytes = max_size_mb * 1024 * 1024

    if file.size > max_size_bytes:
        actual_size = file.size / (1024 * 1024)
        return False, f"Файл слишком большой. Максимум {max_size_mb}МБ, ваш файл {actual_size:.1f}МБ"

    return True, ""


def get_file_type(filename):
    ext = os.path.splitext(filename)[1].lower()

    image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.heic', '.heif']
    video_exts = ['.mp4', '.webm', '.mov', '.avi', '.mkv', '.m4v']
    audio_exts = ['.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac']

    if ext in image_exts:
        return 'image'
    elif ext in video_exts:
        return 'video'
    elif ext in audio_exts:
        return 'voice'
    else:
        return 'file'


def get_readable_size(size_bytes):
    for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} ТБ"