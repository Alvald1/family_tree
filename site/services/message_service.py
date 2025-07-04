"""
Сервис для работы с сообщениями
"""

import json
from pathlib import Path


class MessageService:
    def __init__(self, messages_dir):
        self.messages_dir = Path(messages_dir)
        self.messages_dir.mkdir(exist_ok=True)

    def get_messages(self, person_id):
        """Получение сообщений чата персоны"""
        messages_file = self.messages_dir / f"{person_id}.json"

        if messages_file.exists():
            with open(messages_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_messages(self, person_id, messages):
        """Сохранение сообщений чата персоны"""
        messages_file = self.messages_dir / f"{person_id}.json"
        with open(messages_file, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
