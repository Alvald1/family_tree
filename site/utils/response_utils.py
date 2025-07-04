"""
Утилиты для работы с HTTP ответами и общими функциями
"""

import json
from datetime import datetime


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


def setup_cors_headers(handler):
    """Настройка CORS заголовков"""
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.send_header(
        'Access-Control-Allow-Methods',
        'GET, POST, PUT, DELETE, OPTIONS')
    handler.send_header('Access-Control-Allow-Headers', 'Content-Type')
    handler.send_header(
        'Cache-Control',
        'no-cache, no-store, must-revalidate')
    handler.send_header('Pragma', 'no-cache')
    handler.send_header('Expires', '0')
