#!/usr/bin/env python3
"""Render the site SVG from a GEDCOM file."""

import argparse
from pathlib import Path
import sys

from gedcom_tree_builder import GedcomTreeBuilder


def main():
    parser = argparse.ArgumentParser(
        description="Render family_tree_vector.svg from GEDCOM"
    )
    parser.add_argument(
        "gedcom",
        nargs="?",
        default="family_tree.ged",
        help="Path to GEDCOM file",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="site/family_tree_vector",
        help="Output SVG path without .svg extension",
    )
    args = parser.parse_args()

    gedcom_path = Path(args.gedcom)
    if not gedcom_path.exists():
        print(f"GEDCOM file not found: {gedcom_path}", file=sys.stderr)
        return 1

    builder = GedcomTreeBuilder()
    builder.parse_gedcom_file(gedcom_path)
    issues = builder.validate_data()
    if issues:
        print("Cannot render GEDCOM while validation has issues:", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        return 1

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    builder.create_svg_only(str(output_path))
    print(f"Rendered GEDCOM SVG to {output_path}.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
