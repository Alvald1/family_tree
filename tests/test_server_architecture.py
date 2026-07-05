import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = PROJECT_ROOT / "site"
sys.path.insert(0, str(SITE_ROOT))

from api.routes import parse_api_path
from config.settings import load_settings
from handlers.http_handler import PersonalDataHandler
from utils.response_utils import setup_cors_headers


class SettingsTest(unittest.TestCase):
    def test_load_settings_reads_site_config_without_losing_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site_root = Path(temp_dir)
            config_dir = site_root / "config"
            config_dir.mkdir()
            (config_dir / "site_config.py").write_text(
                'host = "0.0.0.0"\nport = 8123\ndata_directory = "custom_data"\n',
                encoding="utf-8",
            )

            settings = load_settings(site_root)

            self.assertEqual(settings.host, "0.0.0.0")
            self.assertEqual(settings.port, 8123)
            self.assertEqual(settings.data_dir, site_root.parent.resolve() / "custom_data")
            self.assertEqual(settings.source_file, site_root.parent.resolve() / "source.txt")

    def test_environment_overrides_file_config_for_container_runtime(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            site_root = Path(temp_dir)
            config_dir = site_root / "config"
            config_dir.mkdir()
            (config_dir / "site_config.py").write_text(
                'host = "127.0.0.1"\nport = 9000\ndata_directory = "person_data"\n',
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {
                    "FAMILY_TREE_HOST": "0.0.0.0",
                    "FAMILY_TREE_PORT": "8000",
                    "FAMILY_TREE_DATA_DIR": "/data/person_data",
                    "FAMILY_TREE_SOURCE_FILE": "/data/source.txt",
                },
            ):
                settings = load_settings(site_root)

            self.assertEqual(settings.host, "0.0.0.0")
            self.assertEqual(settings.port, 8000)
            self.assertEqual(settings.data_dir, Path("/data/person_data"))
            self.assertEqual(settings.source_file, Path("/data/source.txt"))


class ApiRoutesTest(unittest.TestCase):
    def test_parse_api_path_ignores_query_string(self):
        self.assertEqual(
            parse_api_path("/api/person/node7/photos?cache=1"),
            ["api", "person", "node7", "photos"],
        )

    def test_parse_api_path_decodes_url_parts(self):
        self.assertEqual(
            parse_api_path("/api/person/node%207/messages"),
            ["api", "person", "node 7", "messages"],
        )


class ResponseHeadersTest(unittest.TestCase):
    def test_same_origin_responses_do_not_allow_all_origins(self):
        class FakeHandler:
            def __init__(self):
                self.headers = []

            def send_header(self, name, value):
                self.headers.append((name, value))

        handler = FakeHandler()

        setup_cors_headers(handler)

        self.assertNotIn(("Access-Control-Allow-Origin", "*"), handler.headers)



class CachePolicyTest(unittest.TestCase):
    def test_static_assets_are_cacheable(self):
        self.assertTrue(PersonalDataHandler.is_cacheable_path("/assets/js/app.js"))
        self.assertTrue(PersonalDataHandler.is_cacheable_path("/assets/css/main.css"))
        self.assertTrue(PersonalDataHandler.is_cacheable_path("/family_tree_vector.svg"))
        self.assertTrue(
            PersonalDataHandler.is_cacheable_path(
                "/person_data/photos/node7/example.jpg"
            )
        )

    def test_html_api_and_json_data_are_not_cacheable(self):
        self.assertFalse(PersonalDataHandler.is_cacheable_path("/"))
        self.assertFalse(PersonalDataHandler.is_cacheable_path("/person.html?id=node7"))
        self.assertFalse(PersonalDataHandler.is_cacheable_path("/api/person/node7"))
        self.assertFalse(
            PersonalDataHandler.is_cacheable_path("/person_data/messages/node7.json")
        )


if __name__ == "__main__":
    unittest.main()
