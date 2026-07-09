"""Основной HTTP обработчик."""

import http.server
import secrets
import time
from collections import defaultdict, deque
from urllib.parse import parse_qs, quote, urlparse
from utils.file_utils import serve_file, ensure_directories_exist
from utils.response_utils import setup_cors_headers
from api.person_api import PersonAPI
from api.routes import parse_api_path
from config.settings import load_settings
from auth.yandex_id import YandexIDAuth
from storage.object_storage import S3ObjectStorage


class RateLimiter:
    def __init__(self, limit=120, window_seconds=60):
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)

    def allow(self, key, now=None):
        now = now if now is not None else time.time()
        entries = self.requests[key]
        cutoff = now - self.window_seconds
        while entries and entries[0] <= cutoff:
            entries.popleft()
        if len(entries) >= self.limit:
            return False
        entries.append(now)
        return True


class PersonalDataHandler(http.server.SimpleHTTPRequestHandler):
    CACHEABLE_EXTENSIONS = {
        ".css", ".js", ".svg", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".ico",
    }
    settings = load_settings()
    person_api = None
    auth = YandexIDAuth(settings.auth)
    rate_limiter = RateLimiter()
    object_storage = None

    @classmethod
    def configure(cls, settings):
        cls.settings = settings
        data_dirs = ensure_directories_exist(settings.data_dir)
        cls.object_storage = S3ObjectStorage.from_config(settings.object_storage)
        cls.person_api = PersonAPI(
            data_dirs,
            source_file=settings.source_file,
            object_storage=cls.object_storage,
        )
        cls.auth = YandexIDAuth(settings.auth)

    def __init__(self, *args, **kwargs):
        if self.__class__.person_api is None:
            self.__class__.configure(self.__class__.settings)

        super().__init__(*args, **kwargs)

    def do_GET(self):
        if not self._check_rate_limit():
            return
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
            serve_file(
                self,
                self.path,
                data_dir=self.settings.data_dir,
                object_storage=self.object_storage,
            )
        elif self.path == '/':
            self.path = '/index.html'
            super().do_GET()
        else:
            super().do_GET()

    def do_HEAD(self):
        if not self._check_rate_limit():
            return
        if not self._require_auth():
            return

        if self._path_parts() == ["api", "health"]:
            self.send_response(200)
            self.end_headers()
        elif self.path.startswith('/person_data/'):
            serve_file(
                self,
                self.path,
                send_body=False,
                data_dir=self.settings.data_dir,
                object_storage=self.object_storage,
            )
        else:
            super().do_HEAD()

    def do_POST(self):
        if not self._check_rate_limit():
            return
        if not self._require_auth():
            return

        if self.path.startswith('/api/'):
            self.handle_api_post()
        else:
            self.send_error(404)

    def do_PUT(self):
        if not self._check_rate_limit():
            return
        if not self._require_auth():
            return

        if self.path.startswith('/api/'):
            self.handle_api_put()
        else:
            self.send_error(404)

    def do_PATCH(self):
        if not self._check_rate_limit():
            return
        if not self._require_auth():
            return

        if self.path.startswith('/api/'):
            self.handle_api_patch()
        else:
            self.send_error(404)

    def do_DELETE(self):
        if not self._check_rate_limit():
            return
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
        login = self.auth.login_from_cookie_header(cookie_header)
        if login:
            is_write_request = getattr(self, "command", "GET") in {
                "POST", "PUT", "PATCH", "DELETE",
            }
            if is_write_request and not self.auth.can_write(login):
                self.send_response(403)
                self.end_headers()
                return False
            if is_write_request:
                print(f"AUDIT write login={login} method={self.command} path={urlparse(self.path).path}")
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

    def _is_write_request(self):
        return getattr(self, "command", "GET") in {"POST", "PUT", "PATCH", "DELETE"}

    def _audit_write(self, login):
        print(f"AUDIT write login={login} method={self.command} path={urlparse(self.path).path}")

    def _check_rate_limit(self):
        client_ip = self.client_address[0] if getattr(self, "client_address", None) else "unknown"
        if self.rate_limiter.allow(client_ip):
            return True
        self.send_response(429)
        self.send_header("Retry-After", str(self.rate_limiter.window_seconds))
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
        elif path == "/auth/logged-out":
            self.handle_auth_logged_out()
        else:
            self.send_error(404)

    def handle_auth_login(self):
        query = parse_qs(urlparse(self.path).query)
        next_path = query.get("next", ["/"])[0]
        force_confirm = query.get("force_confirm", [""])[0].lower() in {
            "1", "true", "yes",
        }
        state = secrets.token_urlsafe(24)

        self.send_response(302)
        self.send_header("Set-Cookie", self.auth.state_set_cookie(state, next_path))
        self.send_header(
            "Location",
            self.auth.authorization_url(state, force_confirm=force_confirm),
        )
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
            self.send_response(302)
            self.send_header("Set-Cookie", self.auth.expired_session_cookie())
            self.send_header("Set-Cookie", self.auth.expired_state_cookie())
            self.send_header("Location", "/auth/logged-out?reason=access-denied")
            self.end_headers()
            return

        self.send_response(302)
        self.send_header("Set-Cookie", self.auth.session_set_cookie(login))
        self.send_header("Set-Cookie", self.auth.expired_state_cookie())
        self.send_header("Location", state_payload.get("next", "/"))
        self.end_headers()

    def handle_auth_logout(self):
        self.send_response(302)
        self.send_header("Set-Cookie", self.auth.expired_session_cookie())
        self.send_header("Location", "/auth/logged-out")
        self.end_headers()

    def handle_auth_logged_out(self):
        reason = parse_qs(urlparse(self.path).query).get("reason", [""])[0]
        access_denied = reason == "access-denied"
        title = "Доступа нет" if access_denied else "Вы вышли из аккаунта"
        message = (
            "Ваш Yandex-логин не добавлен в список доступа к семейному дереву."
            if access_denied
            else "Сессия семейного дерева завершена. Чтобы вернуться, войдите через Yandex ID и выберите нужный аккаунт."
        )
        button_text = "Войти другим аккаунтом" if access_denied else "Войти / выбрать аккаунт"
        login_url = "/auth/login?force_confirm=yes"
        body = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="/assets/css/main.css?v=tree-node-id-20260709-1">
</head>
<body class="auth-status-page">
    <main class="auth-status-card">
        <h1>{title}</h1>
        <p>{message}</p>
        <a class="btn" href="{login_url}">{button_text}</a>
    </main>
</body>
</html>
"""
        encoded = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

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
