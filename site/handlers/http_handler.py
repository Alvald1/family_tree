"""Основной HTTP обработчик."""

import http.server
from utils.file_utils import serve_file, ensure_directories_exist
from utils.response_utils import setup_cors_headers
from api.person_api import PersonAPI
from api.routes import parse_api_path
from config.settings import load_settings


class PersonalDataHandler(http.server.SimpleHTTPRequestHandler):
    settings = load_settings()
    person_api = None

    @classmethod
    def configure(cls, settings):
        cls.settings = settings
        data_dirs = ensure_directories_exist(settings.data_dir)
        cls.person_api = PersonAPI(data_dirs, source_file=settings.source_file)

    def __init__(self, *args, **kwargs):
        if self.__class__.person_api is None:
            self.__class__.configure(self.__class__.settings)

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

    def do_HEAD(self):
        if self._path_parts() == ["api", "health"]:
            self.send_response(200)
            self.end_headers()
        else:
            super().do_HEAD()

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

    def do_PATCH(self):
        if self.path.startswith('/api/'):
            self.handle_api_patch()
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

    def _path_parts(self):
        return parse_api_path(self.path)

    def handle_api_get(self):
        """Обработка GET запросов к API"""
        try:
            path_parts = self._path_parts()

            if path_parts == ["api", "health"]:
                self.person_api.handle_health(self)
            elif len(path_parts) >= 3 and path_parts[1] == 'person':
                self.person_api.handle_get(self, path_parts)
            else:
                self.send_error(404)

        except Exception as e:
            print(f"Ошибка API GET: {e}")
            self.send_error(500)

    def handle_api_post(self):
        """Обработка POST запросов к API"""
        try:
            path_parts = self._path_parts()

            if len(path_parts) >= 4 and path_parts[1] == 'person':
                self.person_api.handle_post(self, path_parts)
            else:
                self.send_error(404)

        except Exception as e:
            print(f"Ошибка API POST: {e}")
            self.send_error(500)

    def handle_api_put(self):
        """Обработка PUT запросов к API"""
        try:
            path_parts = self._path_parts()

            if len(path_parts) >= 4 and path_parts[1] == 'person':
                self.person_api.handle_put(self, path_parts)
            else:
                self.send_error(404)

        except Exception as e:
            print(f"Ошибка API PUT: {e}")
            self.send_error(500)

    def handle_api_patch(self):
        """Обработка PATCH запросов к API"""
        try:
            path_parts = self._path_parts()

            if len(path_parts) >= 4 and path_parts[1] == 'person':
                self.person_api.handle_patch(self, path_parts)
            else:
                self.send_error(404)

        except Exception as e:
            print(f"Ошибка API PATCH: {e}")
            self.send_error(500)

    def handle_api_delete(self):
        """Обработка DELETE запросов к API"""
        try:
            path_parts = self._path_parts()

            if len(path_parts) >= 5 and path_parts[1] == 'person':
                self.person_api.handle_delete(self, path_parts)
            else:
                self.send_error(404)

        except Exception as e:
            print(f"Ошибка API DELETE: {e}")
            self.send_error(500)

    def end_headers(self):
        # Настройка CORS и других заголовков
        setup_cors_headers(self)

        super().end_headers()
