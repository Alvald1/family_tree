import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = PROJECT_ROOT / "site"
sys.path.insert(0, str(SITE_ROOT))

from api.routes import parse_api_path
from auth.yandex_id import AuthConfig, YandexIDAuth
from config.settings import load_settings
from handlers.http_handler import PersonalDataHandler
from utils.file_utils import serve_file
from utils.response_utils import setup_cors_headers


class FakeReadableObjectStorage:
    def __init__(self, objects):
        self.objects = objects

    def get_object(self, key):
        return self.objects.get(key)


class SettingsTest(unittest.TestCase):
    def test_load_settings_reads_site_config_without_losing_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site_root = Path(temp_dir)
            config_dir = site_root / "config"
            config_dir.mkdir()
            (config_dir / "site_config.py").write_text(
                'host = "0.0.0.0"\nport = 8123\ndata_directory = "custom_data"\n',
                encoding="utf-8",
            )

            settings = load_settings(site_root)

            self.assertEqual(settings.host, "0.0.0.0")
            self.assertEqual(settings.port, 8123)
            self.assertEqual(settings.data_dir, site_root.parent.resolve() / "custom_data")
            self.assertEqual(settings.source_file, site_root.parent.resolve() / "source.txt")

    def test_environment_overrides_file_config_for_container_runtime(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site_root = Path(temp_dir)
            config_dir = site_root / "config"
            config_dir.mkdir()
            (config_dir / "site_config.py").write_text(
                'host = "127.0.0.1"\nport = 9000\ndata_directory = "person_data"\n',
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {
                    "FAMILY_TREE_HOST": "0.0.0.0",
                    "FAMILY_TREE_PORT": "8000",
                    "FAMILY_TREE_DATA_DIR": "/data/person_data",
                    "FAMILY_TREE_SOURCE_FILE": "/data/source.txt",
                },
            ):
                settings = load_settings(site_root)

            self.assertEqual(settings.host, "0.0.0.0")
            self.assertEqual(settings.port, 8000)
            self.assertEqual(settings.data_dir, Path("/data/person_data"))
            self.assertEqual(settings.source_file, Path("/data/source.txt"))
            self.assertFalse(settings.auth.enabled)

    def test_s3_settings_are_loaded_from_environment(self):
        with patch.dict(
            "os.environ",
            {
                "FAMILY_TREE_S3_BUCKET": "s3-gribovka",
                "FAMILY_TREE_S3_ENDPOINT_URL": "https://storage.yandexcloud.net",
                "AWS_ACCESS_KEY_ID": "access-key",
                "AWS_SECRET_ACCESS_KEY": "secret-key",
            },
            clear=True,
        ):
            settings = load_settings(SITE_ROOT)

        self.assertTrue(settings.object_storage.enabled)
        self.assertEqual(settings.object_storage.bucket, "s3-gribovka")
        self.assertEqual(
            settings.object_storage.endpoint_url,
            "https://storage.yandexcloud.net",
        )
        self.assertEqual(settings.object_storage.access_key_id, "access-key")
        self.assertEqual(settings.object_storage.secret_access_key, "secret-key")

    def test_container_runtime_defaults_to_auth_enabled(self):
        with patch.dict("os.environ", {"FAMILY_TREE_CONTAINER_RUNTIME": "true"}, clear=True):
            with self.assertRaises(ValueError):
                load_settings(SITE_ROOT)

    def test_enabled_auth_rejects_weak_session_secret(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site_root = Path(temp_dir)

            with patch.dict(
                "os.environ",
                {
                    "FAMILY_TREE_AUTH_ENABLED": "true",
                    "YANDEX_CLIENT_ID": "client-id",
                    "YANDEX_CLIENT_SECRET": "client-secret",
                    "YANDEX_REDIRECT_URI": "https://drevo.gribovka.ru/auth/callback",
                    "YANDEX_ALLOWED_LOGINS": "alice",
                    "FAMILY_TREE_SESSION_SECRET": "short",
                },
            ):
                with self.assertRaises(ValueError):
                    load_settings(site_root)

    def test_environment_enables_yandex_id_auth(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site_root = Path(temp_dir)

            with patch.dict(
                "os.environ",
                {
                    "FAMILY_TREE_AUTH_ENABLED": "true",
                    "YANDEX_CLIENT_ID": "client-id",
                    "YANDEX_CLIENT_SECRET": "client-secret",
                    "YANDEX_REDIRECT_URI": "https://drevo.gribovka.ru/auth/callback",
                    "YANDEX_ALLOWED_LOGINS": "alice, bob ",
                    "YANDEX_EDITOR_LOGINS": "bob",
                    "YANDEX_ADMIN_LOGINS": "carol",
                    "FAMILY_TREE_SESSION_SECRET": "a" * 32,
                },
            ):
                settings = load_settings(site_root)

            self.assertTrue(settings.auth.enabled)
            self.assertEqual(settings.auth.client_id, "client-id")
            self.assertEqual(settings.auth.redirect_uri, "https://drevo.gribovka.ru/auth/callback")
            self.assertEqual(settings.auth.allowed_logins, frozenset({"alice", "bob"}))
            self.assertEqual(settings.auth.editor_logins, frozenset({"bob"}))
            self.assertEqual(settings.auth.admin_logins, frozenset({"carol"}))


class YandexIDAuthTest(unittest.TestCase):
    def auth(self):
        return YandexIDAuth(
            AuthConfig(
                enabled=True,
                client_id="client-id",
                client_secret="client-secret",
                redirect_uri="https://drevo.gribovka.ru/auth/callback",
                allowed_logins=frozenset({"alice"}),
                editor_logins=frozenset({"editor"}),
                admin_logins=frozenset({"admin"}),
                session_secret="session-secret",
            )
        )

    def test_session_cookie_round_trips_allowed_login(self):
        auth = self.auth()

        cookie_value = auth.create_session_value("alice", now=100)

        self.assertEqual(
            auth.login_from_cookie_header(f"family_tree_session={cookie_value}", now=101),
            "alice",
        )

    def test_tampered_session_cookie_is_rejected(self):
        auth = self.auth()
        cookie_value = auth.create_session_value("alice", now=100)

        self.assertIsNone(
            auth.login_from_cookie_header(f"family_tree_session={cookie_value}x", now=101)
        )

    def test_health_and_auth_routes_are_public(self):
        auth = self.auth()

        self.assertTrue(auth.is_public_path("/api/health"))
        self.assertTrue(auth.is_public_path("/auth/login"))
        self.assertTrue(auth.is_public_path("/auth/logged-out"))
        self.assertFalse(auth.is_public_path("/api/person/node7"))

    def test_write_access_requires_editor_or_admin(self):
        auth = self.auth()

        self.assertFalse(auth.can_write("alice"))
        self.assertTrue(auth.can_write("editor"))
        self.assertTrue(auth.can_write("admin"))

    def test_authorization_url_uses_yandex_ru_oauth_endpoint(self):
        auth = self.auth()

        authorization_url = auth.authorization_url("state-value")

        self.assertTrue(
            authorization_url.startswith("https://oauth.yandex.ru/authorize?"),
            authorization_url,
        )

    def test_authorization_url_can_force_account_selection(self):
        auth = self.auth()

        authorization_url = auth.authorization_url("state-value", force_confirm=True)

        self.assertIn("force_confirm=yes", authorization_url)

    def test_token_exchange_uses_yandex_ru_oauth_endpoint(self):
        auth = self.auth()
        captured_request = None

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return b'{"access_token":"token"}'

        def fake_urlopen(request, timeout):
            nonlocal captured_request
            captured_request = request
            return FakeResponse()

        with patch.object(urllib.request, "urlopen", fake_urlopen):
            auth.exchange_code("code-value")

        self.assertIsNotNone(captured_request)
        self.assertEqual(captured_request.full_url, "https://oauth.yandex.ru/token")


class RateLimiterTest(unittest.TestCase):
    def test_blocks_after_limit_inside_window(self):
        limiter = PersonalDataHandler.rate_limiter.__class__(limit=2, window_seconds=60)

        self.assertTrue(limiter.allow("ip", now=100))
        self.assertTrue(limiter.allow("ip", now=101))
        self.assertFalse(limiter.allow("ip", now=102))
        self.assertTrue(limiter.allow("ip", now=161))


class ApiRoutesTest(unittest.TestCase):
    def test_parse_api_path_ignores_query_string(self):
        self.assertEqual(
            parse_api_path("/api/person/node7/photos?cache=1"),
            ["api", "person", "node7", "photos"],
        )

    def test_parse_api_path_decodes_url_parts(self):
        self.assertEqual(
            parse_api_path("/api/person/node%207/messages"),
            ["api", "person", "node 7", "messages"],
        )


class ResponseHeadersTest(unittest.TestCase):
    def test_same_origin_responses_do_not_allow_all_origins(self):
        class FakeHandler:
            def __init__(self):
                self.headers = []

            def send_header(self, name, value):
                self.headers.append((name, value))

        handler = FakeHandler()

        setup_cors_headers(handler)

        self.assertNotIn(("Access-Control-Allow-Origin", "*"), handler.headers)


class LogoutButtonTest(unittest.TestCase):
    def test_main_pages_link_to_yandex_logout(self):
        for page in ("index.html", "person.html"):
            with self.subTest(page=page):
                html = (SITE_ROOT / page).read_text(encoding="utf-8")

                self.assertIn('href="/auth/logout"', html)
                self.assertIn("Выйти", html)
                self.assertIn("logout-button", html)

    def test_main_pages_use_versioned_stylesheets_for_logout_button(self):
        for page in ("index.html", "person.html"):
            with self.subTest(page=page):
                html = (SITE_ROOT / page).read_text(encoding="utf-8")

                self.assertIn('assets/css/main.css?v=', html)


class AuthGuardTest(unittest.TestCase):
    def make_handler(self, path, cookie=None):
        auth = YandexIDAuth(
            AuthConfig(
                enabled=True,
                client_id="client-id",
                client_secret="client-secret",
                redirect_uri="https://drevo.gribovka.ru/auth/callback",
                allowed_logins=frozenset({"alice"}),
                session_secret="session-secret",
            )
        )

        class FakeHandler:
            def __init__(self):
                self.path = path
                self.auth = auth
                self.headers = {}
                self.responses = []
                self.sent_headers = []
                self.ended = False

            def send_response(self, code):
                self.responses.append(code)

            def send_header(self, name, value):
                self.sent_headers.append((name, value))

            def end_headers(self):
                self.ended = True

        handler = FakeHandler()
        if cookie:
            handler.headers["Cookie"] = cookie
        return handler, auth

    def test_protected_page_redirects_to_login_without_session(self):
        handler, _ = self.make_handler("/person.html?id=node7")

        self.assertFalse(PersonalDataHandler._require_auth(handler))

        self.assertEqual(handler.responses, [302])
        self.assertIn(
            ("Location", "/auth/login?next=%2Fperson.html%3Fid%3Dnode7"),
            handler.sent_headers,
        )

    def test_force_confirm_login_redirects_to_yandex_account_selection(self):
        handler, _ = self.make_handler("/auth/login?force_confirm=yes")

        PersonalDataHandler.handle_auth_login(handler)

        self.assertEqual(handler.responses, [302])
        locations = [value for name, value in handler.sent_headers if name == "Location"]
        self.assertEqual(len(locations), 1)
        self.assertIn("https://oauth.yandex.ru/authorize?", locations[0])
        self.assertIn("force_confirm=yes", locations[0])

    def test_protected_page_allows_valid_session(self):
        handler, auth = self.make_handler("/person.html?id=node7")
        handler.headers["Cookie"] = (
            f"family_tree_session={auth.create_session_value('alice')}"
        )

        self.assertTrue(PersonalDataHandler._require_auth(handler))

    def test_health_check_does_not_require_auth(self):
        handler, _ = self.make_handler("/api/health")

        self.assertTrue(PersonalDataHandler._require_auth(handler))

    def test_logout_expires_session_cookie_and_redirects_to_logged_out_page(self):
        handler, _ = self.make_handler("/auth/logout")

        PersonalDataHandler.handle_auth_logout(handler)

        self.assertEqual(handler.responses, [302])
        self.assertIn(("Location", "/auth/logged-out"), handler.sent_headers)
        self.assertTrue(
            any(
                name == "Set-Cookie"
                and "family_tree_session=" in value
                and "Max-Age=0" in value
                for name, value in handler.sent_headers
            )
        )

    def test_logged_out_page_is_rendered_without_starting_oauth(self):
        handler, _ = self.make_handler("/auth/logged-out")
        written = []

        class FakeWriter:
            def write(self, data):
                written.append(data)

        handler.wfile = FakeWriter()

        PersonalDataHandler.handle_auth_logged_out(handler)

        body = b"".join(written).decode("utf-8")
        self.assertEqual(handler.responses, [200])
        self.assertIn(("Content-Type", "text/html; charset=utf-8"), handler.sent_headers)
        self.assertIn("Вы вышли из аккаунта", body)
        self.assertIn('href="/auth/login"', body)

    def test_logged_out_page_explains_access_denied(self):
        handler, _ = self.make_handler("/auth/logged-out?reason=access-denied")
        written = []

        class FakeWriter:
            def write(self, data):
                written.append(data)

        handler.wfile = FakeWriter()

        PersonalDataHandler.handle_auth_logged_out(handler)

        body = b"".join(written).decode("utf-8")
        self.assertEqual(handler.responses, [200])
        self.assertIn("Доступа нет", body)
        self.assertIn("не добавлен в список доступа", body)
        self.assertIn('href="/auth/login?force_confirm=yes"', body)
        self.assertNotIn("passport.yandex.ru", body)
        self.assertNotIn('href="/auth/login">Войти другим аккаунтом</a>', body)

    def test_disallowed_yandex_login_redirects_to_access_denied_logout_page(self):
        handler, auth = self.make_handler("/auth/callback?state=state-value&code=code-value")
        handler.headers["Cookie"] = (
            f"family_tree_oauth_state={auth.create_state_value('state-value', '/')}"
        )
        auth.exchange_code = lambda code: {"access_token": "token-value"}
        auth.fetch_user_info = lambda token: {"login": "bob"}

        PersonalDataHandler.handle_auth_callback(handler)

        self.assertEqual(handler.responses, [302])
        self.assertIn(
            ("Location", "/auth/logged-out?reason=access-denied"),
            handler.sent_headers,
        )
        self.assertTrue(
            any(
                name == "Set-Cookie"
                and "family_tree_session=" in value
                and "Max-Age=0" in value
                for name, value in handler.sent_headers
            )
        )
        self.assertTrue(
            any(
                name == "Set-Cookie"
                and "family_tree_oauth_state=" in value
                and "Max-Age=0" in value
                for name, value in handler.sent_headers
            )
        )

    def test_write_request_requires_editor_session(self):
        handler, auth = self.make_handler("/api/person/node7/messages")
        handler.command = "POST"
        handler.client_address = ("127.0.0.1", 12345)
        handler.headers["Cookie"] = (
            f"family_tree_session={auth.create_session_value('alice')}"
        )

        self.assertFalse(PersonalDataHandler._require_auth(handler))
        self.assertEqual(handler.responses, [403])


class FileServingTest(unittest.TestCase):
    def test_person_data_serves_from_configured_data_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "private_data"
            photo_dir = data_dir / "photos" / "node1"
            photo_dir.mkdir(parents=True)
            (photo_dir / "face.png").write_bytes(b"image")

            class FakeHandler:
                def __init__(self):
                    self.responses = []
                    self.headers = []
                    self.body = bytearray()

                    class Writer:
                        def __init__(self, outer):
                            self.outer = outer

                        def write(self, data):
                            self.outer.body.extend(data)

                    self.wfile = Writer(self)

                def send_response(self, code):
                    self.responses.append(code)

                def send_header(self, name, value):
                    self.headers.append((name, value))

                def end_headers(self):
                    pass

                def send_error(self, code, message=None):
                    self.responses.append(code)

            handler = FakeHandler()

            serve_file(handler, "/person_data/photos/node1/face.png", data_dir=data_dir)

            self.assertEqual(handler.responses, [200])
            self.assertEqual(bytes(handler.body), b"image")

    def test_person_data_serves_photos_from_object_storage(self):
        class FakeHandler:
            def __init__(self):
                self.responses = []
                self.headers = []
                self.body = bytearray()

                class Writer:
                    def __init__(self, outer):
                        self.outer = outer

                    def write(self, data):
                        self.outer.body.extend(data)

                self.wfile = Writer(self)

            def send_response(self, code):
                self.responses.append(code)

            def send_header(self, name, value):
                self.headers.append((name, value))

            def end_headers(self):
                pass

            def send_error(self, code, message=None):
                self.responses.append(code)

        handler = FakeHandler()
        object_storage = FakeReadableObjectStorage({
            "photos/node1/face.png": {
                "data": b"image-from-s3",
                "content_type": "image/png",
            }
        })

        serve_file(
            handler,
            "/person_data/photos/node1/face.png",
            data_dir=Path("/does/not/exist"),
            object_storage=object_storage,
        )

        self.assertEqual(handler.responses, [200])
        self.assertIn(("Content-Type", "image/png"), handler.headers)
        self.assertEqual(bytes(handler.body), b"image-from-s3")


class CachePolicyTest(unittest.TestCase):
    def test_static_assets_are_cacheable(self):
        self.assertTrue(PersonalDataHandler.is_cacheable_path("/assets/js/app.js"))
        self.assertTrue(PersonalDataHandler.is_cacheable_path("/assets/css/main.css"))
        self.assertTrue(PersonalDataHandler.is_cacheable_path("/family_tree_vector.svg"))
        self.assertTrue(
            PersonalDataHandler.is_cacheable_path(
                "/person_data/photos/node7/example.jpg"
            )
        )

    def test_html_api_and_json_data_are_not_cacheable(self):
        self.assertFalse(PersonalDataHandler.is_cacheable_path("/"))
        self.assertFalse(PersonalDataHandler.is_cacheable_path("/person.html?id=node7"))
        self.assertFalse(PersonalDataHandler.is_cacheable_path("/api/person/node7"))
        self.assertFalse(
            PersonalDataHandler.is_cacheable_path("/person_data/messages/node7.json")
        )


if __name__ == "__main__":
    unittest.main()
