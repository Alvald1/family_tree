import re
import graphviz
from typing import Dict, List, Tuple, Set


class FamilyTreeBuilder:
    def find_longest_lineage(self) -> List[str]:
        def get_children(person_id):
            children = []
            for parent1, parent2, kids in self.marriages:
                if parent1 == person_id or parent2 == person_id:
                    children.extend(kids)
            for parent1, parent2, known_kids, _ in self.mixed_children_marriages:
                if parent1 == person_id or parent2 == person_id:
                    children.extend(known_kids)
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
        root_persons = set(self.people.keys())
        for _, _, children in self.marriages:
            root_persons -= set(children)
        for _, _, known_children, _ in self.mixed_children_marriages:
            root_persons -= set(known_children)
        longest_lineage = []
        for root in root_persons:
            lineage = find_lineage_length(root)
            if len(lineage) > len(longest_lineage):
                longest_lineage = lineage
        return longest_lineage

    def get_generation_statistics(self) -> Dict[str, int]:
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

    def find_largest_families(
            self, top_n: int = 3) -> List[Tuple[str, str, int]]:
        family_sizes = []
        for parent1, parent2, children in self.marriages:
            parent1_name = self.people.get(parent1, f"ID {parent1}")
            parent2_name = self.people.get(parent2, f"ID {parent2}")
            family_sizes.append((parent1_name, parent2_name, len(children)))
        for parent1, parent2, known_children, unknown_count in self.mixed_children_marriages:
            parent1_name = self.people.get(parent1, f"ID {parent1}")
            parent2_name = self.people.get(parent2, f"ID {parent2}")
            total_children = len(known_children) + unknown_count
            family_sizes.append((parent1_name, parent2_name, total_children))
        return sorted(family_sizes, key=lambda x: x[2], reverse=True)[:top_n]

    def print_data_analysis(self):
        issues = self.find_data_issues()
        print("\n📊 АНАЛИЗ КАЧЕСТВА ДАННЫХ:")
        print("-" * 40)
        for category, problems in issues.items():
            if problems:
                print(f"\n⚠️  {category} ({len(problems)}):")
                for problem in problems[:5]:
                    print(f"  - {problem}")
                if len(problems) > 5:
                    print(f"  ... и еще {len(problems) - 5}")
            else:
                print(f"\n✅ {category}: проблем не найдено")

    def find_data_issues(self) -> Dict[str, List[str]]:
        issues = {
            "Неполные имена": [],
            "Неизвестные даты": [],
            "Возможные опечатки": [],
            "Одиночные дети": []
        }
        for person_id, info in self.people.items():
            if person_id >= 1000:
                continue
            name_part = info.split('(')[0].strip()
            words = name_part.split()
            if len(words) == 1:
                issues["Неполные имена"].append(f"{person_id}: {name_part}")
            elif "неизвестны" in info:
                issues["Неизвестные даты"].append(f"{person_id}: {name_part}")
            if any(typo in info for typo in ['Владислававна', 'Николая']):
                issues["Возможные опечатки"].append(f"{person_id}: {info}")
        all_children = set()
        for _, _, children in self.marriages:
            all_children.update(children)
        for person_id in self.people:
            if person_id not in all_children and person_id < 1000:
                is_parent = any(person_id in [p1, p2]
                                for p1, p2, _ in self.marriages)
                if not is_parent:
                    name = self.people[person_id].split('(')[0].strip()
                    issues["Одиночные дети"].append(f"{person_id}: {name}")
        return issues

    def print_validation_report(self):
        issues = self.validate_data()
        if issues:
            print("\n⚠️  Найдены проблемы в данных:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("\n✅ Данные прошли валидацию успешно")

    def validate_data(self) -> List[str]:
        issues = []
        for parent1, parent2, children in self.marriages:
            if parent1 not in self.people:
                issues.append(f"Родитель {parent1} не найден в списке людей")
            if parent2 not in self.people:
                issues.append(f"Родитель {parent2} не найден в списке людей")
            for child in children:
                if child not in self.people:
                    issues.append(f"Ребенок {child} не найден в списке людей")
        for parent1, parent2 in self.childless_marriages:
            if parent1 not in self.people:
                issues.append(
                    f"Супруг {parent1} (брак без детей) не найден в списке людей")
            if parent2 not in self.people:
                issues.append(
                    f"Супруг {parent2} (брак без детей) не найден в списке людей")
        for parent1, parent2 in self.unknown_children_marriages:
            if parent1 not in self.people:
                issues.append(
                    f"Супруг {parent1} (брак с неизвестными детьми) не найден в списке людей")
            if parent2 not in self.people:
                issues.append(
                    f"Супруг {parent2} (брак с неизвестными детьми) не найден в списке людей")
        for parent1, parent2, known_children, unknown_count in self.mixed_children_marriages:
            if parent1 not in self.people:
                issues.append(
                    f"Супруг {parent1} (брак со смешанными детьми) не найден в списке людей")
            if parent2 not in self.people:
                issues.append(
                    f"Супруг {parent2} (брак со смешанными детьми) не найден в списке людей")
            for child in known_children:
                if child not in self.people:
                    issues.append(
                        f"Ребенок {child} (смешанный брак) не найден в списке людей")
        for parent, child in self.single_parent_children:
            if parent not in self.people:
                issues.append(f"Родитель {parent} не найден в списке людей")
            if child not in self.people:
                issues.append(f"Ребенок {child} не найден в списке людей")
        return issues

    def _get_generation_color(
            self,
            birth_year: int,
            is_unknown: bool = False) -> str:
        if is_unknown:
            return '#F0F0F0'
        if birth_year <= 1920:
            return '#FFE4E1'
        elif 1921 <= birth_year <= 1940:
            return '#E6E6FA'
        elif 1941 <= birth_year <= 1960:
            return '#E0E6FF'
        elif 1961 <= birth_year <= 1980:
            return '#E6FFE6'
        elif 1981 <= birth_year <= 2000:
            return '#FFFACD'
        else:
            return '#FFE4E6'

    def _extract_birth_year(self, info: str) -> int:
        year_patterns = [
            r'\((\d{4})-\d{4}\)',
            r'\((\d{4})\)',
            r'\((\d{2})\.(\d{2})\.(\d{4})',
            r'\((\d{4})-',
        ]
        for pattern in year_patterns:
            match = re.search(pattern, info)
            if match:
                if len(match.groups()) == 1:
                    return int(match.group(1))
                elif len(match.groups()) == 3:
                    return int(match.group(3))
                else:
                    return int(match.group(1))
        return 1950

    def _normalize_person_info(self, info: str) -> str:
        info = ' '.join(info.split())
        if '(' not in info:
            year_match = re.search(r'\s(\d{4})$', info)
            if year_match:
                year = year_match.group(1)
                info = info.replace(f' {year}', f' ({year})')
        return info

    def _get_next_unknown_id(self) -> int:
        unknown_id = 1000
        while unknown_id in self.people:
            unknown_id += 1
        return unknown_id

    def _analyze_generations(self) -> Dict[str, List[int]]:
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
            if person_id >= 1000:
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

    def print_statistics(self):
        print(f"\nСтатистика генеалогического дерева:")
        print(f"Всего людей: {len(self.people)}")
        print(f"Количество браков с детьми: {len(self.marriages)}")
        print(f"Количество браков без детей: {len(self.childless_marriages)}")
        print(
            f"Количество браков с неизвестными детьми: {len(self.unknown_children_marriages)}")
        print(
            f"Количество браков со смешанными детьми: {len(self.mixed_children_marriages)}")
        print(f"Общее количество браков: {len(self.marriages) +
                                          len(self.childless_marriages) +
                                          len(self.unknown_children_marriages) +
                                          len(self.mixed_children_marriages)}")
        total_known_children = sum(len(children)
                                   for _, _, children in self.marriages)
        total_mixed_known_children = sum(
            len(known_children) for _,
            _,
            known_children,
            _ in self.mixed_children_marriages)
        total_unknown_children = sum(
            unknown_count for _,
            _,
            _,
            unknown_count in self.mixed_children_marriages)
        print(
            f"Количество известных детей от браков: {
                total_known_children +
                total_mixed_known_children}")
        print(f"Количество неизвестных детей: {total_unknown_children}")
        print(f"Одиночные связи: {len(self.single_parent_children)}")
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
        for parent1, parent2, _, _ in self.mixed_children_marriages:
            total_married_people.add(parent1)
            total_married_people.add(parent2)
        print(f"Количество людей в браке: {len(total_married_people)}")
        print(
            f"Количество одиноких людей: {len(self.people) - len(total_married_people)}")

    def _format_person_info(self, info: str) -> str:
        if len(info) > 25:
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

    def create_family_tree(self, output_filename: str = 'family_tree'):
        """Создание графа генеалогического дерева"""
        dot = graphviz.Digraph(comment='Генеалогическое дерево')
        dot.attr(rankdir='TB', bgcolor='white', size='20,30!')
        dot.attr(dpi='400')
        dot.attr(resolution='400')
        dot.attr(
            'node',
            shape='box',
            style='filled,rounded',
            fontname='Arial',
            fontsize='12')
        dot.attr('edge', fontname='Arial', fontsize='10')
        for person_id, info in self.people.items():
            formatted_info = self._format_person_info(info)
            birth_year = self._extract_birth_year(info)
            color = self._get_generation_color(birth_year, person_id >= 1000)
            dot.node(str(person_id), formatted_info, fillcolor=color)
        marriage_counter = 1
        for parent1, parent2, children in self.marriages:
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
            dot.edge(str(parent1), marriage_node, dir='none', style='bold')
            dot.edge(str(parent2), marriage_node, dir='none', style='bold')
            for child in children:
                dot.edge(marriage_node, str(child), color='blue')
            marriage_counter += 1
        for parent1, parent2, known_children, unknown_count in self.mixed_children_marriages:
            marriage_node = f"marriage_{marriage_counter}"
            dot.node(
                marriage_node,
                "♥",
                shape='circle',
                style='filled',
                fillcolor='#FFA07A',
                width='0.5',
                height='0.5',
                fontsize='16')
            dot.edge(str(parent1), marriage_node, dir='none', style='bold')
            dot.edge(str(parent2), marriage_node, dir='none', style='bold')
            for child in known_children:
                dot.edge(marriage_node, str(child), color='blue')
            for i in range(unknown_count):
                unknown_child_node = f"unknown_child_{marriage_counter}_{i}"
                dot.node(
                    unknown_child_node,
                    "?",
                    shape='box',
                    style='filled,dashed',
                    fillcolor='#F0F0F0',
                    fontsize='10')
                dot.edge(
                    marriage_node,
                    unknown_child_node,
                    color='gray',
                    style='dashed')
            marriage_counter += 1
        for parent1, parent2 in self.childless_marriages:
            marriage_node = f"marriage_{marriage_counter}"
            dot.node(
                marriage_node,
                "♥",
                shape='circle',
                style='filled',
                fillcolor='#E6E6FA',
                width='0.4',
                height='0.4',
                fontsize='14')
            dot.edge(str(parent1), marriage_node, dir='none', style='bold')
            dot.edge(str(parent2), marriage_node, dir='none', style='bold')
            marriage_counter += 1
        for parent1, parent2 in self.unknown_children_marriages:
            marriage_node = f"marriage_{marriage_counter}"
            dot.node(
                marriage_node,
                "♥",
                shape='circle',
                style='filled',
                fillcolor='#FFFACD',
                width='0.5',
                height='0.5',
                fontsize='12')
            dot.edge(str(parent1), marriage_node, dir='none', style='bold')
            dot.edge(str(parent2), marriage_node, dir='none', style='bold')
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
        processed_pairs: Set[Tuple[int, int]] = set()
        for parent, child in self.single_parent_children:
            if (parent, child) not in processed_pairs and (
                    child, parent) not in processed_pairs:
                dot.edge(str(parent), str(child), color='gray', style='dashed')
                processed_pairs.add((parent, child))
        try:
            dot.render(output_filename, format='png', cleanup=False)
            svg_filename = f"{output_filename}_vector.svg"
            dot.render(f"{output_filename}_vector", format='svg', cleanup=True)
            self._fix_svg_viewbox(svg_filename)
            print(f"Генеалогическое дерево сохранено как:")
            print(f"  - {output_filename}.png (высокое разрешение 400 DPI)")
            print(
                f"  - {output_filename}_vector.svg (векторный формат с исправленным viewBox)")
        except Exception as e:
            print(f"Ошибка при сохранении: {e}")
            with open(f"{output_filename}.dot", 'w', encoding='utf-8') as f:
                f.write(dot.source)
            print(f"DOT файл сохранен как {output_filename}.dot")
        return dot

    def create_svg_only(self, output_filename: str = 'family_tree_vector'):
        """Создание только SVG файла генеалогического дерева"""
        dot = graphviz.Digraph(comment='Генеалогическое дерево')
        dot.attr(rankdir='TB', bgcolor='white', size='20,30!')
        dot.attr(dpi='400')
        dot.attr(resolution='400')
        dot.attr(
            'node',
            shape='box',
            style='filled,rounded',
            fontname='Arial',
            fontsize='12')
        dot.attr('edge', fontname='Arial', fontsize='10')
        for person_id, info in self.people.items():
            formatted_info = self._format_person_info(info)
            birth_year = self._extract_birth_year(info)
            color = self._get_generation_color(birth_year, person_id >= 1000)
            dot.node(str(person_id), formatted_info, fillcolor=color)
        marriage_counter = 1
        for parent1, parent2, children in self.marriages:
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
            dot.edge(str(parent1), marriage_node, dir='none', style='bold')
            dot.edge(str(parent2), marriage_node, dir='none', style='bold')
            for child in children:
                dot.edge(marriage_node, str(child), color='blue')
            marriage_counter += 1
        for parent1, parent2, known_children, unknown_count in self.mixed_children_marriages:
            marriage_node = f"marriage_{marriage_counter}"
            dot.node(
                marriage_node,
                "♥",
                shape='circle',
                style='filled',
                fillcolor='#FFA07A',
                width='0.5',
                height='0.5',
                fontsize='16')
            dot.edge(str(parent1), marriage_node, dir='none', style='bold')
            dot.edge(str(parent2), marriage_node, dir='none', style='bold')
            for child in known_children:
                dot.edge(marriage_node, str(child), color='blue')
            for i in range(unknown_count):
                unknown_child_node = f"unknown_child_{marriage_counter}_{i}"
                dot.node(
                    unknown_child_node,
                    "?",
                    shape='box',
                    style='filled,dashed',
                    fillcolor='#F0F0F0',
                    fontsize='10')
                dot.edge(
                    marriage_node,
                    unknown_child_node,
                    color='gray',
                    style='dashed')
            marriage_counter += 1
        for parent1, parent2 in self.childless_marriages:
            marriage_node = f"marriage_{marriage_counter}"
            dot.node(
                marriage_node,
                "♥",
                shape='circle',
                style='filled',
                fillcolor='#E6E6FA',
                width='0.4',
                height='0.4',
                fontsize='14')
            dot.edge(str(parent1), marriage_node, dir='none', style='bold')
            dot.edge(str(parent2), marriage_node, dir='none', style='bold')
            marriage_counter += 1
        for parent1, parent2 in self.unknown_children_marriages:
            marriage_node = f"marriage_{marriage_counter}"
            dot.node(
                marriage_node,
                "♥",
                shape='circle',
                style='filled',
                fillcolor='#FFFACD',
                width='0.5',
                height='0.5',
                fontsize='12')
            dot.edge(str(parent1), marriage_node, dir='none', style='bold')
            dot.edge(str(parent2), marriage_node, dir='none', style='bold')
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
        processed_pairs: Set[Tuple[int, int]] = set()
        for parent, child in self.single_parent_children:
            if (parent, child) not in processed_pairs and (
                    child, parent) not in processed_pairs:
                dot.edge(str(parent), str(child), color='gray', style='dashed')
                processed_pairs.add((parent, child))
        try:
            svg_filename = f"{output_filename}.svg"
            dot.render(output_filename, format='svg', cleanup=True)
            self._fix_svg_viewbox(svg_filename)
            print(f"SVG файл сохранен как: {svg_filename}")
        except Exception as e:
            print(f"Ошибка при сохранении SVG: {e}")
            with open(f"{output_filename}.dot", 'w', encoding='utf-8') as f:
                f.write(dot.source)
            print(f"DOT файл сохранен как {output_filename}.dot")
        return dot

    def __init__(self):
        self.people: Dict[int, str] = {}
        self.marriages: List[Tuple[int, int, List[int]]] = []
        self.single_parent_children: List[Tuple[int, int]] = []
        self.childless_marriages: List[Tuple[int, int]] = []
        self.unknown_children_marriages: List[Tuple[int, int]] = []
        self.mixed_children_marriages: List[Tuple[int, int, List[int], int]] = [
        ]

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
        self.mixed_children_marriages.clear()

        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue

            relation_match = re.match(
                r'^(\d+)\s*(--|->)\s*(\?|\d+)(?:\s*\(([^)]*)\))?$', line)
            if relation_match:
                parent1 = int(relation_match.group(1))
                relation_operator = relation_match.group(2)
                parent2_str = relation_match.group(3)
                children_str = relation_match.group(
                    4) if relation_match.group(4) is not None else None

                if relation_operator == '->':
                    if parent2_str.isdigit():
                        self.single_parent_children.append(
                            (parent1, int(parent2_str)))
                    continue

                if parent2_str == '?':
                    unknown_id = self._get_next_unknown_id()
                    unknown_name = "?"
                    self.people[unknown_id] = unknown_name
                    parent2 = unknown_id
                else:
                    parent2 = int(parent2_str)

                if children_str is None:
                    self.childless_marriages.append((parent1, parent2))
                elif children_str.strip() == '?':
                    self.unknown_children_marriages.append((parent1, parent2))
                elif children_str.strip() == '':
                    self.childless_marriages.append((parent1, parent2))
                else:
                    children = []
                    unknown_count = 0
                    for child_str in children_str.split(','):
                        child_str = child_str.strip()
                        if child_str == '?':
                            unknown_count += 1
                        elif child_str and child_str.isdigit():
                            children.append(int(child_str))
                    if unknown_count > 0 and len(children) > 0:
                        self.mixed_children_marriages.append(
                            (parent1, parent2, children, unknown_count))
                    elif unknown_count > 0:
                        self.mixed_children_marriages.append(
                            (parent1, parent2, [], unknown_count))
                    else:
                        self.marriages.append((parent1, parent2, children))
                continue

            person_match = re.match(r'^(\d+)\s*-\s*(.+)$', line)
            if person_match:
                number = int(person_match.group(1))
                info = person_match.group(2).strip()
                normalized_info = self._normalize_person_info(info)
                self.people[number] = normalized_info
                continue

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

            content = self.normalize_svg_node_ids(content)

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
                content)

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

    @staticmethod
    def normalize_svg_node_ids(content: str) -> str:
        """Replaces Graphviz-generated SVG group IDs with DOT node names.

        Graphviz emits internal IDs like ``node9`` and stores the original DOT
        node name in the nested ``title`` tag. The site uses IDs for profile
        navigation, so keep the SVG group ID aligned with the source person ID.
        """
        replacements = {}

        def normalize_group(match):
            old_id = match.group("id")
            title = match.group("title").strip()
            if re.fullmatch(r"\d+", title):
                new_id = f"node{title}"
            elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", title):
                new_id = title
            else:
                return match.group(0)

            replacements[old_id] = new_id
            return match.group(0).replace(
                f'id="{old_id}"',
                f'id="{new_id}"',
                1,
            )

        content = re.sub(
            r'<g id="(?P<id>node\d+)" class="node">\s*<title>(?P<title>[^<]+)</title>',
            normalize_group,
            content,
        )

        for old_id, new_id in replacements.items():
            content = content.replace(f'="#{old_id}"', f'="#{new_id}"')
            content = content.replace(f'url(#{old_id})', f'url(#{new_id})')

        return content
