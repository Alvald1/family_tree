"""Runtime settings for the family tree site."""

import os
import runpy
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    site_root: Path
    project_root: Path
    host: str = "127.0.0.1"
    port: int = 8000
    data_dir: Path = None
    source_file: Path = None


def load_settings(site_root=None):
    site_root = Path(site_root).resolve() if site_root else Path(__file__).resolve().parents[1]
    project_root = site_root.parent
    config_path = site_root / "config" / "site_config.py"

    values = {}
    if config_path.exists():
        values = runpy.run_path(str(config_path))

    data_directory = os.environ.get(
        "FAMILY_TREE_DATA_DIR",
        values.get("data_directory", "person_data"),
    )
    source_file = os.environ.get("FAMILY_TREE_SOURCE_FILE")
    data_dir = _project_path(project_root, data_directory)

    return Settings(
        site_root=site_root,
        project_root=project_root,
        host=os.environ.get("FAMILY_TREE_HOST", values.get("host", "127.0.0.1")),
        port=int(os.environ.get("FAMILY_TREE_PORT", values.get("port", 8000))),
        data_dir=data_dir,
        source_file=_project_path(project_root, source_file or "source.txt"),
    )


def _project_path(project_root, path_value):
    path = Path(path_value)
    if path.is_absolute():
        return path
    return project_root / path
