"""Сервис для работы с блогами."""

from storage.json_store import JsonListStore


class BlogService:
    def __init__(self, blog_dir):
        self.store = JsonListStore(blog_dir)

    def get_posts(self, person_id):
        """Получение записей блога персоны"""
        return self.store.load(person_id)

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
        return self.store.load(person_id)

    def _save_posts(self, person_id, posts):
        """Сохранение записей блога"""
        self.store.save(person_id, posts)
