from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import os
import subprocess
import tempfile


def compress_image(image_file, max_size_mb=15, quality=85):
    max_size_bytes = max_size_mb * 1024 * 1024

    if image_file.size <= max_size_bytes:
        return image_file

    img = Image.open(image_file)

    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background

    current_size = image_file.size
    scale_factor = (max_size_bytes / current_size) ** 0.5
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
        f"Сжатие изображения: {image_file.size / (1024 * 1024):.2f}MB → {compressed_file.size / (1024 * 1024):.2f}MB")

    return compressed_file


def compress_video_preview(video_file, max_size_mb=100):
    # TODO: Дань, я потом буду сжимать через ffmpeg. Пока тут прото проверка на размер
    max_size_bytes = max_size_mb * 1024 * 1024

    if video_file.size <= max_size_bytes:
        return video_file

    print(f"Видео слишком большое: {video_file.size / (1024 * 1024):.2f}MB")
    return video_file


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