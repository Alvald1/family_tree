"""Основной HTTP обработчик."""

import http.server
import secrets
from urllib.parse import parse_qs, quote, urlparse
from utils.file_utils import serve_file, ensure_directories_exist
from utils.response_utils import setup_cors_headers
from api.person_api import PersonAPI
from api.routes import parse_api_path
from config.settings import load_settings
from auth.yandex_id import YandexIDAuth


class PersonalDataHandler(http.server.SimpleHTTPRequestHandler):
    CACHEABLE_EXTENSIONS = {
        ".css", ".js", ".svg", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".ico",
    }
    settings = load_settings()
    person_api = None
    auth = YandexIDAuth(settings.auth)

    @classmethod
    def configure(cls, settings):
        cls.settings = settings
        data_dirs = ensure_directories_exist(settings.data_dir)
        cls.person_api = PersonAPI(data_dirs, source_file=settings.source_file)
        cls.auth = YandexIDAuth(settings.auth)

    def __init__(self, *args, **kwargs):
        if self.__class__.person_api is None:
            self.__class__.configure(self.__class__.settings)

        super().__init__(*args, **kwargs)

    def do_GET(self):
        if not self._require_auth():
            return

        if self.path.startswith('/auth/'):
            self.handle_auth_get()
            return

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
        if not self._require_auth():
            return

        if self._path_parts() == ["api", "health"]:
            self.send_response(200)
            self.end_headers()
        elif self.path.startswith('/person_data/'):
            serve_file(self, self.path, send_body=False)
        else:
            super().do_HEAD()

    def do_POST(self):
        if not self._require_auth():
            return

        if self.path.startswith('/api/'):
            self.handle_api_post()
        else:
            self.send_error(404)

    def do_PUT(self):
        if not self._require_auth():
            return

        if self.path.startswith('/api/'):
            self.handle_api_put()
        else:
            self.send_error(404)

    def do_PATCH(self):
        if not self._require_auth():
            return

        if self.path.startswith('/api/'):
            self.handle_api_patch()
        else:
            self.send_error(404)

    def do_DELETE(self):
        if not self._require_auth():
            return

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

    @classmethod
    def is_cacheable_path(cls, path):
        request_path = urlparse(path).path
        if request_path in {"", "/"}:
            return False
        if request_path.startswith("/api/"):
            return False
        if request_path.endswith(".html") or request_path.endswith(".json"):
            return False
        return any(request_path.endswith(ext) for ext in cls.CACHEABLE_EXTENSIONS)

    def _require_auth(self):
        if not self.auth.config.enabled:
            return True

        if self.auth.is_public_path(self.path):
            return True

        cookie_header = self.headers.get("Cookie", "")
        if self.auth.login_from_cookie_header(cookie_header):
            return True

        request_path = urlparse(self.path).path
        if request_path.startswith("/api/"):
            self.send_response(401)
            self.end_headers()
            return False

        self.send_response(302)
        self.send_header("Location", f"/auth/login?next={quote(self.path, safe='')}")
        self.end_headers()
        return False

    def handle_auth_get(self):
        path = urlparse(self.path).path
        if path == "/auth/login":
            self.handle_auth_login()
        elif path == "/auth/callback":
            self.handle_auth_callback()
        elif path == "/auth/logout":
            self.handle_auth_logout()
        else:
            self.send_error(404)

    def handle_auth_login(self):
        query = parse_qs(urlparse(self.path).query)
        next_path = query.get("next", ["/"])[0]
        state = secrets.token_urlsafe(24)

        self.send_response(302)
        self.send_header("Set-Cookie", self.auth.state_set_cookie(state, next_path))
        self.send_header("Location", self.auth.authorization_url(state))
        self.end_headers()

    def handle_auth_callback(self):
        query = parse_qs(urlparse(self.path).query)
        state = query.get("state", [""])[0]
        code = query.get("code", [""])[0]
        state_payload = self.auth.state_from_cookie_header(
            self.headers.get("Cookie", "")
        )

        if not code or not state_payload or state_payload.get("state") != state:
            self.send_error(400, "Invalid OAuth callback")
            return

        try:
            token = self.auth.exchange_code(code)
            user_info = self.auth.fetch_user_info(token["access_token"])
        except Exception as e:
            print(f"Ошибка Yandex ID OAuth: {e}")
            self.send_error(502, "Yandex ID authentication failed")
            return

        login = str(user_info.get("login", "")).lower()
        if login not in self.auth.config.allowed_logins:
            self.send_error(403, "Yandex login is not allowed")
            return

        self.send_response(302)
        self.send_header("Set-Cookie", self.auth.session_set_cookie(login))
        self.send_header("Set-Cookie", self.auth.expired_state_cookie())
        self.send_header("Location", state_payload.get("next", "/"))
        self.end_headers()

    def handle_auth_logout(self):
        self.send_response(302)
        self.send_header("Set-Cookie", self.auth.expired_session_cookie())
        self.send_header("Location", "/auth/login")
        self.end_headers()

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
        setup_cors_headers(self, cacheable=self.is_cacheable_path(self.path))

        super().end_headers()
