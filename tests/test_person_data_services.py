import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = PROJECT_ROOT / "site"
sys.path.insert(0, str(SITE_ROOT))

from services.message_service import MessageService
from services.person_service import PersonService
from services.photo_service import PhotoService
from storage.json_store import JsonListStore


class JsonListStoreTest(unittest.TestCase):
    def test_round_trips_lists_and_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = JsonListStore(Path(temp_dir) / "nested")

            store.save("node1", [{"text": "hello"}])

            self.assertEqual(store.load("node1"), [{"text": "hello"}])
            self.assertTrue((Path(temp_dir) / "nested" / "node1.json").exists())

    def test_rejects_unsafe_ids(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = JsonListStore(temp_dir)

            with self.assertRaises(ValueError):
                store.load("../source")


class PersonServiceTest(unittest.TestCase):
    def test_reads_person_by_node_id_from_source_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = Path(temp_dir) / "source.txt"
            source_file.write_text(
                "12 - Иванов Иван Иванович (1901-1980)\n"
                "13 - Петрова Мария (неизвестны)\n",
                encoding="utf-8",
            )

            service = PersonService(source_file=source_file)

            self.assertEqual(
                service.get_person_info("node12"),
                {
                    "id": "node12",
                    "name": "Иванов Иван Иванович",
                    "dates": "1901-1980",
                    "full_info": "Иванов Иван Иванович (1901-1980)",
                },
            )


class MessageServiceTest(unittest.TestCase):
    def test_saves_and_loads_messages_as_json_list(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = MessageService(temp_dir)
            messages = [{"id": "m1", "text": "memo"}]

            service.save_messages("node7", messages)

            self.assertEqual(service.get_messages("node7"), messages)

    def test_rejects_non_list_messages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = MessageService(temp_dir)

            with self.assertRaises(ValueError):
                service.save_messages("node7", {"text": "not a list"})


class PhotoServiceTest(unittest.TestCase):
    def test_uploads_photo_from_multipart_request(self):
        boundary = "----test-boundary"
        image_bytes = b"\x89PNG\r\nsample"
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="photo"; filename="face.png"\r\n'
            "Content-Type: image/png\r\n"
            "\r\n"
        ).encode("utf-8") + image_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

        with tempfile.TemporaryDirectory() as temp_dir:
            service = PhotoService(temp_dir)

            photo = service.upload_photo("node9", body, boundary)

            self.assertEqual(photo["caption"], "face.png")
            self.assertTrue(photo["url"].startswith("/person_data/photos/node9/"))
            self.assertEqual(len(service.get_photos("node9")), 1)
            self.assertTrue((Path(temp_dir) / "node9" / photo["filename"]).exists())

    def test_reorder_rejects_mismatched_photo_count(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = PhotoService(temp_dir)
            (Path(temp_dir) / "node9.json").write_text(
                json.dumps([{"filename": "a.jpg"}, {"filename": "b.jpg"}]),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                service.reorder_photos("node9", new_photos=[{"filename": "a.jpg"}])


if __name__ == "__main__":
    unittest.main()
