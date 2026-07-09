import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TREE_GEN_ROOT = PROJECT_ROOT / "tree_gen"
sys.path.insert(0, str(TREE_GEN_ROOT))

from gedcom_tree_builder import GedcomTreeBuilder


class GedcomTreeBuilderTest(unittest.TestCase):
    def build_tree(self, gedcom_text):
        with tempfile.TemporaryDirectory() as temp_dir:
            gedcom_file = Path(temp_dir) / "tree.ged"
            gedcom_file.write_text(gedcom_text, encoding="utf-8")
            builder = GedcomTreeBuilder()
            builder.parse_gedcom_file(gedcom_file)
            return builder

    def test_imports_gedcom_family_as_site_compatible_tree(self):
        builder = self.build_tree(
            "\n".join([
                "0 HEAD",
                "1 GEDC",
                "2 VERS 5.5.1",
                "1 CHAR UTF-8",
                "0 @I1@ INDI",
                "1 NAME Иван Иванович /Иванов/",
                "1 BIRT",
                "2 DATE 1 FEB 1980",
                "1 NOTE Source ID: 1",
                "1 NOTE Original: Иванов Иван Иванович (01.02.1980-...)",
                "0 @I2@ INDI",
                "1 NAME Мария Петровна /Иванова/",
                "1 NOTE Source ID: 2",
                "1 NOTE Original: Иванова Мария Петровна (1982)",
                "0 @I3@ INDI",
                "1 NAME Анна Ивановна /Иванова/",
                "1 NOTE Source ID: 3",
                "0 @F1@ FAM",
                "1 HUSB @I1@",
                "1 WIFE @I2@",
                "1 CHIL @I3@",
                "0 TRLR",
            ]) + "\n"
        )

        self.assertEqual(
            builder.people,
            {
                1: "Иванов Иван Иванович (01.02.1980-...)",
                2: "Иванова Мария Петровна (1982)",
                3: "Иванова Анна Ивановна",
            },
        )
        self.assertEqual(builder.marriages, [(1, 2, [3])])
        self.assertEqual(builder.validate_data(), [])

    def test_imports_single_parent_family(self):
        builder = self.build_tree(
            "\n".join([
                "0 HEAD",
                "0 @I10@ INDI",
                "1 NAME Parent /One/",
                "0 @I11@ INDI",
                "1 NAME Child /One/",
                "0 @F1@ FAM",
                "1 HUSB @I10@",
                "1 CHIL @I11@",
                "0 TRLR",
            ]) + "\n"
        )

        self.assertEqual(builder.people[10], "One Parent")
        self.assertEqual(builder.people[11], "One Child")
        self.assertEqual(builder.single_parent_children, [(10, 11)])


if __name__ == "__main__":
    unittest.main()
