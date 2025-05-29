#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой HTTP сервер для отображения SVG файла генеалогического дерева
"""

import http.server
import socketserver
import os


class StaticFileHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Если запрос к корню, отдаем index.html
        if self.path == '/':
            self.path = '/index.html'

        # Используем стандартный обработчик для всех файлов
        return super().do_GET()

    def end_headers(self):
        # Добавляем заголовки для корректного отображения SVG и отключения
        # кэширования
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header(
            'Cache-Control',
            'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        if self.path.endswith('.svg'):
            self.send_header('Content-Type', 'image/svg+xml')
        super().end_headers()


def main():
    PORT = 8002

    print(f"Запуск HTTP сервера на порту {PORT}")
    print(f"Откройте в браузере: http://localhost:{PORT}")
    print("Для остановки нажмите Ctrl+C")

    try:
        with socketserver.TCPServer(("", PORT), StaticFileHandler) as httpd:
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
