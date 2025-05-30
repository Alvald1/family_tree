#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Расширенный HTTP сервер для генеалогического дерева
с поддержкой персональных страниц, загрузки фотографий и блогов
"""

import http.server
import socketserver
import os
import json
import urllib.parse
import shutil
import uuid
from pathlib import Path
import mimetypes
import re


class PersonalDataHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Создаем директории для данных
        self.data_dir = Path('person_data')
        self.data_dir.mkdir(exist_ok=True)

        self.photos_dir = self.data_dir / 'photos'
        self.photos_dir.mkdir(exist_ok=True)

        self.blog_dir = self.data_dir / 'blog'
        self.blog_dir.mkdir(exist_ok=True)

        self.messages_dir = self.data_dir / 'messages'
        self.messages_dir.mkdir(exist_ok=True)

        super().__init__(*args, **kwargs)

    def do_GET(self):
        # Обработка API запросов
        if self.path.startswith('/api/'):
            self.handle_api_get()
        # Обработка запросов к данным персон (включая фотографии)
        elif self.path.startswith('/person_data/'):
            self.serve_person_data()
        elif self.path == '/':
            self.path = '/index.html'
            super().do_GET()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith('/api/'):
            self.handle_api_post()
        else:
            self.send_error(404)

    def do_DELETE(self):
        if self.path.startswith('/api/'):
            self.handle_api_delete()
        else:
            self.send_error(404)

    def handle_api_get(self):
        """Обработка GET запросов к API"""
        try:
            # Парсинг пути API
            path_parts = self.path.split('/')

            if len(path_parts) >= 4 and path_parts[2] == 'person':
                person_id = path_parts[3]

                if len(path_parts) == 4:
                    # GET /api/person/{id} - информация о персоне
                    self.get_person_info(person_id)
                elif len(path_parts) == 5:
                    resource = path_parts[4]
                    if resource == 'photos':
                        # GET /api/person/{id}/photos - список фотографий
                        self.get_person_photos(person_id)
                    elif resource == 'blog':
                        # GET /api/person/{id}/blog - записи блога
                        self.get_person_blog(person_id)
                    elif resource == 'messages':
                        # GET /api/person/{id}/messages - сообщения чата
                        self.get_person_messages(person_id)
                    else:
                        self.send_error(404)
                else:
                    self.send_error(404)
            else:
                self.send_error(404)

        except Exception as e:
            print(f"Ошибка API GET: {e}")
            self.send_error(500)

    def handle_api_post(self):
        """Обработка POST запросов к API"""
        try:
            path_parts = self.path.split('/')

            if len(path_parts) >= 5 and path_parts[2] == 'person':
                person_id = path_parts[3]
                resource = path_parts[4]

                if resource == 'photos':
                    # POST /api/person/{id}/photos - загрузка фотографии
                    self.upload_photo(person_id)
                elif resource == 'blog':
                    # POST /api/person/{id}/blog - добавление записи в блог
                    self.add_blog_post(person_id)
                elif resource == 'messages':
                    # POST /api/person/{id}/messages - сохранение сообщений
                    # чата
                    self.save_person_messages(person_id)
                else:
                    self.send_error(404)
            else:
                self.send_error(404)

        except Exception as e:
            print(f"Ошибка API POST: {e}")
            self.send_error(500)

    def handle_api_delete(self):
        """Обработка DELETE запросов к API"""
        try:
            path_parts = self.path.split('/')

            if len(path_parts) >= 6 and path_parts[2] == 'person':
                person_id = path_parts[3]
                resource = path_parts[4]
                item_id = int(path_parts[5])

                if resource == 'photos':
                    # DELETE /api/person/{id}/photos/{index}
                    self.delete_photo(person_id, item_id)
                elif resource == 'blog':
                    # DELETE /api/person/{id}/blog/{index}
                    self.delete_blog_post(person_id, item_id)
                else:
                    self.send_error(404)
            else:
                self.send_error(404)

        except Exception as e:
            print(f"Ошибка API DELETE: {e}")
            self.send_error(500)

    def get_person_info(self, person_id):
        """Получение информации о персоне из source.txt"""
        try:
            # Извлекаем числовой ID из person_id (убираем префикс "node" если
            # есть)
            numeric_id = person_id
            if person_id.startswith('node'):
                numeric_id = person_id[4:]  # убираем "node"

            if os.path.exists('source.txt'):
                with open('source.txt', 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line in lines:
                    line = line.strip()
                    if line.startswith(f"{numeric_id} -"):
                        person_info = line[line.find('-') + 1:].strip()

                        # Попытка извлечь даты из скобок
                        dates_match = re.search(r'\(([^)]+)\)', person_info)
                        dates = dates_match.group(1) if dates_match else ''
                        name = re.sub(r'\s*\([^)]+\)', '', person_info).strip()

                        response_data = {
                            'id': person_id,
                            'name': name,
                            'dates': dates,
                            'full_info': person_info
                        }

                        self.send_json_response(response_data)
                        return

            # Если персона не найдена
            self.send_json_response({
                'id': person_id,
                'name': f'Персона {person_id}',
                'dates': '',
                'full_info': f'Персона {person_id}'
            })

        except Exception as e:
            print(f"Ошибка получения информации о персоне: {e}")
            self.send_error(500)

    def get_person_photos(self, person_id):
        """Получение списка фотографий персоны"""
        photos_file = self.photos_dir / f"{person_id}.json"

        if photos_file.exists():
            with open(photos_file, 'r', encoding='utf-8') as f:
                photos = json.load(f)
        else:
            photos = []

        self.send_json_response(photos)

    def get_person_blog(self, person_id):
        """Получение записей блога персоны"""
        blog_file = self.blog_dir / f"{person_id}.json"

        if blog_file.exists():
            with open(blog_file, 'r', encoding='utf-8') as f:
                posts = json.load(f)
        else:
            posts = []

        self.send_json_response(posts)

    def get_person_messages(self, person_id):
        """Получение сообщений чата персоны"""
        messages_dir = self.data_dir / 'messages'
        messages_dir.mkdir(exist_ok=True)

        messages_file = messages_dir / f"{person_id}.json"

        if messages_file.exists():
            with open(messages_file, 'r', encoding='utf-8') as f:
                messages = json.load(f)
        else:
            messages = []

        self.send_json_response(messages)

    def save_person_messages(self, person_id):
        """Сохранение сообщений чата персоны"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')

            messages = json.loads(post_data)

            # Создание директории для сообщений
            messages_dir = self.data_dir / 'messages'
            messages_dir.mkdir(exist_ok=True)

            # Сохранение сообщений
            messages_file = messages_dir / f"{person_id}.json"
            with open(messages_file, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)

            self.send_json_response({'success': True})

        except Exception as e:
            print(f"Ошибка сохранения сообщений: {e}")
            self.send_error(500)

    def upload_photo(self, person_id):
        """Загрузка фотографии"""
        try:
            # Получение данных POST запроса
            content_type = self.headers.get('Content-Type', '')
            if not content_type.startswith('multipart/form-data'):
                self.send_error(400, "Неправильный тип содержимого")
                return

            # Парсинг multipart данных
            boundary = content_type.split('boundary=')[1]
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)

            # Простой парсер multipart (для более сложных случаев используйте
            # библиотеку)
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
                    photos_file = self.photos_dir / f"{person_id}.json"

                    if photos_file.exists():
                        with open(photos_file, 'r', encoding='utf-8') as f:
                            photos = json.load(f)
                    else:
                        photos = []

                    # Добавление новой фотографии
                    new_photo = {
                        'url': f'/person_data/photos/{person_id}/{unique_filename}',
                        'caption': original_filename,
                        'date': self.get_current_timestamp(),
                        'filename': unique_filename}

                    photos.append(new_photo)

                    # Сохранение обновленного списка
                    with open(photos_file, 'w', encoding='utf-8') as f:
                        json.dump(photos, f, ensure_ascii=False, indent=2)

                    self.send_json_response(
                        {'success': True, 'photo': new_photo})
                    return

            self.send_error(400, "Файл не найден в запросе")

        except Exception as e:
            print(f"Ошибка загрузки фотографии: {e}")
            self.send_error(500)

    def add_blog_post(self, person_id):
        """Добавление записи в блог"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')

            post_info = json.loads(post_data)

            # Загрузка существующих записей
            blog_file = self.blog_dir / f"{person_id}.json"

            if blog_file.exists():
                with open(blog_file, 'r', encoding='utf-8') as f:
                    posts = json.load(f)
            else:
                posts = []

            # Добавление новой записи в начало списка
            posts.insert(0, post_info)

            # Сохранение обновленного списка
            with open(blog_file, 'w', encoding='utf-8') as f:
                json.dump(posts, f, ensure_ascii=False, indent=2)

            self.send_json_response({'success': True})

        except Exception as e:
            print(f"Ошибка добавления записи в блог: {e}")
            self.send_error(500)

    def delete_photo(self, person_id, photo_index):
        """Удаление фотографии"""
        try:
            photos_file = self.photos_dir / f"{person_id}.json"

            if not photos_file.exists():
                self.send_error(404, "Фотографии не найдены")
                return

            with open(photos_file, 'r', encoding='utf-8') as f:
                photos = json.load(f)

            if photo_index >= len(photos):
                self.send_error(404, "Фотография не найдена")
                return

            # Удаление файла фотографии
            photo_to_delete = photos[photo_index]
            if 'filename' in photo_to_delete:
                photo_path = self.photos_dir / \
                    person_id / photo_to_delete['filename']
                if photo_path.exists():
                    photo_path.unlink()

            # Удаление из списка
            photos.pop(photo_index)

            # Сохранение обновленного списка
            with open(photos_file, 'w', encoding='utf-8') as f:
                json.dump(photos, f, ensure_ascii=False, indent=2)

            self.send_json_response({'success': True})

        except Exception as e:
            print(f"Ошибка удаления фотографии: {e}")
            self.send_error(500)

    def delete_blog_post(self, person_id, post_index):
        """Удаление записи блога"""
        try:
            blog_file = self.blog_dir / f"{person_id}.json"

            if not blog_file.exists():
                self.send_error(404, "Записи блога не найдены")
                return

            with open(blog_file, 'r', encoding='utf-8') as f:
                posts = json.load(f)

            if post_index >= len(posts):
                self.send_error(404, "Запись не найдена")
                return

            # Удаление записи
            posts.pop(post_index)

            # Сохранение обновленного списка
            with open(blog_file, 'w', encoding='utf-8') as f:
                json.dump(posts, f, ensure_ascii=False, indent=2)

            self.send_json_response({'success': True})

        except Exception as e:
            print(f"Ошибка удаления записи блога: {e}")
            self.send_error(500)

    def serve_person_data(self):
        """Обслуживание файлов данных персон (фотографии и т.д.)"""
        try:
            # Убираем ведущий слэш и декодируем URL
            file_path = urllib.parse.unquote(
                self.path[1:])  # убираем ведущий /
            full_path = Path(file_path)

            # Проверяем, что путь безопасен (находится в person_data)
            if not str(full_path).startswith('person_data/'):
                self.send_error(403, "Доступ запрещен")
                return

            # Проверяем, что файл существует
            if not full_path.exists() or not full_path.is_file():
                self.send_error(404, "Файл не найден")
                return

            # Определяем MIME тип
            mime_type, _ = mimetypes.guess_type(str(full_path))
            if mime_type is None:
                mime_type = 'application/octet-stream'

            # Читаем и отправляем файл
            with open(full_path, 'rb') as f:
                file_data = f.read()

            self.send_response(200)
            self.send_header('Content-Type', mime_type)
            self.send_header('Content-Length', str(len(file_data)))
            self.end_headers()
            self.wfile.write(file_data)

        except Exception as e:
            print(f"Ошибка обслуживания файла: {e}")
            self.send_error(500)

    def send_json_response(self, data):
        """Отправка JSON ответа"""
        response = json.dumps(data, ensure_ascii=False)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(response.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def get_current_timestamp(self):
        """Получение текущего времени в ISO формате"""
        from datetime import datetime
        return datetime.now().isoformat()

    def end_headers(self):
        # Добавляем заголовки для CORS и отключения кэширования
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header(
            'Access-Control-Allow-Methods',
            'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header(
            'Cache-Control',
            'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')

        if self.path.endswith('.svg'):
            self.send_header('Content-Type', 'image/svg+xml')

        super().end_headers()

    def do_OPTIONS(self):
        """Обработка OPTIONS запросов для CORS"""
        self.send_response(200)
        self.end_headers()


def main():
    PORT = 8003

    print(f"Запуск расширенного HTTP сервера на порту {PORT}")
    print(f"Откройте в браузере: http://localhost:{PORT}")
    print("Доступны следующие функции:")
    print("- Просмотр генеалогического дерева")
    print("- Персональные страницы для каждого человека")
    print("- Загрузка и просмотр фотографий")
    print("- Ведение личных блогов")
    print("Для остановки нажмите Ctrl+C")

    try:
        with socketserver.TCPServer(("", PORT), PersonalDataHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"Порт {PORT} уже занят. Попробуйте другой порт.")
        else:
            print(f"Ошибка запуска сервера: {e}")


if __name__ == "__main__":
    main()
