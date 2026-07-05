"""Сервис для работы с сообщениями."""

from storage.json_store import JsonListStore


class MessageService:
    def __init__(self, messages_dir):
        self.store = JsonListStore(messages_dir)

    def get_messages(self, person_id):
        """Получение сообщений чата персоны"""
        return self.store.load(person_id)

    def save_messages(self, person_id, messages):
        """Сохранение сообщений чата персоны"""
        self.store.save(person_id, messages)
