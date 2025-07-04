"""
Утилиты для работы с файлами
"""

import os
import mimetypes
import urllib.parse
from pathlib import Path


def serve_file(handler, file_path):
    """Обслуживание статических файлов"""
    try:
        # Убираем ведущий слэш и декодируем URL
        clean_path = urllib.parse.unquote(file_path[1:])  # убираем ведущий /

        # Проверяем, что путь безопасен (находится в person_data)
        if not clean_path.startswith('person_data/'):
            handler.send_error(403, "Доступ запрещен")
            return

        # Строим полный путь - файлы находятся в родительской директории
        full_path = Path('..') / clean_path

        # Проверяем, что файл существует
        if not full_path.exists() or not full_path.is_file():
            print(f"Файл не найден: {full_path.absolute()}")
            handler.send_error(404, "Файл не найден")
            return

        # Определяем MIME тип
        mime_type, _ = mimetypes.guess_type(str(full_path))
        if mime_type is None:
            mime_type = 'application/octet-stream'

        # Читаем и отправляем файл
        with open(full_path, 'rb') as f:
            file_data = f.read()

        handler.send_response(200)
        handler.send_header('Content-Type', mime_type)
        handler.send_header('Content-Length', str(len(file_data)))
        handler.end_headers()
        handler.wfile.write(file_data)

    except Exception as e:
        print(f"Ошибка обслуживания файла: {e}")
        handler.send_error(500)


def ensure_directories_exist(data_dir):
    """Создание необходимых директорий для данных"""
    directories = ['photos', 'blog', 'messages']

    for dir_name in directories:
        dir_path = data_dir / dir_name
        dir_path.mkdir(exist_ok=True)

    return {
        'photos': data_dir / 'photos',
        'blog': data_dir / 'blog',
        'messages': data_dir / 'messages'
    }
