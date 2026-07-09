"""Runtime settings for the family tree site."""

import os
import runpy
from dataclasses import dataclass
from pathlib import Path
from auth.yandex_id import AuthConfig, load_auth_config


@dataclass(frozen=True)
class ObjectStorageConfig:
    enabled: bool = False
    bucket: str = ""
    endpoint_url: str = "https://storage.yandexcloud.net"
    access_key_id: str = ""
    secret_access_key: str = ""
    region_name: str = "ru-central1"


@dataclass(frozen=True)
class Settings:
    site_root: Path
    project_root: Path
    host: str = "127.0.0.1"
    port: int = 8000
    data_dir: Path = None
    source_file: Path = None
    auth: AuthConfig = AuthConfig()
    object_storage: ObjectStorageConfig = ObjectStorageConfig()


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
        auth=load_auth_config(),
        object_storage=load_object_storage_config(),
    )


def _project_path(project_root, path_value):
    path = Path(path_value)
    if path.is_absolute():
        return path
    return project_root / path


def load_object_storage_config():
    bucket = os.environ.get("FAMILY_TREE_S3_BUCKET", "").strip()
    if not bucket:
        return ObjectStorageConfig()

    access_key_id = os.environ.get("AWS_ACCESS_KEY_ID", "").strip()
    secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "").strip()
    missing = [
        name
        for name, value in [
            ("AWS_ACCESS_KEY_ID", access_key_id),
            ("AWS_SECRET_ACCESS_KEY", secret_access_key),
        ]
        if not value
    ]
    if missing:
        raise ValueError(
            "S3 object storage is enabled but required credentials are missing: "
            + ", ".join(missing)
        )

    return ObjectStorageConfig(
        enabled=True,
        bucket=bucket,
        endpoint_url=os.environ.get(
            "FAMILY_TREE_S3_ENDPOINT_URL",
            "https://storage.yandexcloud.net",
        ).strip(),
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        region_name=os.environ.get("FAMILY_TREE_S3_REGION", "ru-central1").strip(),
    )
