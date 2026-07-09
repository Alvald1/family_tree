"""Build the site-compatible family tree model from GEDCOM."""

import re
from pathlib import Path

from family_tree_builder import FamilyTreeBuilder


class GedcomTreeBuilder(FamilyTreeBuilder):
    """Parse GEDCOM 5.5/5.5.1 records into the existing tree model.

    The renderer and web viewer expect numeric person IDs because Graphviz
    emits them as SVG groups like ``node12``.  GEDCOM files exported by this
    project include ``NOTE Source ID: <number>``; external GEDCOM files fall
    back to numeric parts of ``@I...@`` xrefs or generated IDs.
    """

    def parse_gedcom_file(self, filename):
        self.people.clear()
        self.marriages.clear()
        self.single_parent_children.clear()
        self.childless_marriages.clear()
        self.unknown_children_marriages.clear()
        self.mixed_children_marriages.clear()

        records = parse_gedcom_records(Path(filename))
        individuals = {
            record["xref"]: record
            for record in records
            if record["tag"] == "INDI" and record["xref"]
        }
        families = [
            record
            for record in records
            if record["tag"] == "FAM" and record["xref"]
        ]

        xref_to_person_id = {}
        for xref, record in individuals.items():
            person_id = self._person_id_for_record(xref, record, xref_to_person_id)
            xref_to_person_id[xref] = person_id
            self.people[person_id] = self._person_info_for_record(record)

        for family in families:
            parent_xrefs = family.get("HUSB", []) + family.get("WIFE", [])
            child_xrefs = family.get("CHIL", [])
            parent_ids = [
                self._person_id_for_xref(xref, xref_to_person_id)
                for xref in parent_xrefs
            ]
            child_ids = [
                self._person_id_for_xref(xref, xref_to_person_id)
                for xref in child_xrefs
            ]

            if len(parent_ids) >= 2:
                parent1, parent2 = parent_ids[:2]
                if child_ids:
                    self.marriages.append((parent1, parent2, child_ids))
                else:
                    self.childless_marriages.append((parent1, parent2))
            elif len(parent_ids) == 1:
                for child_id in child_ids:
                    self.single_parent_children.append((parent_ids[0], child_id))

    def _person_id_for_record(self, xref, record, used_ids):
        source_id = first_source_id(record)
        if source_id and source_id.isdigit():
            candidate = int(source_id)
            if candidate not in used_ids.values():
                return candidate

        match = re.search(r"\d+", xref)
        if match:
            candidate = int(match.group(0))
            if candidate not in used_ids.values():
                return candidate

        return self._get_next_unknown_id()

    def _person_id_for_xref(self, xref, xref_to_person_id):
        if xref in xref_to_person_id:
            return xref_to_person_id[xref]

        person_id = self._get_next_unknown_id()
        xref_to_person_id[xref] = person_id
        self.people[person_id] = "?"
        return person_id

    def _person_info_for_record(self, record):
        original = first_prefixed_note(record, "Original:")
        if original:
            return self._normalize_person_info(original)

        name = gedcom_name_to_display(first_value(record, "NAME") or "?")
        birth_date = gedcom_date_to_source_date(first_nested_value(record, "BIRT", "DATE"))
        death_date = gedcom_date_to_source_date(first_nested_value(record, "DEAT", "DATE"))

        if birth_date and death_date:
            return f"{name} ({birth_date}-{death_date})"
        if birth_date:
            return f"{name} ({birth_date})"
        if death_date:
            return f"{name} (...-{death_date})"
        return name


def parse_gedcom_records(path):
    records = []
    current = None
    current_parent_tag = None
    current_text_tag = None

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        parsed = parse_gedcom_line(raw_line)
        if not parsed:
            continue
        level, xref, tag, value = parsed

        if level == 0:
            if current:
                records.append(current)
            current = {"xref": xref, "tag": tag}
            current_parent_tag = None
            current_text_tag = None
            continue

        if current is None:
            continue

        if level == 1:
            current_parent_tag = tag
            current_text_tag = tag if tag in {"NOTE"} else None
            current.setdefault(tag, []).append(value)
        elif level == 2 and current_parent_tag:
            if tag in {"CONC", "CONT"} and current_text_tag:
                append_continuation(current[current_text_tag], value, tag)
            else:
                current.setdefault(current_parent_tag, [])
                current.setdefault(f"{current_parent_tag}.{tag}", []).append(value)
                current_text_tag = tag if tag in {"NOTE"} else None
        elif tag in {"CONC", "CONT"} and current_text_tag:
            append_continuation(current[current_text_tag], value, tag)

    if current:
        records.append(current)
    return records


def parse_gedcom_line(line):
    match = re.match(r"^(\d+)\s+(?:(@[^@]+@)\s+)?([A-Za-z0-9_]+)(?:\s+(.*))?$", line)
    if not match:
        return None
    level = int(match.group(1))
    xref = match.group(2)
    tag = match.group(3)
    value = match.group(4) or ""
    return level, xref, tag, value


def append_continuation(values, value, tag):
    if not values:
        values.append(value)
    elif tag == "CONT":
        values[-1] = f"{values[-1]}\n{value}"
    else:
        values[-1] = f"{values[-1]}{value}"


def first_value(record, tag):
    values = record.get(tag, [])
    return values[0] if values else ""


def first_nested_value(record, parent_tag, child_tag):
    return first_value(record, f"{parent_tag}.{child_tag}")


def first_prefixed_note(record, prefix):
    for note in record.get("NOTE", []):
        if note.startswith(prefix):
            return note[len(prefix):].strip()
    return ""


def first_source_id(record):
    return first_prefixed_note(record, "Source ID:")


def gedcom_name_to_display(value):
    value = " ".join(value.replace("/", " / ").split())
    surname_match = re.search(r"/([^/]*)/", value)
    if not surname_match:
        return value.replace("/", "").strip()

    surname = surname_match.group(1).strip()
    given = (value[:surname_match.start()] + value[surname_match.end():]).strip()
    return " ".join(part for part in [surname, given] if part)


def gedcom_date_to_source_date(value):
    value = (value or "").strip()
    if not value:
        return ""

    year = re.fullmatch(r"\d{4}", value)
    if year:
        return value

    full_date = re.fullmatch(r"(\d{1,2})\s+([A-Z]{3})\s+(\d{4})", value.upper())
    if full_date:
        month = SOURCE_MONTHS.get(full_date.group(2))
        if month:
            return f"{int(full_date.group(1)):02d}.{month}.{full_date.group(3)}"

    return value


SOURCE_MONTHS = {
    "JAN": "01",
    "FEB": "02",
    "MAR": "03",
    "APR": "04",
    "MAY": "05",
    "JUN": "06",
    "JUL": "07",
    "AUG": "08",
    "SEP": "09",
    "OCT": "10",
    "NOV": "11",
    "DEC": "12",
}
