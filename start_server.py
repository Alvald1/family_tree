#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Запуск сервера семейного дерева
"""

import subprocess
import sys
import os
from pathlib import Path


def load_config():
    """Загружает конфигурацию из файла"""
    try:
        # Получаем путь к конфиг файлу
        config_file = Path(__file__).parent / 'site' / \
            'config' / 'site_config.py'

        if not config_file.exists():
            print(f"⚠️  Конфиг файл не найден: {config_file}")
            return "127.0.0.1", 8000

        # Читаем конфиг как обычный Python файл
        spec = {}
        with open(config_file, 'r', encoding='utf-8') as f:
            exec(f.read(), spec)

        host = spec.get('host', '127.0.0.1')
        port = spec.get('port', 8000)

        return host, port

    except Exception as e:
        print(f"⚠️  Ошибка загрузки конфигурации: {e}")
        return "127.0.0.1", 8000


# Загружаем конфигурацию
host, port = load_config()


def main():
    """Главная функция запуска"""

    # Переходим в папку сайта
    site_dir = Path(__file__).parent / 'site'

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
