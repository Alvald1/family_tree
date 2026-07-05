"""
Small JSON-list storage used by person services.

The public API deliberately works with person IDs rather than arbitrary paths:
callers should not be able to escape the configured data directory.
"""

import json
import re
from pathlib import Path


SAFE_RECORD_ID = re.compile(r"^[A-Za-z0-9_-]+$")


def validate_record_id(record_id):
    record_id = str(record_id)
    if not SAFE_RECORD_ID.fullmatch(record_id):
        raise ValueError(f"Unsafe record id: {record_id}")
    return record_id


class JsonListStore:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def load(self, record_id):
        file_path = self._file_path(record_id)
        if not file_path.exists():
            return []

        with file_path.open("r", encoding="utf-8") as source:
            data = json.load(source)

        if isinstance(data, list):
            return data

        raise ValueError(f"Expected a JSON list in {file_path}")

    def save(self, record_id, records):
        if not isinstance(records, list):
            raise ValueError("JsonListStore can only save lists")

        file_path = self._file_path(record_id)
        temp_path = file_path.with_suffix(".json.tmp")

        with temp_path.open("w", encoding="utf-8") as target:
            json.dump(records, target, ensure_ascii=False, indent=2)

        temp_path.replace(file_path)

    def _file_path(self, record_id):
        safe_id = validate_record_id(record_id)
        return self.root_dir / f"{safe_id}.json"
