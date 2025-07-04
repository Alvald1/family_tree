#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Основной сервер для генеалогического дерева
"""

from handlers.http_handler import PersonalDataHandler
import socketserver
import sys
import os

# Добавляем текущую директорию в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def load_config():
    """Загружает конфигурацию из файла"""
    try:
        # Получаем путь к текущему файлу
        current_dir = os.path.dirname(os.path.abspath(
            __file__)) if '__file__' in globals() else os.getcwd()
        config_path = os.path.join(current_dir, 'config', 'site_config.py')

        if not os.path.exists(config_path):
            print(f"⚠️  Конфиг файл не найден: {config_path}")
            return "127.0.0.1", 8000, False

        # Читаем конфиг как обычный Python файл
        config_vars = {}
        with open(config_path, 'r', encoding='utf-8') as f:
            exec(f.read(), config_vars)

        host = config_vars.get('host', '127.0.0.1')
        port = config_vars.get('port', 8000)
        debug = config_vars.get('debug', False)

        return host, port, debug

    except Exception as e:
        print(f"⚠️  Ошибка загрузки конфигурации: {e}")
        return "127.0.0.1", 8000, False


def main():
    """Главная функция запуска сервера"""
    host, port, debug = load_config()

    print(f"Запуск HTTP сервера на порту {port}")
    print(f"Откройте в браузере: http://{host}:{port}")
    print("Доступны следующие функции:")
    print("- Просмотр генеалогического дерева")
    print("- Персональные страницы для каждого человека")
    print("- Загрузка и просмотр фотографий")
    print("- Ведение личных блогов")
    print("- Сообщения и чат")
    print("Для остановки нажмите Ctrl+C")

    try:
        with socketserver.TCPServer((host, port), PersonalDataHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"Порт {port} уже занят. Попробуйте другой порт.")
        else:
            print(f"Ошибка запуска сервера: {e}")


if __name__ == "__main__":
    main()
