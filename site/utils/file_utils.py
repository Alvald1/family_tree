"""Утилиты для работы с файлами."""

import mimetypes
import shutil
import urllib.parse
from pathlib import Path


def serve_file(handler, file_path, send_body=True):
    """Обслуживание статических файлов"""
    try:
        clean_path = urllib.parse.unquote(file_path.split("?", 1)[0].lstrip("/"))

        if not clean_path.startswith("person_data/"):
            handler.send_error(403, "Доступ запрещен")
            return

        project_root = Path(__file__).resolve().parents[2]
        data_root = (project_root / "person_data").resolve()
        relative_path = clean_path.removeprefix("person_data/")
        full_path = (data_root / relative_path).resolve()

        if full_path != data_root and data_root not in full_path.parents:
            handler.send_error(403, "Доступ запрещен")
            return

        if not full_path.exists() or not full_path.is_file():
            print(f"Файл не найден: {full_path}")
            handler.send_error(404, "Файл не найден")
            return

        mime_type, _ = mimetypes.guess_type(str(full_path))
        if mime_type is None:
            mime_type = "application/octet-stream"

        handler.send_response(200)
        handler.send_header("Content-Type", mime_type)
        handler.send_header("Content-Length", str(full_path.stat().st_size))
        handler.end_headers()
        if not send_body:
            return
        with full_path.open("rb") as source:
            shutil.copyfileobj(source, handler.wfile)

    except Exception as e:
        print(f"Ошибка обслуживания файла: {e}")
        handler.send_error(500)


def ensure_directories_exist(data_dir):
    """Создание необходимых директорий для данных"""
    directories = ["photos", "blog", "messages"]

    for dir_name in directories:
        dir_path = data_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)

    return {
        'photos': data_dir / 'photos',
        'blog': data_dir / 'blog',
        'messages': data_dir / 'messages'
    }
