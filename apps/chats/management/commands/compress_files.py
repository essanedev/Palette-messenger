from django.core.management.base import BaseCommand
from django.conf import settings
from apps.chats.models import Message
from apps.chats.utils import compress_image, compress_video_preview, get_file_type
import os
import logging
import shutil

logger = logging.getLogger(__name__)


def get_dir_size(path):
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total += os.path.getsize(fp)
    return total


class Command(BaseCommand):
    help = 'Сжать существующие несжатые изображения и видео в базе данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать, что будет сжато, без фактического выполнения',
        )
        parser.add_argument(
            '--recompress',
            action='store_true',
            help='Пересжать оригинальные файлы с новыми настройками',
        )
        parser.add_argument(
            '--image-max-size',
            type=int,
            default=15,
            help='Максимальный размер в МБ для сжатых изображений (по умолчанию: 15)',
        )
        parser.add_argument(
            '--video-max-size',
            type=int,
            default=5,
            help='Максимальный размер в МБ для сжатых видео (по умолчанию: 5)',
        )
        parser.add_argument(
            '--delete-missing',
            action='store_true',
            help='Удалить сообщения с файлами, которые не найдены на диске',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        recompress = options['recompress']
        image_max_size = options['image_max_size']
        video_max_size = options['video_max_size']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No files will be modified'))

        media_messages_dir = os.path.join(settings.MEDIA_ROOT, 'messages')
        if not os.path.exists(media_messages_dir):
            self.stdout.write(self.style.ERROR('Media messages directory does not exist'))
            return

        original_dir = os.path.join(media_messages_dir, 'original')

        source_dir = original_dir if recompress else media_messages_dir
        files_in_dir = os.listdir(source_dir)
        self.stdout.write(f'Found {len(files_in_dir)} files in {"original" if recompress else "media"} directory')

        messages_with_files = Message.objects.exclude(file__isnull=True).exclude(file='')
        self.stdout.write(f'Found {messages_with_files.count()} messages with files in DB')
        for msg in messages_with_files[:10]:
            self.stdout.write(f'Message {msg.id}: file.name = {repr(msg.file.name)}, path = {repr(msg.file.path)}')

        initial_size = get_dir_size(media_messages_dir)

        compressed_count = 0
        error_count = 0
        deleted_count = 0

        for filename in files_in_dir:
            try:
                file_path = os.path.join(source_dir, filename)
                if not os.path.isfile(file_path):
                    continue

                if not recompress:
                    original_file_path = os.path.join(original_dir, filename)
                    if os.path.exists(original_file_path):
                        self.stdout.write(f'Skipping already processed: {filename}')
                        continue

                file_type = get_file_type(filename)

                if file_type not in ['image', 'video']:
                    self.stdout.write(f'Skipping non-compressible file: {filename} (type: {file_type})')
                    continue

                original_size = os.path.getsize(file_path)

                max_size_bytes = (image_max_size if file_type == 'image' else video_max_size) * 1024 * 1024

                if original_size <= max_size_bytes:
                    self.stdout.write(f'Skipping (already small): {filename} ({original_size / (1024*1024):.2f}MB)')
                    continue

                self.stdout.write(f'Processing {file_type}: {filename} ({original_size / (1024*1024):.2f}MB)')

                if dry_run:
                    compressed_count += 1
                    continue

                if not recompress:
                    os.makedirs(original_dir, exist_ok=True)
                    shutil.move(file_path, os.path.join(original_dir, filename))
                    original_file_path = os.path.join(original_dir, filename)
                else:
                    original_file_path = file_path

                with open(original_file_path, 'rb') as f:
                    file_content = f.read()

                from django.core.files.uploadedfile import SimpleUploadedFile
                uploaded_file = SimpleUploadedFile(
                    name=filename,
                    content=file_content,
                    content_type=None 
                )

                if file_type == 'image':
                    compressed_file = compress_image(uploaded_file, max_size_mb=image_max_size)
                elif file_type == 'video':
                    compressed_file = compress_video_preview(uploaded_file, max_size_mb=video_max_size)

                compressed_path = os.path.join(media_messages_dir, filename)
                with open(compressed_path, 'wb') as f:
                    f.write(compressed_file.read())

                new_size = os.path.getsize(compressed_path)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Compressed: {original_size / (1024*1024):.2f}MB -> {new_size / (1024*1024):.2f}MB'
                    )
                )
                compressed_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing {filename}: {e}'))
                error_count += 1

        self.stdout.write(self.style.SUCCESS(f'Compression complete: {compressed_count} files compressed, {error_count} errors'))

        final_size = get_dir_size(media_messages_dir)
        self.stdout.write(f'Initial directory size: {initial_size / (1024*1024):.2f} MB')
        self.stdout.write(f'Final directory size: {final_size / (1024*1024):.2f} MB')
        self.stdout.write(f'Space saved: {(initial_size - final_size) / (1024*1024):.2f} MB')