import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TREE_GEN_ROOT = PROJECT_ROOT / "tree_gen"
sys.path.insert(0, str(TREE_GEN_ROOT))

from family_tree_builder import FamilyTreeBuilder
from gedcom_exporter import GedcomExporter


class GedcomExporterTest(unittest.TestCase):
    def build_tree(self, source_text):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = Path(temp_dir) / "source.txt"
            source_file.write_text(source_text, encoding="utf-8")
            builder = FamilyTreeBuilder()
            builder.parse_source_file(source_file)
            return builder

    def test_exports_people_dates_and_family_links(self):
        builder = self.build_tree(
            "\n".join(
                [
                    "1 - Иванов Иван Иванович (01.02.1980-03.04.2020)",
                    "2 - Иванова Мария Петровна (1982)",
                    "3 - Иванов Петр Иванович (2005)",
                    "1 -- 2 (3)",
                ]
            )
        )

        gedcom = GedcomExporter(builder).to_string()

        self.assertIn("0 HEAD", gedcom)
        self.assertIn("1 GEDC", gedcom)
        self.assertIn("2 VERS 5.5.1", gedcom)
        self.assertIn("1 CHAR UTF-8", gedcom)
        self.assertIn("0 @I1@ INDI", gedcom)
        self.assertIn("1 NAME Иван Иванович /Иванов/", gedcom)
        self.assertIn("1 BIRT\n2 DATE 1 FEB 1980", gedcom)
        self.assertIn("1 DEAT\n2 DATE 3 APR 2020", gedcom)
        self.assertIn("0 @F1@ FAM", gedcom)
        self.assertIn("1 HUSB @I1@", gedcom)
        self.assertIn("1 WIFE @I2@", gedcom)
        self.assertIn("1 CHIL @I3@", gedcom)
        self.assertTrue(gedcom.endswith("0 TRLR\n"))

    def test_exports_unknown_spouses_and_children_as_placeholders(self):
        builder = self.build_tree(
            "\n".join(
                [
                    "1 - Петров Петр Петрович (1950)",
                    "2 - Петрова Анна Петровна (1975)",
                    "1 -- ? (2,?)",
                ]
            )
        )

        gedcom = GedcomExporter(builder).to_string()

        self.assertIn("1 NOTE Unknown person placeholder", gedcom)
        self.assertIn("1 NAME ? //", gedcom)
        self.assertIn("1 CHIL @I2@", gedcom)
        self.assertIn("1 NOTE Unknown child placeholder", gedcom)

    def test_exports_single_parent_links_as_family_records(self):
        builder = self.build_tree(
            "\n".join(
                [
                    "1 - Сидоров Сергей (1970)",
                    "2 - Сидорова Ольга (1995)",
                    "1 -> 2",
                ]
            )
        )

        gedcom = GedcomExporter(builder).to_string()

        self.assertIn("0 @F1@ FAM", gedcom)
        self.assertIn("1 HUSB @I1@", gedcom)
        self.assertIn("1 CHIL @I2@", gedcom)


if __name__ == "__main__":
    unittest.main()
