#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Запуск сервера семейного дерева."""

import subprocess
import sys
import os
from pathlib import Path


SITE_DIR = Path(__file__).parent / "site"
sys.path.insert(0, str(SITE_DIR))

from config.settings import load_settings


settings = load_settings(SITE_DIR)
host, port = settings.host, settings.port


def main():
    """Главная функция запуска"""

    # Переходим в папку сайта
    site_dir = SITE_DIR

    if not site_dir.exists():
        print("❌ Папка 'site' не найдена!")
        print("Убедитесь, что вы запускаете скрипт из корневой папки проекта.")
        return 1

    os.chdir(site_dir)

    # Проверяем наличие основных файлов
    required_files = [
        'index.html',
        'person.html',
        'server.py',
        'family_tree_vector.svg'
    ]

    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)

    if missing_files:
        print("❌ Отсутствуют необходимые файлы:")
        for file in missing_files:
            print(f"   - {file}")
        return 1

    print("🌳 Запуск сервера семейного дерева...")
    print(f"📁 Рабочая папка: {site_dir.absolute()}")
    print(f"🌐 Сайт будет доступен по адресу: http://{host}:{port}")
    print("⏹️  Для остановки нажмите Ctrl+C")
    print("-" * 50)

    try:
        # Запускаем сервер
        subprocess.run([sys.executable, 'server.py'], check=True)
    except KeyboardInterrupt:
        print("\n✅ Сервер остановлен пользователем")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка запуска сервера: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
