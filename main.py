#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Программа для построения генеалогического дерева с использованием Graphviz
"""

import re
import graphviz
from typing import Dict, List, Tuple, Set


class FamilyTreeBuilder:
    def __init__(self):
        # номер -> полная информация о человеке
        self.people: Dict[int, str] = {}
        # (родитель1, родитель2, дети)
        self.marriages: List[Tuple[int, int, List[int]]] = []
        # (родитель, ребенок)
        self.single_parent_children: List[Tuple[int, int]] = []
        # (родитель1, родитель2) - браки без детей
        self.childless_marriages: List[Tuple[int, int]] = []
        # (родитель1, родитель2) - браки с неизвестными детьми
        self.unknown_children_marriages: List[Tuple[int, int]] = []

    def parse_source_file(self, filename: str):
        """Парсинг исходного файла с данными о людях и связях"""
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # Очистка данных
        self.people.clear()
        self.marriages.clear()
        self.single_parent_children.clear()
        self.childless_marriages.clear()
        self.unknown_children_marriages.clear()

        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue

            # Сначала парсим связи (поддерживаем знак вопроса для неизвестных супругов и детей)
            # Форматы:
            # номер1 -- номер2 (дети) - брак с известными детьми
            # номер1 -- номер2 (?) - брак с неизвестными детьми
            # номер1 -- номер2 - брак без детей
            # номер1 -- ? (дети) - брак с неизвестным супругом
            # номер1 -- ? (?) - брак с неизвестным супругом и неизвестными детьми
            # номер1 -- ? - брак с неизвестным супругом без детей
            relation_match = re.match(
                r'^(\d+)\s*(?:--|->)\s*(\?|\d+)(?:\s*\(([^)]*)\))?$', line)
            if relation_match:
                parent1 = int(relation_match.group(1))
                parent2_str = relation_match.group(2)
                children_str = relation_match.group(
                    3) if relation_match.group(3) is not None else None

                # Обрабатываем неизвестного супруга
                if parent2_str == '?':
                    # Создаем временного неизвестного супруга
                    unknown_id = self._get_next_unknown_id()
                    unknown_name = "?"
                    self.people[unknown_id] = unknown_name
                    parent2 = unknown_id
                else:
                    parent2 = int(parent2_str)

                # Обрабатываем детей
                if children_str is None:
                    # Нет скобок - брак без детей
                    self.childless_marriages.append((parent1, parent2))
                elif children_str.strip() == '?':
                    # Скобки с вопросом - неизвестные дети
                    self.unknown_children_marriages.append((parent1, parent2))
                elif children_str.strip() == '':
                    # Пустые скобки - брак без детей
                    self.childless_marriages.append((parent1, parent2))
                else:
                    # Есть конкретные дети - обычный брак
                    children = []
                    for child_str in children_str.split(','):
                        child_str = child_str.strip()
                        if child_str and child_str.isdigit():
                            children.append(int(child_str))
                    self.marriages.append((parent1, parent2, children))
                continue

            # Потом парсим людей (формат: номер - имя [(даты)])
            person_match = re.match(r'^(\d+)\s*-\s*(.+)$', line)
            if person_match:
                number = int(person_match.group(1))
                info = person_match.group(2).strip()

                # Нормализуем информацию о человеке
                normalized_info = self._normalize_person_info(info)
                self.people[number] = normalized_info
                continue

    def create_family_tree(self, output_filename: str = 'family_tree'):
        """Создание графа генеалогического дерева"""
        dot = graphviz.Digraph(comment='Генеалогическое дерево')

        # Настройки для высокого разрешения
        dot.attr(rankdir='TB', bgcolor='white', size='20,30!')
        dot.attr(dpi='300')  # Высокое разрешение 300 DPI
        dot.attr(resolution='300')  # Дополнительная настройка разрешения

        dot.attr(
            'node',
            shape='box',
            style='filled,rounded',
            fontname='Arial',
            fontsize='12')  # Увеличиваем размер шрифта для читаемости
        # Увеличиваем размер шрифта для рёбер
        dot.attr('edge', fontname='Arial', fontsize='10')

        # Добавляем всех людей как узлы с разными цветами для разных поколений
        for person_id, info in self.people.items():
            formatted_info = self._format_person_info(info)

            # Определяем цвет узла по году рождения
            birth_year = self._extract_birth_year(info)
            color = self._get_generation_color(birth_year, person_id >= 1000)

            dot.node(str(person_id), formatted_info, fillcolor=color)

        # Обрабатываем браки
        marriage_counter = 1
        for parent1, parent2, children in self.marriages:
            # Создаем узел брака
            marriage_node = f"marriage_{marriage_counter}"
            dot.node(
                marriage_node,
                "♥",
                shape='circle',
                style='filled',
                fillcolor='#FFB6C1',
                width='0.5',
                height='0.5',
                fontsize='16')

            # Связываем родителей с браком
            dot.edge(str(parent1), marriage_node, dir='none', style='bold')
            dot.edge(str(parent2), marriage_node, dir='none', style='bold')

            # Связываем брак с детьми
            for child in children:
                dot.edge(marriage_node, str(child), color='blue')

            marriage_counter += 1

        # Обрабатываем браки без детей
        for parent1, parent2 in self.childless_marriages:
            # Создаем узел брака
            marriage_node = f"marriage_{marriage_counter}"
            dot.node(
                marriage_node,
                "♥",
                shape='circle',
                style='filled',
                fillcolor='#E6E6FA',  # Лавандовый цвет для браков без детей
                width='0.4',
                height='0.4',
                fontsize='14')

            # Связываем родителей с браком
            dot.edge(str(parent1), marriage_node, dir='none', style='bold')
            dot.edge(str(parent2), marriage_node, dir='none', style='bold')

            marriage_counter += 1

        # Обрабатываем браки с неизвестными детьми
        for parent1, parent2 in self.unknown_children_marriages:
            # Создаем узел брака
            marriage_node = f"marriage_{marriage_counter}"
            dot.node(
                marriage_node,
                "♥",
                shape='circle',
                style='filled',
                fillcolor='#FFFACD',  # Светло-желтый для браков с неизвестными детьми
                width='0.5',
                height='0.5',
                fontsize='12')

            # Связываем родителей с браком
            dot.edge(str(parent1), marriage_node, dir='none', style='bold')
            dot.edge(str(parent2), marriage_node, dir='none', style='bold')

            # Добавляем узел неизвестных детей
            unknown_children_node = f"unknown_children_{marriage_counter}"
            dot.node(
                unknown_children_node,
                "?",
                shape='box',
                style='filled,dashed',
                fillcolor='#F0F0F0',
                fontsize='10')

            dot.edge(
                marriage_node,
                unknown_children_node,
                color='gray',
                style='dashed')

            marriage_counter += 1

        # Обрабатываем одиночные связи родитель-ребенок
        processed_pairs: Set[Tuple[int, int]] = set()
        for parent, child in self.single_parent_children:
            # Избегаем дублирования
            if (parent, child) not in processed_pairs and (
                    child, parent) not in processed_pairs:
                dot.edge(str(parent), str(child), color='gray', style='dashed')
                processed_pairs.add((parent, child))

        # Сохраняем файл
        try:
            # Сохраняем PNG в высоком разрешении
            dot.render(output_filename, format='png', cleanup=False)

            # Дополнительно сохраняем в векторном формате
            svg_filename = f"{output_filename}_vector.svg"
            dot.render(f"{output_filename}_vector", format='svg', cleanup=True)

            # Исправляем viewBox в SVG файле
            self._fix_svg_viewbox(svg_filename)

            print(f"Генеалогическое дерево сохранено как:")
            print(f"  - {output_filename}.png (высокое разрешение 300 DPI)")
            print(
                f"  - {output_filename}_vector.svg (векторный формат с исправленным viewBox)")
        except Exception as e:
            print(f"Ошибка при сохранении: {e}")
            # Сохраняем хотя бы DOT файл
            with open(f"{output_filename}.dot", 'w', encoding='utf-8') as f:
                f.write(dot.source)
            print(f"DOT файл сохранен как {output_filename}.dot")

        return dot

    def _format_person_info(self, info: str) -> str:
        """Форматирование информации о человеке для отображения"""
        # Разбиваем длинные строки для лучшего отображения
        if len(info) > 25:
            # Пытаемся разбить по словам
            words = info.split()
            lines = []
            current_line = ""

            for word in words:
                if len(current_line + " " + word) <= 25:
                    if current_line:
                        current_line += " " + word
                    else:
                        current_line = word
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word

            if current_line:
                lines.append(current_line)

            return "\\n".join(lines)

        return info

    def print_statistics(self):
        """Вывод статистики по дереву"""
        print(f"\nСтатистика генеалогического дерева:")
        print(f"Всего людей: {len(self.people)}")
        print(f"Количество браков с детьми: {len(self.marriages)}")
        print(f"Количество браков без детей: {len(self.childless_marriages)}")
        print(
            f"Количество браков с неизвестными детьми: {len(self.unknown_children_marriages)}")
        print(f"Общее количество браков: {len(self.marriages) +
                                          len(self.childless_marriages) +
                                          len(self.unknown_children_marriages)}")
        print(
            f"Количество детей от браков: {sum(len(children) for _, _, children in self.marriages)}")
        print(f"Одиночные связи: {len(self.single_parent_children)}")

        # Дополнительная статистика
        total_married_people = set()
        for parent1, parent2, _ in self.marriages:
            total_married_people.add(parent1)
            total_married_people.add(parent2)
        for parent1, parent2 in self.childless_marriages:
            total_married_people.add(parent1)
            total_married_people.add(parent2)
        for parent1, parent2 in self.unknown_children_marriages:
            total_married_people.add(parent1)
            total_married_people.add(parent2)

        print(f"Количество людей в браке: {len(total_married_people)}")
        print(
            f"Количество одиноких людей: {len(self.people) - len(total_married_people)}")

    def _analyze_generations(self) -> Dict[str, List[int]]:
        """Анализ поколений по годам рождения"""
        generations = {
            "Дореволюционное поколение (до 1920)": [],
            "Первое поколение (1921-1940)": [],
            "Второе поколение (1941-1960)": [],
            "Третье поколение (1961-1980)": [],
            "Четвертое поколение (1981-2000)": [],
            "Пятое поколение (после 2000)": [],
            "Неизвестные супруги": []
        }

        for person_id, info in self.people.items():
            if person_id >= 1000:  # Неизвестные супруги
                generations["Неизвестные супруги"].append(person_id)
                continue

            birth_year = self._extract_birth_year(info)

            if birth_year <= 1920:
                generations["Дореволюционное поколение (до 1920)"].append(
                    person_id)
            elif 1921 <= birth_year <= 1940:
                generations["Первое поколение (1921-1940)"].append(person_id)
            elif 1941 <= birth_year <= 1960:
                generations["Второе поколение (1941-1960)"].append(person_id)
            elif 1961 <= birth_year <= 1980:
                generations["Третье поколение (1961-1980)"].append(person_id)
            elif 1981 <= birth_year <= 2000:
                generations["Четвертое поколение (1981-2000)"].append(person_id)
            else:
                generations["Пятое поколение (после 2000)"].append(person_id)

        return generations

    def _get_next_unknown_id(self) -> int:
        """Получить следующий ID для неизвестного супруга"""
        # Начинаем с 1000 для неизвестных супругов
        unknown_id = 1000
        while unknown_id in self.people:
            unknown_id += 1
        return unknown_id

    def _normalize_person_info(self, info: str) -> str:
        """Нормализация информации о человеке"""
        # Убираем лишние пробелы
        info = ' '.join(info.split())

        # Если нет дат в скобках, добавляем заглушку
        if '(' not in info:
            # Проверяем, есть ли год в конце строки
            year_match = re.search(r'\s(\d{4})$', info)
            if year_match:
                year = year_match.group(1)
                info = info.replace(f' {year}', f' ({year})')

        return info

    def _extract_birth_year(self, info: str) -> int:
        """Извлечение года рождения из информации о человеке"""
        # Ищем год в различных форматах
        year_patterns = [
            r'\((\d{4})-\d{4}\)',  # (1950-1999) - диапазон годов
            r'\((\d{4})\)',        # (1950) - только год
            r'\((\d{2})\.(\d{2})\.(\d{4})',  # (01.01.1950 - полная дата
            # (1950-... - год рождения с неизвестной смертью
            r'\((\d{4})-',
        ]

        for pattern in year_patterns:
            match = re.search(pattern, info)
            if match:
                # Всегда возвращаем первый найденный год (год рождения)
                if len(match.groups()) == 1:
                    return int(match.group(1))
                elif len(match.groups()) == 3:  # Полная дата
                    return int(match.group(3))
                else:
                    return int(match.group(1))

        # Если год не найден, пытаемся определить по поколению
        # или возвращаем средний год для неизвестных
        return 1950

    def _get_generation_color(
            self,
            birth_year: int,
            is_unknown: bool = False) -> str:
        """Определение цвета узла по году рождения"""
        if is_unknown:
            return '#F0F0F0'  # Серый для неизвестных супругов

        if birth_year <= 1920:
            return '#FFE4E1'  # Светло-розовый для очень старшего поколения
        elif 1921 <= birth_year <= 1940:
            return '#E6E6FA'  # Лавандовый для старшего поколения
        elif 1941 <= birth_year <= 1960:
            return '#E0E6FF'  # Светло-голубой для среднего поколения
        elif 1961 <= birth_year <= 1980:
            return '#E6FFE6'  # Светло-зеленый для молодого поколения
        elif 1981 <= birth_year <= 2000:
            return '#FFFACD'  # Светло-желтый для младшего поколения
        else:
            return '#FFE4E6'  # Светло-персиковый для детей

    def validate_data(self) -> List[str]:
        """Валидация данных и поиск проблем"""
        issues = []

        # Проверяем, что все родители в браках с детьми существуют
        for parent1, parent2, children in self.marriages:
            if parent1 not in self.people:
                issues.append(f"Родитель {parent1} не найден в списке людей")
            if parent2 not in self.people:
                issues.append(f"Родитель {parent2} не найден в списке людей")

            # Проверяем, что все дети существуют
            for child in children:
                if child not in self.people:
                    issues.append(f"Ребенок {child} не найден в списке людей")

        # Проверяем браки без детей
        for parent1, parent2 in self.childless_marriages:
            if parent1 not in self.people:
                issues.append(
                    f"Супруг {parent1} (брак без детей) не найден в списке людей")
            if parent2 not in self.people:
                issues.append(
                    f"Супруг {parent2} (брак без детей) не найден в списке людей")

        # Проверяем браки с неизвестными детьми
        for parent1, parent2 in self.unknown_children_marriages:
            if parent1 not in self.people:
                issues.append(
                    f"Супруг {parent1} (брак с неизвестными детьми) не найден в списке людей")
            if parent2 not in self.people:
                issues.append(
                    f"Супруг {parent2} (брак с неизвестными детьми) не найден в списке людей")

        # Проверяем одиночные связи
        for parent, child in self.single_parent_children:
            if parent not in self.people:
                issues.append(f"Родитель {parent} не найден в списке людей")
            if child not in self.people:
                issues.append(f"Ребенок {child} не найден в списке людей")

        return issues

    def print_validation_report(self):
        """Вывод отчета о валидации данных"""
        issues = self.validate_data()
        if issues:
            print("\n⚠️  Найдены проблемы в данных:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("\n✅ Данные прошли валидацию успешно")

    def find_data_issues(self) -> Dict[str, List[str]]:
        """Поиск различных проблем в данных"""
        issues = {
            "Неполные имена": [],
            "Неизвестные даты": [],
            "Возможные опечатки": [],
            "Одиночные дети": []
        }

        # Проверяем неполные имена
        for person_id, info in self.people.items():
            if person_id >= 1000:  # Пропускаем неизвестных супругов
                continue

            name_part = info.split('(')[0].strip()
            words = name_part.split()

            if len(words) == 1:
                issues["Неполные имена"].append(f"{person_id}: {name_part}")
            elif "неизвестны" in info:
                issues["Неизвестные даты"].append(f"{person_id}: {name_part}")

            # Проверяем возможные опечатки
            if any(typo in info for typo in ['Владислававна', 'Николая']):
                issues["Возможные опечатки"].append(f"{person_id}: {info}")

        # Ищем детей без родителей
        all_children = set()
        for _, _, children in self.marriages:
            all_children.update(children)

        for person_id in self.people:
            if person_id not in all_children and person_id < 1000:
                # Проверяем, не является ли этот человек корневым предком
                is_parent = any(person_id in [p1, p2]
                                for p1, p2, _ in self.marriages)
                if not is_parent:
                    name = self.people[person_id].split('(')[0].strip()
                    issues["Одиночные дети"].append(f"{person_id}: {name}")

        return issues

    def print_data_analysis(self):
        """Выводит анализ качества данных"""
        issues = self.find_data_issues()

        print("\n📊 АНАЛИЗ КАЧЕСТВА ДАННЫХ:")
        print("-" * 40)

        for category, problems in issues.items():
            if problems:
                print(f"\n⚠️  {category} ({len(problems)}):")
                for problem in problems[:5]:  # Показываем только первые 5
                    print(f"  - {problem}")
                if len(problems) > 5:
                    print(f"  ... и еще {len(problems) - 5}")
            else:
                print(f"\n✅ {category}: проблем не найдено")

    def find_largest_families(
            self, top_n: int = 3) -> List[Tuple[str, str, int]]:
        """Находит семьи с наибольшим количеством детей"""
        family_sizes = []
        for parent1, parent2, children in self.marriages:
            parent1_name = self.people.get(parent1, f"ID {parent1}")
            parent2_name = self.people.get(parent2, f"ID {parent2}")
            family_sizes.append((parent1_name, parent2_name, len(children)))

        return sorted(family_sizes, key=lambda x: x[2], reverse=True)[:top_n]

    def get_generation_statistics(self) -> Dict[str, int]:
        """Получает статистику по поколениям"""
        generations = {
            'Дореволюционное (до 1920)': 0,
            'Первое (1921-1940)': 0,
            'Второе (1941-1960)': 0,
            'Третье (1961-1980)': 0,
            'Четвертое (1981-2000)': 0,
            'Пятое (после 2000)': 0,
            'Неизвестно': 0
        }

        for person_id, person_info in self.people.items():
            birth_year = self._extract_birth_year(person_info)

            if birth_year is None:
                generations['Неизвестно'] += 1
            elif birth_year < 1920:
                generations['Дореволюционное (до 1920)'] += 1
            elif 1921 <= birth_year <= 1940:
                generations['Первое (1921-1940)'] += 1
            elif 1941 <= birth_year <= 1960:
                generations['Второе (1941-1960)'] += 1
            elif 1961 <= birth_year <= 1980:
                generations['Третье (1961-1980)'] += 1
            elif 1981 <= birth_year <= 2000:
                generations['Четвертое (1981-2000)'] += 1
            else:
                generations['Пятое (после 2000)'] += 1

        return generations

    def find_longest_lineage(self) -> List[str]:
        """Находит самую длинную линию родства"""
        def get_children(person_id):
            children = []
            for parent1, parent2, kids in self.marriages:
                if parent1 == person_id or parent2 == person_id:
                    children.extend(kids)
            return children

        def find_lineage_length(person_id, visited=None):
            if visited is None:
                visited = set()
            if person_id in visited:
                return []

            visited.add(person_id)
            children = get_children(person_id)

            if not children:
                return [person_id]

            longest_path = [person_id]
            max_length = 0

            for child in children:
                child_path = find_lineage_length(child, visited.copy())
                if len(child_path) > max_length:
                    max_length = len(child_path)
                    longest_path = [person_id] + child_path

            return longest_path

        # Находим самую длинную линию, начиная с корневых персон
        root_persons = set(self.people.keys())
        for _, _, children in self.marriages:
            root_persons -= set(children)

        longest_lineage = []
        for root in root_persons:
            lineage = find_lineage_length(root)
            if len(lineage) > len(longest_lineage):
                longest_lineage = lineage

        return longest_lineage

    def print_extended_analysis(self):
        """Выводит расширенный анализ семьи"""
        print("\n📈 РАСШИРЕННЫЙ АНАЛИЗ СЕМЬИ:")
        print("-" * 50)

        # Самые большие семьи
        largest_families = self.find_largest_families()
        print(f"\n👨‍👩‍👧‍👦 Самые большие семьи:")
        for i, (parent1, parent2, children_count) in enumerate(
                largest_families, 1):
            print(f"  {i}. {parent1} и {parent2} - {children_count} детей")

        # Статистика по поколениям
        gen_stats = self.get_generation_statistics()
        print(f"\n🕰️  Распределение по поколениям:")
        for generation, count in gen_stats.items():
            if count > 0:
                print(f"  {generation}: {count} чел.")

        # Самая длинная линия родства
        longest_lineage = self.find_longest_lineage()
        if longest_lineage:
            print(
                f"\n🔗 Самая длинная линия родства ({
                    len(longest_lineage)} поколений):")
            for i, person_id in enumerate(longest_lineage, 1):
                person_name = self.people.get(person_id, f"ID {person_id}")
                print(f"  {i}. {person_name}")

    def _fix_svg_viewbox(self, svg_filename: str):
        """Исправляет viewBox в SVG файле для корректного отображения"""
        try:
            with open(svg_filename, 'r', encoding='utf-8') as f:
                content = f.read()

            # Ищем polygon с границами содержимого
            polygon_match = re.search(
                r'<polygon[^>]*points="([^"]+)"', content)
            if not polygon_match:
                print("⚠️  Не удалось найти границы содержимого в SVG")
                return

            points_str = polygon_match.group(1)
            # Парсим координаты: "-4,4 -4,-619.08 2298.5,-619.08 2298.5,4 -4,4"
            points = []
            for point_pair in points_str.split():
                if ',' in point_pair:
                    x, y = map(float, point_pair.split(','))
                    points.append((x, y))

            if not points:
                print("⚠️  Не удалось распарсить координаты в SVG")
                return

            # Находим границы
            min_x = min(p[0] for p in points)
            max_x = max(p[0] for p in points)
            min_y = min(p[1] for p in points)
            max_y = max(p[1] for p in points)

            width = max_x - min_x
            height = max_y - min_y

            # Создаем правильный viewBox
            new_viewbox = f"0 0 {width} {height}"

            # Заменяем viewBox в SVG
            content = re.sub(
                r'viewBox="[^"]*"',
                f'viewBox="{new_viewbox}"',
                content
            )

            # Убираем лишний scale из transform, оставляем только translate
            content = re.sub(
                r'transform="scale\([^)]+\)\s*rotate\([^)]+\)\s*translate\(([^)]+)\)"',
                r'transform="translate(\1)"',
                content)

            # Сохраняем исправленный файл
            with open(svg_filename, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"✅ SVG viewBox исправлен: {new_viewbox}")

        except Exception as e:
            print(f"⚠️  Ошибка при исправлении SVG: {e}")


def main():
    """Основная функция программы"""
    print("Программа построения генеалогического дерева")
    print("=" * 45)

    # Создаем объект построителя дерева
    tree_builder = FamilyTreeBuilder()

    try:
        # Парсим исходный файл
        print("Загрузка данных из source.txt...")
        tree_builder.parse_source_file('source.txt')

        # Проводим валидацию данных
        tree_builder.print_validation_report()

        # Проводим анализ качества данных
        tree_builder.print_data_analysis()

        # Проводим расширенный анализ семьи
        tree_builder.print_extended_analysis()

        # Выводим статистику
        tree_builder.print_statistics()

        # Создаем генеалогическое дерево
        print("\nСоздание генеалогического дерева...")
        tree_builder.create_family_tree('family_tree')

        print("\n" + "=" * 50)
        print("ГОТОВО! Созданы следующие файлы:")
        print("📊 Визуализация:")
        print("  - family_tree.png (высокое разрешение 300 DPI)")
        print("  - family_tree_vector.svg (векторный формат)")
        print("📄 Отчеты:")
        print("  - family_tree.dot - исходный DOT файл")
        print("=" * 50)

    except FileNotFoundError:
        print("❌ Ошибка: файл source.txt не найден!")
        print("Создайте файл source.txt в формате:")
        print("\nЛюди:")
        print("1 - Иванов Иван Иванович (01.01.1980-...)")
        print("2 - Иванова Мария Петровна (02.02.1985-...)")
        print("\nСвязи:")
        print("1 -- 2 (3,4)           # брак с детьми 3 и 4")
        print("1 -- 2                 # брак без детей")
        print("1 -- 2 (?)             # брак с неизвестными детьми")
        print("1 -- ?                 # брак с неизвестным супругом")
        print("1 -- ? (5,6)           # брак с неизвестным супругом и детьми")
        print("1 -- ? (?)             # брак с неизвестным супругом и неизвестными детьми")
    except Exception as e:
        print(f"❌ Произошла ошибка: {e}")


if __name__ == "__main__":
    main()
