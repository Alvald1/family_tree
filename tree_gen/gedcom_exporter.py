"""GEDCOM export for the parsed family tree."""

import re
from dataclasses import dataclass, field
from pathlib import Path


GEDCOM_MONTHS = {
    "01": "JAN",
    "02": "FEB",
    "03": "MAR",
    "04": "APR",
    "05": "MAY",
    "06": "JUN",
    "07": "JUL",
    "08": "AUG",
    "09": "SEP",
    "10": "OCT",
    "11": "NOV",
    "12": "DEC",
}


@dataclass
class IndividualRecord:
    xref: str
    name: str
    source_id: str
    original_info: str
    birth_date: str = ""
    death_date: str = ""
    notes: list[str] = field(default_factory=list)
    fams: list[str] = field(default_factory=list)
    famc: list[str] = field(default_factory=list)


@dataclass
class FamilyRecord:
    xref: str
    parent1: str | None = None
    parent2: str | None = None
    children: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class GedcomExporter:
    def __init__(self, builder):
        self.builder = builder

    def to_string(self):
        individuals = self._build_individuals()
        families = self._build_families(individuals)

        lines = self._header_lines()
        for xref in sorted(individuals, key=self._xref_sort_key):
            lines.extend(self._individual_lines(individuals[xref]))
        for family in families:
            lines.extend(self._family_lines(family))
        lines.append("0 TRLR")
        return "\n".join(lines) + "\n"

    def write_file(self, output_path):
        output_path = Path(output_path)
        output_path.write_text(self.to_string(), encoding="utf-8")

    def _build_individuals(self):
        individuals = {}
        for person_id, info in sorted(self.builder.people.items()):
            xref = self._person_xref(person_id)
            birth_date, death_date, date_note = parse_dates(info)
            notes = [f"Source ID: {person_id}", f"Original: {info}"]
            if person_id >= 1000 or info.strip() == "?":
                notes.append("Unknown person placeholder")
            if date_note:
                notes.append(date_note)
            individuals[xref] = IndividualRecord(
                xref=xref,
                name=format_gedcom_name(extract_name(info)),
                source_id=str(person_id),
                original_info=info,
                birth_date=birth_date,
                death_date=death_date,
                notes=notes,
            )
        return individuals

    def _build_families(self, individuals):
        families = []

        def add_family(parent1=None, parent2=None, children=None, notes=None):
            family = FamilyRecord(
                xref=f"@F{len(families) + 1}@",
                parent1=self._person_xref(parent1) if parent1 is not None else None,
                parent2=self._person_xref(parent2) if parent2 is not None else None,
                children=[
                    self._person_xref(child)
                    if isinstance(child, int)
                    else child
                    for child in (children or [])
                ],
                notes=notes or [],
            )
            families.append(family)
            for parent in [family.parent1, family.parent2]:
                if parent and parent in individuals:
                    individuals[parent].fams.append(family.xref)
            for child in family.children:
                if child in individuals:
                    individuals[child].famc.append(family.xref)
            return family

        for parent1, parent2, children in self.builder.marriages:
            add_family(parent1, parent2, children)

        unknown_child_counter = 1
        for parent1, parent2, known_children, unknown_count in self.builder.mixed_children_marriages:
            children = list(known_children)
            for _ in range(unknown_count):
                xref = f"@IUNKNOWN{unknown_child_counter}@"
                unknown_child_counter += 1
                individuals[xref] = IndividualRecord(
                    xref=xref,
                    name="? //",
                    source_id=xref.strip("@"),
                    original_info="?",
                    notes=["Unknown child placeholder"],
                )
                children.append(xref)
            add_family(parent1, parent2, children, notes=["Family has unknown child placeholders"])

        for parent1, parent2 in self.builder.childless_marriages:
            add_family(parent1, parent2, notes=["Family has no known children in source"])

        for parent1, parent2 in self.builder.unknown_children_marriages:
            xref = f"@IUNKNOWN{unknown_child_counter}@"
            unknown_child_counter += 1
            individuals[xref] = IndividualRecord(
                xref=xref,
                name="? //",
                source_id=xref.strip("@"),
                original_info="?",
                notes=["Unknown child placeholder"],
            )
            add_family(parent1, parent2, [xref], notes=["Family has unknown children in source"])

        for parent, child in self.builder.single_parent_children:
            add_family(parent1=parent, children=[child], notes=["Single-parent relationship in source"])

        return families

    def _individual_lines(self, individual):
        lines = [
            f"0 {individual.xref} INDI",
            f"1 NAME {gedcom_text(individual.name)}",
        ]
        if individual.birth_date:
            lines.extend(["1 BIRT", f"2 DATE {individual.birth_date}"])
        if individual.death_date:
            lines.extend(["1 DEAT", f"2 DATE {individual.death_date}"])
        for fams in individual.fams:
            lines.append(f"1 FAMS {fams}")
        for famc in individual.famc:
            lines.append(f"1 FAMC {famc}")
        for note in individual.notes:
            lines.append(f"1 NOTE {gedcom_text(note)}")
        return lines

    def _family_lines(self, family):
        lines = [f"0 {family.xref} FAM"]
        if family.parent1:
            lines.append(f"1 HUSB {family.parent1}")
        if family.parent2:
            lines.append(f"1 WIFE {family.parent2}")
        for child in family.children:
            lines.append(f"1 CHIL {child}")
        for note in family.notes:
            lines.append(f"1 NOTE {gedcom_text(note)}")
        return lines

    def _header_lines(self):
        return [
            "0 HEAD",
            "1 SOUR family_tree",
            "1 GEDC",
            "2 VERS 5.5.1",
            "2 FORM LINEAGE-LINKED",
            "1 CHAR UTF-8",
        ]

    def _person_xref(self, person_id):
        return f"@I{person_id}@"

    def _xref_sort_key(self, xref):
        match = re.search(r"\d+", xref)
        if match:
            return (0, int(match.group(0)), xref)
        return (1, 0, xref)


def extract_name(info):
    return info.split("(", 1)[0].strip()


def format_gedcom_name(name):
    name = gedcom_text(name.strip())
    if name == "?":
        return "? //"
    parts = name.split()
    if len(parts) >= 2:
        return f"{' '.join(parts[1:])} /{parts[0]}/"
    return name


def parse_dates(info):
    match = re.search(r"\(([^)]*)\)", info)
    if not match:
        return "", "", ""
    value = " ".join(match.group(1).split())
    if not value or "неизвест" in value.lower():
        return "", "", f"Date text: {value}" if value else ""

    date_range = re.fullmatch(r"(.+?)\s*-\s*(.+)", value)
    if date_range:
        birth_date = format_date(date_range.group(1).strip())
        death_date = format_date(date_range.group(2).strip())
        return birth_date, death_date, "" if birth_date or death_date else f"Date text: {value}"

    date_value = format_date(value)
    return date_value, "", "" if date_value else f"Date text: {value}"


def format_date(value):
    value = value.strip()
    if not value or value in {"...", "?", "неизвестно", "неизвестны"}:
        return ""

    full_date = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", value)
    if full_date:
        day = str(int(full_date.group(1)))
        month = GEDCOM_MONTHS.get(full_date.group(2).zfill(2))
        year = full_date.group(3)
        if month:
            return f"{day} {month} {year}"

    year = re.fullmatch(r"\d{4}", value)
    if year:
        return value

    return ""


def gedcom_text(value):
    return str(value).replace("\r", " ").replace("\n", " ").replace("@", "(at)")
