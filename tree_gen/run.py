#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Новый основной файл для запуска программы построения генеалогического дерева
"""

from cli import main
import sys
import os

# Универсальное добавление текущей папки в путь Python
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


if __name__ == "__main__":
    main()
