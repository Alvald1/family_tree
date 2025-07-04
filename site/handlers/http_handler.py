"""
Основной HTTP обработчик
"""

import http.server
from pathlib import Path
from utils.file_utils import serve_file, ensure_directories_exist
from utils.response_utils import setup_cors_headers
from api.person_api import PersonAPI


class PersonalDataHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Создаем директории для данных (в родительской директории)
        self.data_dir = Path('..', 'person_data')
        self.data_dir.mkdir(exist_ok=True)

        # Создаем поддиректории и получаем их пути
        self.data_dirs = ensure_directories_exist(self.data_dir)

        # Инициализируем API
        self.person_api = PersonAPI(self.data_dirs)

        super().__init__(*args, **kwargs)

    def do_GET(self):
        # Обработка API запросов
        if self.path.startswith('/api/'):
            self.handle_api_get()
        # Обработка запросов к данным персон (включая фотографии)
        elif self.path.startswith('/person_data/'):
            serve_file(self, self.path)
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

    def do_PUT(self):
        if self.path.startswith('/api/'):
            self.handle_api_put()
        else:
            self.send_error(404)

    def do_DELETE(self):
        if self.path.startswith('/api/'):
            self.handle_api_delete()
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        """Обработка OPTIONS запросов для CORS"""
        self.send_response(200)
        self.end_headers()

    def handle_api_get(self):
        """Обработка GET запросов к API"""
        try:
            path_parts = self.path.split('/')

            if len(path_parts) >= 4 and path_parts[2] == 'person':
                self.person_api.handle_get(self, path_parts)
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
                self.person_api.handle_post(self, path_parts)
            else:
                self.send_error(404)

        except Exception as e:
            print(f"Ошибка API POST: {e}")
            self.send_error(500)

    def handle_api_put(self):
        """Обработка PUT запросов к API"""
        try:
            path_parts = self.path.split('/')

            if len(path_parts) >= 5 and path_parts[2] == 'person':
                self.person_api.handle_put(self, path_parts)
            else:
                self.send_error(404)

        except Exception as e:
            print(f"Ошибка API PUT: {e}")
            self.send_error(500)

    def handle_api_delete(self):
        """Обработка DELETE запросов к API"""
        try:
            path_parts = self.path.split('/')

            if len(path_parts) >= 6 and path_parts[2] == 'person':
                self.person_api.handle_delete(self, path_parts)
            else:
                self.send_error(404)

        except Exception as e:
            print(f"Ошибка API DELETE: {e}")
            self.send_error(500)

    def end_headers(self):
        # Настройка CORS и других заголовков
        setup_cors_headers(self)

        if self.path.endswith('.svg'):
            self.send_header('Content-Type', 'image/svg+xml')

        super().end_headers()
