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
        output_path = os.path.join(source_dir, 'family_tree')
        tree_builder.create_family_tree(output_path)

        # Удаляем DOT файл (без расширения), оставляем только PNG и SVG
        dot_file = output_path  # Graphviz создает файл без расширения
        if os.path.exists(dot_file):
            os.remove(dot_file)

        print("\n" + "=" * 50)
        print("ГОТОВО! Созданы следующие файлы:")
        print("📊 Визуализация:")
        print(f"  - {output_path}.png (высокое разрешение 300 DPI)")
        print(f"  - {output_path}_vector.svg (векторный формат)")
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
