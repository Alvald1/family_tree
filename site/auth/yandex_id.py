"""Yandex ID OAuth helpers."""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from http.cookies import SimpleCookie


AUTHORIZE_URL = "https://oauth.yandex.ru/authorize"
TOKEN_URL = "https://oauth.yandex.ru/token"
USER_INFO_URL = "https://login.yandex.ru/info?format=json"


@dataclass(frozen=True)
class AuthConfig:
    enabled: bool = False
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""
    allowed_logins: frozenset = frozenset()
    editor_logins: frozenset = frozenset()
    admin_logins: frozenset = frozenset()
    session_secret: str = ""
    session_cookie_name: str = "family_tree_session"
    state_cookie_name: str = "family_tree_oauth_state"
    session_ttl_seconds: int = 7 * 24 * 60 * 60
    state_ttl_seconds: int = 10 * 60


def load_auth_config(environ=None):
    environ = environ or os.environ
    enabled_value = environ.get("FAMILY_TREE_AUTH_ENABLED")
    explicit_enabled = (
        _env_bool(enabled_value)
        if enabled_value is not None
        else _env_bool(environ.get("FAMILY_TREE_CONTAINER_RUNTIME"))
    )
    allowed_logins = frozenset(
        login.strip().lower()
        for login in environ.get("YANDEX_ALLOWED_LOGINS", "").split(",")
        if login.strip()
    )
    editor_logins = frozenset(
        login.strip().lower()
        for login in environ.get("YANDEX_EDITOR_LOGINS", "").split(",")
        if login.strip()
    )
    admin_logins = frozenset(
        login.strip().lower()
        for login in environ.get("YANDEX_ADMIN_LOGINS", "").split(",")
        if login.strip()
    )
    config = AuthConfig(
        enabled=explicit_enabled,
        client_id=environ.get("YANDEX_CLIENT_ID", ""),
        client_secret=environ.get("YANDEX_CLIENT_SECRET", ""),
        redirect_uri=environ.get("YANDEX_REDIRECT_URI", ""),
        allowed_logins=allowed_logins,
        editor_logins=editor_logins,
        admin_logins=admin_logins,
        session_secret=environ.get("FAMILY_TREE_SESSION_SECRET", ""),
    )

    if config.enabled:
        missing = [
            name
            for name, value in {
                "YANDEX_CLIENT_ID": config.client_id,
                "YANDEX_CLIENT_SECRET": config.client_secret,
                "YANDEX_REDIRECT_URI": config.redirect_uri,
                "YANDEX_ALLOWED_LOGINS": config.allowed_logins,
                "FAMILY_TREE_SESSION_SECRET": config.session_secret,
            }.items()
            if not value
        ]
        if missing:
            raise ValueError(
                "Yandex ID auth is enabled, but required settings are missing: "
                + ", ".join(missing)
            )
        if not _is_strong_session_secret(config.session_secret):
            raise ValueError(
                "FAMILY_TREE_SESSION_SECRET must be at least 32 characters "
                "and must not use the example value"
            )

    return config


class YandexIDAuth:
    def __init__(self, config):
        self.config = config

    def is_public_path(self, path):
        request_path = urllib.parse.urlparse(path).path
        return request_path in {
            "/api/health",
            "/auth/login",
            "/auth/callback",
            "/auth/logout",
            "/auth/logged-out",
        }

    def create_session_value(self, login, now=None):
        now = int(now if now is not None else time.time())
        payload = {
            "login": login.lower(),
            "iat": now,
            "exp": now + self.config.session_ttl_seconds,
        }
        return self._sign(payload)

    def login_from_cookie_header(self, cookie_header, now=None):
        payload = self._payload_from_cookie(
            cookie_header,
            self.config.session_cookie_name,
            now=now,
        )
        if not payload:
            return None
        login = str(payload.get("login", "")).lower()
        if login not in self.config.allowed_logins:
            return None
        return login

    def can_write(self, login):
        login = str(login or "").lower()
        return login in self.config.editor_logins or login in self.config.admin_logins

    def create_state_value(self, state, next_path="/", now=None):
        now = int(now if now is not None else time.time())
        return self._sign(
            {
                "state": state,
                "next": _safe_next_path(next_path),
                "exp": now + self.config.state_ttl_seconds,
            }
        )

    def state_from_cookie_header(self, cookie_header, now=None):
        return self._payload_from_cookie(
            cookie_header,
            self.config.state_cookie_name,
            now=now,
        )

    def authorization_url(self, state, force_confirm=False):
        params = {
            "response_type": "code",
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "scope": "login:info login:email",
            "state": state,
        }
        if force_confirm:
            params["force_confirm"] = "yes"
        query = urllib.parse.urlencode(params)
        return f"{AUTHORIZE_URL}?{query}"

    def exchange_code(self, code):
        body = urllib.parse.urlencode(
            {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            TOKEN_URL,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def fetch_user_info(self, access_token):
        request = urllib.request.Request(
            USER_INFO_URL,
            headers={"Authorization": f"OAuth {access_token}"},
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def session_set_cookie(self, login):
        return _cookie_header(
            self.config.session_cookie_name,
            self.create_session_value(login),
            self.config.session_ttl_seconds,
        )

    def state_set_cookie(self, state, next_path):
        return _cookie_header(
            self.config.state_cookie_name,
            self.create_state_value(state, next_path),
            self.config.state_ttl_seconds,
        )

    def expired_session_cookie(self):
        return _cookie_header(self.config.session_cookie_name, "", 0)

    def expired_state_cookie(self):
        return _cookie_header(self.config.state_cookie_name, "", 0)

    def _payload_from_cookie(self, cookie_header, cookie_name, now=None):
        if not cookie_header:
            return None
        cookie = SimpleCookie()
        cookie.load(cookie_header)
        morsel = cookie.get(cookie_name)
        if not morsel:
            return None
        payload = self._verify(morsel.value)
        if not payload:
            return None
        now = int(now if now is not None else time.time())
        if int(payload.get("exp", 0)) < now:
            return None
        return payload

    def _sign(self, payload):
        payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode(
            "utf-8"
        )
        payload_part = _urlsafe_b64(payload_json)
        signature = hmac.new(
            self.config.session_secret.encode("utf-8"),
            payload_part.encode("ascii"),
            hashlib.sha256,
        ).digest()
        return f"{payload_part}.{_urlsafe_b64(signature)}"

    def _verify(self, value):
        try:
            payload_part, signature_part = value.split(".", 1)
        except ValueError:
            return None
        expected = hmac.new(
            self.config.session_secret.encode("utf-8"),
            payload_part.encode("ascii"),
            hashlib.sha256,
        ).digest()
        actual = _urlsafe_b64_decode(signature_part)
        if not hmac.compare_digest(expected, actual):
            return None
        try:
            return json.loads(_urlsafe_b64_decode(payload_part).decode("utf-8"))
        except (ValueError, json.JSONDecodeError):
            return None


def _env_bool(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _is_strong_session_secret(value):
    if not value or len(value) < 32:
        return False
    return value != "change-me-to-a-long-random-secret"


def _cookie_header(name, value, max_age):
    return (
        f"{name}={value}; Max-Age={max_age}; Path=/; "
        "HttpOnly; Secure; SameSite=Lax"
    )


def _safe_next_path(value):
    parsed = urllib.parse.urlparse(value or "/")
    if parsed.scheme or parsed.netloc:
        return "/"
    path = parsed.path or "/"
    if not path.startswith("/"):
        return "/"
    return path + (f"?{parsed.query}" if parsed.query else "")


def _urlsafe_b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _urlsafe_b64_decode(value):
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))
