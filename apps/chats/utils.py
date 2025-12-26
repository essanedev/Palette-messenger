from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import os
import subprocess
import tempfile
import logging
import queue
import threading
import time
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


compression_queue = queue.Queue()

def compression_worker():
    while True:
        item = compression_queue.get()
        if item is None:
            break
        video_file, message, max_size_mb = item
        compress_video_preview_task(video_file, message, max_size_mb)
        compression_queue.task_done()

worker_thread = threading.Thread(target=compression_worker, daemon=True)
worker_thread.start()


def compress_image(image_file, max_size_mb=15, quality=85):
    logging.info(f"Starting image compression for {image_file.name}, original size: {image_file.size / (1024 * 1024):.2f}MB")
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

    logging.info(
        f"Image compression completed for {image_file.name}: {image_file.size / (1024 * 1024):.2f}MB -> {compressed_file.size / (1024 * 1024):.2f}MB")

    return compressed_file


def compress_video_preview(video_file, max_size_mb=10):
    max_size_bytes = max_size_mb * 1024 * 1024

    if video_file.size <= max_size_bytes:
        return video_file

    original_size = video_file.size / (1024 * 1024)
    logging.info(f"Starting video compression for {video_file.name}, original size: {original_size:.2f}MB")

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(video_file.name)[1]) as temp_input:
        for chunk in video_file.chunks():
            temp_input.write(chunk)
        temp_input_path = temp_input.name

    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    temp_output.close()
    temp_output_path = temp_output.name

    # Create a temp file for FFmpeg progress
    progress_file = tempfile.NamedTemporaryFile(delete=False, suffix='.log')
    progress_file.close()
    progress_path = progress_file.name

    try:
        command = [
            'ffmpeg',
            '-i', temp_input_path,
            '-vcodec', 'libx264',
            '-acodec', 'aac',
            '-crf', '35',
            '-preset', 'fast',
            '-b:a', '128k',
            '-threads', '0',
            '-progress', progress_path,
            '-y', temp_output_path
        ]
        logging.info(f"Running FFmpeg command for {video_file.name}")
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        last_progress = ""
        while process.poll() is None:
            time.sleep(2)
            try:
                with open(progress_path, 'r') as pf:
                    lines = pf.readlines()
                    if lines:
                        current_progress = lines[-1].strip()
                        if current_progress != last_progress:
                            logging.info(f"FFmpeg progress for {video_file.name}: {current_progress}")
                            last_progress = current_progress
            except Exception as e:
                logging.warning(f"Error reading progress for {video_file.name}: {e}")
        
        if process.returncode != 0:
            logging.error(f"FFmpeg failed for {video_file.name} with return code {process.returncode}")
            raise subprocess.CalledProcessError(process.returncode, command)
        
        logging.info(f"FFmpeg completed successfully for {video_file.name}")

    except subprocess.TimeoutExpired:
        logging.error(f"FFmpeg compression timed out for {video_file.name} after 600 seconds")
        os.unlink(temp_input_path)
        os.unlink(temp_output_path)
        os.unlink(progress_path)
        return video_file
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg error for {video_file.name}: {e}")
        os.unlink(temp_input_path)
        os.unlink(temp_output_path)
        os.unlink(progress_path)
        return video_file
    except FileNotFoundError:
        logging.error("FFmpeg not found. Please install FFmpeg and ensure it is available in PATH.")
        os.unlink(temp_input_path)
        os.unlink(temp_output_path)
        os.unlink(progress_path)
        return video_file

    with open(temp_output_path, 'rb') as f:
        compressed_data = f.read()

    compressed_size = len(compressed_data) / (1024 * 1024)

    os.unlink(temp_input_path)
    os.unlink(temp_output_path)
    os.unlink(progress_path)

    output = BytesIO(compressed_data)
    compressed_file = InMemoryUploadedFile(
        output,
        'FileField',
        f"{os.path.splitext(video_file.name)[0]}.mp4",
        'video/mp4',
        len(compressed_data),
        None
    )

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

def compress_video_preview_task(video_file, message, max_size_mb=10):
    logging.info(f"Starting video compression task for message {message.id}, file {video_file.name}")
    try:
        compressed_file = compress_video_preview(video_file, max_size_mb=max_size_mb)
        
        logging.info(f"Updating message {message.id} with compressed file (saving to storage)")
        try:
            compressed_file.file.seek(0)
            data = compressed_file.file.read()
        except Exception:
            try:
                data = compressed_file.read()
            except Exception as e:
                logging.error(f"Could not read compressed data for message {message.id}: {e}")
                raise

        try:
            old_name = message.file.name if message.file else None
            if old_name and default_storage.exists(old_name):
                default_storage.delete(old_name)
        except Exception as e:
            logging.warning(f"Failed to delete old file for message {message.id}: {e}")

        new_name = os.path.basename(old_name) if old_name else os.path.basename(compressed_file.name)
        message.file.save(new_name, ContentFile(data), save=True)
        logging.info(f"Message {message.id} updated successfully, new file_url: {message.file.url}")
        
        logging.info(f"Video compression completed for message {message.id}: {video_file.size / (1024 * 1024):.2f}MB -> {compressed_file.size / (1024 * 1024):.2f}MB")
        
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{message.chat.id}',
            {
                'type': 'message_updated',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sender': message.sender.username,
                    'sender_avatar': message.sender.avatar.url if message.sender.avatar else None,
                    'created_at': message.created_at.isoformat(),
                    'message_type': message.message_type,
                    'file_url': message.file.url if message.file else None,
                    'file_size': message.file.size if message.file else None,
                }
            }
        )
        
    except Exception as e:
        logging.error(f"Video compression failed for message {message.id}: {e}")