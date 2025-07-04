"""
Сервис для работы с фотографиями
"""

import json
import uuid
import os
import re
from pathlib import Path
from utils.response_utils import get_current_timestamp


class PhotoService:
    def __init__(self, photos_dir):
        self.photos_dir = Path(photos_dir)
        self.photos_dir.mkdir(exist_ok=True)

    def get_photos(self, person_id):
        """Получение списка фотографий персоны"""
        photos_file = self.photos_dir / f"{person_id}.json"

        if photos_file.exists():
            with open(photos_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def upload_photo(self, person_id, post_data, boundary):
        """Загрузка фотографии"""
        # Парсинг multipart данных
        parts = post_data.split(f'--{boundary}'.encode())

        for part in parts:
            if b'filename=' in part and b'Content-Type: image' in part:
                # Извлечение имени файла
                filename_match = re.search(rb'filename="([^"]*)"', part)
                if not filename_match:
                    continue

                original_filename = filename_match.group(1).decode('utf-8')

                # Извлечение содержимого файла
                file_start = part.find(b'\r\n\r\n') + 4
                file_end = part.rfind(b'\r\n')
                file_data = part[file_start:file_end]

                # Генерация уникального имени файла
                file_extension = os.path.splitext(original_filename)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"

                # Создание директории для фотографий персоны
                person_photos_dir = self.photos_dir / person_id
                person_photos_dir.mkdir(exist_ok=True)

                # Сохранение файла
                file_path = person_photos_dir / unique_filename
                with open(file_path, 'wb') as f:
                    f.write(file_data)

                # Обновление списка фотографий
                photos = self._load_photos_list(person_id)

                # Добавление новой фотографии
                new_photo = {
                    'url': f'/person_data/photos/{person_id}/{unique_filename}',
                    'caption': original_filename,
                    'date': get_current_timestamp(),
                    'filename': unique_filename}

                photos.append(new_photo)
                self._save_photos_list(person_id, photos)

                return new_photo

        raise ValueError("Файл не найден в запросе")

    def delete_photo(self, person_id, photo_index):
        """Удаление фотографии"""
        photos = self._load_photos_list(person_id)

        if photo_index >= len(photos):
            raise IndexError("Фотография не найдена")

        # Удаление файла фотографии
        photo_to_delete = photos[photo_index]
        if 'filename' in photo_to_delete:
            photo_path = self.photos_dir / \
                person_id / photo_to_delete['filename']
            if photo_path.exists():
                photo_path.unlink()

        # Удаление из списка
        photos.pop(photo_index)
        self._save_photos_list(person_id, photos)

    def _load_photos_list(self, person_id):
        """Загрузка списка фотографий"""
        photos_file = self.photos_dir / f"{person_id}.json"

        if photos_file.exists():
            with open(photos_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save_photos_list(self, person_id, photos):
        """Сохранение списка фотографий"""
        photos_file = self.photos_dir / f"{person_id}.json"
        with open(photos_file, 'w', encoding='utf-8') as f:
            json.dump(photos, f, ensure_ascii=False, indent=2)
