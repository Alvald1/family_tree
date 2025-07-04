import os
from family_tree_builder import FamilyTreeBuilder


def main():
    print("Программа построения генеалогического дерева")
    print("=" * 45)

    tree_builder = FamilyTreeBuilder()

    try:
        print("Загрузка данных из source.txt...")
        # Ищем source.txt в текущей директории, затем в родительской
        source_file = 'source.txt'
        if not os.path.exists(source_file):
            parent_source = os.path.join('..', 'source.txt')
            if os.path.exists(parent_source):
                source_file = parent_source

        tree_builder.parse_source_file(source_file)
        tree_builder.print_validation_report()
        tree_builder.print_data_analysis()
        tree_builder.print_extended_analysis()
        tree_builder.print_statistics()
        print("\nСоздание генеалогического дерева...")

        # Определяем директорию для сохранения файлов (там же, где source.txt)
        source_dir = os.path.dirname(os.path.abspath(source_file))
        png_output_path = os.path.join(source_dir, 'family_tree')

        # Создаем PNG файл в корневой директории (только PNG)
        tree_builder.create_family_tree(png_output_path)

        # Создаем SVG файл в папке site
        site_dir = os.path.join(source_dir, 'site')
        if not os.path.exists(site_dir):
            os.makedirs(site_dir)
        svg_output_path = os.path.join(site_dir, 'family_tree_vector')

        # Создаем отдельно SVG файл в папке site
        tree_builder.create_svg_only(svg_output_path)

        # Удаляем временные DOT файлы
        dot_file = png_output_path  # Graphviz создает файл без расширения
        if os.path.exists(dot_file):
            os.remove(dot_file)
        svg_dot_file = svg_output_path
        if os.path.exists(svg_dot_file):
            os.remove(svg_dot_file)

        # Удаляем SVG файл из корневой директории, если он там был создан
        root_svg = f"{png_output_path}_vector.svg"
        if os.path.exists(root_svg):
            os.remove(root_svg)

        print("\n" + "=" * 50)
        print("ГОТОВО! Созданы следующие файлы:")
        print("📊 Визуализация:")
        print(f"  - {png_output_path}.png (высокое разрешение 300 DPI)")
        print(f"  - {svg_output_path}.svg (векторный формат в папке site)")
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
        print("1 -- 2 (3,?,?)         # брак с известным ребенком 3 и двумя неизвестными")
        print("1 -- ?                 # брак с неизвестным супругом")
        print("1 -- ? (5,6)           # брак с неизвестным супругом и детьми")
        print("1 -- ? (?)             # брак с неизвестным супругом и неизвестными детьми")
    except Exception as e:
        print(f"❌ Произошла ошибка: {e}")


if __name__ == "__main__":
    main()
