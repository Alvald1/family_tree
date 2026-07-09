#!/usr/bin/env python3
"""Export family_tree source.txt to GEDCOM."""

import argparse
from pathlib import Path

from family_tree_builder import FamilyTreeBuilder
from gedcom_exporter import GedcomExporter


def main():
    parser = argparse.ArgumentParser(
        description="Export family tree source data to GEDCOM 5.5.1",
    )
    parser.add_argument(
        "source",
        nargs="?",
        default="source.txt",
        help="Path to source.txt",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="family_tree.ged",
        help="Output GEDCOM file path",
    )
    args = parser.parse_args()

    source_path = Path(args.source)
    output_path = Path(args.output)

    builder = FamilyTreeBuilder()
    builder.parse_source_file(source_path)
    issues = builder.validate_data()
    if issues:
        raise SystemExit(
            "Cannot export GEDCOM while source validation has issues:\n"
            + "\n".join(f"- {issue}" for issue in issues)
        )

    GedcomExporter(builder).write_file(output_path)
    print(f"GEDCOM saved to {output_path}")


if __name__ == "__main__":
    main()
