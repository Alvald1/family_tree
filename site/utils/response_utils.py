"""
Утилиты для работы с HTTP ответами и общими функциями
"""

import json
from datetime import datetime

NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}

STATIC_CACHE_HEADERS = {
    "Cache-Control": "public, max-age=3600",
}


def send_json_response(handler, data):
    """Отправка JSON ответа"""
    response = json.dumps(data, ensure_ascii=False)

    handler.send_response(200)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Content-Length', str(len(response.encode('utf-8'))))
    handler.end_headers()
    handler.wfile.write(response.encode('utf-8'))


def get_current_timestamp():
    """Получение текущего времени в ISO формате"""
    return datetime.now().isoformat()


def setup_cors_headers(handler, cacheable=False):
    """Настройка общих заголовков ответа для same-origin сайта."""
    headers = STATIC_CACHE_HEADERS if cacheable else NO_CACHE_HEADERS
    for name, value in headers.items():
        handler.send_header(name, value)
