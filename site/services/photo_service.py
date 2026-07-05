"""Сервис для работы с фотографиями."""

import os
import uuid
from email import policy
from email.parser import BytesParser
from pathlib import Path
from utils.response_utils import get_current_timestamp
from storage.json_store import JsonListStore, validate_record_id


class PhotoService:
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    ALLOWED_CONTENT_TYPES = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    def __init__(self, photos_dir):
        self.photos_dir = Path(photos_dir)
        self.photos_dir.mkdir(parents=True, exist_ok=True)
        self.store = JsonListStore(self.photos_dir)

    def get_photos(self, person_id):
        """Получение списка фотографий персоны"""
        return self._load_photos_list(person_id)

    def upload_photo(self, person_id, post_data, boundary):
        """Загрузка фотографии"""
        safe_person_id = validate_record_id(person_id)
        message = self._parse_multipart(post_data, boundary)

        for part in message.iter_parts():
            original_filename = part.get_filename()
            content_type = part.get_content_type()
            if not original_filename or not content_type.startswith("image/"):
                continue

            file_data = part.get_payload(decode=True)
            if not file_data:
                raise ValueError("Пустой файл")

            original_filename = Path(original_filename).name
            file_extension = os.path.splitext(original_filename)[1].lower()
            self._validate_upload(original_filename, file_extension, content_type, file_data)
            unique_filename = f"{uuid.uuid4()}{file_extension}"

            person_photos_dir = self.photos_dir / safe_person_id
            person_photos_dir.mkdir(parents=True, exist_ok=True)

            file_path = person_photos_dir / unique_filename
            file_path.write_bytes(file_data)

            photos = self._load_photos_list(safe_person_id)
            new_photo = {
                "url": f"/person_data/photos/{safe_person_id}/{unique_filename}",
                "caption": original_filename,
                "date": get_current_timestamp(),
                "filename": unique_filename,
            }

            photos.append(new_photo)
            self._save_photos_list(safe_person_id, photos)

            return new_photo

        raise ValueError("Файл не найден в запросе")

    def delete_photo(self, person_id, photo_index):
        """Удаление фотографии"""
        photos = self._load_photos_list(person_id)

        if photo_index < 0 or photo_index >= len(photos):
            raise IndexError("Фотография не найдена")

        photo_to_delete = photos[photo_index]
        if "filename" in photo_to_delete:
            safe_person_id = validate_record_id(person_id)
            photo_path = self.photos_dir / safe_person_id / Path(photo_to_delete["filename"]).name
            if photo_path.exists():
                photo_path.unlink()

        photos.pop(photo_index)
        self._save_photos_list(person_id, photos)

    def reorder_photos(self, person_id, new_photos=None, new_order=None):
        """Изменение порядка фотографий"""
        photos = self._load_photos_list(person_id)

        if new_photos is not None:
            raise ValueError("Принимается только порядок фотографий по индексам")
        elif new_order is not None:
            if not isinstance(new_order, list) or len(
                    new_order) != len(photos):
                raise ValueError("Неверный порядок фотографий")

            if not all(0 <= idx < len(photos) for idx in new_order):
                raise ValueError("Неверные индексы в порядке фотографий")

            reordered_photos = [photos[idx] for idx in new_order]
            self._save_photos_list(person_id, reordered_photos)
            return reordered_photos
        else:
            raise ValueError(
                "Не указан ни новый порядок, ни новый список фотографий")

    def _load_photos_list(self, person_id):
        """Загрузка списка фотографий"""
        return self.store.load(person_id)

    def _save_photos_list(self, person_id, photos):
        """Сохранение списка фотографий"""
        self.store.save(person_id, photos)

    def _parse_multipart(self, post_data, boundary):
        if not boundary:
            raise ValueError("Не указан multipart boundary")

        header = (
            "Content-Type: multipart/form-data; "
            f"boundary={boundary}\r\nMIME-Version: 1.0\r\n\r\n"
        ).encode("utf-8")
        return BytesParser(policy=policy.default).parsebytes(header + post_data)

    def _validate_upload(self, original_filename, file_extension, content_type, file_data):
        if file_extension not in self.ALLOWED_EXTENSIONS:
            raise ValueError("Неподдерживаемый формат изображения")
        if content_type != self.ALLOWED_CONTENT_TYPES[file_extension]:
            raise ValueError("Тип содержимого не соответствует расширению файла")
        if not self._has_allowed_magic_bytes(file_extension, file_data):
            raise ValueError("Содержимое файла не похоже на разрешенное изображение")

    def _has_allowed_magic_bytes(self, file_extension, file_data):
        if file_extension in {".jpg", ".jpeg"}:
            return file_data.startswith(b"\xff\xd8\xff")
        if file_extension == ".png":
            return file_data.startswith(b"\x89PNG\r\n")
        if file_extension == ".webp":
            return file_data.startswith(b"RIFF") and file_data[8:12] == b"WEBP"
        return False
