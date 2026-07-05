#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Основной сервер для генеалогического дерева."""

from handlers.http_handler import PersonalDataHandler
import socketserver
import sys
import os
from config.settings import load_settings

# Добавляем текущую директорию в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class FamilyTreeTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


def main():
    """Главная функция запуска сервера"""
    settings = load_settings()
    host, port = settings.host, settings.port
    PersonalDataHandler.configure(settings)

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
        with FamilyTreeTCPServer((host, port), PersonalDataHandler) as httpd:
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
