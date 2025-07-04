"""
Сервис для работы с информацией о персонах
"""

import os
import re


class PersonService:
    def __init__(self):
        self.source_file = os.path.join('..', 'source.txt')

    def get_person_info(self, person_id):
        """Получение информации о персоне из source.txt"""
        try:
            # Извлекаем числовой ID из person_id (убираем префикс "node" если
            # есть)
            numeric_id = person_id
            if person_id.startswith('node'):
                numeric_id = person_id[4:]  # убираем "node"

            if os.path.exists(self.source_file):
                with open(self.source_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line in lines:
                    line = line.strip()
                    search_pattern = f"{numeric_id} -"

                    if line.startswith(search_pattern):
                        person_info = line[line.find('-') + 1:].strip()

                        # Попытка извлечь даты из последних скобок
                        dates_match = re.search(
                            r'\(([^)]+)\)(?![^(]*\()', person_info)
                        dates = dates_match.group(1) if dates_match else ''

                        # Если в скобках не даты, пробуем найти другие скобки
                        if dates and not re.search(r'[\d\-]', dates):
                            all_dates = re.findall(
                                r'\(([^)]*\d[^)]*)\)', person_info)
                            dates = all_dates[-1] if all_dates else ''

                        name = re.sub(r'\s*\([^)]+\)', '', person_info).strip()

                        return {
                            'id': person_id,
                            'name': name,
                            'dates': dates,
                            'full_info': person_info
                        }

            # Если персона не найдена
            return {
                'id': person_id,
                'name': f'Персона {person_id}',
                'dates': '',
                'full_info': f'Персона {person_id}'
            }

        except Exception as e:
            print(f"Ошибка получения информации о персоне: {e}")
            raise
