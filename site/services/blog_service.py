"""
Сервис для работы с блогами
"""

import json
from pathlib import Path


class BlogService:
    def __init__(self, blog_dir):
        self.blog_dir = Path(blog_dir)
        self.blog_dir.mkdir(exist_ok=True)

    def get_posts(self, person_id):
        """Получение записей блога персоны"""
        blog_file = self.blog_dir / f"{person_id}.json"

        if blog_file.exists():
            with open(blog_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def add_post(self, person_id, post_info):
        """Добавление записи в блог"""
        posts = self._load_posts(person_id)

        # Добавление новой записи в начало списка
        posts.insert(0, post_info)

        self._save_posts(person_id, posts)

    def delete_post(self, person_id, post_index):
        """Удаление записи блога"""
        posts = self._load_posts(person_id)

        if post_index >= len(posts):
            raise IndexError("Запись не найдена")

        # Удаление записи
        posts.pop(post_index)
        self._save_posts(person_id, posts)

    def _load_posts(self, person_id):
        """Загрузка записей блога"""
        blog_file = self.blog_dir / f"{person_id}.json"

        if blog_file.exists():
            with open(blog_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save_posts(self, person_id, posts):
        """Сохранение записей блога"""
        blog_file = self.blog_dir / f"{person_id}.json"
        with open(blog_file, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
